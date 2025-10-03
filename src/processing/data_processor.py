"""
Processador de dados - Camada Silver
Limpeza, validação e enriquecimento dos dados brutos
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re
from dataclasses import dataclass

from ..config import settings, TSE_DATA_SCHEMAS, DEMOGRAPHIC_MAPPING, WOMEN_KEYWORDS


@dataclass
class DataQualityReport:
    """Relatório de qualidade dos dados"""
    total_records: int
    valid_records: int
    invalid_records: int
    missing_values: Dict[str, int]
    duplicates: int
    quality_score: float
    issues: List[str]


class DataProcessor:
    """Processador principal de dados para camada Silver"""
    
    def __init__(self):
        self.bronze_path = Path(settings.BRONZE_PATH)
        self.silver_path = Path(settings.SILVER_PATH)
        self.silver_path.mkdir(parents=True, exist_ok=True)
    
    def clean_candidate_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, DataQualityReport]:
        """Limpa e valida dados de candidatos"""
        original_count = len(df)
        issues = []
        
        # 1. Limpeza de nomes
        if 'NM_CANDIDATO' in df.columns:
            df['NM_CANDIDATO'] = df['NM_CANDIDATO'].str.strip().str.title()
            df['NM_CANDIDATO_CLEAN'] = df['NM_CANDIDATO'].apply(self._clean_name)
        
        if 'NM_URNA_CANDIDATO' in df.columns:
            df['NM_URNA_CANDIDATO'] = df['NM_URNA_CANDIDATO'].str.strip().str.upper()
        
        # 2. Padronização de gênero
        if 'DS_GENERO' in df.columns:
            df['GENERO'] = df['DS_GENERO'].map(DEMOGRAPHIC_MAPPING['genero'])
            missing_gender = df['GENERO'].isna().sum()
            if missing_gender > 0:
                issues.append(f"{missing_gender} registros com gênero não identificado")
        
        # 3. Padronização de cor/raça
        if 'DS_COR_RACA' in df.columns:
            df['COR_RACA'] = df['DS_COR_RACA'].map(DEMOGRAPHIC_MAPPING['cor_raca'])
            missing_race = df['COR_RACA'].isna().sum()
            if missing_race > 0:
                issues.append(f"{missing_race} registros com cor/raça não identificada")
        
        # 4. Limpeza de valores monetários
        money_columns = ['VR_DESPESA_MAX_CAMPANHA', 'VR_RECEITA', 'VR_DESPESA']
        for col in money_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 5. Padronização de cargos
        if 'DS_CARGO' in df.columns:
            df['CARGO_CATEGORY'] = df['DS_CARGO'].apply(self._categorize_cargo)
        
        # 6. Criação de flags de análise
        df['IS_WOMAN'] = df.get('GENERO') == 'F'
        df['IS_MINORITY_RACE'] = df.get('COR_RACA').isin(['preta', 'parda', 'indigena'])
        
        # 7. Remoção de duplicatas
        duplicates = df.duplicated().sum()
        df = df.drop_duplicates()
        
        # 8. Validação de dados obrigatórios
        required_cols = TSE_DATA_SCHEMAS.get('candidatos', {}).get('required_columns', [])
        missing_required = {}
        for col in required_cols:
            if col in df.columns:
                missing_count = df[col].isna().sum()
                if missing_count > 0:
                    missing_required[col] = missing_count
        
        # Relatório de qualidade
        final_count = len(df)
        quality_report = DataQualityReport(
            total_records=original_count,
            valid_records=final_count,
            invalid_records=original_count - final_count,
            missing_values=missing_required,
            duplicates=duplicates,
            quality_score=self._calculate_quality_score(df, required_cols),
            issues=issues
        )
        
        return df, quality_report
    
    def enrich_candidate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enriquece dados de candidatos com informações adicionais"""
        
        # 1. Análise de nomes para identificar potenciais candidatas mulheres
        df['POTENTIAL_WOMAN_INDICATOR'] = df.apply(self._analyze_name_for_gender, axis=1)
        
        # 2. Score de diversidade
        df['DIVERSITY_SCORE'] = self._calculate_diversity_score(df)
        
        # 3. Categoria de faixa etária (se idade disponível)
        if 'DT_NASCIMENTO' in df.columns:
            df['IDADE'] = self._calculate_age(df['DT_NASCIMENTO'])
            df['FAIXA_ETARIA'] = pd.cut(df['IDADE'], 
                                      bins=[0, 30, 40, 50, 60, 100],
                                      labels=['Até 30', '31-40', '41-50', '51-60', '60+'])
        
        # 4. Indicador de potencial eleitoral feminino
        df['WOMEN_POTENTIAL_SCORE'] = self._calculate_women_potential_score(df)
        
        # 5. Região geográfica (baseada em UE)
        if 'SG_UE' in df.columns:
            df['REGIAO'] = df['SG_UE'].apply(self._map_region)
        
        return df
    
    def process_voting_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Processa dados de votação"""
        
        # Limpeza básica
        df['QT_VOTOS_NOMINAIS'] = pd.to_numeric(df['QT_VOTOS_NOMINAIS'], errors='coerce')
        
        # Cálculo de percentuais
        if 'QT_VOTOS_NOMINAIS' in df.columns:
            df['PERCENTUAL_VOTOS'] = df.groupby('SG_UE')['QT_VOTOS_NOMINAIS'].transform(
                lambda x: (x / x.sum()) * 100
            )
        
        # Performance por gênero
        if 'DS_GENERO' in df.columns:
            df['PERFORMANCE_GENERO'] = df.groupby(['SG_UE', 'DS_GENERO'])['QT_VOTOS_NOMINAIS'].transform('mean')
        
        return df
    
    def create_women_analysis_dataset(self, candidatos_df: pd.DataFrame, votacao_df: pd.DataFrame = None) -> pd.DataFrame:
        """Cria dataset específico para análise de candidaturas femininas"""
        
        # Filtrar apenas candidatas mulheres
        women_df = candidatos_df[candidatos_df['IS_WOMAN'] == True].copy()
        
        # Juntar com dados de votação se disponível
        if votacao_df is not None:
            women_df = women_df.merge(
                votacao_df[['NM_CANDIDATO', 'SG_UE', 'QT_VOTOS_NOMINAIS', 'PERCENTUAL_VOTOS']], 
                on=['NM_CANDIDATO', 'SG_UE'], 
                how='left'
            )
        
        # Análises específicas para mulheres
        women_df['SUCCESS_INDICATOR'] = self._calculate_success_indicator(women_df)
        women_df['MARKETING_POTENTIAL'] = self._calculate_marketing_potential(women_df)
        
        return women_df
    
    def _clean_name(self, name: str) -> str:
        """Limpa e padroniza nomes"""
        if pd.isna(name):
            return ""
        
        # Remove caracteres especiais
        clean_name = re.sub(r'[^\w\s]', '', str(name))
        # Remove espaços extras
        clean_name = ' '.join(clean_name.split())
        return clean_name.title()
    
    def _categorize_cargo(self, cargo: str) -> str:
        """Categoriza cargos por nível"""
        if pd.isna(cargo):
            return "OUTROS"
        
        cargo_upper = cargo.upper()
        
        if any(term in cargo_upper for term in ['PRESIDENTE', 'VICE-PRESIDENTE']):
            return "EXECUTIVO_FEDERAL"
        elif any(term in cargo_upper for term in ['GOVERNADOR', 'VICE-GOVERNADOR']):
            return "EXECUTIVO_ESTADUAL"
        elif any(term in cargo_upper for term in ['PREFEITO', 'VICE-PREFEITO']):
            return "EXECUTIVO_MUNICIPAL"
        elif 'SENADOR' in cargo_upper:
            return "LEGISLATIVO_FEDERAL"
        elif 'DEPUTADO FEDERAL' in cargo_upper:
            return "LEGISLATIVO_FEDERAL"
        elif 'DEPUTADO ESTADUAL' in cargo_upper or 'DEPUTADO DISTRITAL' in cargo_upper:
            return "LEGISLATIVO_ESTADUAL"
        elif 'VEREADOR' in cargo_upper:
            return "LEGISLATIVO_MUNICIPAL"
        else:
            return "OUTROS"
    
    def _analyze_name_for_gender(self, row) -> float:
        """Analisa nome para indicar probabilidade de ser mulher"""
        if pd.isna(row.get('NM_CANDIDATO')):
            return 0.0
        
        name = str(row['NM_CANDIDATO']).lower()
        
        # Terminações tipicamente femininas
        feminine_endings = ['a', 'ana', 'ina', 'lia', 'cia', 'ria', 'na', 'ta']
        feminine_score = sum(1 for ending in feminine_endings if name.endswith(ending))
        
        # Nomes tipicamente femininos
        feminine_names = ['maria', 'ana', 'joana', 'carla', 'paula', 'lucia', 'cristina']
        name_score = sum(1 for fname in feminine_names if fname in name)
        
        return min((feminine_score + name_score) / 5, 1.0)
    
    def _calculate_diversity_score(self, df: pd.DataFrame) -> pd.Series:
        """
        Calcula score de diversidade de forma justa e transparente
        
        Critérios objetivos (sem viés racial):
        - Representatividade regional (25%)
        - Experiência política (30%) 
        - Formação acadêmica (20%)
        - Histórico de diversidade (25%)
        """
        score = pd.Series(0.0, index=df.index)
        
        # 1. Representatividade Regional (0-0.25)
        if 'REGIAO' in df.columns:
            underrepresented_regions = ['NORTE', 'NORDESTE', 'CENTRO-OESTE']
            score += df['REGIAO'].isin(underrepresented_regions).astype(int) * 0.25
            score += (~df['REGIAO'].isin(underrepresented_regions)).astype(int) * 0.15
        
        # 2. Experiência Política por tipo de cargo (0-0.3)
        if 'CARGO_CATEGORY' in df.columns:
            experience_weights = {
                'EXECUTIVO_MUNICIPAL': 0.3,  # Prefeito
                'LEGISLATIVO_FEDERAL': 0.25,  # Senador/Dep Federal
                'LEGISLATIVO_ESTADUAL': 0.2,  # Deputado Estadual
                'EXECUTIVO_ESTADUAL': 0.3,   # Governador
            }
            
            for cargo, weight in experience_weights.items():
                score += (df['CARGO_CATEGORY'] == cargo).astype(int) * weight
        
        # 3. Formação Acadêmica (0-0.2)
        if 'GRAU_INSTRUCAO' in df.columns:
            education_weights = {
                'SUPERIOR COMPLETO': 0.2,
                'SUPERIOR INCOMPLETO': 0.15,
                'ENSINO MÉDIO COMPLETO': 0.1,
                'ENSINO MÉDIO INCOMPLETO': 0.05
            }
            
            for education, weight in education_weights.items():
                score += (df['GRAU_INSTRUCAO'] == education).astype(int) * weight
        
        # 4. Histórico de Diversidade baseado na ocupação (0-0.25)
        if 'OCUPACAO' in df.columns:
            diversity_occupations = [
                'PROFESSOR', 'EDUCADOR', 'ASSISTENTE SOCIAL', 
                'ADVOGADO', 'JORNALISTA', 'PSICÓLOGO',
                'SERVIDOR PÚBLICO', 'LÍDER COMUNITÁRIO'
            ]
            
            # Verifica se a ocupação está relacionada com causas sociais
            diversity_mask = df['OCUPACAO'].str.upper().str.contains('|'.join(diversity_occupations), na=False)
            score += diversity_mask.astype(int) * 0.25
            score += (~diversity_mask).astype(int) * 0.1  # Outras ocupações
        
        # Normalizar para escala 0-1
        return score.clip(0, 1)
    
    def _calculate_age(self, birth_dates: pd.Series) -> pd.Series:
        """Calcula idade baseada na data de nascimento"""
        birth_dates = pd.to_datetime(birth_dates, errors='coerce')
        current_year = datetime.now().year
        return current_year - birth_dates.dt.year
    
    def _map_region(self, ue_code: str) -> str:
        """Mapeia código UE para região"""
        if pd.isna(ue_code):
            return "DESCONHECIDO"
        
        # Mapeamento básico por estado (primeiros 2 dígitos)
        state_code = str(ue_code)[:2] if len(str(ue_code)) >= 2 else "00"
        
        region_mapping = {
            # Norte
            '11': 'NORTE', '12': 'NORTE', '13': 'NORTE', '14': 'NORTE',
            '15': 'NORTE', '16': 'NORTE', '17': 'NORTE',
            # Nordeste
            '21': 'NORDESTE', '22': 'NORDESTE', '23': 'NORDESTE', '24': 'NORDESTE',
            '25': 'NORDESTE', '26': 'NORDESTE', '27': 'NORDESTE', '28': 'NORDESTE',
            '29': 'NORDESTE',
            # Sudeste
            '31': 'SUDESTE', '32': 'SUDESTE', '33': 'SUDESTE', '35': 'SUDESTE',
            # Sul
            '41': 'SUL', '42': 'SUL', '43': 'SUL',
            # Centro-Oeste
            '50': 'CENTRO_OESTE', '51': 'CENTRO_OESTE', '52': 'CENTRO_OESTE', '53': 'CENTRO_OESTE'
        }
        
        return region_mapping.get(state_code, 'OUTROS')
    
    def _calculate_women_potential_score(self, df: pd.DataFrame) -> pd.Series:
        """Calcula score de potencial para candidaturas femininas"""
        score = pd.Series(0.0, index=df.index)
        
        # Base score para mulheres
        if 'IS_WOMAN' in df.columns:
            score += df['IS_WOMAN'].astype(int) * 0.5
        
        # Score por educação
        if 'DS_GRAU_INSTRUCAO' in df.columns:
            education_score = df['DS_GRAU_INSTRUCAO'].str.contains(
                'SUPERIOR|MESTRADO|DOUTORADO', na=False
            ).astype(int) * 0.2
            score += education_score
        
        # Score por recursos financeiros
        if 'VR_DESPESA_MAX_CAMPANHA' in df.columns:
            financial_score = (df['VR_DESPESA_MAX_CAMPANHA'] > df['VR_DESPESA_MAX_CAMPANHA'].median()).astype(int) * 0.2
            score += financial_score
        
        # Score por cargo (executivo tem maior potencial)
        if 'CARGO_CATEGORY' in df.columns:
            executive_score = df['CARGO_CATEGORY'].str.contains('EXECUTIVO', na=False).astype(int) * 0.1
            score += executive_score
        
        return score
    
    def _calculate_success_indicator(self, df: pd.DataFrame) -> pd.Series:
        """Calcula indicador de sucesso eleitoral"""
        if 'QT_VOTOS_NOMINAIS' in df.columns:
            # Sucesso baseado em estar acima da mediana de votos
            median_votes = df['QT_VOTOS_NOMINAIS'].median()
            return (df['QT_VOTOS_NOMINAIS'] > median_votes).astype(int)
        return pd.Series(0, index=df.index)
    
    def _calculate_marketing_potential(self, df: pd.DataFrame) -> pd.Series:
        """Calcula potencial de marketing"""
        potential = pd.Series(0.0, index=df.index)
        
        # Mulheres jovens têm maior potencial
        if 'IDADE' in df.columns:
            potential += (df['IDADE'] <= 40).astype(int) * 0.3
        
        # Diversidade racial
        if 'IS_MINORITY_RACE' in df.columns:
            potential += df['IS_MINORITY_RACE'].astype(int) * 0.3
        
        # Educação superior
        if 'DS_GRAU_INSTRUCAO' in df.columns:
            potential += df['DS_GRAU_INSTRUCAO'].str.contains(
                'SUPERIOR', na=False
            ).astype(int) * 0.2
        
        # Performance eleitoral prévia
        potential += df.get('SUCCESS_INDICATOR', 0) * 0.2
        
        return potential
    
    def _calculate_quality_score(self, df: pd.DataFrame, required_cols: List[str]) -> float:
        """Calcula score de qualidade dos dados"""
        if not required_cols:
            return 1.0
        
        available_cols = [col for col in required_cols if col in df.columns]
        completeness = len(available_cols) / len(required_cols)
        
        # Calcula completude dos dados
        if available_cols:
            missing_ratio = df[available_cols].isna().sum().sum() / (len(df) * len(available_cols))
            data_quality = 1 - missing_ratio
        else:
            data_quality = 0
        
        return (completeness + data_quality) / 2
    
    def save_processed_data(self, df: pd.DataFrame, filename: str, quality_report: DataQualityReport = None):
        """Salva dados processados na camada Silver"""
        output_path = self.silver_path / f"{filename}.parquet"
        df.to_parquet(output_path, index=False)
        
        # Salva relatório de qualidade
        if quality_report:
            report_path = self.silver_path / f"{filename}_quality_report.json"
            import json
            with open(report_path, 'w') as f:
                json.dump({
                    'total_records': quality_report.total_records,
                    'valid_records': quality_report.valid_records,
                    'invalid_records': quality_report.invalid_records,
                    'missing_values': quality_report.missing_values,
                    'duplicates': quality_report.duplicates,
                    'quality_score': quality_report.quality_score,
                    'issues': quality_report.issues,
                    'processed_at': datetime.now().isoformat()
                }, f, indent=2)
        
        print(f"Saved processed data to {output_path}")


# Função principal de processamento
def process_all_data():
    """Processa todos os dados da camada Bronze para Silver"""
    processor = DataProcessor()
    
    # Processar dados por ano
    for year in settings.ELECTION_YEARS_MAJOR + settings.ELECTION_YEARS_LOCAL:
        year_bronze_path = processor.bronze_path / "tse" / str(year)
        
        if year_bronze_path.exists():
            # Processar candidatos
            candidatos_files = list(year_bronze_path.glob("**/candidatos*.parquet"))
            for file_path in candidatos_files:
                df = pd.read_parquet(file_path)
                processed_df, quality_report = processor.clean_candidate_data(df)
                enriched_df = processor.enrich_candidate_data(processed_df)
                
                filename = f"candidatos_{year}_processed"
                processor.save_processed_data(enriched_df, filename, quality_report)
    
    print("Data processing completed!")


if __name__ == "__main__":
    process_all_data()
"""
Conector avançado para dados do TSE
Busca dados reais de candidaturas diretamente do portal do TSE
"""
import requests
import pandas as pd
import json
import zipfile
import io
from pathlib import Path
from typing import List, Dict, Optional
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TSEConnector:
    """Cliente avançado para acessar dados reais do TSE"""
    
    def __init__(self):
        self.base_url = "https://dadosabertos.tse.jus.br/dataset"
        self.cdn_url = "https://cdn.tse.jus.br/estatistica/sead/odsele"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_available_elections(self) -> List[Dict]:
        """Lista eleições disponíveis com URLs atualizadas"""
        elections = [
            {
                "year": 2022,
                "type": "Eleições Gerais",
                "description": "Presidente, Governador, Senador, Deputados",
                "url_candidates": f"{self.cdn_url}/consulta_cand/consulta_cand_2022.zip",
                "url_votes": f"{self.cdn_url}/votacao_candidato_munzona/votacao_candidato_munzona_2022.zip"
            },
            {
                "year": 2020, 
                "type": "Eleições Municipais",
                "description": "Prefeito, Vereador",
                "url_candidates": f"{self.cdn_url}/consulta_cand/consulta_cand_2020.zip",
                "url_votes": f"{self.cdn_url}/votacao_candidato_munzona/votacao_candidato_munzona_2020.zip"
            },
            {
                "year": 2018,
                "type": "Eleições Gerais", 
                "description": "Presidente, Governador, Senador, Deputados",
                "url_candidates": f"{self.cdn_url}/consulta_cand/consulta_cand_2018.zip",
                "url_votes": f"{self.cdn_url}/votacao_candidato_munzona/votacao_candidato_munzona_2018.zip"
            }
        ]
        return elections
    
    def test_tse_connection(self) -> bool:
        """Testa conexão com o TSE"""
        try:
            response = self.session.get("https://www.tse.jus.br", timeout=10)
            logger.info(f"✅ Conexão TSE OK - Status: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ Erro na conexão TSE: {e}")
            return False
    
    def download_and_extract_zip(self, url: str, extract_to: str) -> List[str]:
        """
        Baixa e extrai arquivo ZIP do TSE
        
        Returns:
            Lista de arquivos extraídos
        """
        try:
            logger.info(f"📥 Baixando dados de: {url}")
            
            response = self.session.get(url, timeout=60)
            response.raise_for_status()
            
            logger.info(f"✅ Download concluído - {len(response.content) / 1024 / 1024:.1f} MB")
            
            # Extrair ZIP em memória
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
                extract_path = Path(extract_to)
                extract_path.mkdir(parents=True, exist_ok=True)
                
                extracted_files = []
                for file_info in zip_file.filelist:
                    if file_info.filename.endswith('.csv'):
                        zip_file.extract(file_info, extract_path)
                        extracted_files.append(str(extract_path / file_info.filename))
                        logger.info(f"📄 Extraído: {file_info.filename}")
                
                return extracted_files
                
        except Exception as e:
            logger.error(f"❌ Erro no download/extração: {e}")
            return []
    
    def load_candidates_csv(self, csv_path: str, sample_size: Optional[int] = None) -> pd.DataFrame:
        """
        Carrega CSV de candidatos do TSE
        
        Args:
            csv_path: Caminho para o arquivo CSV
            sample_size: Número de linhas para carregar (None = todas)
        """
        try:
            logger.info(f"📊 Carregando CSV: {csv_path}")
            
            # Tentar diferentes encodings
            encodings = ['latin1', 'utf-8', 'cp1252']
            
            for encoding in encodings:
                try:
                    if sample_size:
                        df = pd.read_csv(csv_path, encoding=encoding, sep=';', nrows=sample_size)
                    else:
                        df = pd.read_csv(csv_path, encoding=encoding, sep=';')
                    
                    logger.info(f"✅ CSV carregado com encoding {encoding}: {len(df)} linhas, {len(df.columns)} colunas")
                    return df
                    
                except UnicodeDecodeError:
                    continue
            
            raise ValueError("Não foi possível decodificar o arquivo com os encodings testados")
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar CSV: {e}")
            return pd.DataFrame()
    
    def filter_women_candidates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filtra apenas candidatas mulheres"""
        try:
            # Identificar coluna de gênero (pode variar)
            gender_columns = ['DS_GENERO', 'GENERO', 'SEXO', 'CD_GENERO']
            gender_col = None
            
            for col in gender_columns:
                if col in df.columns:
                    gender_col = col
                    break
            
            if not gender_col:
                logger.warning("⚠️ Coluna de gênero não encontrada")
                return df
            
            # Filtrar mulheres
            women_df = df[df[gender_col].isin(['FEMININO', 'F', '4', 4])].copy()
            
            logger.info(f"👩 Candidatas mulheres: {len(women_df)} de {len(df)} ({len(women_df)/len(df)*100:.1f}%)")
            
            return women_df
            
        except Exception as e:
            logger.error(f"❌ Erro ao filtrar mulheres: {e}")
            return df
    
    def standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Padroniza nomes das colunas para nosso sistema"""
        try:
            # Mapeamento de colunas TSE para nosso padrão
            column_mapping = {
                'NM_CANDIDATO': 'name',
                'NM_URNA_CANDIDATO': 'ballot_name', 
                'NR_CPF_CANDIDATO': 'cpf',
                'DS_GENERO': 'gender',
                'DS_COR_RACA': 'race',
                'DS_GRAU_INSTRUCAO': 'education',
                'DS_OCUPACAO': 'occupation',
                'DS_CARGO': 'cargo',
                'SG_UE': 'state',
                'NM_UE': 'city',
                'NR_ANO_ELEICAO': 'election_year',
                'SG_UF': 'state_code'
            }
            
            # Renomear colunas que existem
            df_renamed = df.rename(columns=column_mapping)
            
            # Adicionar colunas derivadas
            if 'gender' in df_renamed.columns:
                df_renamed['is_woman'] = df_renamed['gender'].isin(['FEMININO', 'F'])
            
            if 'race' in df_renamed.columns:
                minority_races = ['PRETA', 'PARDA', 'INDÍGENA', 'AMARELA']
                df_renamed['is_minority_race'] = df_renamed['race'].isin(minority_races)
            
            # Mapear região por estado
            if 'state_code' in df_renamed.columns:
                df_renamed['region'] = df_renamed['state_code'].map(self._get_region_mapping())
            
            logger.info(f"📋 Colunas padronizadas: {list(df_renamed.columns)}")
            
            return df_renamed
            
        except Exception as e:
            logger.error(f"❌ Erro na padronização: {e}")
            return df
    
    def _get_region_mapping(self) -> Dict[str, str]:
        """Mapeia códigos de estado para regiões"""
        return {
            # Norte
            'AC': 'NORTE', 'AP': 'NORTE', 'AM': 'NORTE', 'PA': 'NORTE', 
            'RO': 'NORTE', 'RR': 'NORTE', 'TO': 'NORTE',
            # Nordeste
            'AL': 'NORDESTE', 'BA': 'NORDESTE', 'CE': 'NORDESTE', 'MA': 'NORDESTE',
            'PB': 'NORDESTE', 'PE': 'NORDESTE', 'PI': 'NORDESTE', 'RN': 'NORDESTE', 'SE': 'NORDESTE',
            # Centro-Oeste
            'GO': 'CENTRO-OESTE', 'MT': 'CENTRO-OESTE', 'MS': 'CENTRO-OESTE', 'DF': 'CENTRO-OESTE',
            # Sudeste
            'ES': 'SUDESTE', 'MG': 'SUDESTE', 'RJ': 'SUDESTE', 'SP': 'SUDESTE',
            # Sul
            'PR': 'SUL', 'RS': 'SUL', 'SC': 'SUL'
        }
    
    def _calculate_fair_diversity_score(self, df: pd.DataFrame) -> pd.Series:
        """
        Calcula score de diversidade baseado em critérios justos
        
        Critérios objetivos:
        - Representação regional (25%)
        - Experiência política (30%) 
        - Formação acadêmica (20%)
        - Histórico em diversidade (25%)
        """
        scores = pd.Series(0.0, index=df.index)
        
        try:
            # 1. Representação Regional (25%)
            if 'region' in df.columns:
                # Regiões sub-representadas têm peso maior
                region_weights = {
                    'NORTE': 1.0,
                    'NORDESTE': 0.9,
                    'CENTRO-OESTE': 1.0,
                    'SUDESTE': 0.7,
                    'SUL': 0.8
                }
                regional_score = df['region'].map(region_weights).fillna(0.5)
                scores += regional_score * 0.25
            
            # 2. Experiência Política (30%)
            if 'cargo' in df.columns:
                # Cargos executivos e legislativos têm peso maior
                position_weights = {
                    'PRESIDENTE': 1.0,
                    'GOVERNADOR': 0.9,
                    'SENADOR': 0.8,
                    'DEPUTADO FEDERAL': 0.7,
                    'DEPUTADO ESTADUAL': 0.6,
                    'PREFEITO': 0.5,
                    'VEREADOR': 0.4
                }
                experience_score = df['cargo'].map(position_weights).fillna(0.3)
                scores += experience_score * 0.30
            
            # 3. Formação Acadêmica (20%)
            if 'education' in df.columns:
                education_weights = {
                    'SUPERIOR COMPLETO': 1.0,
                    'PÓS-GRADUAÇÃO': 1.0,
                    'MESTRADO': 1.0,
                    'DOUTORADO': 1.0,
                    'SUPERIOR INCOMPLETO': 0.8,
                    'ENSINO MÉDIO COMPLETO': 0.6,
                    'ENSINO MÉDIO INCOMPLETO': 0.4,
                    'ENSINO FUNDAMENTAL COMPLETO': 0.3,
                    'ENSINO FUNDAMENTAL INCOMPLETO': 0.2
                }
                education_score = df['education'].map(education_weights).fillna(0.5)
                scores += education_score * 0.20
            
            # 4. Diversidade e Inclusão (25%)
            diversity_score = 0.0
            
            # Raça/Etnia (histórico de sub-representação)
            if 'is_minority_race' in df.columns:
                diversity_score += df['is_minority_race'].astype(float) * 0.15
            
            # Ocupação (áreas relacionadas a direitos e inclusão)
            if 'occupation' in df.columns:
                inclusion_occupations = [
                    'ADVOGADO', 'PROFESSOR', 'ASSISTENTE SOCIAL', 
                    'JORNALISTA', 'MÉDICO', 'PSICÓLOGO'
                ]
                occupation_diversity = df['occupation'].isin(inclusion_occupations).astype(float)
                diversity_score += occupation_diversity * 0.10
            
            scores += diversity_score
            
            # Normalizar scores entre 0 e 1
            if scores.max() > 0:
                scores = scores / scores.max()
            
            return scores.round(2)
            
        except Exception as e:
            logger.error(f"❌ Erro no cálculo de score: {e}")
            return pd.Series(0.5, index=df.index)

    def export_to_api_format(self, df: pd.DataFrame) -> List[Dict]:
        """
        Converte dados TSE para formato da nossa API
        
        Returns:
            Lista de candidatas no formato esperado
        """
        try:
            candidates = []
            
            for _, row in df.iterrows():
                candidate = {
                    "id": len(candidates) + 1,
                    "name": row.get('name', 'Nome não informado'),
                    "age": self._estimate_age(row),
                    "education": self._normalize_education(row.get('education', '')),
                    "political_experience": self._extract_experience(row),
                    "region": row.get('region', 'NÃO INFORMADO'),
                    "diversity_score": float(row.get('diversity_score', 0.5)),
                    "social_media_engagement": self._estimate_engagement(row),
                    "policy_areas": self._extract_policy_areas(row),
                    "source": "TSE",
                    "election_year": int(row.get('election_year', 2022)),
                    "raw_data": {
                        "ballot_name": row.get('ballot_name', ''),
                        "race": row.get('race', ''),
                        "occupation": row.get('occupation', ''),
                        "state": row.get('state_code', ''),
                        "city": row.get('city', '')
                    }
                }
                
                candidates.append(candidate)
            
            logger.info(f"📋 Convertidos {len(candidates)} candidatas para formato API")
            return candidates
            
        except Exception as e:
            logger.error(f"❌ Erro na exportação: {e}")
            return []
    
    def _estimate_age(self, row: pd.Series) -> int:
        """Estima idade baseada em dados disponíveis"""
        # Implementação simplificada - pode ser melhorada com data de nascimento
        current_year = datetime.now().year
        election_year = row.get('election_year', 2022)
        
        # Estimativa baseada em experiência política
        experience = row.get('cargo', '')
        if 'DEPUTADO' in experience or 'SENADOR' in experience:
            return 45  # Estimativa para legislativo
        elif 'PREFEITO' in experience or 'GOVERNADOR' in experience:
            return 50  # Estimativa para executivo
        else:
            return 40  # Estimativa padrão
    
    def _normalize_education(self, education: str) -> str:
        """Normaliza nível de educação"""
        education = str(education).upper()
        
        if any(term in education for term in ['SUPERIOR', 'GRADUAÇÃO', 'UNIVERSITÁRIO']):
            return "Ensino Superior"
        elif any(term in education for term in ['PÓS', 'MESTRADO', 'DOUTORADO', 'ESPECIALIZAÇÃO']):
            return "Pós-graduação"
        elif 'MÉDIO' in education:
            return "Ensino Médio"
        elif 'FUNDAMENTAL' in education:
            return "Ensino Fundamental"
        else:
            return "Não informado"
    
    def _extract_experience(self, row: pd.Series) -> str:
        """Extrai experiência política"""
        cargo = row.get('cargo', '')
        occupation = row.get('occupation', '')
        
        if cargo and cargo != 'nan':
            return f"Candidata a {cargo}"
        elif occupation and occupation != 'nan':
            return f"Atuação como {occupation}"
        else:
            return "Experiência não informada"
    
    def _estimate_engagement(self, row: pd.Series) -> int:
        """Estima engajamento em redes sociais"""
        # Estimativa baseada em cargo e região
        cargo = row.get('cargo', '')
        region = row.get('region', '')
        
        base_score = 1000
        
        # Cargos de maior visibilidade
        if any(term in cargo for term in ['PRESIDENTE', 'GOVERNADOR', 'SENADOR']):
            base_score *= 5
        elif 'DEPUTADO FEDERAL' in cargo:
            base_score *= 3
        elif 'DEPUTADO ESTADUAL' in cargo:
            base_score *= 2
        
        # Regiões com mais acesso digital
        if region in ['SUDESTE', 'SUL']:
            base_score *= 1.5
        
        return min(base_score, 50000)  # Máximo 50k
    
    def _extract_policy_areas(self, row: pd.Series) -> List[str]:
        """Extrai áreas de política baseadas na ocupação"""
        occupation = str(row.get('occupation', '')).upper()
        
        policy_mapping = {
            'PROFESSOR': ['Educação', 'Direitos Humanos'],
            'MÉDICO': ['Saúde', 'Bem-estar Social'],
            'ADVOGADO': ['Justiça', 'Direitos Humanos'],
            'ASSISTENTE SOCIAL': ['Assistência Social', 'Direitos Humanos'],
            'JORNALISTA': ['Comunicação', 'Transparência'],
            'EMPRESÁRIO': ['Economia', 'Desenvolvimento'],
            'AGRICULTOR': ['Meio Ambiente', 'Desenvolvimento Rural']
        }
        
        for job, areas in policy_mapping.items():
            if job in occupation:
                return areas
        
        return ['Desenvolvimento Social', 'Direitos das Mulheres']

    def fetch_real_data(self, year: int = 2022, limit: Optional[int] = 1000) -> pd.DataFrame:
        """
        Busca dados reais do TSE para um ano específico
        
        Args:
            year: Ano da eleição
            limit: Limite de registros (None = todos)
            
        Returns:
            DataFrame com candidatas mulheres
        """
        try:
            logger.info(f"🔍 Buscando dados reais do TSE - Eleições {year}")
            
            # Verificar conexão
            if not self.test_tse_connection():
                logger.error("❌ Falha na conexão com TSE")
                return pd.DataFrame()
            
            # Obter informações da eleição
            elections = self.get_available_elections()
            election = next((e for e in elections if e['year'] == year), None)
            
            if not election:
                logger.error(f"❌ Eleição {year} não encontrada")
                return pd.DataFrame()
            
            # Criar diretório temporário
            temp_dir = f"data/bronze/tse_{year}"
            
            # Baixar e extrair dados
            extracted_files = self.download_and_extract_zip(
                election['url_candidates'], 
                temp_dir
            )
            
            if not extracted_files:
                logger.error("❌ Nenhum arquivo extraído")
                return pd.DataFrame()
            
            # Processar cada arquivo CSV
            all_candidates = []
            
            for csv_file in extracted_files:
                df_raw = self.load_candidates_csv(csv_file, sample_size=limit)
                
                if df_raw.empty:
                    continue
                
                # Filtrar mulheres
                df_women = self.filter_women_candidates(df_raw)
                
                # Padronizar colunas
                df_standardized = self.standardize_columns(df_women)
                
                all_candidates.append(df_standardized)
            
            # Combinar todos os dados
            if all_candidates:
                final_df = pd.concat(all_candidates, ignore_index=True)
                
                # Calcular score de diversidade com sistema justo
                final_df['diversity_score'] = self._calculate_fair_diversity_score(final_df)
                
                logger.info(f"🎉 Dados processados: {len(final_df)} candidatas mulheres")
                
                return final_df.head(limit) if limit else final_df
            else:
                logger.warning("⚠️ Nenhum dado processado")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"❌ Erro na busca de dados: {e}")
            return pd.DataFrame()

# Funções utilitárias para integração
def test_tse_integration():
    """Testa integração completa com TSE"""
    print("🔍 Testando integração TSE...")
    
    connector = TSEConnector()
    
    # Teste de conexão
    if not connector.test_tse_connection():
        print("❌ Falha na conexão")
        return False
    
    # Buscar amostra de dados
    df = connector.fetch_real_data(year=2022, limit=100)
    
    if df.empty:
        print("❌ Nenhum dado encontrado")
        return False
    
    print(f"✅ Dados carregados: {len(df)} registros")
    print(f"📊 Colunas: {list(df.columns)}")
    
    # Converter para formato API
    candidates = connector.export_to_api_format(df)
    
    if candidates:
        print(f"🎉 Integração TSE funcionando! {len(candidates)} candidatas processadas")
        
        # Mostrar exemplo
        if candidates:
            example = candidates[0]
            print(f"\n📋 Exemplo de candidata:")
            print(f"   Nome: {example['name']}")
            print(f"   Região: {example['region']}")
            print(f"   Score: {example['diversity_score']}")
            print(f"   Experiência: {example['political_experience']}")
        
        return True
    else:
        print("❌ Falha na conversão de dados")
        return False

if __name__ == "__main__":
    test_tse_integration()
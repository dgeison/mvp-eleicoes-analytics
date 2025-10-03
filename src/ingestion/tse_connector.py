"""
Conector básico para dados do TSE
Primeira versão para buscar dados reais de candidatos
"""
import requests
import pandas as pd
import json
from pathlib import Path
from typing import List, Dict, Optional

class TSEConnector:
    """Cliente para acessar dados do TSE"""
    
    def __init__(self):
        self.base_url = "https://dadosabertos.tse.jus.br/dataset"
        self.session = requests.Session()
    
    def get_available_elections(self) -> List[Dict]:
        """Lista eleições disponíveis"""
        # URLs conhecidas para dados do TSE
        elections = [
            {
                "year": 2022,
                "type": "Eleições Gerais",
                "url_candidates": "https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/consulta_cand_2022.zip"
            },
            {
                "year": 2020, 
                "type": "Eleições Municipais",
                "url_candidates": "https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/consulta_cand_2020.zip"
            }
        ]
        return elections
    
    def download_candidates_data(self, year: int, save_path: str = "data/bronze") -> bool:
        """
        Baixa dados de candidatos do TSE
        
        Args:
            year: Ano da eleição
            save_path: Caminho para salvar os dados
            
        Returns:
            bool: True se sucesso, False caso contrário
        """
        try:
            elections = self.get_available_elections()
            election = next((e for e in elections if e['year'] == year), None)
            
            if not election:
                print(f"❌ Eleição de {year} não encontrada")
                return False
            
            print(f"📥 Baixando dados de candidatos de {year}...")
            
            # Criar diretório se não existir
            Path(save_path).mkdir(parents=True, exist_ok=True)
            
            # Download do arquivo
            response = self.session.get(election['url_candidates'], stream=True)
            response.raise_for_status()
            
            file_path = Path(save_path) / f"candidatos_{year}.zip"
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✅ Dados salvos em: {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao baixar dados: {str(e)}")
            return False
    
    def parse_candidates_csv(self, csv_path: str) -> pd.DataFrame:
        """
        Processa arquivo CSV de candidatos do TSE
        
        Args:
            csv_path: Caminho para o arquivo CSV
            
        Returns:
            DataFrame com dados processados
        """
        try:
            # Ler CSV com encoding correto
            df = pd.read_csv(csv_path, encoding='latin1', delimiter=';')
            
            # Mapeamento de colunas TSE para nosso schema
            column_mapping = {
                'NM_CANDIDATO': 'name',
                'NM_URNA_CANDIDATO': 'ballot_name', 
                'NR_CPF_CANDIDATO': 'cpf',
                'DS_GENERO': 'gender',
                'DS_COR_RACA': 'race',
                'DS_GRAU_INSTRUCAO': 'education',
                'DS_OCUPACAO': 'occupation',
                'DS_CARGO': 'cargo',
                'SG_UF': 'state',
                'NM_MUNICIPIO': 'city',
                'ANO_ELEICAO': 'election_year'
            }
            
            # Selecionar e renomear colunas
            available_cols = [col for col in column_mapping.keys() if col in df.columns]
            df_filtered = df[available_cols].copy()
            df_filtered = df_filtered.rename(columns=column_mapping)
            
            # Limpeza básica
            df_filtered['gender'] = df_filtered['gender'].map({
                'FEMININO': 'F',
                'MASCULINO': 'M'
            })
            
            # Filtrar apenas mulheres
            df_women = df_filtered[df_filtered['gender'] == 'F'].copy()
            
            # Adicionar campos calculados
            df_women['is_woman'] = True
            df_women['is_minority_race'] = df_women['race'].isin(['PRETA', 'PARDA', 'INDÍGENA'])
            
            # Calcular score de diversidade básico
            df_women['diversity_score'] = 0.5  # Placeholder
            df_women.loc[df_women['is_minority_race'], 'diversity_score'] += 0.3
            
            print(f"✅ Processados {len(df_women)} candidatas mulheres")
            return df_women
            
        except Exception as e:
            print(f"❌ Erro ao processar CSV: {str(e)}")
            return pd.DataFrame()

def main():
    """Função principal para testar o conector"""
    connector = TSEConnector()
    
    print("🔗 TSE Connector - Teste")
    print("=" * 30)
    
    # Listar eleições disponíveis
    elections = connector.get_available_elections()
    print("📊 Eleições disponíveis:")
    for election in elections:
        print(f"  - {election['year']}: {election['type']}")
    
    print("\n💡 Para baixar dados:")
    print("connector.download_candidates_data(2022)")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Script para baixar dados reais de votação do TSE
Eleições 2022 - Resultados por candidata
"""

import requests
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import zipfile
import tempfile
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# URLs dos dados do TSE (Eleições 2022)
TSE_URLS = {
    'candidatos': 'https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/consulta_cand_2022.zip',
    'votacao_candidato': 'https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_candidato_munzona/votacao_candidato_munzona_2022.zip'
}

def conectar_bd():
    """Conectar ao banco PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            port='5432',
            database='eleicoes_analytics',
            user='postgres',
            password='postgres123'
        )
        return conn
    except Exception as e:
        logger.error(f"Erro ao conectar ao BD: {e}")
        return None

def baixar_arquivo_tse(url, nome_arquivo):
    """Baixar arquivo do TSE"""
    try:
        logger.info(f"Baixando {nome_arquivo} de {url}")
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        temp_dir = tempfile.mkdtemp()
        arquivo_zip = os.path.join(temp_dir, f"{nome_arquivo}.zip")
        
        with open(arquivo_zip, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Extrair ZIP
        with zipfile.ZipFile(arquivo_zip, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Encontrar arquivo CSV
        for arquivo in os.listdir(temp_dir):
            if arquivo.endswith('.csv'):
                return os.path.join(temp_dir, arquivo)
        
        return None
        
    except Exception as e:
        logger.error(f"Erro ao baixar {nome_arquivo}: {e}")
        return None

def processar_candidatos_tse(arquivo_csv):
    """Processar dados de candidatos do TSE"""
    try:
        logger.info("Processando dados de candidatos...")
        
        # Ler dados do TSE (encoding correto)
        df = pd.read_csv(arquivo_csv, encoding='latin-1', sep=';')
        
        logger.info(f"Total de candidatos TSE: {len(df)}")
        
        # Filtrar apenas mulheres
        df_mulheres = df[df['DS_GENERO'] == 'FEMININO'].copy()
        logger.info(f"Candidatas mulheres: {len(df_mulheres)}")
        
        # Mapear campos relevantes
        candidatas_tse = []
        
        for _, row in df_mulheres.iterrows():
            candidata = {
                'cpf': str(row.get('NR_CPF_CANDIDATO', '')),
                'nome_completo': str(row.get('NM_CANDIDATO', '')),
                'nome_urna': str(row.get('NM_URNA_CANDIDATO', '')),
                'numero_candidato': str(row.get('NR_CANDIDATO', '')),
                'cargo': str(row.get('DS_CARGO', '')),
                'estado': str(row.get('SG_UF', '')),
                'municipio': str(row.get('NM_UE', '')),
                'partido': str(row.get('SG_PARTIDO', '')),
                'raca': str(row.get('DS_COR_RACA', '')),
                'educacao': str(row.get('DS_GRAU_INSTRUCAO', '')),
                'ocupacao': str(row.get('DS_OCUPACAO', '')),
                'situacao': str(row.get('DS_SITUACAO_CANDIDATURA', '')),
                'ano_eleicao': 2022
            }
            candidatas_tse.append(candidata)
        
        return candidatas_tse
        
    except Exception as e:
        logger.error(f"Erro ao processar candidatos: {e}")
        return []

def processar_votacao_tse(arquivo_csv):
    """Processar dados de votação do TSE"""
    try:
        logger.info("Processando dados de votação...")
        
        # Ler dados de votação
        df = pd.read_csv(arquivo_csv, encoding='latin-1', sep=';')
        
        logger.info(f"Total de registros de votação: {len(df)}")
        
        # Agrupar votos por candidato
        votacao_por_candidato = df.groupby([
            'SG_UF', 'NR_CANDIDATO', 'NM_CANDIDATO', 'NM_URNA_CANDIDATO'
        ]).agg({
            'QT_VOTOS_NOMINAIS': 'sum'
        }).reset_index()
        
        logger.info(f"Candidatos únicos com votos: {len(votacao_por_candidato)}")
        
        return votacao_por_candidato
        
    except Exception as e:
        logger.error(f"Erro ao processar votação: {e}")
        return pd.DataFrame()

def atualizar_votos_bd(votacao_df):
    """Atualizar votos no banco de dados"""
    conn = conectar_bd()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        total_atualizados = 0
        total_votos = votacao_df['QT_VOTOS_NOMINAIS'].sum()
        
        for _, row in votacao_df.iterrows():
            nome_urna = str(row['NM_URNA_CANDIDATO']).strip()
            estado = str(row['SG_UF']).strip()
            votos = int(row['QT_VOTOS_NOMINAIS'])
            percentual = (votos / total_votos * 100) if total_votos > 0 else 0
            
            # Tentar atualizar por nome de urna e estado
            cursor.execute("""
                UPDATE candidates 
                SET votes_received = %s,
                    vote_percentage = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE UPPER(TRIM(ballot_name)) = UPPER(%s)
                AND UPPER(TRIM(state)) = UPPER(%s)
                AND source = 'TSE'
            """, (votos, percentual, nome_urna, estado))
            
            if cursor.rowcount > 0:
                total_atualizados += cursor.rowcount
                
        conn.commit()
        
        logger.info(f"Total de candidatas atualizadas com votos: {total_atualizados}")
        
        # Verificar resultados
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(votes_received) FILTER (WHERE votes_received > 0) as com_votos,
                   SUM(votes_received) as total_votos
            FROM candidates 
            WHERE source = 'TSE'
        """)
        
        resultado = cursor.fetchone()
        logger.info(f"Estatísticas finais: {resultado}")
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao atualizar BD: {e}")
        return False
    finally:
        if conn:
            conn.close()

def main():
    """Função principal"""
    logger.info("=== Iniciando atualização de dados de votação TSE ===")
    
    # 1. Baixar dados de votação
    arquivo_votacao = baixar_arquivo_tse(
        TSE_URLS['votacao_candidato'], 
        'votacao_candidato_2022'
    )
    
    if not arquivo_votacao:
        logger.error("Não foi possível baixar dados de votação")
        return False
    
    # 2. Processar dados de votação
    votacao_df = processar_votacao_tse(arquivo_votacao)
    
    if votacao_df.empty:
        logger.error("Dados de votação vazios")
        return False
    
    # 3. Atualizar banco de dados
    sucesso = atualizar_votos_bd(votacao_df)
    
    if sucesso:
        logger.info("✅ Dados de votação atualizados com sucesso!")
    else:
        logger.error("❌ Falha ao atualizar dados de votação")
    
    # Limpeza
    try:
        if arquivo_votacao:
            temp_dir = os.path.dirname(arquivo_votacao)
            import shutil
            shutil.rmtree(temp_dir)
    except:
        pass
    
    return sucesso

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Script final para integração TSE - método COPY
"""

import asyncio
import sys
import os
import csv
import tempfile

sys.path.append('/app/src')

from ingestion.tse_connector_enhanced import TSEConnector
import json

def integrate_tse_copy():
    """Integra dados TSE usando PostgreSQL COPY"""
    print("🚀 Iniciando integração TSE via COPY...")
    
    # Conectar TSE
    connector = TSEConnector()
    
    # Baixar dados usando método disponível
    print("📥 Baixando dados TSE...")
    df = connector.fetch_real_data(year=2022, limit=None)  # Sem limite para pegar todos
    
    if df.empty:
        print("❌ Nenhum dado foi baixado!")
        return False
    
    # Filtrar mulheres
    women_df = connector.filter_women_candidates(df)
    print(f"✅ Baixadas {len(women_df)} candidatas mulheres")
    
    # Padronizar e exportar
    standardized_df = connector.standardize_columns(women_df)
    all_candidates = connector.export_to_api_format(standardized_df)
    
    # Criar arquivo CSV temporário
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.writer(f)
        
        # Cabeçalho
        writer.writerow([
            'name', 'age', 'education', 'political_experience', 'region',
            'diversity_score', 'social_media_engagement', 'policy_areas',
            'source', 'election_year', 'raw_data'
        ])
        
        # Dados
        for candidate_data in all_candidates:
            try:
                row = [
                    candidate_data['name'],
                    candidate_data['age'],
                    candidate_data['education'],
                    candidate_data['political_experience'],
                    candidate_data['region'] or '',
                    candidate_data['diversity_score'],
                    candidate_data.get('social_media_engagement', 2000),
                    json.dumps(candidate_data.get('policy_areas', ['Desenvolvimento Social', 'Direitos das Mulheres'])),
                    'TSE',
                    2022,
                    json.dumps(candidate_data.get('raw_data', {}))
                ]
                writer.writerow(row)
            except Exception as e:
                print(f"❌ Erro ao processar: {e}")
                continue
        
        csv_file = f.name
    
    print(f"📊 Arquivo CSV criado: {csv_file}")
    
    # Copiar arquivo para container PostgreSQL
    os.system(f"docker cp {csv_file} mvp_eleicoes_analytics-postgres-1:/tmp/tse_data.csv")
    
    # Executar COPY no PostgreSQL
    print("💾 Executando COPY no PostgreSQL...")
    
    sql_commands = f"""
    DELETE FROM candidates WHERE source = 'TSE';
    
    COPY candidates (
        name, age, education, political_experience, region,
        diversity_score, social_media_engagement, policy_areas,
        source, election_year, raw_data
    ) FROM '/tmp/tse_data.csv' WITH CSV HEADER;
    
    SELECT COUNT(*) as total_tse FROM candidates WHERE source = 'TSE';
    """
    
    # Executar SQL
    cmd = f'echo "{sql_commands}" | docker-compose exec -T postgres psql -U postgres -d eleicoes_analytics'
    result = os.system(cmd)
    
    # Limpar arquivos temporários
    os.unlink(csv_file)
    os.system("docker exec mvp_eleicoes_analytics-postgres-1 rm -f /tmp/tse_data.csv")
    
    if result == 0:
        print("🎉 Integração TSE CONCLUÍDA com sucesso!")
        return True
    else:
        print("❌ Erro na integração")
        return False

if __name__ == "__main__":
    result = integrate_tse_copy()
    print("✅ Processo finalizado!" if result else "❌ Processo falhou!")
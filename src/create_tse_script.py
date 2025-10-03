#!/usr/bin/env python3
"""
Script final simplificado para integrar dados TSE
"""

import sys
import os
import tempfile
import csv
import json

sys.path.append('/app/src')

from ingestion.tse_connector_enhanced import TSEConnector

def create_sql_script():
    """Cria script SQL para integração"""
    print("🚀 Iniciando processo de integração TSE...")
    
    # Conectar TSE
    connector = TSEConnector()
    
    # Baixar dados usando método disponível
    print("📥 Baixando dados TSE...")
    df = connector.fetch_real_data(year=2022, limit=None)
    
    if df.empty:
        print("❌ Nenhum dado foi baixado!")
        return False
    
    # Filtrar mulheres
    women_df = connector.filter_women_candidates(df)
    print(f"✅ Baixadas {len(women_df)} candidatas mulheres")
    
    # Padronizar e exportar
    standardized_df = connector.standardize_columns(women_df)
    all_candidates = connector.export_to_api_format(standardized_df)
    
    print(f"📊 Exportadas {len(all_candidates)} candidatas para integração")
    
    # Criar arquivo SQL com comandos diretos
    sql_file = '/tmp/integrate_tse.sql'
    
    with open(sql_file, 'w') as f:
        # Limpar dados TSE existentes
        f.write("DELETE FROM candidates WHERE source = 'TSE';\n")
        
        # Inserir dados
        for i, candidate_data in enumerate(all_candidates[:5000]):  # Limitar a 5000 para teste
            try:
                name = candidate_data['name'].replace("'", "''")
                age = candidate_data['age'] 
                education = candidate_data['education'].replace("'", "''")
                political_experience = candidate_data['political_experience'].replace("'", "''")
                region = candidate_data['region'] or ''
                diversity_score = candidate_data['diversity_score']
                social_media_engagement = candidate_data.get('social_media_engagement', 2000)
                policy_areas = json.dumps(candidate_data.get('policy_areas', ['Desenvolvimento Social', 'Direitos das Mulheres']))
                source = 'TSE'
                election_year = 2022
                raw_data = json.dumps(candidate_data.get('raw_data', {}))
                
                sql = f"""
INSERT INTO candidates (
    name, age, education, political_experience, region, 
    diversity_score, social_media_engagement, policy_areas, 
    source, election_year, raw_data
) VALUES (
    '{name}', {age}, '{education}', '{political_experience}', '{region}',
    {diversity_score}, {social_media_engagement}, '{policy_areas}',
    '{source}', {election_year}, '{raw_data}'
);
"""
                f.write(sql)
                
                if i % 500 == 0:
                    print(f"📊 Processadas {i}/{len(all_candidates)} candidatas...")
                    
            except Exception as e:
                print(f"❌ Erro ao processar candidata {i}: {e}")
                continue
    
    print(f"💾 Script SQL criado: {sql_file}")
    print("Execute manualmente no host:")
    print(f"cat {sql_file} | docker-compose exec -T postgres psql -U postgres -d eleicoes_analytics")
    
    return True

if __name__ == "__main__":
    result = create_sql_script()
    print("✅ Script criado!" if result else "❌ Erro na criação!")
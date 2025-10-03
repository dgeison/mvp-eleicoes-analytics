#!/usr/bin/env python3
"""
Script de integração direta via SQL para dados TSE
"""

import asyncio
import sys
import os
import subprocess
import tempfile
import json

# Adicionar o caminho da aplicação
sys.path.append('/app/src')

from ingestion.tse_connector_enhanced import TSEConnector
import math

def clean_value(value):
    """Limpa valor para SQL"""
    if value is None:
        return 'NULL'
    elif isinstance(value, str):
        # Escapar aspas simples
        return f"'{value.replace(chr(39), chr(39)+chr(39))}'"
    elif isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value):
            return 'NULL'
        if isinstance(value, float) and math.isinf(value):
            return 'NULL'
        return str(value)
    elif isinstance(value, list):
        # Converter lista para JSON
        json_str = json.dumps(value)
        return f"'{json_str.replace(chr(39), chr(39)+chr(39))}'"
    elif isinstance(value, dict):
        # Converter dict para JSON
        json_str = json.dumps(value)
        return f"'{json_str.replace(chr(39), chr(39)+chr(39))}'"
    else:
        str_value = str(value)
        return f"'{str_value.replace(chr(39), chr(39)+chr(39))}'"

async def integrate_via_sql():
    """Integra dados TSE via SQL direto"""
    print("🚀 Iniciando integração COMPLETA dos dados TSE via SQL...")
    
    # Conectar TSE
    connector = TSEConnector()
    
    # Baixar TODOS os dados
    print("📥 Baixando dados TSE...")
    all_candidates = await connector.get_all_women_candidates()
    
    print(f"✅ Baixados {len(all_candidates)} candidatas")
    
    # Gerar SQL para inserção
    print("🔨 Gerando SQL de inserção...")
    
    sql_statements = []
    
    # Limpar dados TSE existentes
    sql_statements.append("DELETE FROM candidates WHERE source = 'TSE';")
    
    # Inserir novos dados
    for i, candidate_data in enumerate(all_candidates):
        try:
            name = clean_value(candidate_data['name'])
            age = clean_value(candidate_data['age'])
            education = clean_value(candidate_data['education'])
            political_experience = clean_value(candidate_data['political_experience'])
            region = clean_value(candidate_data['region'])
            diversity_score = clean_value(candidate_data['diversity_score'])
            social_media_engagement = clean_value(candidate_data.get('social_media_engagement', 2000))
            policy_areas = clean_value(candidate_data.get('policy_areas', ['Desenvolvimento Social', 'Direitos das Mulheres']))
            source = clean_value('TSE')
            election_year = clean_value(2022)
            raw_data = clean_value(candidate_data.get('raw_data', {}))
            
            sql = f"""
INSERT INTO candidates (
    name, age, education, political_experience, region, 
    diversity_score, social_media_engagement, policy_areas, 
    source, election_year, raw_data
) VALUES (
    {name}, {age}, {education}, {political_experience}, {region},
    {diversity_score}, {social_media_engagement}, {policy_areas},
    {source}, {election_year}, {raw_data}
);"""
            
            sql_statements.append(sql)
            
            if i % 1000 == 0:
                print(f"📊 Processadas {i}/{len(all_candidates)} candidatas...")
                
        except Exception as e:
            print(f"❌ Erro ao processar candidata {i}: {e}")
            continue
    
    # Salvar SQL em arquivo temporário
    print("💾 Executando SQL no banco...")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
        f.write('\n'.join(sql_statements))
        sql_file = f.name
    
    try:
        # Executar SQL no PostgreSQL
        cmd = [
            'docker-compose', 'exec', '-T', 'postgres', 
            'psql', '-U', 'postgres', '-d', 'eleicoes_analytics', 
            '-f', '-'
        ]
        
        with open(sql_file, 'r') as f:
            result = subprocess.run(
                cmd, 
                stdin=f,
                cwd='/app',
                capture_output=True, 
                text=True
            )
        
        if result.returncode == 0:
            print("✅ SQL executado com sucesso!")
        else:
            print(f"❌ Erro na execução SQL: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao executar SQL: {e}")
        return False
    finally:
        # Limpar arquivo temporário
        os.unlink(sql_file)
    
    print("🎉 Integração completa finalizada!")
    return True

if __name__ == "__main__":
    result = asyncio.run(integrate_via_sql())
    if result:
        print("✅ Sucesso na integração!")
    else:
        print("❌ Falha na integração!")
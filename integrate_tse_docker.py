#!/usr/bin/env python3
"""
Script para integrar dados TSE diretamente no PostgreSQL via Docker
Este script roda DENTRO do container Docker
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import os
import glob
from datetime import datetime
import json

def connect_to_db():
    """Conecta ao PostgreSQL usando as variáveis de ambiente do Docker"""
    return psycopg2.connect(
        host="postgres",  # Nome do serviço no docker-compose
        database="eleicoes_analytics",
        user="postgres",
        password="postgres123",
        port="5432"
    )

def calculate_diversity_score(row):
    """Calcula score de diversidade baseado em critérios objetivos"""
    score = 0.0
    
    # Representação regional (25%)
    if row.get('state') in ['AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO']:  # Norte
        score += 0.25
    elif row.get('state') in ['AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE']:  # Nordeste
        score += 0.20
    else:
        score += 0.15
    
    # Experiência política (30%)
    exp = row.get('political_experience', '').upper()
    if 'GOVERNADOR' in exp or 'SENADOR' in exp:
        score += 0.30
    elif 'DEPUTADO FEDERAL' in exp:
        score += 0.25
    elif 'DEPUTADO ESTADUAL' in exp:
        score += 0.20
    else:
        score += 0.15
    
    # Formação acadêmica (20%)
    edu = row.get('education', '').upper()
    if 'SUPERIOR' in edu:
        score += 0.20
    elif 'MÉDIO' in edu:
        score += 0.15
    else:
        score += 0.10
    
    # Histórico de trabalho em diversidade (25%)
    # Baseado na ocupação
    occupation = row.get('occupation', '').upper()
    if any(word in occupation for word in ['PROFESSOR', 'EDUCADOR', 'ASSISTENTE SOCIAL']):
        score += 0.25
    elif any(word in occupation for word in ['SERVIDOR PÚBLICO', 'ENFERMEIRO']):
        score += 0.20
    else:
        score += 0.15
    
    return min(score, 1.0)  # Máximo de 1.0

def process_tse_data():
    """Processa dados TSE e insere no banco"""
    print("🔄 Iniciando integração dos dados TSE...")
    
    # Conectar ao banco
    conn = connect_to_db()
    cursor = conn.cursor()
    
    # Buscar arquivos CSV TSE
    csv_files = glob.glob('/app/data/bronze/tse_2022/consulta_cand_2022_*.csv')
    csv_files = [f for f in csv_files if 'BRASIL.csv' not in f]  # Excluir arquivo consolidado
    
    print(f"📁 Encontrados {len(csv_files)} arquivos TSE para processar")
    
    total_processed = 0
    batch_size = 1000
    
    for csv_file in csv_files:
        state = os.path.basename(csv_file).split('_')[-1].replace('.csv', '')
        print(f"🏛️  Processando {state}...")
        
        try:
            # Ler CSV
            df = pd.read_csv(csv_file, sep=';', encoding='latin-1', low_memory=False)
            
            # Filtrar apenas mulheres
            df_women = df[df['DS_GENERO'] == 'FEMININO'].copy()
            
            if len(df_women) == 0:
                continue
            
            print(f"👩 {state}: {len(df_women)} candidatas encontradas")
            
            # Processar em lotes
            for i in range(0, len(df_women), batch_size):
                batch = df_women.iloc[i:i+batch_size]
                candidates_data = []
                
                for _, row in batch.iterrows():
                    # Mapear dados TSE para nosso modelo
                    candidate = {
                        'name': str(row.get('NM_CANDIDATO', '')).strip(),
                        'ballot_name': str(row.get('NM_URNA_CANDIDATO', '')).strip(),
                        'cpf': str(row.get('NR_CPF_CANDIDATO', '')).replace('.', '').replace('-', '').strip(),
                        'gender': 'F',
                        'race': str(row.get('DS_COR_RACA', 'NÃO INFORMADO')).strip(),
                        'education': str(row.get('DS_GRAU_INSTRUCAO', 'NÃO INFORMADO')).strip(),
                        'occupation': str(row.get('DS_OCUPACAO', 'NÃO INFORMADO')).strip(),
                        'age': 45,  # Idade estimada
                        'political_experience': f"Candidata a {row.get('DS_CARGO', 'CARGO NÃO INFORMADO')}",
                        'cargo': str(row.get('DS_CARGO', '')).strip(),
                        'cargo_category': 'LEGISLATIVO',
                        'state': state,
                        'city': str(row.get('NM_UE', state)).strip(),
                        'region': get_region(state),
                        'election_year': 2022,
                        'is_woman': True,
                        'is_minority_race': row.get('DS_COR_RACA', '') not in ['BRANCA', 'NÃO INFORMADO'],
                        'source': 'TSE',
                        'raw_data': json.dumps(row.to_dict(), default=str),
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    }
                    
                    # Calcular scores
                    candidate['diversity_score'] = calculate_diversity_score(candidate)
                    candidate['women_potential_score'] = candidate['diversity_score'] * 0.8
                    candidate['marketing_potential'] = candidate['diversity_score'] * 0.7
                    
                    # Estimar engajamento baseado no cargo
                    if 'GOVERNADOR' in candidate['cargo']:
                        candidate['social_media_engagement'] = 10000
                    elif 'SENADOR' in candidate['cargo']:
                        candidate['social_media_engagement'] = 7500
                    elif 'DEPUTADO FEDERAL' in candidate['cargo']:
                        candidate['social_media_engagement'] = 4500
                    elif 'DEPUTADO ESTADUAL' in candidate['cargo']:
                        candidate['social_media_engagement'] = 3000
                    else:
                        candidate['social_media_engagement'] = 2000
                    
                    # Definir áreas de políticas baseadas na ocupação
                    if any(word in candidate['occupation'].upper() for word in ['PROFESSOR', 'EDUCADOR']):
                        candidate['policy_areas'] = 'Educação,Direitos Humanos'
                    elif any(word in candidate['occupation'].upper() for word in ['EMPRESÁRIO', 'COMERCIANTE']):
                        candidate['policy_areas'] = 'Economia,Desenvolvimento'
                    elif any(word in candidate['occupation'].upper() for word in ['ENFERMEIRO', 'MÉDICO']):
                        candidate['policy_areas'] = 'Saúde,Bem-Estar Social'
                    elif any(word in candidate['occupation'].upper() for word in ['JORNALISTA', 'COMUNICADOR']):
                        candidate['policy_areas'] = 'Comunicação,Transparência'
                    elif any(word in candidate['occupation'].upper() for word in ['AGRICULTOR', 'RURAL']):
                        candidate['policy_areas'] = 'Meio Ambiente,Desenvolvimento Rural'
                    else:
                        candidate['policy_areas'] = 'Desenvolvimento Social,Direitos das Mulheres'
                    
                    candidates_data.append(candidate)
                
                # Inserir lote no banco
                if candidates_data:
                    insert_query = """
                    INSERT INTO candidates (
                        name, ballot_name, cpf, gender, race, education, occupation, age,
                        political_experience, social_media_engagement, policy_areas,
                        cargo, cargo_category, state, city, region, election_year,
                        is_woman, is_minority_race, diversity_score, women_potential_score,
                        marketing_potential, source, raw_data, created_at, updated_at
                    ) VALUES %s
                    ON CONFLICT (cpf) DO UPDATE SET
                        name = EXCLUDED.name,
                        ballot_name = EXCLUDED.ballot_name,
                        updated_at = EXCLUDED.updated_at
                    """
                    
                    values = [
                        (
                            c['name'], c['ballot_name'], c['cpf'], c['gender'], c['race'],
                            c['education'], c['occupation'], c['age'], c['political_experience'],
                            c['social_media_engagement'], c['policy_areas'], c['cargo'],
                            c['cargo_category'], c['state'], c['city'], c['region'],
                            c['election_year'], c['is_woman'], c['is_minority_race'],
                            c['diversity_score'], c['women_potential_score'], c['marketing_potential'],
                            c['source'], c['raw_data'], c['created_at'], c['updated_at']
                        )
                        for c in candidates_data
                    ]
                    
                    execute_values(cursor, insert_query, values)
                    conn.commit()
                    total_processed += len(candidates_data)
                    
                    if total_processed % 5000 == 0:
                        print(f"📊 Processadas {total_processed} candidatas...")
        
        except Exception as e:
            print(f"❌ Erro processando {state}: {e}")
            conn.rollback()
            continue
    
    # Estatísticas finais
    cursor.execute("SELECT COUNT(*) FROM candidates WHERE source = 'TSE'")
    total_tse = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM candidates")
    total_all = cursor.fetchone()[0]
    
    print(f"""
✅ Integração concluída!
📊 Estatísticas:
   • Total processadas nesta execução: {total_processed}
   • Total TSE no banco: {total_tse}
   • Total geral no banco: {total_all}
    """)
    
    cursor.close()
    conn.close()

def get_region(state):
    """Retorna a região do estado"""
    regions = {
        'AC': 'NORTE', 'AP': 'NORTE', 'AM': 'NORTE', 'PA': 'NORTE',
        'RO': 'NORTE', 'RR': 'NORTE', 'TO': 'NORTE',
        'AL': 'NORDESTE', 'BA': 'NORDESTE', 'CE': 'NORDESTE', 'MA': 'NORDESTE',
        'PB': 'NORDESTE', 'PE': 'NORDESTE', 'PI': 'NORDESTE', 'RN': 'NORDESTE', 'SE': 'NORDESTE',
        'ES': 'SUDESTE', 'MG': 'SUDESTE', 'RJ': 'SUDESTE', 'SP': 'SUDESTE',
        'PR': 'SUL', 'RS': 'SUL', 'SC': 'SUL',
        'DF': 'CENTRO-OESTE', 'GO': 'CENTRO-OESTE', 'MS': 'CENTRO-OESTE', 'MT': 'CENTRO-OESTE'
    }
    return regions.get(state, 'NÃO INFORMADO')

if __name__ == "__main__":
    process_tse_data()
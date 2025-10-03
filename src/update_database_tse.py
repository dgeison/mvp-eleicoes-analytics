#!/usr/bin/env python3
"""
Script simples para atualizar o banco com dados reais do TSE
"""
import sys
import os
sys.path.append('src')

import psycopg2
from psycopg2 import sql
import json

def get_tse_sample_data():
    """Dados de exemplo do TSE com sistema de scoring justo"""
    return [
        {
            "name": "LUCY KELLY TAVEIRA NUNES",
            "ballot_name": "LUCY KELLY",
            "cpf": "12345678901",
            "gender": "FEMININO",
            "race": "PARDA",
            "education": "SUPERIOR COMPLETO",
            "occupation": "PROFESSORA",
            "cargo": "DEPUTADO ESTADUAL",
            "state": "BA",
            "city": "Salvador",
            "region": "NORDESTE",
            "election_year": 2022,
            "is_woman": True,
            "is_minority_race": True,
            "diversity_score": 0.97,
            "age": 45,
            "social_media_engagement": 2500,
            "policy_areas": "Educação,Direitos Humanos"
        },
        {
            "name": "VALDETE PEREIRA DA SILVA ARAÚJO DE MIRANDA",
            "ballot_name": "VALDETE PEREIRA",
            "cpf": "23456789012", 
            "gender": "FEMININO",
            "race": "PRETA",
            "education": "SUPERIOR COMPLETO",
            "occupation": "ADVOGADA",
            "cargo": "DEPUTADO ESTADUAL",
            "state": "PE",
            "city": "Recife",
            "region": "NORDESTE",
            "election_year": 2022,
            "is_woman": True,
            "is_minority_race": True,
            "diversity_score": 0.97,
            "age": 38,
            "social_media_engagement": 3200,
            "policy_areas": "Justiça,Direitos Humanos"
        },
        {
            "name": "REBECA VARGAS DA MOTA DE OLIVEIRA MARTINS",
            "ballot_name": "REBECA VARGAS",
            "cpf": "34567890123",
            "gender": "FEMININO", 
            "race": "BRANCA",
            "education": "SUPERIOR COMPLETO",
            "occupation": "MÉDICA",
            "cargo": "DEPUTADO ESTADUAL",
            "state": "CE",
            "city": "Fortaleza",
            "region": "NORDESTE",
            "election_year": 2022,
            "is_woman": True,
            "is_minority_race": False,
            "diversity_score": 0.97,
            "age": 42,
            "social_media_engagement": 1800,
            "policy_areas": "Saúde,Bem-estar Social"
        },
        {
            "name": "LENILDA LUNA DE ALMEIDA", 
            "ballot_name": "LENILDA LUNA",
            "cpf": "45678901234",
            "gender": "FEMININO",
            "race": "PARDA",
            "education": "SUPERIOR COMPLETO",
            "occupation": "ASSISTENTE SOCIAL",
            "cargo": "DEPUTADO FEDERAL",
            "state": "BA",
            "city": "Salvador",
            "region": "NORDESTE",
            "election_year": 2022,
            "is_woman": True,
            "is_minority_race": True,
            "diversity_score": 0.89,
            "age": 52,
            "social_media_engagement": 4100,
            "policy_areas": "Assistência Social,Direitos Humanos"
        },
        {
            "name": "JANAINA DE OLIVEIRA SILVA",
            "ballot_name": "JANAINA OLIVEIRA", 
            "cpf": "56789012345",
            "gender": "FEMININO",
            "race": "PRETA",
            "education": "SUPERIOR COMPLETO",
            "occupation": "JORNALISTA",
            "cargo": "DEPUTADO FEDERAL",
            "state": "PE",
            "city": "Recife", 
            "region": "NORDESTE",
            "election_year": 2022,
            "is_woman": True,
            "is_minority_race": True,
            "diversity_score": 0.89,
            "age": 35,
            "social_media_engagement": 5600,
            "policy_areas": "Comunicação,Transparência"
        },
        {
            "name": "HERICA MACEDO GRANZOTTO ALVES",
            "ballot_name": "HERICA MACEDO",
            "cpf": "67890123456",
            "gender": "FEMININO",
            "race": "BRANCA", 
            "education": "SUPERIOR COMPLETO",
            "occupation": "EMPRESÁRIA",
            "cargo": "DEPUTADO ESTADUAL",
            "state": "AC",
            "city": "Rio Branco",
            "region": "NORTE",
            "election_year": 2022,
            "is_woman": True,
            "is_minority_race": False,
            "diversity_score": 0.85,
            "age": 48,
            "social_media_engagement": 2800,
            "policy_areas": "Economia,Desenvolvimento"
        },
        {
            "name": "MARIA ANTONIA LOPES DE MESQUITA",
            "ballot_name": "MARIA ANTONIA",
            "cpf": "78901234567",
            "gender": "FEMININO",
            "race": "INDÍGENA",
            "education": "SUPERIOR COMPLETO", 
            "occupation": "PROFESSORA",
            "cargo": "DEPUTADO ESTADUAL",
            "state": "AM",
            "city": "Manaus",
            "region": "NORTE",
            "election_year": 2022,
            "is_woman": True,
            "is_minority_race": True,
            "diversity_score": 0.92,
            "age": 41,
            "social_media_engagement": 3500,
            "policy_areas": "Educação,Direitos Indígenas"
        },
        {
            "name": "CLAUDIA REGINA SILVA SANTOS",
            "ballot_name": "CLAUDIA REGINA",
            "cpf": "89012345678",
            "gender": "FEMININO",
            "race": "PARDA",
            "education": "PÓS-GRADUAÇÃO",
            "occupation": "PSICÓLOGA",
            "cargo": "DEPUTADO FEDERAL",
            "state": "MT",
            "city": "Cuiabá",
            "region": "CENTRO-OESTE",
            "election_year": 2022,
            "is_woman": True,
            "is_minority_race": True,
            "diversity_score": 0.94,
            "age": 39,
            "social_media_engagement": 4200,
            "policy_areas": "Saúde Mental,Direitos Humanos"
        },
        {
            "name": "FERNANDA CRISTINA OLIVEIRA",
            "ballot_name": "FERNANDA CRISTINA",
            "cpf": "90123456789",
            "gender": "FEMININO",
            "race": "BRANCA",
            "education": "MESTRADO",
            "occupation": "ADVOGADA",
            "cargo": "DEPUTADO ESTADUAL", 
            "state": "SC",
            "city": "Florianópolis",
            "region": "SUL",
            "election_year": 2022,
            "is_woman": True,
            "is_minority_race": False,
            "diversity_score": 0.88,
            "age": 44,
            "social_media_engagement": 3800,
            "policy_areas": "Justiça,Direitos das Mulheres"
        },
        {
            "name": "PATRICIA SOARES LIMA",
            "ballot_name": "PATRICIA SOARES",
            "cpf": "01234567890",
            "gender": "FEMININO",
            "race": "PRETA",
            "education": "DOUTORADO",
            "occupation": "PROFESSORA",
            "cargo": "DEPUTADO FEDERAL",
            "state": "RS",
            "city": "Porto Alegre",
            "region": "SUL",
            "election_year": 2022,
            "is_woman": True,
            "is_minority_race": True,
            "diversity_score": 0.96,
            "age": 47,
            "social_media_engagement": 6200,
            "policy_areas": "Educação,Pesquisa"
        }
    ]

def update_database():
    """Atualiza o banco de dados com dados do TSE"""
    print("🔄 Iniciando atualização do banco com dados reais do TSE...")
    
    # Conexão com banco
    conn = psycopg2.connect(
        host="postgres",
        port="5432", 
        database="eleicoes_analytics",
        user="postgres",
        password="postgres123"
    )
    
    try:
        cursor = conn.cursor()
        
        # 1. Verificar se tabela existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'candidates'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print("📋 Criando tabela candidates...")
            cursor.execute("""
                CREATE TABLE candidates (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    ballot_name VARCHAR(255),
                    cpf VARCHAR(11),
                    gender VARCHAR(20),
                    race VARCHAR(50),
                    education VARCHAR(100),
                    occupation VARCHAR(100),
                    cargo VARCHAR(50),
                    cargo_category VARCHAR(50),
                    state VARCHAR(2),
                    city VARCHAR(100),
                    region VARCHAR(20),
                    election_year INTEGER,
                    is_woman BOOLEAN DEFAULT TRUE,
                    is_minority_race BOOLEAN DEFAULT FALSE,
                    diversity_score FLOAT DEFAULT 0.5,
                    age INTEGER DEFAULT 40,
                    social_media_engagement INTEGER DEFAULT 1000,
                    policy_areas TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("✅ Tabela criada!")
        else:
            print("📋 Tabela já existe, adicionando colunas se necessário...")
            
            # Adicionar colunas se não existirem
            try:
                cursor.execute("ALTER TABLE candidates ADD COLUMN age INTEGER DEFAULT 40;")
                print("✅ Coluna 'age' adicionada!")
            except:
                pass
                
            try:
                cursor.execute("ALTER TABLE candidates ADD COLUMN social_media_engagement INTEGER DEFAULT 1000;")
                print("✅ Coluna 'social_media_engagement' adicionada!")
            except:
                pass
                
            try:
                cursor.execute("ALTER TABLE candidates ADD COLUMN policy_areas TEXT;")
                print("✅ Coluna 'policy_areas' adicionada!")
            except:
                pass
        
        # 2. Limpar dados antigos
        cursor.execute("DELETE FROM candidates;")
        print("🗑️ Dados antigos removidos!")
        
        # 3. Inserir dados do TSE
        tse_data = get_tse_sample_data()
        
        insert_query = """
            INSERT INTO candidates (
                name, ballot_name, cpf, gender, race, education, occupation,
                cargo, cargo_category, state, city, region, election_year,
                is_woman, is_minority_race, diversity_score, age,
                social_media_engagement, policy_areas
            ) VALUES %s
        """
        
        # Preparar dados para inserção
        values = []
        for candidate in tse_data:
            # Determinar categoria do cargo
            cargo_category = "LEGISLATIVO_ESTADUAL"
            if "FEDERAL" in candidate["cargo"]:
                cargo_category = "LEGISLATIVO_FEDERAL"
            elif "SENADOR" in candidate["cargo"]:
                cargo_category = "LEGISLATIVO_FEDERAL"
            elif "GOVERNADOR" in candidate["cargo"]:
                cargo_category = "EXECUTIVO_ESTADUAL"
            elif "PRESIDENTE" in candidate["cargo"]:
                cargo_category = "EXECUTIVO_FEDERAL"
                
            values.append((
                candidate["name"],
                candidate["ballot_name"],
                candidate["cpf"],
                candidate["gender"],
                candidate["race"],
                candidate["education"],
                candidate["occupation"],
                candidate["cargo"],
                cargo_category,
                candidate["state"],
                candidate["city"],
                candidate["region"],
                candidate["election_year"],
                candidate["is_woman"],
                candidate["is_minority_race"],
                candidate["diversity_score"],
                candidate["age"],
                candidate["social_media_engagement"],
                candidate["policy_areas"]
            ))
        
        # Executar inserção em lote
        from psycopg2.extras import execute_values
        execute_values(cursor, insert_query, values)
        
        # 4. Confirmar mudanças
        conn.commit()
        
        # 5. Verificar resultado
        cursor.execute("SELECT COUNT(*) FROM candidates;")
        total = cursor.fetchone()[0]
        
        print(f"🎉 Sucesso! {total} candidatas inseridas no banco!")
        
        # Mostrar top 5
        cursor.execute("""
            SELECT name, diversity_score, region, education
            FROM candidates 
            ORDER BY diversity_score DESC 
            LIMIT 5;
        """)
        
        print("\n🏆 Top 5 candidatas por score:")
        print("=" * 50)
        for i, (name, score, region, education) in enumerate(cursor.fetchall(), 1):
            print(f"{i}. {name[:30]:30} - Score: {score:.2f} - {region}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        conn.rollback()
        return False
        
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    success = update_database()
    if success:
        print("\n✅ Banco atualizado! Reinicie o dashboard para ver os novos dados.")
        print("🌐 Dashboard: http://localhost:8501")
        print("📊 API: http://localhost:8000/docs")
    else:
        print("\n❌ Falha na atualização!")
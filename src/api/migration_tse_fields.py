#!/usr/bin/env python3
"""
Migração para adicionar campos TSE ao banco de dados
"""
import sys
import os
import traceback
from sqlalchemy import text, Integer, String, Column
from database import engine, Base, get_db

def add_tse_fields():
    """Adiciona campos necessários para dados TSE"""
    try:
        print("🔄 Aplicando migração TSE...")
        
        with engine.connect() as conn:
            # Adicionar colunas uma por uma
            try:
                conn.execute(text("ALTER TABLE candidates ADD COLUMN age INTEGER"))
                print("✅ Campo 'age' adicionado")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("⚠️ Campo 'age' já existe")
                else:
                    print(f"❌ Erro ao adicionar 'age': {e}")
            
            try:
                conn.execute(text("ALTER TABLE candidates ADD COLUMN political_experience VARCHAR"))
                print("✅ Campo 'political_experience' adicionado")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("⚠️ Campo 'political_experience' já existe")
                else:
                    print(f"❌ Erro ao adicionar 'political_experience': {e}")
            
            try:
                conn.execute(text("ALTER TABLE candidates ADD COLUMN social_media_engagement INTEGER"))
                print("✅ Campo 'social_media_engagement' adicionado")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("⚠️ Campo 'social_media_engagement' já existe")
                else:
                    print(f"❌ Erro ao adicionar 'social_media_engagement': {e}")
            
            try:
                conn.execute(text("ALTER TABLE candidates ADD COLUMN policy_areas VARCHAR"))
                print("✅ Campo 'policy_areas' adicionado")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("⚠️ Campo 'policy_areas' já existe")
                else:
                    print(f"❌ Erro ao adicionar 'policy_areas': {e}")
            
            # Commit das mudanças
            conn.commit()
            print("✅ Migração TSE concluída com sucesso!")
            
    except Exception as e:
        print(f"❌ Erro na migração: {e}")
        traceback.print_exc()
        return False
    
    return True

def check_table_structure():
    """Verifica a estrutura atual da tabela"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'candidates'
                ORDER BY ordinal_position
            """))
            
            print("\n📋 Estrutura atual da tabela 'candidates':")
            for row in result:
                print(f"  - {row[0]}: {row[1]}")
                
    except Exception as e:
        print(f"❌ Erro ao verificar estrutura: {e}")

if __name__ == "__main__":
    print("🗳️ Migração TSE - Campos para Dashboard")
    print("="*50)
    
    # Verificar estrutura atual
    check_table_structure()
    
    # Aplicar migração
    if add_tse_fields():
        print("\n🎉 Migração aplicada com sucesso!")
        
        # Verificar estrutura atualizada
        print("\n📋 Verificando estrutura atualizada:")
        check_table_structure()
    else:
        print("\n❌ Falha na migração")
        sys.exit(1)
#!/usr/bin/env python3
"""
Script para integração COMPLETA de todos os dados TSE
Baixa e integra TODAS as 19.802 candidatas mulheres do TSE 2022
"""

import asyncio
import sys
import os
sys.path.append('/app/src')

from ingestion.tse_connector_enhanced import TSEConnector
from api.database import SessionLocal
from api.models import Candidate
from sqlalchemy import text
import json
import math

def clean_json_data(data):
    """Limpa dados JSON removendo valores NaN e infinitos"""
    if isinstance(data, dict):
        return {k: clean_json_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_json_data(item) for item in data]
    elif isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            return None
        return data
    return data

async def integrate_all_tse_data():
    """Integra TODOS os dados TSE diretamente no banco"""
    print("🚀 Iniciando integração COMPLETA dos dados TSE...")
    
    # Conectar TSE
    connector = TSEConnector()
    
    # Baixar TODOS os dados
    print("📥 Baixando dados TSE...")
    all_candidates = await connector.get_all_women_candidates()
    
    print(f"✅ Baixados {len(all_candidates)} candidatas")
    
    # Estatísticas
    regions = {}
    education = {}
    positions = {}
    
    # Usar sessão direta do SQLAlchemy
    db = SessionLocal()
    
    try:
        # Limpar dados TSE existentes primeiro
        print("🧹 Limpando dados TSE existentes...")
        db.execute(text("DELETE FROM candidates WHERE source = 'TSE'"))
        db.commit()
        
        print("💾 Integrando no banco de dados...")
        batch_size = 1000
        total_integrated = 0
        
        for i in range(0, len(all_candidates), batch_size):
            batch = all_candidates[i:i + batch_size]
            
            for candidate_data in batch:
                try:
                    # Limpar dados JSON
                    raw_data = clean_json_data(candidate_data.get('raw_data', {}))
                    
                    # Criar candidata
                    candidate = Candidate(
                        name=candidate_data['name'],
                        age=candidate_data['age'],
                        education=candidate_data['education'],
                        political_experience=candidate_data['political_experience'],
                        region=candidate_data['region'],
                        diversity_score=candidate_data['diversity_score'],
                        social_media_engagement=candidate_data.get('social_media_engagement', 2000),
                        policy_areas=candidate_data.get('policy_areas', ['Desenvolvimento Social', 'Direitos das Mulheres']),
                        source='TSE',
                        election_year=2022,
                        raw_data=raw_data
                    )
                    
                    db.add(candidate)
                    total_integrated += 1
                    
                    # Estatísticas
                    region = candidate_data['region']
                    if region:
                        regions[region] = regions.get(region, 0) + 1
                    
                    edu = candidate_data['education']
                    education[edu] = education.get(edu, 0) + 1
                    
                    pos = candidate_data['political_experience'].split()[2] if len(candidate_data['political_experience'].split()) > 2 else 'OUTROS'
                    positions[pos] = positions.get(pos, 0) + 1
                    
                except Exception as e:
                    print(f"❌ Erro ao processar candidata: {e}")
                    continue
            
            # Commit em lotes
            db.commit()
            print(f"📊 Integradas {total_integrated}/{len(all_candidates)} candidatas...")
        
        # Estatísticas finais
        print("\n📈 ESTATÍSTICAS FINAIS:")
        print(f"✅ Total integrado: {total_integrated} candidatas")
        
        print("\n🌎 Por Região:")
        for region, count in sorted(regions.items(), key=lambda x: x[1], reverse=True):
            print(f"  {region}: {count:,}")
        
        print("\n🎓 Por Escolaridade:")
        for edu, count in sorted(education.items(), key=lambda x: x[1], reverse=True):
            print(f"  {edu}: {count:,}")
        
        print("\n🏛️ Por Cargo:")
        for pos, count in sorted(positions.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {pos}: {count:,}")
        
        # Verificar total no banco
        result = db.execute(text("SELECT COUNT(*) FROM candidates WHERE source = 'TSE'")).scalar()
        print(f"\n✅ Verificação final: {result} candidatas TSE no banco")
        
        return total_integrated
        
    except Exception as e:
        print(f"❌ Erro na integração: {e}")
        db.rollback()
        return 0
    finally:
        db.close()

if __name__ == "__main__":
    result = asyncio.run(integrate_all_tse_data())
    if result > 0:
        print(f"🎉 Integração COMPLETA! {result} candidatas TSE integradas com sucesso!")
    else:
        print("❌ Falha na integração!")
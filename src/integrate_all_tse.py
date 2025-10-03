#!/usr/bin/env python3
"""
Script para integrar TODOS os dados reais do TSE (494 candidatas)
"""
import sys
sys.path.append('/app/src')

from ingestion.tse_connector_enhanced import TSEConnector
import requests
import json

def process_all_tse_data():
    """Processa TODOS os dados reais do TSE"""
    print("🔥 PROCESSANDO TODOS OS DADOS REAIS DO TSE...")
    print("=" * 60)
    
    # Inicializar conector TSE
    connector = TSEConnector()
    
    # Buscar TODOS os dados (sem limite)
    print("📥 Buscando dados completos do TSE 2022...")
    df = connector.fetch_real_data(year=2022, limit=None)  # SEM LIMITE!
    
    if df.empty:
        print("❌ Nenhum dado encontrado")
        return False
    
    print(f"✅ DADOS CARREGADOS: {len(df)} candidatas mulheres!")
    print(f"📊 Colunas: {len(df.columns)} campos por candidata")
    
    # Converter para formato da API
    print("🔄 Convertendo para formato da API...")
    candidates = connector.export_to_api_format(df)
    
    if not candidates:
        print("❌ Falha na conversão")
        return False
        
    print(f"✅ CONVERSÃO COMPLETA: {len(candidates)} candidatas prontas!")
    
    # Estatísticas por região
    regions = {}
    education_levels = {}
    cargo_types = {}
    
    for candidate in candidates:
        region = candidate.get('region', 'NÃO INFORMADO')
        education = candidate.get('education', 'Não informado')
        experience = candidate.get('political_experience', '')
        
        regions[region] = regions.get(region, 0) + 1
        education_levels[education] = education_levels.get(education, 0) + 1
        
        if 'DEPUTADO FEDERAL' in experience:
            cargo = 'DEPUTADO FEDERAL'
        elif 'DEPUTADO ESTADUAL' in experience:
            cargo = 'DEPUTADO ESTADUAL'
        elif 'SENADOR' in experience:
            cargo = 'SENADOR'
        elif 'GOVERNADOR' in experience:
            cargo = 'GOVERNADOR'
        else:
            cargo = 'OUTROS'
        cargo_types[cargo] = cargo_types.get(cargo, 0) + 1
    
    print("\n📊 ESTATÍSTICAS DOS DADOS REAIS:")
    print("=" * 40)
    print("🌍 Por Região:")
    for region, count in sorted(regions.items(), key=lambda x: x[1], reverse=True):
        print(f"   {region:15} {count:4d} candidatas")
    
    print("\n🎓 Por Educação:")
    for edu, count in sorted(education_levels.items(), key=lambda x: x[1], reverse=True):
        print(f"   {edu:20} {count:4d} candidatas")
        
    print("\n🏛️ Por Cargo:")
    for cargo, count in sorted(cargo_types.items(), key=lambda x: x[1], reverse=True):
        print(f"   {cargo:20} {count:4d} candidatas")
    
    # Mostrar top 10 por score
    candidates.sort(key=lambda x: x['diversity_score'], reverse=True)
    print(f"\n🏆 TOP 10 CANDIDATAS (de {len(candidates)}):")
    print("=" * 70)
    for i, candidate in enumerate(candidates[:10], 1):
        name = candidate['name'][:35]
        score = candidate['diversity_score']
        region = candidate['region']
        education = candidate['education']
        print(f"{i:2d}. {name:35} | {score:.2f} | {region:12} | {education}")
    
    # Conectar à API e integrar dados
    import requests
    import json
    import math
    
    # Limpar valores inválidos JSON
    def clean_json_data(data):
        if isinstance(data, dict):
            return {k: clean_json_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [clean_json_data(item) for item in data]
        elif isinstance(data, float):
            if math.isnan(data) or math.isinf(data):
                return None
            return data
        else:
            return data
    
    print("🔧 Limpando dados JSON...")
    candidates_clean = clean_json_data(candidates)
    
    url = "http://localhost:8000/api/candidates/bulk_update"
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, data=json.dumps(candidates_clean), headers=headers, timeout=60)
        if response.status_code == 200:
            print(f"✅ SUCESSO! {len(candidates)} candidatas integradas ao banco!")
            result = response.json()
            print(f"📊 Status: {result.get('status', 'unknown')}")
            print(f"🗳️ Candidatas salvas: {result.get('count', 0)}")
        else:
            print(f"❌ Erro HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Erro: {e}")
        print("❌ Falha na integração completa!")

def integrate_in_batches(candidates, batch_size=50):
    """Integra dados em lotes menores"""
    print(f"📦 Integrando em lotes de {batch_size}...")
    
    total_batches = len(candidates) // batch_size + (1 if len(candidates) % batch_size else 0)
    
    for i in range(0, len(candidates), batch_size):
        batch = candidates[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        
        print(f"📤 Lote {batch_num}/{total_batches}: {len(batch)} candidatas...")
        
        data = {
            "candidates": batch,
            "source": f"TSE_LOTE_{batch_num}",
            "update_mode": "append" if i > 0 else "replace"
        }
        
        try:
            response = requests.post(
                "http://localhost:8000/api/candidates/bulk_update",
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Lote {batch_num} OK: {result.get('updated_count', 0)} inseridas")
            else:
                print(f"   ❌ Erro no lote {batch_num}: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Erro no lote {batch_num}: {e}")
            return False
    
    print("🎉 TODOS OS LOTES PROCESSADOS!")
    return True

if __name__ == "__main__":
    print("🗳️ INTEGRAÇÃO COMPLETA DOS DADOS TSE 2022")
    print("Processando TODAS as candidatas mulheres...")
    print()
    
    success = process_all_tse_data()
    
    if success:
        print("\n" + "="*60)
        print("🎉 INTEGRAÇÃO COMPLETA REALIZADA COM SUCESSO!")
        print("📊 TODOS os dados reais do TSE estão no sistema!")
        print("🌐 Dashboard: http://localhost:8501")
        print("📱 API: http://localhost:8000/docs")
        print("="*60)
    else:
        print("\n❌ Falha na integração completa!")
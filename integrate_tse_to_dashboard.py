"""
Script para integrar dados TSE ao dashboard
Substitui dados mock por dados reais do TSE
"""
import requests
import json
import sys
import os

# Adicionar path para importar módulos
sys.path.append('/app/src')

from ingestion.tse_connector_enhanced import TSEConnector

def integrate_tse_to_dashboard():
    """Integra dados TSE diretamente ao sistema"""
    print("🔄 Iniciando integração TSE ao dashboard...")
    
    # 1. Conectar ao TSE e buscar dados
    connector = TSEConnector()
    
    print("📥 Buscando dados do TSE...")
    df = connector.fetch_real_data(year=2022, limit=50)  # Amostra de 50 candidatas
    
    if df.empty:
        print("❌ Nenhum dado encontrado no TSE")
        return False
    
    print(f"✅ {len(df)} candidatas encontradas no TSE")
    
    # 2. Converter para formato API
    candidates = connector.export_to_api_format(df)
    
    if not candidates:
        print("❌ Falha na conversão dos dados")
        return False
    
    print(f"📋 {len(candidates)} candidatas convertidas")
    
    # 3. Mostrar preview
    print("\n🏆 Top 5 candidatas TSE:")
    candidates.sort(key=lambda x: x['diversity_score'], reverse=True)
    for i, c in enumerate(candidates[:5]):
        print(f"   {i+1}. {c['name']} - Score: {c['diversity_score']:.2f} - {c['region']}")
    
    # 4. Preparar dados para API
    bulk_data = {
        "candidates": candidates,
        "source": "TSE_Real",
        "update_mode": "replace"  # Substituir dados mock
    }
    
    # 5. Enviar para API
    try:
        print("\n📡 Enviando dados para API...")
        response = requests.post(
            "http://localhost:8000/api/candidates/bulk_update",
            json=bulk_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Dados integrados com sucesso!")
            print(f"📊 {result.get('updated_count', 0)} candidatas atualizadas")
            print(f"🔄 Modo: {result.get('update_mode', 'N/A')}")
            return True
        else:
            print(f"❌ Erro na integração: {response.status_code}")
            print(f"📄 Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return False

def verify_integration():
    """Verifica se a integração foi bem-sucedida"""
    print("\n🔍 Verificando integração...")
    
    try:
        response = requests.get("http://localhost:8000/api/v1/candidates")
        if response.status_code == 200:
            data = response.json()
            candidates = data.get('data', [])
            
            print(f"✅ API respondendo: {len(candidates)} candidatas")
            
            if candidates:
                first = candidates[0]
                source = first.get('source', 'Unknown')
                print(f"📋 Fonte dos dados: {source}")
                
                if source == 'TSE':
                    print("🎉 Integração TSE confirmada!")
                    return True
                else:
                    print("⚠️ Ainda usando dados mock")
                    return False
            else:
                print("❌ Nenhuma candidata encontrada")
                return False
        else:
            print(f"❌ Erro na API: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro na verificação: {e}")
        return False

if __name__ == "__main__":
    print("🗳️ Integração TSE ao Dashboard")
    print("=" * 40)
    
    # Executar integração
    success = integrate_tse_to_dashboard()
    
    if success:
        # Verificar resultado
        verify_integration()
        
        print("\n🌐 Dashboard atualizado!")
        print("📊 Acesse: http://localhost:8501")
        print("🔍 API: http://localhost:8000/docs")
    else:
        print("\n❌ Falha na integração")
        print("🔧 Verifique os logs para mais detalhes")
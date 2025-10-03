#!/usr/bin/env python3
"""
Script de teste dos endpoints da API
"""
import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_endpoint(endpoint, description):
    """Testa um endpoint e retorna o status"""
    try:
        print(f"🔍 Testando: {description}")
        response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {description} - Status: {response.status_code}")
            
            # Mostrar informações específicas baseadas no endpoint
            if endpoint == "/health":
                print(f"   📊 Database: {data.get('database')}")
                print(f"   📊 Data Available: {data.get('data_available')}")
                print(f"   📊 Candidate Count: {data.get('candidate_count')}")
            elif "candidates" in endpoint:
                print(f"   📊 Total Candidates: {data.get('total', 0)}")
                print(f"   📊 Returned: {len(data.get('data', []))}")
            
            return True
        else:
            print(f"❌ {description} - Status: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ {description} - Connection Error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ {description} - Error: {str(e)}")
        return False

def main():
    print("🚀 MVP Eleições Analytics - Teste de Endpoints")
    print("=" * 50)
    print(f"⏰ Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Base URL: {BASE_URL}")
    print("=" * 50)
    
    tests = [
        ("/health", "Health Check"),
        ("/api/v1/candidates", "Lista de Candidatos"),
        ("/api/v1/candidates?gender=F", "Candidatos Femininos"),
        ("/api/v1/candidates?state=SP", "Candidatos de SP"),
        ("/api/v1/candidates?year=2022", "Candidatos de 2022"),
        ("/api/v1/elections/years", "Anos de Eleições"),
    ]
    
    passed = 0
    total = len(tests)
    
    for endpoint, description in tests:
        if test_endpoint(endpoint, description):
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 RESULTADOS FINAIS:")
    print(f"✅ Testes Passaram: {passed}/{total}")
    print(f"❌ Testes Falharam: {total - passed}/{total}")
    print(f"📈 Taxa de Sucesso: {(passed/total)*100:.1f}%")
    
    # Verificar serviços
    print("\n🔗 SERVIÇOS DISPONÍVEIS:")
    print(f"📋 API Documentation: {BASE_URL}/docs")
    print(f"🎨 Streamlit Dashboard: http://localhost:8501")
    print(f"🗄️  PostgreSQL Database: localhost:5432")
    print(f"⚡ Redis Cache: localhost:6379")
    print(f"🪣 MinIO Storage: http://localhost:9000")
    
    if passed == total:
        print("\n🎉 PARABÉNS! Todos os testes passaram! O MVP está funcionando perfeitamente!")
        sys.exit(0)
    else:
        print(f"\n⚠️  ATENÇÃO: {total - passed} teste(s) falharam. Verifique os logs.")
        sys.exit(1)

if __name__ == "__main__":
    main()
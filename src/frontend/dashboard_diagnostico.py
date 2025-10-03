"""
Dashboard Simplificado para Diagnóstico
"""
import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="Eleições 2026 - Diagnóstico",
    page_icon="🔧",
    layout="wide"
)

st.title("🔧 Dashboard de Diagnóstico - Eleições 2026")

# Função para testar API
def test_api_connection():
    """Testa conectividade com a API"""
    try:
        response = requests.get('http://api:8000/health', timeout=10)
        return True, response.status_code, response.json()
    except Exception as e:
        return False, None, str(e)

# Teste de conectividade
st.header("🔍 Teste de Conectividade")

if st.button("🔄 Testar Conexão com API"):
    with st.spinner("Testando conexão..."):
        success, status, data = test_api_connection()
        
        if success:
            st.success(f"✅ API conectada! Status: {status}")
            st.json(data)
            
            # Teste de endpoints
            st.subheader("📊 Testando Endpoints")
            
            # Teste summary
            try:
                summary_response = requests.get('http://api:8000/analytics/summary', timeout=10)
                if summary_response.status_code == 200:
                    st.success("✅ Endpoint /analytics/summary funcionando")
                    summary_data = summary_response.json()
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Candidatas", summary_data.get('total_candidates', 0))
                    with col2:
                        st.metric("Estados", summary_data.get('states_covered', 0))
                    with col3:
                        st.metric("Score Médio", f"{summary_data.get('avg_diversity_score', 0):.3f}")
                    with col4:
                        st.metric("Taxa Diversidade", f"{summary_data.get('diversity_rate', 0):.1f}%")
                else:
                    st.error(f"❌ Erro no endpoint summary: {summary_response.status_code}")
            except Exception as e:
                st.error(f"❌ Erro ao testar summary: {e}")
            
            # Teste regional
            try:
                regional_response = requests.get('http://api:8000/analytics/regional', timeout=10)
                if regional_response.status_code == 200:
                    st.success("✅ Endpoint /analytics/regional funcionando")
                    regional_data = pd.DataFrame(regional_response.json())
                    if not regional_data.empty:
                        st.dataframe(regional_data)
                else:
                    st.error(f"❌ Erro no endpoint regional: {regional_response.status_code}")
            except Exception as e:
                st.error(f"❌ Erro ao testar regional: {e}")
            
            # Teste paginado
            try:
                paginated_response = requests.get('http://api:8000/candidates/paginated?limit=10', timeout=10)
                if paginated_response.status_code == 200:
                    st.success("✅ Endpoint /candidates/paginated funcionando")
                    paginated_data = paginated_response.json()
                    candidates = pd.DataFrame(paginated_data.get('candidates', []))
                    if not candidates.empty:
                        st.subheader("📋 Amostra de Candidatas")
                        st.dataframe(candidates[['name', 'state', 'region', 'diversity_score']])
                        st.info(f"Total de candidatas no banco: {paginated_data.get('total_count', 0)}")
                else:
                    st.error(f"❌ Erro no endpoint paginado: {paginated_response.status_code}")
            except Exception as e:
                st.error(f"❌ Erro ao testar paginado: {e}")
                
        else:
            st.error(f"❌ Erro de conexão: {data}")

# Informações do sistema
st.header("ℹ️ Informações do Sistema")

info_col1, info_col2 = st.columns(2)

with info_col1:
    st.subheader("🐳 Container Info")
    st.text(f"Timestamp: {datetime.now()}")
    
    # Teste de rede Docker
    try:
        import socket
        hostname = socket.gethostname()
        st.text(f"Hostname: {hostname}")
        
        # Tentar resolver DNS da API
        api_ip = socket.gethostbyname('api')
        st.text(f"API IP: {api_ip}")
        st.success("✅ DNS Resolution funcionando")
    except Exception as e:
        st.error(f"❌ Erro de DNS: {e}")

with info_col2:
    st.subheader("📦 Dependencies")
    
    # Verificar dependências
    dependencies = ['requests', 'pandas', 'streamlit']
    for dep in dependencies:
        try:
            __import__(dep)
            st.success(f"✅ {dep}")
        except ImportError:
            st.error(f"❌ {dep} não encontrado")

# Debug manual
st.header("🛠️ Debug Manual")

if st.checkbox("🔧 Modo Debug Avançado"):
    url_input = st.text_input("URL para testar", "http://api:8000/health")
    
    if st.button("🔍 Testar URL"):
        try:
            response = requests.get(url_input, timeout=10)
            st.success(f"Status: {response.status_code}")
            st.text("Headers:")
            st.json(dict(response.headers))
            st.text("Response:")
            try:
                st.json(response.json())
            except:
                st.text(response.text)
        except Exception as e:
            st.error(f"Erro: {e}")

st.markdown("---")
st.markdown("🔧 **Dashboard de Diagnóstico** - Use para identificar problemas de conectividade")
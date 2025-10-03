"""
Dashboard Excel-Style SIMPLIFICADO - Versão de Correção
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Eleições 2026 - Excel Filters",
    page_icon="🏛️",
    layout="wide"
)

# Função simples para API
def get_candidates_simple():
    """Função simples para buscar candidatas"""
    try:
        # Testar primeiro a API health
        health_response = requests.get("http://api:8000/health", timeout=10)
        st.sidebar.success(f"✅ API Health: {health_response.status_code}")
        
        # Buscar candidatas com parâmetros mínimos
        url = "http://api:8000/candidates/paginated"
        params = {"limit": 1000, "skip": 0}
        
        st.sidebar.info(f"🔗 Tentando: {url}")
        st.sidebar.info(f"📋 Parâmetros: {params}")
        
        response = requests.get(url, params=params, timeout=30)
        st.sidebar.info(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            candidates = data.get('candidates', [])
            st.sidebar.success(f"✅ Sucesso: {len(candidates)} candidatas")
            
            if candidates:
                df = pd.DataFrame(candidates)
                st.sidebar.info(f"📋 Colunas: {list(df.columns)}")
                return df
            else:
                st.sidebar.warning("⚠️ Lista de candidatas vazia")
                return pd.DataFrame()
        else:
            error_text = response.text[:200]
            st.sidebar.error(f"❌ Erro {response.status_code}: {error_text}")
            return pd.DataFrame()
            
    except requests.exceptions.ConnectionError:
        st.sidebar.error("🔌 Erro de conexão - API não disponível")
        return pd.DataFrame()
    except requests.exceptions.Timeout:
        st.sidebar.error("⏰ Timeout - API demorou muito para responder")
        return pd.DataFrame()
    except Exception as e:
        st.sidebar.error(f"💥 Erro inesperado: {str(e)}")
        return pd.DataFrame()

# Header
st.markdown("""
<div style="background: linear-gradient(90deg, #1f77b4, #ff7f0e); padding: 1rem; border-radius: 10px; color: white; text-align: center; margin-bottom: 2rem;">
    <h1>📊 Eleições 2026 - Dashboard Simplificado</h1>
    <p>Versão de Correção - Teste de Conectividade</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.header("🔧 Debug e Testes")

# Botão para testar
if st.sidebar.button("🔄 Testar Agora"):
    st.sidebar.write("--- INICIANDO TESTE ---")
    df = get_candidates_simple()
    
    if not df.empty:
        st.sidebar.write(f"✅ DataFrame criado: {df.shape}")
        st.session_state['candidates_df'] = df
    else:
        st.sidebar.write("❌ Falha ao criar DataFrame")

# Verificar se temos dados em cache
if 'candidates_df' in st.session_state:
    df = st.session_state['candidates_df']
    st.success(f"✅ Dados carregados: {len(df)} candidatas")
    
    # Mostrar informações básicas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📊 Total", f"{len(df):,}")
    
    with col2:
        if 'votes_received' in df.columns:
            total_votes = df['votes_received'].sum()
            st.metric("🗳️ Total Votos", f"{total_votes:,}")
        else:
            st.metric("🗳️ Dados Votação", "N/A")
    
    with col3:
        if 'state' in df.columns:
            states = df['state'].nunique()
            st.metric("🗺️ Estados", f"{states}")
        else:
            st.metric("🗺️ Estados", "N/A")
    
    # Mostrar amostra dos dados
    st.subheader("📋 Amostra dos Dados")
    st.dataframe(df.head(10), use_container_width=True)
    
    # Informações sobre colunas
    st.subheader("📊 Informações das Colunas")
    col_info = []
    for col in df.columns:
        non_null = df[col].notna().sum()
        col_info.append({
            'Coluna': col,
            'Tipo': str(df[col].dtype),
            'Não Nulos': non_null,
            '% Preenchido': f"{(non_null/len(df)*100):.1f}%"
        })
    
    col_df = pd.DataFrame(col_info)
    st.dataframe(col_df, use_container_width=True)
    
    # Se temos dados de votação, mostrar Top 10
    if 'votes_received' in df.columns and 'ballot_name' in df.columns:
        st.subheader("🏆 Top 10 Mais Votadas")
        top_10 = df.nlargest(10, 'votes_received')[['ballot_name', 'state', 'votes_received']]
        st.dataframe(top_10, use_container_width=True)
        
        # Gráfico simples
        fig = px.bar(
            top_10, 
            x='ballot_name', 
            y='votes_received',
            title="Top 10 Candidatas Mais Votadas"
        )
        fig.update_layout(xaxis_tickangle=45)
        st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("⚠️ Nenhum dado carregado ainda")
    st.info("👆 Use o botão 'Testar Agora' na sidebar para carregar os dados")

# Status da API
st.sidebar.markdown("---")
st.sidebar.subheader("🌐 Status dos Serviços")

# Testar conectividade básica
try:
    health_check = requests.get("http://api:8000/health", timeout=5)
    if health_check.status_code == 200:
        st.sidebar.success("✅ API Online")
        health_data = health_check.json()
        st.sidebar.json(health_data)
    else:
        st.sidebar.error(f"❌ API Erro {health_check.status_code}")
except:
    st.sidebar.error("❌ API Offline")

# Instruções
st.sidebar.markdown("---")
st.sidebar.markdown("""
### 📋 Instruções

1. **Clique em 'Testar Agora'** para carregar dados
2. **Verifique os logs** na sidebar
3. **Analise os dados** na tela principal

### 🔧 Debug Info
- Esta versão simplificada remove cache
- Testa conectividade passo a passo  
- Mostra erros detalhados
- Carrega dados mínimos primeiro
""")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>🔧 <strong>Versão de Debug</strong> - Eleições 2026 Analytics</p>
    <p>Testando conectividade e carregamento de dados</p>
</div>
""", unsafe_allow_html=True)
"""
Dashboard Streamlit Simplificado - Testando
"""
import streamlit as st
import requests
import pandas as pd
import json

# Configuração da página
st.set_page_config(
    page_title="Eleições 2026 - Analytics Feminino",
    page_icon="👩‍💼",
    layout="wide"
)

st.title("🗳️ Eleições 2026 - Analytics Feminino")
st.markdown("**MVP para análise de candidaturas femininas**")

# URL da API
API_BASE_URL = "http://api:8000/api/v1"

def load_candidates():
    """Carrega candidatos da API"""
    try:
        response = requests.get(f"{API_BASE_URL}/candidates?limit=100")
        if response.status_code == 200:
            data = response.json()
            return pd.DataFrame(data['data'])
        else:
            st.error(f"Erro ao carregar dados: {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro de conexão: {str(e)}")
        return pd.DataFrame()

# Sidebar
with st.sidebar:
    st.markdown("### 📋 Menu")
    page = st.selectbox(
        "Escolha uma seção:",
        ["📊 Visão Geral", "👩 Candidatas", "🎯 Filtros"]
    )

# Carregar dados
with st.spinner("Carregando dados..."):
    df = load_candidates()

if df.empty:
    st.error("❌ Não foi possível carregar os dados da API")
    st.info("Verifique se a API está funcionando em http://localhost:8000")
    st.stop()

# Páginas
if page == "📊 Visão Geral":
    st.header("📊 Visão Geral")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Candidatas", len(df))
    
    with col2:
        unique_states = df['state'].nunique()
        st.metric("Estados", unique_states)
    
    with col3:
        unique_races = df['race'].nunique()
        st.metric("Diversidade Racial", unique_races)
    
    with col4:
        unique_cargos = df['cargo'].nunique()
        st.metric("Tipos de Cargo", unique_cargos)
    
    st.subheader("📋 Dados das Candidatas")
    st.dataframe(df[['name', 'race', 'cargo', 'state', 'city']], use_container_width=True)

elif page == "👩 Candidatas":
    st.header("👩 Perfil das Candidatas")
    
    st.subheader("🌈 Distribuição por Cor/Raça")
    race_counts = df['race'].value_counts()
    st.bar_chart(race_counts)
    
    st.subheader("🏛️ Distribuição por Cargo")
    cargo_counts = df['cargo'].value_counts()
    st.bar_chart(cargo_counts)
    
    st.subheader("🗺️ Distribuição por Estado")
    state_counts = df['state'].value_counts()
    st.bar_chart(state_counts)

elif page == "🎯 Filtros":
    st.header("🎯 Filtros e Busca")
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_state = st.selectbox(
            "Filtrar por Estado:",
            ["Todos"] + list(df['state'].unique())
        )
    
    with col2:
        selected_race = st.selectbox(
            "Filtrar por Cor/Raça:",
            ["Todos"] + list(df['race'].unique())
        )
    
    # Aplicar filtros
    filtered_df = df.copy()
    
    if selected_state != "Todos":
        filtered_df = filtered_df[filtered_df['state'] == selected_state]
    
    if selected_race != "Todos":
        filtered_df = filtered_df[filtered_df['race'] == selected_race]
    
    st.subheader(f"📊 Resultados ({len(filtered_df)} candidatas)")
    
    if not filtered_df.empty:
        st.dataframe(
            filtered_df[['name', 'race', 'education', 'occupation', 'cargo', 'state']], 
            use_container_width=True
        )
    else:
        st.warning("Nenhuma candidata encontrada com os filtros selecionados.")

# Footer
st.markdown("---")
st.markdown("💡 **Dica:** Use a sidebar para navegar entre as seções!")
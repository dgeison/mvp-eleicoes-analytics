"""
Dashboard Avançado com gráficos e métricas
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configuração da página
st.set_page_config(
    page_title="Eleições 2026 - Analytics Avançado",
    page_icon="👩‍💼",
    layout="wide"
)

# URL da API
API_BASE_URL = "http://api:8000/api/v1"

@st.cache_data
def load_candidates():
    """Carrega candidatos da API com cache"""
    try:
        response = requests.get(f"{API_BASE_URL}/candidates?limit=1000")
        if response.status_code == 200:
            data = response.json()
            return pd.DataFrame(data['data'])
        else:
            st.error(f"Erro ao carregar dados: {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro de conexão: {str(e)}")
        return pd.DataFrame()

def create_diversity_chart(df):
    """Cria gráfico de diversidade racial"""
    race_counts = df['race'].value_counts()
    
    fig = px.pie(
        values=race_counts.values,
        names=race_counts.index,
        title="🌈 Diversidade Racial das Candidatas",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig

def create_state_distribution(df):
    """Cria gráfico de distribuição por estado"""
    state_counts = df['state'].value_counts().head(10)
    
    fig = px.bar(
        x=state_counts.values,
        y=state_counts.index,
        orientation='h',
        title="🗺️ Top 10 Estados com Mais Candidatas",
        labels={'x': 'Número de Candidatas', 'y': 'Estado'}
    )
    
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    return fig

def create_cargo_analysis(df):
    """Cria análise por cargo"""
    cargo_counts = df['cargo'].value_counts()
    
    fig = px.bar(
        x=cargo_counts.index,
        y=cargo_counts.values,
        title="🏛️ Distribuição por Cargo Político",
        labels={'x': 'Cargo', 'y': 'Número de Candidatas'}
    )
    
    fig.update_xaxis(tickangle=45)
    return fig

def create_diversity_score_distribution(df):
    """Cria distribuição do score de diversidade"""
    fig = px.histogram(
        df,
        x='diversity_score',
        nbins=20,
        title="📊 Distribuição do Score de Diversidade",
        labels={'x': 'Score de Diversidade', 'y': 'Número de Candidatas'}
    )
    
    return fig

def main():
    """Função principal do dashboard"""
    
    # Header
    st.title("🗳️ Eleições 2026 - Analytics Avançado")
    st.markdown("**Análise aprofundada de candidaturas femininas**")
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🎛️ Controles")
        
        # Filtros
        show_filters = st.checkbox("Mostrar Filtros Avançados")
        
        if show_filters:
            st.markdown("#### 🔍 Filtros")
            selected_states = st.multiselect("Estados:", options=[])
            selected_races = st.multiselect("Cor/Raça:", options=[])
            min_diversity_score = st.slider("Score Mínimo de Diversidade:", 0.0, 1.0, 0.0)
    
    # Carregar dados
    with st.spinner("🔄 Carregando dados..."):
        df = load_candidates()
    
    if df.empty:
        st.error("❌ Não foi possível carregar os dados")
        st.stop()
    
    # Aplicar filtros se existirem
    if 'show_filters' in locals() and show_filters:
        if selected_states:
            df = df[df['state'].isin(selected_states)]
        if selected_races:
            df = df[df['race'].isin(selected_races)]
        if min_diversity_score > 0:
            df = df[df['diversity_score'] >= min_diversity_score]
    
    # Métricas principais
    st.markdown("### 📊 Métricas Principais")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("👥 Total Candidatas", len(df))
    
    with col2:
        unique_states = df['state'].nunique()
        st.metric("🗺️ Estados", unique_states)
    
    with col3:
        minority_count = df['is_minority_race'].sum()
        st.metric("🌈 Diversidade Racial", f"{minority_count}/{len(df)}")
    
    with col4:
        avg_diversity = df['diversity_score'].mean()
        st.metric("📈 Score Médio", f"{avg_diversity:.2f}")
    
    with col5:
        max_diversity = df['diversity_score'].max()
        st.metric("🏆 Score Máximo", f"{max_diversity:.2f}")
    
    # Gráficos principais
    st.markdown("### 📈 Análises Visuais")
    
    # Primeira linha de gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        fig_diversity = create_diversity_chart(df)
        st.plotly_chart(fig_diversity, use_container_width=True)
    
    with col2:
        fig_states = create_state_distribution(df)
        st.plotly_chart(fig_states, use_container_width=True)
    
    # Segunda linha de gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        fig_cargos = create_cargo_analysis(df)
        st.plotly_chart(fig_cargos, use_container_width=True)
    
    with col2:
        fig_scores = create_diversity_score_distribution(df)
        st.plotly_chart(fig_scores, use_container_width=True)
    
    # Tabela detalhada
    st.markdown("### 📋 Dados Detalhados")
    
    # Filtros para a tabela
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_name = st.text_input("🔍 Buscar por nome:")
    
    with col2:
        filter_state = st.selectbox("Filtrar por estado:", ["Todos"] + list(df['state'].unique()))
    
    with col3:
        filter_race = st.selectbox("Filtrar por raça:", ["Todos"] + list(df['race'].unique()))
    
    # Aplicar filtros da tabela
    table_df = df.copy()
    
    if search_name:
        table_df = table_df[table_df['name'].str.contains(search_name, case=False, na=False)]
    
    if filter_state != "Todos":
        table_df = table_df[table_df['state'] == filter_state]
    
    if filter_race != "Todos":
        table_df = table_df[table_df['race'] == filter_race]
    
    # Exibir tabela
    st.dataframe(
        table_df[['name', 'race', 'education', 'occupation', 'cargo', 'state', 'diversity_score']], 
        use_container_width=True
    )
    
    # Insights automáticos
    st.markdown("### 🧠 Insights Automáticos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"🎯 **Estado com mais candidatas:** {df['state'].value_counts().index[0]} ({df['state'].value_counts().iloc[0]} candidatas)")
        
        most_common_race = df['race'].value_counts().index[0]
        st.info(f"🌈 **Cor/raça mais comum:** {most_common_race} ({df['race'].value_counts().iloc[0]} candidatas)")
    
    with col2:
        most_common_cargo = df['cargo'].value_counts().index[0]
        st.info(f"🏛️ **Cargo mais disputado:** {most_common_cargo} ({df['cargo'].value_counts().iloc[0]} candidatas)")
        
        high_diversity = len(df[df['diversity_score'] > 0.8])
        st.info(f"📈 **Alto potencial de diversidade:** {high_diversity} candidatas (score > 0.8)")
    
    # Footer
    st.markdown("---")
    st.markdown("💡 **Dica:** Use os filtros da sidebar para análises mais específicas!")

if __name__ == "__main__":
    main()
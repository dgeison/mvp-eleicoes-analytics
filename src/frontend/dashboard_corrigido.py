"""
Dashboard Corrigido - Eleições 2026 Analytics
Interface otimizada para grandes volumes de dados - VERSÃO CORRIGIDA
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
import time

# Configuração da página
st.set_page_config(
    page_title="Eleições 2026 - Analytics Corrigido",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuração da API (sem cache para debug)
def get_api_config():
    return {
        'base_url': 'http://api:8000',
        'timeout': 30
    }

# Função para fazer requisições com tratamento de erro
def safe_api_call(endpoint, params=None):
    """Faz requisição segura para a API"""
    try:
        config = get_api_config()
        url = f"{config['base_url']}/{endpoint.lstrip('/')}"
        
        response = requests.get(
            url,
            params=params or {},
            timeout=config['timeout']
        )
        
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
            
    except requests.exceptions.Timeout:
        return False, "Timeout na conexão"
    except requests.exceptions.ConnectionError:
        return False, "Erro de conexão com a API"
    except Exception as e:
        return False, f"Erro inesperado: {str(e)}"

# Cache simples com session state
@st.cache_data(ttl=300)
def fetch_summary_stats():
    """Buscar estatísticas resumidas"""
    success, data = safe_api_call('analytics/summary')
    return data if success else {}

@st.cache_data(ttl=300)
def fetch_regional_stats():
    """Buscar dados regionais"""
    success, data = safe_api_call('analytics/regional')
    return pd.DataFrame(data) if success and data else pd.DataFrame()

def fetch_candidates_paginated(limit=100, page=1, filters=None):
    """Buscar candidatas com paginação"""
    params = {
        'limit': limit,
        'skip': (page - 1) * limit
    }
    
    if filters:
        params.update(filters)
    
    success, data = safe_api_call('candidates/paginated', params)
    
    if success and data:
        return pd.DataFrame(data.get('candidates', [])), data.get('total_count', 0)
    else:
        return pd.DataFrame(), 0

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #FF6B6B;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🏛️ Eleições 2026 - Analytics Corrigido</h1>
    <p>Análise de Candidaturas Femininas - Versão Estável</p>
</div>
""", unsafe_allow_html=True)

# Teste de conectividade na sidebar
st.sidebar.header("🔍 Status do Sistema")

# Botão de teste de conectividade
if st.sidebar.button("🔄 Testar Conexão"):
    with st.sidebar:
        with st.spinner("Testando..."):
            success, data = safe_api_call('health')
            
            if success:
                st.success("✅ API Online")
                st.json(data)
            else:
                st.error(f"❌ API Offline: {data}")

# Sidebar com filtros
st.sidebar.header("🎛️ Configurações")

items_per_page = st.sidebar.selectbox(
    "Itens por página",
    [50, 100, 200, 500],
    index=1
)

current_page = st.sidebar.number_input(
    "Página atual",
    min_value=1,
    value=1
)

# Filtros básicos
st.sidebar.subheader("🔍 Filtros")
region_filter = st.sidebar.selectbox(
    "Região",
    ["Todas", "NORTE", "NORDESTE", "SUDESTE", "SUL", "CENTRO-OESTE"]
)

source_filter = st.sidebar.selectbox(
    "Fonte dos Dados",
    ["Todas", "TSE", "Manual"]
)

# Abas principais
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Visão Geral", 
    "🗺️ Análise Regional", 
    "🔍 Explorar Dados",
    "🔧 Diagnóstico"
])

with tab1:
    st.header("📊 Visão Geral do Sistema")
    
    # Buscar estatísticas
    with st.spinner("Carregando estatísticas..."):
        summary_stats = fetch_summary_stats()
    
    if summary_stats:
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total de Candidatas",
                f"{summary_stats.get('total_candidates', 0):,}",
                summary_stats.get('new_candidates_today', 0)
            )
        
        with col2:
            st.metric(
                "Estados Cobertos",
                summary_stats.get('states_covered', 0),
                summary_stats.get('new_states', 0)
            )
        
        with col3:
            st.metric(
                "Score Médio",
                f"{summary_stats.get('avg_diversity_score', 0):.3f}",
                f"{summary_stats.get('score_improvement', 0):.3f}"
            )
        
        with col4:
            st.metric(
                "Taxa de Diversidade",
                f"{summary_stats.get('diversity_rate', 0):.1f}%",
                f"{summary_stats.get('diversity_improvement', 0):.1f}%"
            )
        
        # Informações adicionais
        st.subheader("📈 Distribuição por Fonte")
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**TSE**: {summary_stats.get('tse_candidates', 0):,} candidatas")
        with col2:
            st.info(f"**Manual**: {summary_stats.get('manual_candidates', 0):,} candidatas")
    
    else:
        st.error("❌ Não foi possível carregar estatísticas da API")

with tab2:
    st.header("🗺️ Análise Regional")
    
    with st.spinner("Carregando dados regionais..."):
        regional_data = fetch_regional_stats()
    
    if not regional_data.empty:
        # Gráfico de barras
        fig_bar = px.bar(
            regional_data,
            x='region',
            y='total_candidates',
            title="Candidatas por Região",
            color='avg_diversity_score',
            color_continuous_scale='viridis',
            labels={
                'region': 'Região',
                'total_candidates': 'Total de Candidatas',
                'avg_diversity_score': 'Score Médio'
            }
        )
        fig_bar.update_layout(height=400)
        st.plotly_chart(fig_bar, use_container_width=True)
        
        # Tabela regional
        st.subheader("📋 Dados Regionais Detalhados")
        st.dataframe(
            regional_data.style.format({
                'avg_diversity_score': '{:.3f}',
                'total_candidates': '{:,}'
            }),
            use_container_width=True
        )
    else:
        st.error("❌ Não foi possível carregar dados regionais")

with tab3:
    st.header("🔍 Explorar Dados")
    
    # Aplicar filtros
    filters = {}
    if region_filter != "Todas":
        filters['region'] = region_filter
    if source_filter != "Todas":
        filters['source'] = source_filter
    
    # Buscar dados paginados
    with st.spinner(f"Carregando {items_per_page} candidatas da página {current_page}..."):
        df, total_count = fetch_candidates_paginated(
            limit=items_per_page,
            page=current_page,
            filters=filters
        )
    
    if not df.empty:
        # Informações da paginação
        start_index = (current_page - 1) * items_per_page + 1
        end_index = start_index + len(df) - 1
        
        st.info(f"📄 Mostrando registros {start_index} a {end_index} de {total_count:,} total")
        
        # Filtros adicionais locais
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'cargo' in df.columns:
                cargo_filter = st.selectbox(
                    "Filtrar por Cargo",
                    ["Todos"] + sorted([c for c in df['cargo'].unique() if pd.notna(c)])
                )
            else:
                cargo_filter = "Todos"
        
        with col2:
            if 'education' in df.columns:
                education_filter = st.selectbox(
                    "Filtrar por Educação",
                    ["Todas"] + sorted([e for e in df['education'].unique() if pd.notna(e)])
                )
            else:
                education_filter = "Todas"
        
        with col3:
            score_min = st.slider(
                "Score Mínimo",
                min_value=0.0,
                max_value=1.0,
                value=0.0,
                step=0.1
            )
        
        # Aplicar filtros locais
        df_filtered = df.copy()
        
        if cargo_filter != "Todos":
            df_filtered = df_filtered[df_filtered['cargo'] == cargo_filter]
        
        if education_filter != "Todas":
            df_filtered = df_filtered[df_filtered['education'] == education_filter]
        
        if 'diversity_score' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['diversity_score'] >= score_min]
        
        # Mostrar dados filtrados
        st.subheader(f"📊 Dados Filtrados ({len(df_filtered)} registros)")
        
        if not df_filtered.empty:
            # Selecionar colunas disponíveis para exibição
            available_columns = df_filtered.columns.tolist()
            display_columns = []
            
            for col in ['name', 'ballot_name', 'state', 'region', 'cargo', 'education', 'diversity_score', 'source']:
                if col in available_columns:
                    display_columns.append(col)
            
            if display_columns:
                display_df = df_filtered[display_columns].copy()
                
                # Formatar scores se existirem
                if 'diversity_score' in display_df.columns:
                    display_df = display_df.style.format({'diversity_score': '{:.3f}'})
                
                st.dataframe(display_df, use_container_width=True, height=400)
                
                # Botão para download
                if st.button("📥 Baixar dados filtrados (CSV)"):
                    csv = df_filtered.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f'candidatas_filtradas_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                        mime='text/csv'
                    )
            else:
                st.warning("Nenhuma coluna de exibição disponível")
        else:
            st.warning("Nenhum registro encontrado com os filtros aplicados.")
    
    else:
        st.error("❌ Não foi possível carregar dados das candidatas")

with tab4:
    st.header("🔧 Diagnóstico do Sistema")
    
    # Status da API
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🌐 Status da API")
        
        if st.button("🔄 Testar Todos os Endpoints"):
            endpoints = [
                ('health', 'Health Check'),
                ('analytics/summary', 'Estatísticas Resumidas'),
                ('analytics/regional', 'Dados Regionais'),
                ('candidates/paginated?limit=5', 'Candidatas Paginadas')
            ]
            
            for endpoint, name in endpoints:
                success, data = safe_api_call(endpoint)
                if success:
                    st.success(f"✅ {name}")
                else:
                    st.error(f"❌ {name}: {data}")
    
    with col2:
        st.subheader("📊 Informações Técnicas")
        
        st.metric("Timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        st.metric("Página Atual", current_page)
        st.metric("Itens por Página", items_per_page)
        
        if st.button("🗑️ Limpar Cache"):
            st.cache_data.clear()
            st.success("Cache limpo!")
            time.sleep(1)
            st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>🏛️ <strong>Eleições 2026 Analytics</strong> | 
    Versão Corrigida | 
    🔧 Com Diagnóstico Integrado</p>
</div>
""", unsafe_allow_html=True)
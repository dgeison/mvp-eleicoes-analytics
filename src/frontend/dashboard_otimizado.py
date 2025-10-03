"""
Dashboard Otimizado - Eleições 2026 Analytics
Interface otimizada para grandes volumes de dados
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

# Configuração da página com cache otimizado
st.set_page_config(
    page_title="Eleições 2026 - Analytics Otimizado",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cache das configurações
@st.cache_data(ttl=300)  # Cache por 5 minutos
def get_api_config():
    return {
        'base_url': 'http://api:8000',
        'timeout': 30
    }

# Cache dos dados com compressão
@st.cache_data(ttl=600, show_spinner=False)  # Cache por 10 minutos
def fetch_candidates_optimized(limit=1000, page=1, filters=None):
    """Fetch paginado com otimizações"""
    try:
        config = get_api_config()
        params = {
            'limit': limit,
            'skip': (page - 1) * limit
        }
        
        # Adicionar filtros se existirem
        if filters:
            params.update(filters)
        
        response = requests.get(
            f"{config['base_url']}/candidates/",
            params=params,
            timeout=config['timeout']
        )
        
        if response.status_code == 200:
            data = response.json()
            return pd.DataFrame(data.get('candidates', []))
        else:
            st.error(f"Erro na API: {response.status_code}")
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=600)
def fetch_summary_stats():
    """Buscar estatísticas resumidas (mais rápido)"""
    try:
        config = get_api_config()
        response = requests.get(
            f"{config['base_url']}/analytics/summary",
            timeout=config['timeout']
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {}
            
    except Exception as e:
        st.error(f"Erro ao carregar estatísticas: {e}")
        return {}

@st.cache_data(ttl=600)
def fetch_regional_stats():
    """Buscar dados agregados por região"""
    try:
        config = get_api_config()
        response = requests.get(
            f"{config['base_url']}/analytics/regional",
            timeout=config['timeout']
        )
        
        if response.status_code == 200:
            return pd.DataFrame(response.json())
        else:
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Erro ao carregar dados regionais: {e}")
        return pd.DataFrame()

# CSS otimizado
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
    .stDataFrame {
        border: 1px solid #e0e0e0;
        border-radius: 5px;
    }
    .loading-spinner {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100px;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🏛️ Eleições 2026 - Analytics Otimizado</h1>
    <p>Análise Inteligente de Candidaturas Femininas com Performance Otimizada</p>
</div>
""", unsafe_allow_html=True)

# Sidebar com filtros otimizados
st.sidebar.header("🎛️ Filtros e Configurações")

# Configurações de visualização
st.sidebar.subheader("📊 Configurações de Dados")
items_per_page = st.sidebar.selectbox(
    "Itens por página",
    [100, 500, 1000, 2000],
    index=2
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

# Buscar estatísticas resumidas primeiro (mais rápido)
with st.spinner("Carregando estatísticas..."):
    summary_stats = fetch_summary_stats()

# Criar abas para organizar o conteúdo
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Visão Geral", 
    "🗺️ Análise Regional", 
    "📈 Rankings", 
    "🔍 Explorar Dados",
    "⚙️ Performance"
])

with tab1:
    st.header("📊 Visão Geral do Sistema")
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total de Candidatas",
            summary_stats.get('total_candidates', 'Carregando...'),
            summary_stats.get('new_candidates_today', 0)
        )
    
    with col2:
        st.metric(
            "Estados Cobertos",
            summary_stats.get('states_covered', 'Carregando...'),
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
    
    # Gráfico de distribuição rápido
    st.subheader("📈 Distribuição por Fonte")
    regional_data = fetch_regional_stats()
    
    if not regional_data.empty:
        fig_sources = px.pie(
            regional_data,
            values='total_candidates',
            names='region',
            title="Distribuição Regional de Candidatas",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_sources.update_layout(height=400)
        st.plotly_chart(fig_sources, use_container_width=True)

with tab2:
    st.header("🗺️ Análise Regional Detalhada")
    
    if not regional_data.empty:
        # Mapa de calor regional
        col1, col2 = st.columns(2)
        
        with col1:
            fig_bar = px.bar(
                regional_data,
                x='region',
                y='total_candidates',
                title="Candidatas por Região",
                color='avg_diversity_score',
                color_continuous_scale='viridis'
            )
            fig_bar.update_layout(height=400)
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with col2:
            fig_scatter = px.scatter(
                regional_data,
                x='total_candidates',
                y='avg_diversity_score',
                size='total_candidates',
                color='region',
                title="Relação: Quantidade vs Score Médio",
                hover_data=['region']
            )
            fig_scatter.update_layout(height=400)
            st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Tabela regional
        st.subheader("📋 Dados Regionais Detalhados")
        st.dataframe(
            regional_data.style.format({
                'avg_diversity_score': '{:.3f}',
                'total_candidates': '{:,}'
            }),
            use_container_width=True
        )

with tab3:
    st.header("📈 Rankings e Top Performers")
    
    # Filtros para busca otimizada
    filters = {}
    if region_filter != "Todas":
        filters['region'] = region_filter
    if source_filter != "Todas":
        filters['source'] = source_filter
    
    # Buscar dados paginados
    with st.spinner(f"Carregando {items_per_page} candidatas..."):
        df = fetch_candidates_optimized(
            limit=items_per_page,
            page=current_page,
            filters=filters
        )
    
    if not df.empty:
        # Top 10 por diversity score
        st.subheader("🏆 Top 10 Candidatas - Score de Diversidade")
        top_diversity = df.nlargest(10, 'diversity_score')[
            ['name', 'state', 'region', 'diversity_score', 'cargo', 'source']
        ]
        
        fig_top = px.bar(
            top_diversity,
            x='diversity_score',
            y='name',
            orientation='h',
            color='region',
            title="Top 10 - Score de Diversidade",
            hover_data=['state', 'cargo']
        )
        fig_top.update_layout(height=500, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_top, use_container_width=True)
        
        # Tabela detalhada
        st.dataframe(
            top_diversity.style.format({
                'diversity_score': '{:.3f}'
            }),
            use_container_width=True
        )

with tab4:
    st.header("🔍 Explorar Dados Detalhados")
    
    if not df.empty:
        # Informações da paginação
        total_showing = len(df)
        start_index = (current_page - 1) * items_per_page + 1
        end_index = start_index + total_showing - 1
        
        st.info(f"📄 Mostrando registros {start_index} a {end_index} (Total na página: {total_showing})")
        
        # Filtros adicionais
        col1, col2, col3 = st.columns(3)
        
        with col1:
            cargo_filter = st.selectbox(
                "Filtrar por Cargo",
                ["Todos"] + sorted(df['cargo'].unique().tolist())
            )
        
        with col2:
            education_filter = st.selectbox(
                "Filtrar por Educação",
                ["Todas"] + sorted(df['education'].unique().tolist())
            )
        
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
        
        df_filtered = df_filtered[df_filtered['diversity_score'] >= score_min]
        
        # Mostrar dados filtrados
        st.subheader(f"📊 Dados Filtrados ({len(df_filtered)} registros)")
        
        if not df_filtered.empty:
            # Colunas selecionadas para visualização
            display_columns = [
                'name', 'ballot_name', 'state', 'region', 'cargo', 
                'education', 'diversity_score', 'source'
            ]
            
            st.dataframe(
                df_filtered[display_columns].style.format({
                    'diversity_score': '{:.3f}'
                }),
                use_container_width=True,
                height=400
            )
            
            # Botão para download
            csv = df_filtered.to_csv(index=False)
            st.download_button(
                label="📥 Baixar dados filtrados (CSV)",
                data=csv,
                file_name=f'candidatas_filtradas_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                mime='text/csv'
            )
        else:
            st.warning("Nenhum registro encontrado com os filtros aplicados.")

with tab5:
    st.header("⚙️ Performance e Sistema")
    
    # Informações de performance
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🚀 Status do Sistema")
        
        # Teste de conectividade
        try:
            start_time = time.time()
            config = get_api_config()
            response = requests.get(f"{config['base_url']}/health", timeout=5)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                st.success(f"✅ API Online ({response_time:.0f}ms)")
                api_status = response.json()
                
                for key, value in api_status.items():
                    if key != 'timestamp':
                        st.metric(key.replace('_', ' ').title(), value)
            else:
                st.error(f"❌ API com problemas ({response.status_code})")
        except Exception as e:
            st.error(f"❌ API inacessível: {e}")
    
    with col2:
        st.subheader("📈 Estatísticas de Cache")
        
        cache_info = st.cache_data.get_stats()
        
        st.metric("Cache Hits", len(cache_info))
        
        if st.button("🗑️ Limpar Cache"):
            st.cache_data.clear()
            st.success("Cache limpo com sucesso!")
            time.sleep(1)
            st.rerun()
    
    # Configurações avançadas
    st.subheader("⚙️ Configurações Avançadas")
    
    if st.button("🔄 Recarregar Dados"):
        st.cache_data.clear()
        st.success("Dados recarregados!")
        time.sleep(1)
        st.rerun()
    
    # Informações técnicas
    st.subheader("🔧 Informações Técnicas")
    
    tech_info = {
        "Itens por página atual": items_per_page,
        "Página atual": current_page,
        "Registros carregados": len(df) if 'df' in locals() else 0,
        "Cache TTL": "10 minutos",
        "Última atualização": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    for key, value in tech_info.items():
        st.metric(key, value)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>🏛️ <strong>Eleições 2026 Analytics</strong> | 
    Versão Otimizada para Alto Volume de Dados | 
    ⚡ Performance Enhanced</p>
</div>
""", unsafe_allow_html=True)

# Auto-refresh opcional
if st.sidebar.checkbox("🔄 Auto-refresh (30s)"):
    time.sleep(30)
    st.rerun()
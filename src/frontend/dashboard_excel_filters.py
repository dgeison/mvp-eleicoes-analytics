"""
Dashboard com Filtros Excel-Style - Eleições 2026 Analytics
Interface com filtros de dropdown nas colunas das tabelas
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
    page_title="Eleições 2026 - Excel Filters",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuração da API
def get_api_config():
    return {
        'base_url': 'http://api:8000',
        'timeout': 30
    }

# Função para fazer requisições com tratamento de erro
def safe_api_call(endpoint, params=None, debug=False):
    """Faz requisição segura para a API"""
    try:
        config = get_api_config()
        url = f"{config['base_url']}/{endpoint.lstrip('/')}"
        
        # Debug info apenas se solicitado
        if debug:
            st.sidebar.write(f"🔗 Conectando: {url}")
        
        response = requests.get(
            url,
            params=params or {},
            timeout=config['timeout']
        )
        
        if response.status_code == 200:
            data = response.json()
            if debug:
                st.sidebar.write(f"✅ Sucesso: {len(data.get('candidates', []))} registros")
            return True, data
        else:
            error_msg = f"HTTP {response.status_code}: {response.text}"
            if debug:
                st.sidebar.write(f"❌ Erro: {error_msg}")
            return False, error_msg
            
    except requests.exceptions.Timeout:
        error_msg = "Timeout na conexão"
        if debug:
            st.sidebar.write(f"⏰ {error_msg}")
        return False, error_msg
    except requests.exceptions.ConnectionError:
        error_msg = "Erro de conexão com a API"
        if debug:
            st.sidebar.write(f"🔌 {error_msg}")
        return False, error_msg
    except Exception as e:
        error_msg = f"Erro inesperado: {str(e)}"
        if debug:
            st.sidebar.write(f"💥 {error_msg}")
        return False, error_msg

# Cache para dados
@st.cache_data(ttl=300)
def fetch_summary_stats():
    """Buscar estatísticas resumidas"""
    success, data = safe_api_call('analytics/summary')
    return data if success else {}

def fetch_all_candidates_no_cache():
    """Buscar candidatas SEM cache para debug"""
    success, data = safe_api_call('candidates/paginated', {'limit': 10000, 'skip': 0}, debug=True)
    
    if success and data:
        df = pd.DataFrame(data.get('candidates', []))
        return df
    else:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def fetch_all_candidates():
    """Buscar todas as candidatas para filtros Excel-style"""
    return fetch_all_candidates_no_cache()

def create_excel_style_filter(df, column_name, key_suffix=""):
    """Criar um filtro estilo Excel para uma coluna específica"""
    if column_name not in df.columns:
        return None
    
    unique_values = sorted(df[column_name].dropna().unique())
    
    if len(unique_values) == 0:
        return None
    
    # Container para o filtro
    with st.expander(f"🔽 Filtrar {column_name.replace('_', ' ').title()}", expanded=False):
        # Opção "Selecionar Tudo"
        select_all = st.checkbox(
            f"✅ Selecionar Tudo ({len(unique_values)} itens)",
            value=True,
            key=f"select_all_{column_name}_{key_suffix}"
        )
        
        if select_all:
            selected_values = st.multiselect(
                f"Valores para {column_name}:",
                options=unique_values,
                default=unique_values,
                key=f"filter_{column_name}_{key_suffix}"
            )
        else:
            selected_values = st.multiselect(
                f"Valores para {column_name}:",
                options=unique_values,
                default=[],
                key=f"filter_{column_name}_{key_suffix}"
            )
    
    return selected_values

def apply_excel_filters(df, filters_dict):
    """Aplicar múltiplos filtros estilo Excel no DataFrame"""
    filtered_df = df.copy()
    
    for column, selected_values in filters_dict.items():
        if selected_values and column in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[column].isin(selected_values)]
    
    return filtered_df

# CSS personalizado para interface Excel-style
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .filter-container {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #dee2e6;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #1f77b4;
    }
    .excel-table {
        border: 1px solid #ddd;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>📊 Eleições 2026 - Filtros Excel-Style</h1>
    <p>Interface com Filtros de Dropdown nas Colunas + Dados de Votação</p>
</div>
""", unsafe_allow_html=True)

# Sidebar básica
st.sidebar.header("🔧 Configurações")

# Teste de conectividade
if st.sidebar.button("🔄 Testar Conexão"):
    with st.sidebar:
        with st.spinner("Testando..."):
            success, data = safe_api_call('health', debug=True)
            
            if success:
                st.success("✅ API Online")
                st.json(data)
            else:
                st.error(f"❌ API Offline: {data}")

# Botão para limpar cache
if st.sidebar.button("🗑️ Limpar Cache"):
    st.cache_data.clear()
    st.success("Cache limpo!")
    st.rerun()

# Configurações de exibição
items_per_page = st.sidebar.selectbox(
    "Itens por página",
    [50, 100, 200, 500, 1000],
    index=2
)

show_voting_data = st.sidebar.checkbox(
    "📊 Mostrar Dados de Votação",
    value=True,
    help="Incluir colunas de votos recebidos e percentual"
)

# Tabs principais
tab1, tab2, tab3 = st.tabs([
    "📊 Visão Geral com Filtros Excel",
    "🗳️ Análise de Votação", 
    "📈 Dashboard Tradicional"
])

with tab1:
    st.header("📊 Dados com Filtros Excel-Style")
    
    # Carregar todos os dados
    with st.spinner("Carregando dados..."):
        df_all = fetch_all_candidates()
        
        # Debug info
        st.sidebar.write("### 🔍 Debug Info")
        if not df_all.empty:
            st.sidebar.write(f"📊 DataFrame shape: {df_all.shape}")
            st.sidebar.write(f"📋 Colunas: {list(df_all.columns)}")
            st.sidebar.write(f"🗳️ Tem votes_received: {'votes_received' in df_all.columns}")
            if 'votes_received' in df_all.columns:
                st.sidebar.write(f"📈 Votos não nulos: {df_all['votes_received'].notna().sum()}")
        else:
            st.sidebar.write("❌ DataFrame vazio!")
    
    if not df_all.empty:
        st.success(f"✅ {len(df_all):,} candidatas carregadas com sucesso!")
        
        # Mostrar informações sobre votação
        if 'votes_received' in df_all.columns:
            total_votes = df_all['votes_received'].sum()
            st.info(f"🗳️ Total de votos no dataset: {total_votes:,}")
        
        # Área de filtros Excel-style
        st.markdown("""
        <div class="filter-container">
        <h3>🔽 Filtros Interativos (Estilo Excel)</h3>
        <p>Use os dropdowns abaixo para filtrar os dados como no Excel. Cada filtro mostra valores únicos da coluna.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Criar filtros em colunas
        filter_cols = st.columns(3)
        filters_dict = {}
        
        # Filtros principais
        with filter_cols[0]:
            st.markdown("#### 🏛️ **Dados Políticos**")
            
            if 'cargo' in df_all.columns:
                filters_dict['cargo'] = create_excel_style_filter(df_all, 'cargo', 'tab1')
            
            if 'state' in df_all.columns:
                filters_dict['state'] = create_excel_style_filter(df_all, 'state', 'tab1')
            
            if 'region' in df_all.columns:
                filters_dict['region'] = create_excel_style_filter(df_all, 'region', 'tab1')
        
        with filter_cols[1]:
            st.markdown("#### 👤 **Dados Demográficos**")
            
            if 'race' in df_all.columns:
                filters_dict['race'] = create_excel_style_filter(df_all, 'race', 'tab1')
            
            if 'education' in df_all.columns:
                filters_dict['education'] = create_excel_style_filter(df_all, 'education', 'tab1')
        
        with filter_cols[2]:
            st.markdown("#### 📊 **Dados Técnicos**")
            
            if 'source' in df_all.columns:
                filters_dict['source'] = create_excel_style_filter(df_all, 'source', 'tab1')
            
            # Filtro por faixa de votos (se dados de votação existirem)
            if show_voting_data and 'votes_received' in df_all.columns:
                st.markdown("**🗳️ Filtro por Votos**")
                votes_range = st.slider(
                    "Faixa de votos recebidos:",
                    min_value=int(df_all['votes_received'].min()),
                    max_value=int(df_all['votes_received'].max()),
                    value=(int(df_all['votes_received'].min()), int(df_all['votes_received'].max())),
                    step=1000,
                    key="votes_range_tab1"
                )
        
        # Aplicar filtros
        filtered_df = apply_excel_filters(df_all, {k: v for k, v in filters_dict.items() if v is not None})
        
        # Filtrar por votos se ativo
        if show_voting_data and 'votes_received' in filtered_df.columns and 'votes_range' in locals():
            filtered_df = filtered_df[
                (filtered_df['votes_received'] >= votes_range[0]) & 
                (filtered_df['votes_received'] <= votes_range[1])
            ]
        
        # Estatísticas dos dados filtrados
        st.markdown("---")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "📊 Total Filtrado",
                f"{len(filtered_df):,}",
                f"{len(filtered_df) - len(df_all):,}" if len(filtered_df) != len(df_all) else "Sem filtro"
            )
        
        with col2:
            if 'diversity_score' in filtered_df.columns and not filtered_df.empty:
                avg_score = filtered_df['diversity_score'].mean()
                st.metric(
                    "⭐ Score Médio",
                    f"{avg_score:.3f}",
                    f"{avg_score - df_all['diversity_score'].mean():.3f}"
                )
        
        with col3:
            if show_voting_data and 'votes_received' in filtered_df.columns and not filtered_df.empty:
                total_votes = filtered_df['votes_received'].sum()
                st.metric(
                    "🗳️ Total de Votos",
                    f"{total_votes:,}",
                    help="Soma dos votos das candidatas filtradas"
                )
        
        with col4:
            if 'state' in filtered_df.columns and not filtered_df.empty:
                unique_states = filtered_df['state'].nunique()
                st.metric(
                    "🗺️ Estados Únicos",
                    f"{unique_states}",
                    help="Número de estados representados"
                )
        
        # Tabela de dados filtrados
        st.markdown("---")
        st.subheader(f"📋 Dados Filtrados ({len(filtered_df)} registros)")
        
        if not filtered_df.empty:
            # Selecionar colunas para exibição
            base_columns = ['name', 'ballot_name', 'state', 'cargo', 'race', 'education']
            
            if show_voting_data:
                base_columns.extend(['votes_received', 'vote_percentage'])
            
            base_columns.extend(['diversity_score', 'source'])
            
            # Filtrar colunas que existem
            display_columns = [col for col in base_columns if col in filtered_df.columns]
            
            if display_columns:
                display_df = filtered_df[display_columns].copy()
                
                # Formatação da tabela
                if 'diversity_score' in display_df.columns:
                    display_df['diversity_score'] = display_df['diversity_score'].round(3)
                
                if show_voting_data and 'vote_percentage' in display_df.columns:
                    display_df['vote_percentage'] = display_df['vote_percentage'].round(4)
                
                # Limitar registros exibidos
                display_df_limited = display_df.head(items_per_page)
                
                st.dataframe(
                    display_df_limited,
                    use_container_width=True,
                    height=500,
                    column_config={
                        "votes_received": st.column_config.NumberColumn(
                            "🗳️ Votos",
                            help="Número de votos recebidos",
                            format="%d"
                        ),
                        "vote_percentage": st.column_config.NumberColumn(
                            "📊 % Votos",
                            help="Percentual de votos",
                            format="%.4f%%"
                        ),
                        "diversity_score": st.column_config.NumberColumn(
                            "⭐ Score",
                            help="Score de diversidade",
                            format="%.3f"
                        )
                    }
                )
                
                if len(filtered_df) > items_per_page:
                    st.info(f"📄 Mostrando primeiros {items_per_page} de {len(filtered_df)} registros")
                
                # Botão de download
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📥 Baixar Dados Filtrados"):
                        csv = filtered_df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv,
                            file_name=f'candidatas_filtradas_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                            mime='text/csv'
                        )
                
                with col2:
                    if st.button("🗑️ Limpar Todos os Filtros"):
                        st.rerun()
        else:
            st.warning("⚠️ Nenhum registro encontrado com os filtros aplicados.")
            st.info("💡 Tente ajustar os filtros ou usar 'Selecionar Tudo' em algumas categorias.")
    
    else:
        st.error("❌ Não foi possível carregar os dados das candidatas")

with tab2:
    st.header("🗳️ Análise Detalhada de Votação")
    
    # Carregar dados
    with st.spinner("Carregando dados de votação..."):
        df_votes = fetch_all_candidates()
    
    if not df_votes.empty and 'votes_received' in df_votes.columns:
        # Estatísticas de votação
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_votes = df_votes['votes_received'].sum()
            st.metric(
                "🗳️ Total de Votos",
                f"{total_votes:,}",
                help="Soma total de todos os votos"
            )
        
        with col2:
            avg_votes = df_votes['votes_received'].mean()
            st.metric(
                "📊 Média de Votos",
                f"{avg_votes:,.0f}",
                help="Média de votos por candidata"
            )
        
        with col3:
            max_votes = df_votes['votes_received'].max()
            winner = df_votes.loc[df_votes['votes_received'].idxmax(), 'name'] if 'name' in df_votes.columns else "N/A"
            st.metric(
                "🏆 Mais Votada",
                f"{max_votes:,}",
                help=f"Candidata: {winner}"
            )
        
        with col4:
            candidates_with_votes = (df_votes['votes_received'] > 0).sum()
            st.metric(
                "✅ Com Votos",
                f"{candidates_with_votes:,}",
                help="Candidatas que receberam pelo menos 1 voto"
            )
        
        # Gráficos de análise
        st.markdown("---")
        
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("📊 Distribuição de Votos")
            
            # Histograma de votos
            fig_hist = px.histogram(
                df_votes,
                x='votes_received',
                bins=50,
                title="Distribuição de Votos Recebidos",
                labels={'votes_received': 'Votos Recebidos', 'count': 'Número de Candidatas'}
            )
            fig_hist.update_layout(height=400)
            st.plotly_chart(fig_hist, use_container_width=True)
        
        with col_right:
            st.subheader("🏆 Top 10 Mais Votadas")
            
            if 'name' in df_votes.columns:
                top_10 = df_votes.nlargest(10, 'votes_received')[['name', 'votes_received', 'vote_percentage']]
                
                fig_top = px.bar(
                    top_10,
                    x='votes_received',
                    y='name',
                    title="Top 10 Candidatas Mais Votadas",
                    orientation='h',
                    labels={'votes_received': 'Votos', 'name': 'Candidata'}
                )
                fig_top.update_layout(height=400)
                st.plotly_chart(fig_top, use_container_width=True)
        
        # Análise por cargo
        if 'cargo' in df_votes.columns:
            st.markdown("---")
            st.subheader("📈 Análise por Cargo")
            
            cargo_stats = df_votes.groupby('cargo').agg({
                'votes_received': ['sum', 'mean', 'count'],
                'vote_percentage': 'mean'
            }).round(2)
            
            cargo_stats.columns = ['Total de Votos', 'Média de Votos', 'Número de Candidatas', 'Média % Votos']
            cargo_stats = cargo_stats.reset_index()
            
            st.dataframe(cargo_stats, use_container_width=True)
            
            # Gráfico por cargo
            fig_cargo = px.bar(
                cargo_stats,
                x='cargo',
                y='Total de Votos',
                title="Total de Votos por Cargo",
                color='Média de Votos',
                color_continuous_scale='viridis'
            )
            fig_cargo.update_xaxis(tickangle=45)
            st.plotly_chart(fig_cargo, use_container_width=True)
        
        # Top candidatas por estado
        if 'state' in df_votes.columns and 'name' in df_votes.columns:
            st.markdown("---")
            st.subheader("🗺️ Mais Votada por Estado")
            
            # Encontrar a candidata mais votada por estado
            top_by_state = df_votes.loc[df_votes.groupby('state')['votes_received'].idxmax()]
            top_by_state = top_by_state[['state', 'name', 'votes_received', 'cargo']].sort_values('votes_received', ascending=False)
            
            st.dataframe(
                top_by_state,
                use_container_width=True,
                column_config={
                    "votes_received": st.column_config.NumberColumn(
                        "🗳️ Votos",
                        format="%d"
                    )
                }
            )
    
    else:
        st.info("📊 Dados de votação não disponíveis ou sendo gerados...")
        st.markdown("""
        **Sobre os Dados de Votação:**
        
        - 🔄 Os dados são simulados para demonstração
        - 📊 Baseados no score de diversidade das candidatas
        - 🗳️ Incluem número de votos e percentual
        - 📈 Permitem análises estatísticas completas
        """)

with tab3:
    st.header("📈 Dashboard Tradicional")
    
    # Estatísticas gerais
    with st.spinner("Carregando estatísticas..."):
        summary_stats = fetch_summary_stats()
    
    if summary_stats:
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
    
    # Gráficos tradicionais
    df_traditional = fetch_all_candidates()
    
    if not df_traditional.empty:
        col_left, col_right = st.columns(2)
        
        with col_left:
            if 'region' in df_traditional.columns:
                st.subheader("📊 Candidatas por Região")
                region_counts = df_traditional['region'].value_counts()
                
                fig_region = px.pie(
                    values=region_counts.values,
                    names=region_counts.index,
                    title="Distribuição Regional"
                )
                st.plotly_chart(fig_region, use_container_width=True)
        
        with col_right:
            if 'cargo' in df_traditional.columns:
                st.subheader("🏛️ Candidatas por Cargo")
                cargo_counts = df_traditional['cargo'].value_counts()
                
                fig_cargo = px.bar(
                    x=cargo_counts.values,
                    y=cargo_counts.index,
                    orientation='h',
                    title="Distribuição por Cargo"
                )
                st.plotly_chart(fig_cargo, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>🏛️ <strong>Eleições 2026 Analytics</strong> - Dashboard com Filtros Excel-Style</p>
    <p>Dados atualizados em tempo real | Filtros interativos nas colunas | Análise de votação integrada</p>
</div>
""", unsafe_allow_html=True)
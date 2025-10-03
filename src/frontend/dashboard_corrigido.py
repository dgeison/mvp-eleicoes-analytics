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

def fetch_candidates_paginated_with_filters(limit=100, page=1):
    """Buscar candidatas com todos os filtros aplicados"""
    params = {
        'limit': limit,
        'skip': (page - 1) * limit
    }
    
    # Aplicar filtros básicos
    if region_filter != "Todas":
        params['region'] = region_filter
    if source_filter != "Todas":
        params['source'] = source_filter
    
    # Aplicar filtro de score mínimo
    if diversity_score_range[0] > 0.0:
        params['min_score'] = diversity_score_range[0]
    
    success, data = safe_api_call('candidates/paginated', params)
    
    if success and data:
        df = pd.DataFrame(data.get('candidates', []))
        total_count = data.get('total_count', 0)
        
        # Aplicar filtros locais que não estão na API
        if not df.empty:
            # Filtro por estado
            if state_filter != "Todos":
                df = df[df.get('state', '') == state_filter]
            
            # Filtro por raça
            if race_filter != "Todas":
                df = df[df.get('race', '') == race_filter]
            
            # Filtro por educação
            if education_filter != "Todas":
                df = df[df.get('education', '') == education_filter]
            
            # Filtro por score máximo
            if 'diversity_score' in df.columns and diversity_score_range[1] < 1.0:
                df = df[df['diversity_score'] <= diversity_score_range[1]]
            
            # Filtro por minorias raciais
            if only_minorities and 'is_minority_race' in df.columns:
                df = df[df['is_minority_race'] == True]
            
            # Filtro por high performers
            if high_performers_only and 'diversity_score' in df.columns:
                df = df[df['diversity_score'] > 0.8]
            
            # Filtro por idade (se disponível e ativo)
            if age_range and 'age' in df.columns:
                df = df[(df['age'] >= age_range[0]) & (df['age'] <= age_range[1])]
            
            # Busca por nome
            if name_search:
                df = df[df.get('name', '').str.contains(name_search, case=False, na=False)]
        
        return df, total_count
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

# Sidebar com filtros dinâmicos
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

# Filtros dinâmicos avançados
st.sidebar.subheader("🔍 Filtros Dinâmicos")

# Filtro por região
region_filter = st.sidebar.selectbox(
    "🗺️ Região",
    ["Todas", "NORTE", "NORDESTE", "SUDESTE", "SUL", "CENTRO-OESTE"],
    help="Filtrar candidatas por região geográfica"
)

# Buscar dados para popular filtros dinâmicos
@st.cache_data(ttl=600)
def get_filter_options():
    """Busca opções disponíveis para filtros"""
    try:
        # Buscar uma amostra maior para ter todas as opções
        success, data = safe_api_call('candidates/paginated', {'limit': 1000})
        if success and data:
            df = pd.DataFrame(data.get('candidates', []))
            return {
                'states': sorted([s for s in df['state'].unique() if pd.notna(s)]),
                'races': sorted([r for r in df.get('race', pd.Series()).unique() if pd.notna(r)]),
                'educations': sorted([e for e in df.get('education', pd.Series()).unique() if pd.notna(e)]),
                'sources': sorted([s for s in df.get('source', pd.Series()).unique() if pd.notna(s)])
            }
    except:
        pass
    
    return {
        'states': ['SP', 'RJ', 'MG', 'PR', 'BA'],
        'races': ['BRANCA', 'PRETA', 'PARDA', 'AMARELA', 'INDÍGENA'],
        'educations': ['SUPERIOR COMPLETO', 'ENSINO MÉDIO COMPLETO', 'PÓS-GRADUAÇÃO'],
        'sources': ['TSE', 'Manual']
    }

# Obter opções para filtros
filter_options = get_filter_options()

# Filtro por estado
state_filter = st.sidebar.selectbox(
    "🏛️ Estado",
    ["Todos"] + filter_options['states'],
    help="Filtrar por estado específico"
)

# Filtro por raça/cor
race_filter = st.sidebar.selectbox(
    "👥 Raça/Cor",
    ["Todas"] + filter_options['races'],
    help="Filtrar por autodeclaração de raça/cor"
)

# Filtro por educação
education_filter = st.sidebar.selectbox(
    "🎓 Educação",
    ["Todas"] + filter_options['educations'],
    help="Filtrar por nível de escolaridade"
)

# Filtro por fonte
source_filter = st.sidebar.selectbox(
    "📊 Fonte dos Dados",
    ["Todas"] + filter_options['sources'],
    help="Filtrar por origem dos dados"
)

# Filtros numéricos
st.sidebar.subheader("📊 Filtros de Score")

# Slider para diversity score
diversity_score_range = st.sidebar.slider(
    "🌟 Score de Diversidade",
    min_value=0.0,
    max_value=1.0,
    value=(0.0, 1.0),
    step=0.05,
    help="Intervalo de score de diversidade"
)

# Filtro por idade (se disponível)
if st.sidebar.checkbox("🎂 Filtrar por Idade"):
    age_range = st.sidebar.slider(
        "Faixa Etária",
        min_value=18,
        max_value=80,
        value=(25, 65),
        step=1,
        help="Idade das candidatas"
    )
else:
    age_range = None

# Filtros booleanos
st.sidebar.subheader("✅ Filtros Especiais")

# Filtro para minorias raciais
only_minorities = st.sidebar.checkbox(
    "👥 Apenas Minorias Raciais",
    help="Mostrar apenas candidatas de minorias raciais"
)

# Filtro para high performers
high_performers_only = st.sidebar.checkbox(
    "⭐ Apenas Alto Score (>0.8)",
    help="Mostrar apenas candidatas com score alto"
)

# Busca por nome
st.sidebar.subheader("🔍 Busca")
name_search = st.sidebar.text_input(
    "👤 Buscar por Nome",
    placeholder="Digite o nome da candidata...",
    help="Busca parcial no nome da candidata"
)

# Botão para limpar filtros
if st.sidebar.button("🗑️ Limpar Todos os Filtros"):
    st.rerun()

# Resumo dos filtros ativos
st.sidebar.subheader("📋 Filtros Ativos")
active_filters = []
if region_filter != "Todas":
    active_filters.append(f"Região: {region_filter}")
if state_filter != "Todos":
    active_filters.append(f"Estado: {state_filter}")
if race_filter != "Todas":
    active_filters.append(f"Raça: {race_filter}")
if education_filter != "Todas":
    active_filters.append(f"Educação: {education_filter}")
if source_filter != "Todas":
    active_filters.append(f"Fonte: {source_filter}")
if diversity_score_range != (0.0, 1.0):
    active_filters.append(f"Score: {diversity_score_range[0]:.2f}-{diversity_score_range[1]:.2f}")
if only_minorities:
    active_filters.append("Apenas Minorias")
if high_performers_only:
    active_filters.append("Alto Score")
if name_search:
    active_filters.append(f"Nome: {name_search}")

if active_filters:
    st.sidebar.success(f"🎯 {len(active_filters)} filtros ativos")
    for filter_text in active_filters:
        st.sidebar.text(f"• {filter_text}")
else:
    st.sidebar.info("ℹ️ Nenhum filtro ativo")

# Abas principais
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Visão Geral", 
    "🗺️ Análise Regional", 
    "🔍 Explorar Dados",
    "📈 Análise Filtros",
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
    
    # Buscar dados paginados com filtros
    with st.spinner(f"Carregando {items_per_page} candidatas da página {current_page}..."):
        df, total_count = fetch_candidates_paginated_with_filters(
            limit=items_per_page,
            page=current_page
        )
    
    if not df.empty:
        # Informações da paginação
        start_index = (current_page - 1) * items_per_page + 1
        end_index = start_index + len(df) - 1
        
        st.info(f"📄 Mostrando registros {start_index} a {end_index} de {total_count:,} total")
        
        # Mostrar dados filtrados
        st.subheader(f"📊 Dados Filtrados ({len(df)} registros)")
        
        if not df.empty:
            # Selecionar colunas disponíveis para exibição
            available_columns = df.columns.tolist()
            display_columns = []
            
            for col in ['name', 'ballot_name', 'state', 'region', 'cargo', 'education', 'race', 'diversity_score', 'source']:
                if col in available_columns:
                    display_columns.append(col)
            
            if display_columns:
                display_df = df[display_columns].copy()
                
                # Formatar scores se existirem
                if 'diversity_score' in display_df.columns:
                    display_df = display_df.style.format({'diversity_score': '{:.3f}'})
                
                st.dataframe(display_df, use_container_width=True, height=400)
                
                # Botão para download
                if st.button("📥 Baixar dados filtrados (CSV)"):
                    csv = df.to_csv(index=False)
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
    st.header("📈 Análise Dinâmica dos Filtros")
    
    if active_filters:
        st.success(f"🎯 **Análise com {len(active_filters)} filtros ativos**")
        
        # Buscar dados com filtros para análise
        with st.spinner("Analisando dados filtrados..."):
            df_analysis, total_filtered = fetch_candidates_paginated_with_filters(
                limit=2000,  # Buscar mais dados para análise
                page=1
            )
        
        if not df_analysis.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Estatísticas dos Dados Filtrados")
                
                # Métricas dos dados filtrados
                st.metric("Total de Candidatas", len(df_analysis))
                
                if 'diversity_score' in df_analysis.columns:
                    avg_score = df_analysis['diversity_score'].mean()
                    st.metric("Score Médio", f"{avg_score:.3f}")
                
                if 'is_minority_race' in df_analysis.columns:
                    minority_pct = (df_analysis['is_minority_race'].sum() / len(df_analysis)) * 100
                    st.metric("% Minorias Raciais", f"{minority_pct:.1f}%")
                
                # Distribuição por estado
                if 'state' in df_analysis.columns:
                    st.subheader("🏛️ Top 5 Estados")
                    state_counts = df_analysis['state'].value_counts().head(5)
                    for state, count in state_counts.items():
                        st.text(f"{state}: {count} candidatas")
            
            with col2:
                st.subheader("📈 Distribuições")
                
                # Gráfico de score de diversidade
                if 'diversity_score' in df_analysis.columns:
                    fig_hist = px.histogram(
                        df_analysis,
                        x='diversity_score',
                        nbins=20,
                        title="Distribuição do Score de Diversidade",
                        labels={'diversity_score': 'Score de Diversidade', 'count': 'Número de Candidatas'}
                    )
                    fig_hist.update_layout(height=300)
                    st.plotly_chart(fig_hist, use_container_width=True)
                
                # Gráfico de raça/cor se disponível
                if 'race' in df_analysis.columns:
                    race_counts = df_analysis['race'].value_counts()
                    if len(race_counts) > 0:
                        fig_race = px.pie(
                            values=race_counts.values,
                            names=race_counts.index,
                            title="Distribuição por Raça/Cor"
                        )
                        fig_race.update_layout(height=300)
                        st.plotly_chart(fig_race, use_container_width=True)
            
            # Análise comparativa
            st.subheader("🔍 Análise Comparativa")
            
            # Buscar dados totais para comparação
            with st.spinner("Comparando com dados totais..."):
                total_stats = fetch_summary_stats()
            
            if total_stats:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    filtered_count = len(df_analysis)
                    total_count = total_stats.get('total_candidates', 1)
                    coverage = (filtered_count / total_count) * 100
                    st.metric(
                        "Cobertura do Filtro",
                        f"{coverage:.1f}%",
                        f"{filtered_count} de {total_count}"
                    )
                
                with col2:
                    if 'diversity_score' in df_analysis.columns:
                        filtered_avg = df_analysis['diversity_score'].mean()
                        total_avg = total_stats.get('avg_diversity_score', 0)
                        score_diff = filtered_avg - total_avg
                        st.metric(
                            "Score vs Média Geral",
                            f"{filtered_avg:.3f}",
                            f"{score_diff:+.3f}"
                        )
                
                with col3:
                    if 'is_minority_race' in df_analysis.columns:
                        filtered_minority = (df_analysis['is_minority_race'].sum() / len(df_analysis)) * 100
                        total_minority = total_stats.get('diversity_rate', 0)
                        minority_diff = filtered_minority - total_minority
                        st.metric(
                            "% Minorias vs Geral",
                            f"{filtered_minority:.1f}%",
                            f"{minority_diff:+.1f}%"
                        )
            
            # Top candidatas filtradas
            st.subheader("🏆 Top 10 Candidatas com Filtros Aplicados")
            if 'diversity_score' in df_analysis.columns:
                top_filtered = df_analysis.nlargest(10, 'diversity_score')
                display_cols = ['name', 'state', 'diversity_score']
                if 'race' in top_filtered.columns:
                    display_cols.append('race')
                if 'education' in top_filtered.columns:
                    display_cols.append('education')
                
                available_cols = [col for col in display_cols if col in top_filtered.columns]
                st.dataframe(
                    top_filtered[available_cols].style.format({'diversity_score': '{:.3f}'}),
                    use_container_width=True
                )
        else:
            st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados")
    
    else:
        st.info("ℹ️ **Aplique filtros na barra lateral para ver análises dinâmicas**")
        
        st.markdown("""
        ### 🎯 Como usar os filtros:
        
        1. **🗺️ Região/Estado**: Filtre por localização geográfica
        2. **👥 Raça/Cor**: Analise diversidade racial
        3. **🎓 Educação**: Filtre por nível educacional
        4. **🌟 Score**: Use o slider para definir faixas de performance
        5. **✅ Filtros Especiais**: Foque em grupos específicos
        6. **🔍 Busca**: Encontre candidatas específicas por nome
        
        **💡 Dica**: Combine múltiplos filtros para análises mais precisas!
        """)

with tab5:
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
        st.metric("Filtros Ativos", len(active_filters))
        
        if st.button("🗑️ Limpar Cache"):
            st.cache_data.clear()
            st.success("Cache limpo!")
            time.sleep(1)
            st.rerun()
    
    # Informações sobre filtros
    st.subheader("🔍 Debug dos Filtros")
    
    debug_info = {
        "Região": region_filter,
        "Estado": state_filter,
        "Raça/Cor": race_filter,
        "Educação": education_filter,
        "Fonte": source_filter,
        "Score Range": f"{diversity_score_range[0]:.2f} - {diversity_score_range[1]:.2f}",
        "Apenas Minorias": only_minorities,
        "Alto Score": high_performers_only,
        "Busca por Nome": name_search or "Não informado",
        "Filtro de Idade": "Ativo" if age_range else "Inativo"
    }
    
    st.json(debug_info)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>🏛️ <strong>Eleições 2026 Analytics</strong> | 
    Versão Corrigida | 
    🔧 Com Diagnóstico Integrado</p>
</div>
""", unsafe_allow_html=True)
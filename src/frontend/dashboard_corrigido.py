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
    """Buscar candidatas com todos os filtros multi-seleção aplicados"""
    params = {
        'limit': limit,
        'skip': (page - 1) * limit
    }
    
    # Aplicar filtros básicos (usar primeiro da lista se multi-selecionado)
    if selected_regions:
        params['region'] = selected_regions[0] if len(selected_regions) == 1 else None
    if selected_sources:
        params['source'] = selected_sources[0] if len(selected_sources) == 1 else None
    
    # Aplicar filtro de score mínimo
    if diversity_score_range[0] > 0.0:
        params['min_score'] = diversity_score_range[0]
    
    success, data = safe_api_call('candidates/paginated', params)
    
    if success and data:
        df = pd.DataFrame(data.get('candidates', []))
        total_count = data.get('total_count', 0)
        
        # Aplicar filtros multi-seleção localmente
        if not df.empty:
            # Filtro por múltiplas regiões
            if selected_regions:
                df = df[df.get('region', '').isin(selected_regions)]
            
            # Filtro por múltiplos estados
            if selected_states:
                df = df[df.get('state', '').isin(selected_states)]
            
            # Filtro por múltiplas raças
            if selected_races:
                df = df[df.get('race', '').isin(selected_races)]
            
            # Filtro por múltiplas educações
            if selected_educations:
                df = df[df.get('education', '').isin(selected_educations)]
            
            # Filtro por múltiplos cargos
            if selected_cargos:
                df = df[df.get('cargo', '').isin(selected_cargos)]
            
            # Filtro por múltiplas fontes
            if selected_sources:
                df = df[df.get('source', '').isin(selected_sources)]
            
            # Filtro por score máximo
            if 'diversity_score' in df.columns and diversity_score_range[1] < 1.0:
                df = df[df['diversity_score'] <= diversity_score_range[1]]
            
            # Filtro por minorias raciais
            if only_minorities and 'is_minority_race' in df.columns:
                df = df[df['is_minority_race'] == True]
            
            # Filtro por high performers
            if high_performers_only and 'diversity_score' in df.columns:
                df = df[df['diversity_score'] > 0.8]
            
            # Filtros especiais booleanos
            if include_indigenous and 'race' in df.columns:
                df = df[df['race'].str.contains('INDÍGENA', case=False, na=False)]
            
            if academic_focus and 'education' in df.columns:
                academic_levels = ['SUPERIOR COMPLETO', 'PÓS-GRADUAÇÃO']
                df = df[df['education'].isin(academic_levels)]
            
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

# 🎯 FILTROS MULTI-SELEÇÃO ESTILO EXCEL
st.sidebar.subheader("🎯 Filtros Multi-Seleção (Excel Style)")

# Buscar dados para popular filtros dinâmicos
@st.cache_data(ttl=600)
def get_comprehensive_filter_options():
    """Busca opções abrangentes para todos os filtros"""
    try:
        # Buscar uma amostra maior para ter todas as opções
        success, data = safe_api_call('candidates/paginated', {'limit': 2000})
        if success and data:
            df = pd.DataFrame(data.get('candidates', []))
            return {
                'states': sorted([s for s in df['state'].unique() if pd.notna(s) and s != '']),
                'races': sorted([r for r in df.get('race', pd.Series()).unique() if pd.notna(r) and r != '']),
                'educations': sorted([e for e in df.get('education', pd.Series()).unique() if pd.notna(e) and e != '']),
                'cargos': sorted([c for c in df.get('cargo', pd.Series()).unique() if pd.notna(c) and c != '']),
                'sources': sorted([s for s in df.get('source', pd.Series()).unique() if pd.notna(s) and s != '']),
                'regions': sorted([r for r in df.get('region', pd.Series()).unique() if pd.notna(r) and r != ''])
            }
    except Exception as e:
        st.sidebar.error(f"Erro ao carregar filtros: {e}")
    
    return {
        'states': ['SP', 'RJ', 'MG', 'PR', 'BA', 'RS', 'PE', 'CE', 'SC', 'GO'],
        'races': ['BRANCA', 'PRETA', 'PARDA', 'AMARELA', 'INDÍGENA', 'NÃO INFORMADO'],
        'educations': ['SUPERIOR COMPLETO', 'ENSINO MÉDIO COMPLETO', 'PÓS-GRADUAÇÃO', 'SUPERIOR INCOMPLETO'],
        'cargos': ['DEPUTADO FEDERAL', 'DEPUTADO ESTADUAL', 'SENADOR', 'GOVERNADOR', 'VICE-GOVERNADOR'],
        'sources': ['TSE', 'Manual'],
        'regions': ['SUDESTE', 'NORDESTE', 'SUL', 'NORTE', 'CENTRO-OESTE']
    }

# Obter opções para filtros
filter_options = get_comprehensive_filter_options()

# 🗺️ FILTROS GEOGRÁFICOS
st.sidebar.markdown("### 🗺️ **Filtros Geográficos**")

# Multi-select para Regiões
selected_regions = st.sidebar.multiselect(
    "Regiões",
    options=filter_options['regions'],
    default=[],
    help="Selecione uma ou mais regiões (Ctrl+Click para múltiplas)",
    key="regions_filter"
)

# Multi-select para Estados
selected_states = st.sidebar.multiselect(
    "Estados",
    options=filter_options['states'],
    default=[],
    help="Selecione um ou mais estados específicos",
    key="states_filter"
)

# 👥 FILTROS DEMOGRÁFICOS
st.sidebar.markdown("### 👥 **Filtros Demográficos**")

# Multi-select para Raça/Cor
selected_races = st.sidebar.multiselect(
    "Raça/Cor",
    options=filter_options['races'],
    default=[],
    help="Selecione uma ou mais autodeclarações de raça/cor",
    key="races_filter"
)

# 🎓 FILTROS EDUCACIONAIS/PROFISSIONAIS
st.sidebar.markdown("### 🎓 **Filtros Educacionais**")

# Multi-select para Educação
selected_educations = st.sidebar.multiselect(
    "Nível de Educação",
    options=filter_options['educations'],
    default=[],
    help="Selecione um ou mais níveis educacionais",
    key="education_filter"
)

# 🏛️ FILTROS POLÍTICOS
st.sidebar.markdown("### 🏛️ **Filtros Políticos**")

# Multi-select para Cargos
selected_cargos = st.sidebar.multiselect(
    "Cargos Políticos",
    options=filter_options['cargos'],
    default=[],
    help="Selecione um ou mais cargos políticos",
    key="cargos_filter"
)

# Multi-select para Fonte dos Dados
selected_sources = st.sidebar.multiselect(
    "Fonte dos Dados",
    options=filter_options['sources'],
    default=[],
    help="Selecione origem dos dados (TSE, Manual, etc.)",
    key="sources_filter"
)

# Manter compatibilidade com código existente
region_filter = selected_regions[0] if selected_regions else "Todas"
state_filter = selected_states[0] if selected_states else "Todos"
race_filter = selected_races[0] if selected_races else "Todas"
education_filter = selected_educations[0] if selected_educations else "Todas"
source_filter = selected_sources[0] if selected_sources else "Todas"

# 📊 FILTROS NUMÉRICOS E SCORING
st.sidebar.markdown("### 📊 **Filtros de Performance**")

# Slider para diversity score
diversity_score_range = st.sidebar.slider(
    "🌟 Score de Diversidade",
    min_value=0.0,
    max_value=1.0,
    value=(0.0, 1.0),
    step=0.05,
    help="Intervalo de score de diversidade (impacta scoring final)"
)

# Componentes do Score (para transparência)
st.sidebar.markdown("#### � **Componentes do Score de Diversidade:**")
st.sidebar.markdown("""
- **25%** - Representação Regional (Norte/Nordeste = +25%)
- **30%** - Experiência Política (Gov/Sen = +30%)  
- **20%** - Formação Acadêmica (Superior = +20%)
- **25%** - Trabalho em Diversidade (Prof/Assist.Social = +25%)
""")

# ✅ FILTROS ESPECIAIS
st.sidebar.markdown("### ✅ **Filtros Especiais**")

# Filtros booleanos em colunas
col1, col2 = st.sidebar.columns(2)

with col1:
    only_minorities = st.checkbox(
        "👥 Só Minorias",
        help="Apenas candidatas de minorias raciais"
    )
    
    high_performers_only = st.checkbox(
        "⭐ Alto Score",
        help="Score > 0.8"
    )

with col2:
    include_indigenous = st.checkbox(
        "🏺 Incluir Indígenas",
        help="Focar em representação indígena"
    )
    
    academic_focus = st.checkbox(
        "🎓 Foco Acadêmico",
        help="Superior completo ou pós-graduação"
    )

# 🔍 BUSCA E FILTROS ADICIONAIS
st.sidebar.markdown("### 🔍 **Busca e Filtros Adicionais**")

# Busca por nome
name_search = st.sidebar.text_input(
    "👤 Buscar por Nome",
    placeholder="Digite parte do nome...",
    help="Busca parcial no nome da candidata"
)

# Filtro de idade (se disponível)
age_enabled = st.sidebar.checkbox("🎂 Filtrar por Idade")
if age_enabled:
    age_range = st.sidebar.slider(
        "Faixa Etária",
        min_value=18,
        max_value=80,
        value=(25, 65),
        step=1
    )
else:
    age_range = None

# 🎛️ CONTROLES
st.sidebar.markdown("### 🎛️ **Controles**")

col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("🗑️ Limpar Filtros", help="Remove todos os filtros"):
        st.rerun()

with col2:
    if st.button("🔄 Atualizar", help="Recarrega os dados"):
        st.cache_data.clear()
        st.rerun()

# 📋 RESUMO DOS FILTROS ATIVOS
st.sidebar.markdown("### 📋 **Filtros Ativos**")

# Compilar todos os filtros ativos
active_filters_detailed = []

if selected_regions:
    active_filters_detailed.append(f"🗺️ Regiões: {', '.join(selected_regions)}")
if selected_states:
    active_filters_detailed.append(f"🏛️ Estados: {', '.join(selected_states)}")
if selected_races:
    active_filters_detailed.append(f"👥 Raças: {', '.join(selected_races)}")
if selected_educations:
    active_filters_detailed.append(f"🎓 Educação: {', '.join(selected_educations)}")
if selected_cargos:
    active_filters_detailed.append(f"🏛️ Cargos: {', '.join(selected_cargos)}")
if selected_sources:
    active_filters_detailed.append(f"📊 Fontes: {', '.join(selected_sources)}")
if diversity_score_range != (0.0, 1.0):
    active_filters_detailed.append(f"🌟 Score: {diversity_score_range[0]:.2f}-{diversity_score_range[1]:.2f}")
if only_minorities:
    active_filters_detailed.append("👥 Apenas Minorias")
if high_performers_only:
    active_filters_detailed.append("⭐ Alto Performance")
if include_indigenous:
    active_filters_detailed.append("🏺 Foco Indígena")
if academic_focus:
    active_filters_detailed.append("🎓 Foco Acadêmico")
if name_search:
    active_filters_detailed.append(f"🔍 Nome: '{name_search}'")
if age_enabled and age_range:
    active_filters_detailed.append(f"🎂 Idade: {age_range[0]}-{age_range[1]}")

# Mostrar filtros ativos
if active_filters_detailed:
    st.sidebar.success(f"🎯 **{len(active_filters_detailed)} filtros ativos**")
    for i, filter_text in enumerate(active_filters_detailed, 1):
        st.sidebar.markdown(f"**{i}.** {filter_text}")
    
    # Calcular impacto estimado dos filtros
    total_filters = len(active_filters_detailed)
    estimated_reduction = min(85, total_filters * 15)  # Estimativa de redução
    st.sidebar.info(f"📉 Redução estimada: ~{estimated_reduction}% dos dados")
else:
    st.sidebar.info("ℹ️ **Nenhum filtro ativo** - Mostrando todos os dados")

# 💡 DICAS DE USO
st.sidebar.markdown("### 💡 **Dicas de Uso**")
st.sidebar.markdown("""
- **Ctrl+Click** para múltiplas seleções
- **Combine filtros** para análises precisas  
- **Score alto** = Potencial de liderança
- **Minorias + Acadêmico** = Diversidade qualificada
- **Use busca** para candidatas específicas
""")

# Manter compatibilidade com código existente para filtros ativos simples
active_filters = active_filters_detailed  # Para compatibilidade

# 🎯 CABEÇALHO COM FILTROS APLICADOS
if active_filters_detailed:
    st.markdown("---")
    st.markdown("### 🎯 **Filtros Aplicados na Análise**")
    
    # Criar colunas dinâmicas baseadas no número de filtros
    if len(active_filters_detailed) <= 3:
        cols = st.columns(len(active_filters_detailed))
    else:
        cols = st.columns(3)
    
    # Mostrar filtros em cards organizados
    for i, filter_text in enumerate(active_filters_detailed):
        col_index = i % len(cols)
        with cols[col_index]:
            # Extrair emoji e texto para melhor visualização
            if ':' in filter_text:
                emoji_part, text_part = filter_text.split(':', 1)
                st.info(f"**{emoji_part}:**\n{text_part.strip()}")
            else:
                st.info(f"**{filter_text}**")
    
    # Resumo compacto
    total_filters = len(active_filters_detailed)
    st.success(f"🎯 **{total_filters} filtros ativos** - Análise customizada em andamento")
    
    # Indicador de impacto
    estimated_reduction = min(85, total_filters * 15)
    st.markdown(f"📊 **Impacto estimado:** ~{estimated_reduction}% de redução no dataset")
    
else:
    st.info("ℹ️ **Análise Completa** - Todos os dados disponíveis estão sendo exibidos")

st.markdown("---")

# Abas principais
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Visão Geral", 
    "🗺️ Análise Regional", 
    "👩‍💼 Análise Feminina",
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
    st.header("👩‍💼 Análise Feminina com Filtros Aplicados")
    
    # Buscar dados filtrados para análise feminina
    with st.spinner("Carregando dados para análise feminina..."):
        df_feminina, total_feminina = fetch_candidates_paginated_with_filters(
            limit=1000,  # Carregar mais dados para análise
            page=1
        )
    
    if not df_feminina.empty:
        # Estatísticas específicas da análise feminina
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "👩‍💼 Total Mulheres",
                f"{len(df_feminina):,}",
                help="Total de candidatas femininas conforme filtros"
            )
        
        with col2:
            if 'diversity_score' in df_feminina.columns:
                avg_score = df_feminina['diversity_score'].mean()
                st.metric(
                    "⭐ Score Médio",
                    f"{avg_score:.3f}",
                    help="Score médio de diversidade das candidatas filtradas"
                )
        
        with col3:
            if 'race' in df_feminina.columns:
                minorities = df_feminina[df_feminina['race'].isin(['PRETA', 'PARDA', 'INDÍGENA', 'AMARELA'])].shape[0]
                minority_pct = (minorities / len(df_feminina)) * 100 if len(df_feminina) > 0 else 0
                st.metric(
                    "🌍 Diversidade Racial",
                    f"{minorities:,} ({minority_pct:.1f}%)",
                    help="Candidatas de minorias raciais"
                )
        
        with col4:
            if 'education' in df_feminina.columns:
                superior = df_feminina[df_feminina['education'].str.contains('SUPERIOR|PÓS', case=False, na=False)].shape[0]
                edu_pct = (superior / len(df_feminina)) * 100 if len(df_feminina) > 0 else 0
                st.metric(
                    "🎓 Formação Superior",
                    f"{superior:,} ({edu_pct:.1f}%)",
                    help="Candidatas com formação superior ou pós-graduação"
                )
        
        # Análises gráficas específicas
        st.markdown("---")
        
        # Gráficos lado a lado
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("📊 Distribuição por Raça/Cor")
            if 'race' in df_feminina.columns:
                race_counts = df_feminina['race'].value_counts()
                fig_race = px.pie(
                    values=race_counts.values,
                    names=race_counts.index,
                    title="Distribuição Racial das Candidatas",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                st.plotly_chart(fig_race, use_container_width=True)
            else:
                st.info("Dados de raça/cor não disponíveis")
        
        with col_right:
            st.subheader("🎓 Distribuição por Educação")
            if 'education' in df_feminina.columns:
                edu_counts = df_feminina['education'].value_counts()
                fig_edu = px.bar(
                    x=edu_counts.index,
                    y=edu_counts.values,
                    title="Nível Educacional das Candidatas",
                    color=edu_counts.values,
                    color_continuous_scale="viridis"
                )
                fig_edu.update_xaxis(tickangle=45)
                st.plotly_chart(fig_edu, use_container_width=True)
            else:
                st.info("Dados de educação não disponíveis")
        
        # Ranking das candidatas de maior score
        st.markdown("---")
        st.subheader("🏆 Top 10 Candidatas por Score de Diversidade")
        
        if 'diversity_score' in df_feminina.columns:
            top_candidates = df_feminina.nlargest(10, 'diversity_score')
            
            # Preparar dados para visualização
            display_cols = []
            for col in ['name', 'ballot_name', 'state', 'cargo', 'race', 'education', 'diversity_score']:
                if col in top_candidates.columns:
                    display_cols.append(col)
            
            if display_cols:
                top_display = top_candidates[display_cols].copy()
                
                # Adicionar ranking
                top_display.insert(0, '🏆 Ranking', range(1, len(top_display) + 1))
                
                # Formatação condicional
                if 'diversity_score' in top_display.columns:
                    top_display = top_display.style.format({'diversity_score': '{:.3f}'})
                
                st.dataframe(top_display, use_container_width=True)
            else:
                st.warning("Dados insuficientes para ranking")
        else:
            st.info("Score de diversidade não disponível para ranking")
        
        # Análise por estado (se filtros geográficos aplicados)
        if selected_states or selected_regions:
            st.markdown("---")
            st.subheader("🗺️ Análise Geográfica Específica")
            
            if 'state' in df_feminina.columns:
                state_analysis = df_feminina.groupby('state').agg({
                    'name': 'count',
                    'diversity_score': 'mean' if 'diversity_score' in df_feminina.columns else 'size'
                }).reset_index()
                
                state_analysis.columns = ['Estado', 'Total Candidatas', 'Score Médio']
                
                # Gráfico de barras por estado
                fig_states = px.bar(
                    state_analysis,
                    x='Estado',
                    y='Total Candidatas',
                    color='Score Médio' if 'Score Médio' in state_analysis.columns else None,
                    title="Candidatas por Estado (Filtros Aplicados)",
                    color_continuous_scale="blues"
                )
                st.plotly_chart(fig_states, use_container_width=True)
                
                # Tabela detalhada
                st.dataframe(
                    state_analysis.style.format({'Score Médio': '{:.3f}'}),
                    use_container_width=True
                )
        
        # Insights automáticos
        st.markdown("---")
        st.subheader("💡 Insights da Análise Feminina")
        
        insights = []
        
        if 'race' in df_feminina.columns:
            minorities_pct = (df_feminina['race'].isin(['PRETA', 'PARDA', 'INDÍGENA', 'AMARELA']).sum() / len(df_feminina)) * 100
            if minorities_pct > 50:
                insights.append(f"🌍 **Diversidade Alta**: {minorities_pct:.1f}% das candidatas são de minorias raciais")
            elif minorities_pct > 30:
                insights.append(f"🌍 **Diversidade Moderada**: {minorities_pct:.1f}% das candidatas são de minorias raciais")
            else:
                insights.append(f"🌍 **Diversidade Baixa**: Apenas {minorities_pct:.1f}% das candidatas são de minorias raciais")
        
        if 'education' in df_feminina.columns:
            superior_pct = (df_feminina['education'].str.contains('SUPERIOR|PÓS', case=False, na=False).sum() / len(df_feminina)) * 100
            if superior_pct > 70:
                insights.append(f"🎓 **Alto Nível Educacional**: {superior_pct:.1f}% têm formação superior")
            elif superior_pct > 40:
                insights.append(f"🎓 **Nível Educacional Moderado**: {superior_pct:.1f}% têm formação superior")
            else:
                insights.append(f"🎓 **Oportunidade de Capacitação**: Apenas {superior_pct:.1f}% têm formação superior")
        
        if 'diversity_score' in df_feminina.columns:
            high_score_pct = (df_feminina['diversity_score'] > 0.8).sum() / len(df_feminina) * 100
            if high_score_pct > 20:
                insights.append(f"⭐ **Potencial Alto**: {high_score_pct:.1f}% das candidatas têm score > 0.8")
            elif high_score_pct > 10:
                insights.append(f"⭐ **Potencial Moderado**: {high_score_pct:.1f}% das candidatas têm score > 0.8")
            else:
                insights.append(f"⭐ **Potencial em Desenvolvimento**: {high_score_pct:.1f}% das candidatas têm score > 0.8")
        
        # Exibir insights
        for insight in insights:
            st.success(insight)
        
        if not insights:
            st.info("💭 Insights serão gerados conforme os dados disponíveis")
    
    else:
        st.warning("⚠️ Nenhum dado encontrado para análise feminina com os filtros aplicados")
        st.info("💡 Tente ajustar os filtros na barra lateral para obter resultados")

with tab4:
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

with tab5:
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

with tab6:
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
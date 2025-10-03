"""
Dashboard Premium - Eleições 2026 Analytics
Interface moderna e completa para análise de candidaturas femininas
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
    page_title="Eleições 2026 - Analytics Premium",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para melhorar o visual
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
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    .stMetric {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Header principal
st.markdown("""
<div class="main-header">
    <h1>🏛️ Eleições 2026 - Analytics Premium</h1>
    <p>Plataforma Avançada para Análise de Candidaturas Femininas</p>
</div>
""", unsafe_allow_html=True)

# URL da API
API_BASE_URL = "http://api:8000/api/v1"

@st.cache_data(ttl=300)  # Cache por 5 minutos
def load_candidates():
    """Carrega candidatos da API com cache"""
    try:
        response = requests.get(f"{API_BASE_URL}/candidates?limit=1000", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return pd.DataFrame(data['data'])
        else:
            st.error(f"❌ Erro ao carregar dados: {response.status_code} - {response.text}")
            return pd.DataFrame()
    except requests.exceptions.ConnectionError:
        st.error("❌ Erro de conexão: Não foi possível conectar à API")
        return pd.DataFrame()
    except requests.exceptions.Timeout:
        st.error("❌ Timeout: API demorou para responder")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Erro inesperado: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_women_analysis():
    """Carrega análise específica de mulheres"""
    try:
        response = requests.get(f"{API_BASE_URL}/women-analysis", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

@st.cache_data(ttl=300)
def load_election_stats():
    """Carrega estatísticas eleitorais"""
    try:
        response = requests.get(f"{API_BASE_URL}/election-stats", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

@st.cache_data(ttl=300)
def load_potential_candidates():
    """Carrega candidatas com maior potencial"""
    try:
        response = requests.get(f"{API_BASE_URL}/potential-candidates?limit=10", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

@st.cache_data(ttl=300)
def load_data_quality():
    """Carrega relatório de qualidade dos dados"""
    try:
        response = requests.get(f"{API_BASE_URL}/data-quality", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def create_diversity_sunburst(df):
    """Cria gráfico sunburst de diversidade"""
    # Preparar dados para sunburst
    df_grouped = df.groupby(['region', 'race']).size().reset_index(name='count')
    
    fig = px.sunburst(
        df_grouped, 
        path=['region', 'race'], 
        values='count',
        title="🌅 Diversidade por Região e Raça",
        color='count',
        color_continuous_scale='Viridis'
    )
    
    fig.update_layout(height=500)
    return fig

def create_advanced_metrics_chart(women_stats):
    """Cria gráfico avançado de métricas"""
    if not women_stats:
        return None
        
    stats = women_stats.get('statistics', {})
    
    # Criar subplot com múltiplos gráficos
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Distribuição Racial', 'Por Estado', 'Por Cargo', 'Métricas Gerais'),
        specs=[[{"type": "pie"}, {"type": "bar"}],
               [{"type": "bar"}, {"type": "indicator"}]]
    )
    
    # Gráfico de pizza - Raça
    if 'by_race' in stats:
        races = list(stats['by_race'].keys())
        values = list(stats['by_race'].values())
        fig.add_trace(
            go.Pie(labels=races, values=values, name="Raça"),
            row=1, col=1
        )
    
    # Gráfico de barras - Estados
    if 'by_state' in stats:
        states = list(stats['by_state'].keys())
        counts = list(stats['by_state'].values())
        fig.add_trace(
            go.Bar(x=states, y=counts, name="Estados", marker_color='lightblue'),
            row=1, col=2
        )
    
    # Gráfico de barras - Cargos
    if 'by_cargo' in stats:
        cargos = list(stats['by_cargo'].keys())
        cargo_counts = list(stats['by_cargo'].values())
        fig.add_trace(
            go.Bar(x=cargos, y=cargo_counts, name="Cargos", marker_color='lightgreen'),
            row=2, col=1
        )
    
    # Indicador - Score de diversidade
    avg_score = stats.get('avg_diversity_score', 0)
    fig.add_trace(
        go.Indicator(
            mode = "gauge+number+delta",
            value = avg_score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Score Médio"},
            gauge = {
                'axis': {'range': [None, 1]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 0.5], 'color': "lightgray"},
                    {'range': [0.5, 0.8], 'color': "yellow"},
                    {'range': [0.8, 1], 'color': "green"}],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 0.9}}
        ),
        row=2, col=2
    )
    
    fig.update_layout(height=600, showlegend=False, title_text="📊 Dashboard de Métricas Avançadas")
    return fig

def create_potential_ranking(potential_data):
    """Cria gráfico de ranking de potencial"""
    if not potential_data or 'candidates' not in potential_data:
        return None
    
    candidates = potential_data['candidates']
    df_potential = pd.DataFrame(candidates)
    
    fig = px.bar(
        df_potential.head(10),
        x='diversity_score',
        y='name',
        orientation='h',
        color='diversity_score',
        color_continuous_scale='RdYlGn',
        title="🏆 Top 10 Candidatas por Potencial",
        labels={'diversity_score': 'Score de Diversidade', 'name': 'Candidata'}
    )
    
    fig.update_layout(height=500, yaxis={'categoryorder':'total ascending'})
    return fig

# Sidebar com navegação
with st.sidebar:
    st.markdown("### 🧭 Navegação")
    
    page = st.selectbox(
        "Escolha uma seção:",
        [
            "🏠 Dashboard Principal",
            "👩‍💼 Análise Feminina",
            "📊 Estatísticas Eleitorais", 
            "🎯 Candidatas Potenciais",
            "🔍 Explorador de Dados",
            "📈 Qualidade dos Dados",
            "⚙️ Configurações"
        ]
    )
    
    st.markdown("---")
    st.markdown("### 📡 Status da API")
    
    try:
        health_response = requests.get(f"http://api:8000/health", timeout=5)
        if health_response.status_code == 200:
            st.success("✅ API Online")
            health_data = health_response.json()
            st.write(f"🗃️ {health_data.get('candidate_count', 0)} candidatos")
        else:
            st.error("❌ API com problemas")
    except:
        st.error("❌ API Offline")
    
    st.markdown("---")
    st.markdown("### 🔄 Controles")
    
    if st.button("🔄 Atualizar Dados"):
        st.cache_data.clear()
        st.rerun()
    
    auto_refresh = st.checkbox("🔄 Auto-refresh (5min)")
    
    if auto_refresh:
        time.sleep(1)
        st.rerun()

# Carregamento de dados com loading
with st.spinner("🔄 Carregando dados..."):
    df = load_candidates()
    women_stats = load_women_analysis()
    election_stats = load_election_stats()
    potential_data = load_potential_candidates()
    quality_data = load_data_quality()

if df.empty:
    st.error("❌ Não foi possível carregar os dados da API")
    st.info("🔧 Verifique se a API está funcionando em http://localhost:8000")
    st.stop()

# === PÁGINAS ===

if page == "🏠 Dashboard Principal":
    st.header("🏠 Dashboard Principal")
    
    # Aviso sobre sistema justo
    st.success("""
    🎉 **SISTEMA ATUALIZADO!** Agora utilizamos uma metodologia **justa e transparente** 
    para calcular os scores de diversidade, focada em **competências e ações**, 
    não em características pessoais. Veja os detalhes na seção ⚙️ Configurações.
    """)
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "👩‍💼 Total Candidatas", 
            len(df),
            delta=f"+{len(df)} esta eleição"
        )
    
    with col2:
        unique_states = df['state'].nunique()
        st.metric(
            "🗺️ Estados", 
            unique_states,
            delta=f"{(unique_states/27)*100:.1f}% do Brasil"
        )
    
    with col3:
        minority_pct = (df['is_minority_race'].sum() / len(df) * 100) if len(df) > 0 else 0
        st.metric(
            "🌈 Diversidade", 
            f"{minority_pct:.1f}%",
            delta="minorias raciais"
        )
    
    with col4:
        avg_score = df['diversity_score'].mean() if 'diversity_score' in df.columns else 0
        st.metric(
            "⭐ Score Médio", 
            f"{avg_score:.2f}",
            delta="de 1.0"
        )
    
    # Gráficos principais
    col1, col2 = st.columns(2)
    
    with col1:
        if not df.empty:
            sunburst_fig = create_diversity_sunburst(df)
            st.plotly_chart(sunburst_fig, use_container_width=True)
    
    with col2:
        if women_stats:
            advanced_fig = create_advanced_metrics_chart(women_stats)
            if advanced_fig:
                st.plotly_chart(advanced_fig, use_container_width=True)
    
    # Tabela resumo
    st.subheader("📋 Visão Geral dos Dados")
    summary_df = df[['name', 'race', 'cargo', 'state', 'diversity_score']].head(10)
    st.dataframe(summary_df, use_container_width=True)

elif page == "👩‍💼 Análise Feminina":
    st.header("👩‍💼 Análise Específica de Candidaturas Femininas")
    
    if women_stats:
        # Estatísticas principais
        stats = women_stats.get('statistics', {})
        insights = women_stats.get('insights', {})
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "👩 Total de Candidatas",
                women_stats.get('total_women_candidates', 0)
            )
        
        with col2:
            st.metric(
                "🌈 % Minorias",
                f"{stats.get('minority_percentage', 0):.1f}%"
            )
        
        with col3:
            st.metric(
                "⭐ Score Médio Diversidade",
                f"{stats.get('avg_diversity_score', 0):.2f}"
            )
        
        # Insights destacados
        st.subheader("💡 Insights Principais")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info(f"**Raça Predominante:** {insights.get('most_common_race', 'N/A')}")
        
        with col2:
            st.info(f"**Estado Mais Ativo:** {insights.get('most_active_state', 'N/A')}")
        
        with col3:
            st.info(f"**Cargo Mais Disputado:** {insights.get('most_disputed_cargo', 'N/A')}")
        
        # Top candidatas
        st.subheader("🏆 Top Candidatas por Potencial")
        top_candidates = women_stats.get('top_candidates', [])
        if top_candidates:
            top_df = pd.DataFrame(top_candidates)
            
            fig = px.bar(
                top_df,
                x='diversity_score',
                y='name',
                orientation='h',
                color='race',
                title="🏆 Ranking por Score de Diversidade"
            )
            fig.update_layout(height=400, yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("❌ Não foi possível carregar a análise feminina")

elif page == "📊 Estatísticas Eleitorais":
    st.header("📊 Estatísticas Eleitorais Gerais")
    
    if election_stats:
        summary = election_stats.get('summary', {})
        demographics = election_stats.get('demographics', {})
        geographic = election_stats.get('geographic', {})
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("👥 Total Candidatos", summary.get('total_candidates', 0))
        
        with col2:
            st.metric("👩 Candidatas", summary.get('women_candidates', 0))
        
        with col3:
            st.metric("👨 Candidatos", summary.get('men_candidates', 0))
        
        with col4:
            st.metric("📊 % Mulheres", f"{summary.get('women_percentage', 0):.1f}%")
        
        # Gráficos demográficos
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribuição por faixa etária
            age_groups = demographics.get('by_age_group', {})
            if age_groups:
                fig = px.pie(
                    values=list(age_groups.values()),
                    names=list(age_groups.keys()),
                    title="👥 Distribuição por Faixa Etária (Estimada)"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Top estados
            top_states = geographic.get('top_states', [])
            if top_states:
                states_df = pd.DataFrame(top_states)
                fig = px.bar(
                    states_df,
                    x='state',
                    y='count',
                    title="🗺️ Top 5 Estados por Número de Candidatos"
                )
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("❌ Não foi possível carregar as estatísticas eleitorais")

elif page == "🎯 Candidatas Potenciais":
    st.header("🎯 Candidatas com Maior Potencial")
    
    if potential_data:
        # Controles de filtro
        col1, col2 = st.columns(2)
        
        with col1:
            min_score = st.slider("Score Mínimo", 0.0, 1.0, 0.5, 0.1)
        
        with col2:
            limit = st.selectbox("Número de Candidatas", [5, 10, 15, 20], index=1)
        
        # Aplicar filtros (simular chamada à API)
        candidates = potential_data.get('candidates', [])
        filtered_candidates = [c for c in candidates if c.get('diversity_score', 0) >= min_score][:limit]
        
        if filtered_candidates:
            # Gráfico de ranking
            ranking_fig = create_potential_ranking({'candidates': filtered_candidates})
            if ranking_fig:
                st.plotly_chart(ranking_fig, use_container_width=True)
            
            # Tabela detalhada
            st.subheader("📋 Detalhes das Candidatas")
            candidates_df = pd.DataFrame(filtered_candidates)
            st.dataframe(candidates_df, use_container_width=True)
            
            # Estatísticas do grupo
            group_stats = potential_data.get('group_statistics', {})
            if group_stats:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("⭐ Score Médio", f"{group_stats.get('average_diversity_score', 0):.3f}")
                
                with col2:
                    st.metric("🌈 Candidatas Minorias", group_stats.get('minority_candidates', 0))
                
                with col3:
                    st.metric("📊 % Minorias", f"{group_stats.get('minority_percentage', 0):.1f}%")
        else:
            st.warning("⚠️ Nenhuma candidata encontrada com os critérios selecionados")
    else:
        st.error("❌ Não foi possível carregar os dados de potencial")

elif page == "🔍 Explorador de Dados":
    st.header("🔍 Explorador Interativo de Dados")
    
    # Filtros interativos
    st.subheader("🎛️ Filtros")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_states = st.multiselect(
            "Estados:",
            options=df['state'].unique(),
            default=list(df['state'].unique())
        )
    
    with col2:
        selected_races = st.multiselect(
            "Raças:",
            options=df['race'].unique(),
            default=list(df['race'].unique())
        )
    
    with col3:
        selected_cargos = st.multiselect(
            "Cargos:",
            options=df['cargo'].unique(),
            default=list(df['cargo'].unique())
        )
    
    # Aplicar filtros
    filtered_df = df[
        (df['state'].isin(selected_states)) &
        (df['race'].isin(selected_races)) &
        (df['cargo'].isin(selected_cargos))
    ]
    
    st.subheader(f"📊 Resultados Filtrados ({len(filtered_df)} candidatas)")
    
    if not filtered_df.empty:
        # Gráficos dos dados filtrados
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.histogram(
                filtered_df, 
                x='race', 
                title="Distribuição por Raça (Filtrado)",
                color='race'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.histogram(
                filtered_df, 
                x='cargo', 
                title="Distribuição por Cargo (Filtrado)",
                color='cargo'
            )
            fig.update_layout(xaxis_tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
        
        # Tabela completa
        st.subheader("📋 Dados Completos")
        st.dataframe(filtered_df, use_container_width=True)
        
        # Download dos dados
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="💾 Download CSV",
            data=csv,
            file_name=f"candidatas_filtradas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.warning("⚠️ Nenhum resultado encontrado com os filtros selecionados")

elif page == "📈 Qualidade dos Dados":
    st.header("📈 Relatório de Qualidade dos Dados")
    
    if quality_data:
        summary = quality_data.get('summary', {})
        completeness = quality_data.get('completeness', {})
        consistency = quality_data.get('consistency', {})
        uniqueness = quality_data.get('uniqueness', {})
        
        # Score geral
        overall_score = summary.get('overall_quality_score', 0)
        rating = summary.get('quality_rating', 'N/A')
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("🎯 Score Geral", f"{overall_score:.1f}/100")
        
        with col2:
            st.metric("⭐ Classificação", rating)
        
        with col3:
            st.metric("📊 Total Registros", summary.get('total_records', 0))
        
        # Gráfico de completude
        st.subheader("📊 Completude dos Campos")
        
        fields = completeness.get('fields', {})
        if fields:
            fig = px.bar(
                x=list(fields.keys()),
                y=list(fields.values()),
                title="% de Completude por Campo",
                color=list(fields.values()),
                color_continuous_scale='RdYlGn'
            )
            fig.update_layout(yaxis_range=[0, 100])
            st.plotly_chart(fig, use_container_width=True)
        
        # Métricas detalhadas
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("✅ Consistência")
            st.metric("Anos Inválidos", consistency.get('invalid_years', 0))
            st.metric("Score Consistência", f"{consistency.get('consistency_score', 0):.1f}/100")
        
        with col2:
            st.subheader("🔍 Unicidade")
            st.metric("Possíveis Duplicatas", uniqueness.get('potential_duplicates', 0))
            st.metric("Score Unicidade", f"{uniqueness.get('uniqueness_score', 0):.1f}/100")
        
        # Recomendações
        recommendations = quality_data.get('recommendations', [])
        if recommendations:
            st.subheader("💡 Recomendações")
            for i, rec in enumerate(recommendations, 1):
                st.info(f"{i}. {rec}")
    else:
        st.error("❌ Não foi possível carregar o relatório de qualidade")

elif page == "⚙️ Configurações":
    st.header("⚙️ Configurações e Informações")
    
    st.subheader("� Metodologia de Score de Diversidade")
    
    st.info("""
    **🎯 OBJETIVO:** Identificar candidatas com potencial para promover diversidade através de 
    **AÇÕES e COMPETÊNCIAS**, não características pessoais.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **📋 CRITÉRIOS DE AVALIAÇÃO:**
        
        **1️⃣ Representatividade Regional (25%)**
        - Norte/Nordeste/Centro-Oeste: 25 pontos
        - Sul/Sudeste: 15 pontos
        - *Promove descentralização política*
        
        **2️⃣ Experiência Política (30%)**
        - Prefeito/Governador: 30 pontos
        - Senador/Dep. Federal: 25 pontos
        - Deputado Estadual: 20 pontos
        - *Capacidade de impacto em políticas*
        """)
    
    with col2:
        st.markdown("""
        **3️⃣ Formação Acadêmica (20%)**
        - Superior: 20 pontos
        - Médio: 15 pontos
        - Fundamental: 10 pontos
        - *Preparação técnica para o cargo*
        
        **4️⃣ Histórico com Diversidade (25%)**
        - Professor/Ativista/Assistente Social: 25 pontos
        - Advogado/Jornalista/Psicólogo: 25 pontos
        - Outras profissões: 10 pontos
        - *Experiência com causas sociais*
        """)
    
    st.success("""
    ✅ **PRINCÍPIOS ÉTICOS:**
    - Sem discriminação racial ou étnica
    - Foco em competências objetivas
    - Transparência total na metodologia
    - Critérios auditáveis
    - Igualdade de oportunidades
    """)
    
    st.warning("""
    ⚠️ **LIMITAÇÕES:**
    - Scores são indicativos, não determinísticos
    - Devem ser complementados com análise qualitativa
    - Não substituem avaliação humana especializada
    """)
    
    st.subheader("�🔧 Configurações da API")
    st.code(f"URL Base: {API_BASE_URL}")
    
    st.subheader("📊 Cache de Dados")
    st.info("Os dados são atualizados automaticamente a cada 5 minutos")
    
    if st.button("🗑️ Limpar Cache"):
        st.cache_data.clear()
        st.success("✅ Cache limpo com sucesso!")
    
    st.subheader("📈 Estatísticas da Sessão")
    st.write(f"**Timestamp atual:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.write(f"**Dados carregados:** {len(df)} registros")
    
    st.subheader("🛠️ Informações Técnicas")
    st.json({
        "streamlit_version": st.__version__,
        "methodology_version": "2.0 - Sistema Justo",
        "last_update": "2025-10-03",
        "api_endpoints": [
            "/candidates",
            "/women-analysis", 
            "/election-stats",
            "/potential-candidates",
            "/data-quality"
        ],
        "features": [
            "Cache automático",
            "Gráficos interativos", 
            "Filtros dinâmicos",
            "Export CSV",
            "Auto-refresh",
            "Sistema de scoring justo e transparente"
        ]
    })

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**🏛️ Eleições 2026 Analytics**")

with col2:
    st.markdown("**💡 Dashboard Premium**")

with col3:
    st.markdown(f"**🕒 Última atualização:** {datetime.now().strftime('%H:%M:%S')}")
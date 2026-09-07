"""
Dashboard Excel-Style COM FILTROS - Versão Funcional
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Eleições 2026 - Com Filtros",
    page_icon="🏛️",
    layout="wide"
)

# Função simples para API
def get_candidates_simple(limit=5000):
    """Função simples para buscar candidatas"""
    try:
        # Buscar candidatas com parâmetros corretos da API
        url = "http://api:8000/candidates/paginated"
        params = {
            "page": 1,
            "page_size": limit
        }
        
        response = requests.get(url, params=params, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            candidates = data.get('candidates', [])
            
            if candidates:
                df = pd.DataFrame(candidates)
                st.write(f"Debug: Carregadas {len(df)} candidatas")
                st.write(f"Debug: Colunas disponíveis: {list(df.columns)}")
                return df
            else:
                st.error("❌ Nenhuma candidata encontrada na resposta")
                return pd.DataFrame()
        else:
            st.error(f"❌ Erro HTTP {response.status_code}: {response.text}")
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return pd.DataFrame()

def apply_filters(df, filters):
    """Aplicar filtros no DataFrame"""
    filtered_df = df.copy()
    
    # Filtro por estados
    if filters['states']:
        filtered_df = filtered_df[filtered_df['state'].isin(filters['states'])]
    
    # Filtro por regiões
    if filters['regions']:
        filtered_df = filtered_df[filtered_df['region'].isin(filters['regions'])]
    
    # Filtro por cargos
    if filters['cargos']:
        filtered_df = filtered_df[filtered_df['cargo'].isin(filters['cargos'])]
    
    # Filtro por educação
    if filters['education']:
        filtered_df = filtered_df[filtered_df['education'].isin(filters['education'])]
    
    # Filtro por faixa de votos
    if 'votes_received' in filtered_df.columns and filters['min_votes'] is not None:
        filtered_df = filtered_df[filtered_df['votes_received'] >= filters['min_votes']]
    
    return filtered_df

def calculate_metrics(df):
    """Calcular métricas relevantes"""
    if df.empty:
        return {}
    
    metrics = {}
    
    # Métricas básicas
    metrics['total_candidates'] = len(df)
    
    if 'votes_received' in df.columns:
        metrics['total_votes'] = df['votes_received'].sum()
        metrics['avg_votes'] = df['votes_received'].mean()
        metrics['max_votes'] = df['votes_received'].max()
        metrics['min_votes'] = df['votes_received'].min()
    
    if 'diversity_score' in df.columns:
        metrics['avg_diversity'] = df['diversity_score'].mean()
        metrics['high_diversity'] = (df['diversity_score'] > 0.8).sum()
    
    # Métricas de diversidade
    if 'race' in df.columns:
        minorities = df[df['race'].isin(['PRETA', 'PARDA', 'INDÍGENA', 'AMARELA'])].shape[0]
        metrics['minorities_count'] = minorities
        metrics['minorities_pct'] = (minorities / len(df)) * 100 if len(df) > 0 else 0
    
    if 'education' in df.columns:
        superior = df[df['education'].str.contains('SUPERIOR|PÓS', case=False, na=False)].shape[0]
        metrics['superior_education'] = superior
        metrics['superior_pct'] = (superior / len(df)) * 100 if len(df) > 0 else 0
    
    return metrics

# Header
st.markdown("""
<div style="background: linear-gradient(90deg, #1f77b4, #ff7f0e); padding: 1rem; border-radius: 10px; color: white; text-align: center; margin-bottom: 2rem;">
    <h1>🎯 Eleições 2026 - Dashboard com Filtros</h1>
    <p>Filtros Interativos + Métricas Relevantes</p>
</div>
""", unsafe_allow_html=True)

# Carregamento inicial
if 'candidates_df' not in st.session_state:
    # Não carregar automaticamente, esperar clique do usuário
    st.session_state['data_loaded'] = False

# Botão para carregar dados
if st.button("🔄 Carregar Dados Iniciais"):
    with st.spinner("Carregando dados da API..."):
        try:
            df = get_candidates_simple(limit=1000)  # Começar com menos dados
            if not df.empty:
                st.session_state['candidates_df'] = df
                st.session_state['data_loaded'] = True
                st.success(f"✅ Sucesso! {len(df)} candidatas carregadas")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ DataFrame vazio - verificar API")
        except Exception as e:
            st.error(f"❌ Erro no carregamento: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

if st.session_state.get('data_loaded', False) and 'candidates_df' in st.session_state:
    df = st.session_state['candidates_df']
    
    # SIDEBAR COM FILTROS
    st.sidebar.header("🎛️ Filtros Interativos")
    
    # Filtro por Estados
    if 'state' in df.columns:
        states_available = sorted(df['state'].dropna().unique())
        selected_states = st.sidebar.multiselect(
            "🗺️ Estados",
            options=states_available,
            default=[],
            help="Selecione um ou mais estados"
        )
    else:
        selected_states = []
    
    # Filtro por Regiões
    if 'region' in df.columns:
        regions_available = sorted(df['region'].dropna().unique())
        selected_regions = st.sidebar.multiselect(
            "🌎 Regiões",
            options=regions_available,
            default=[],
            help="Selecione uma ou mais regiões"
        )
    else:
        selected_regions = []
    
    # Filtro por Cargos
    if 'cargo' in df.columns:
        cargos_available = sorted(df['cargo'].dropna().unique())
        selected_cargos = st.sidebar.multiselect(
            "🏛️ Cargos",
            options=cargos_available,
            default=[],
            help="Selecione um ou mais cargos"
        )
    else:
        selected_cargos = []
    
    # Filtro por Educação
    if 'education' in df.columns:
        education_available = sorted(df['education'].dropna().unique())
        selected_education = st.sidebar.multiselect(
            "🎓 Educação",
            options=education_available,
            default=[],
            help="Selecione níveis de educação"
        )
    else:
        selected_education = []
    
    # Filtro por Votação Mínima
    min_votes = None
    if 'votes_received' in df.columns:
        max_possible = int(df['votes_received'].max())
        min_votes = st.sidebar.slider(
            "🗳️ Votos Mínimos",
            min_value=0,
            max_value=max_possible,
            value=0,
            step=1000,
            help="Candidatas com pelo menos X votos"
        )
    
    # Aplicar filtros
    filters = {
        'states': selected_states,
        'regions': selected_regions,
        'cargos': selected_cargos,
        'education': selected_education,
        'min_votes': min_votes if min_votes and min_votes > 0 else None
    }
    
    filtered_df = apply_filters(df, filters)
    
    # Botão para limpar filtros
    if st.sidebar.button("🗑️ Limpar Todos os Filtros"):
        st.rerun()
    
    # MÉTRICAS PRINCIPAIS
    st.subheader("📊 Métricas dos Dados Filtrados")
    
    metrics = calculate_metrics(filtered_df)
    
    if metrics:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "👥 Total Candidatas",
                f"{metrics.get('total_candidates', 0):,}",
                delta=f"{metrics.get('total_candidates', 0) - len(df):,}" if filtered_df is not df else None
            )
        
        with col2:
            if 'total_votes' in metrics:
                st.metric(
                    "🗳️ Total de Votos",
                    f"{metrics['total_votes']:,.0f}",
                    help="Soma de todos os votos das candidatas filtradas"
                )
        
        with col3:
            if 'avg_votes' in metrics:
                st.metric(
                    "📊 Média de Votos",
                    f"{metrics['avg_votes']:,.0f}",
                    help="Média de votos por candidata"
                )
        
        with col4:
            if 'max_votes' in metrics:
                st.metric(
                    "🏆 Maior Votação",
                    f"{metrics['max_votes']:,.0f}",
                    help="Candidata mais votada"
                )
        
        # Segunda linha de métricas
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            if 'minorities_count' in metrics:
                st.metric(
                    "🌍 Minorias Raciais",
                    f"{metrics['minorities_count']:,} ({metrics['minorities_pct']:.1f}%)",
                    help="Candidatas pretas, pardas, indígenas ou amarelas"
                )
        
        with col6:
            if 'superior_education' in metrics:
                st.metric(
                    "🎓 Ensino Superior",
                    f"{metrics['superior_education']:,} ({metrics['superior_pct']:.1f}%)",
                    help="Candidatas com superior completo ou pós-graduação"
                )
        
        with col7:
            if 'avg_diversity' in metrics:
                st.metric(
                    "⭐ Score Médio",
                    f"{metrics['avg_diversity']:.3f}",
                    help="Score médio de diversidade"
                )
        
        with col8:
            if 'high_diversity' in metrics:
                st.metric(
                    "🌟 Alto Potencial",
                    f"{metrics['high_diversity']:,}",
                    help="Candidatas com score > 0.8"
                )
    
    # VISUALIZAÇÕES
    if not filtered_df.empty:
        
        st.markdown("---")
        st.subheader("📈 Análises Visuais")
        
        # Gráficos lado a lado
        col_left, col_right = st.columns(2)
        
        with col_left:
            # Gráfico por região
            if 'region' in filtered_df.columns:
                region_counts = filtered_df['region'].value_counts()
                fig_region = px.pie(
                    values=region_counts.values,
                    names=region_counts.index,
                    title="📊 Distribuição por Região"
                )
                st.plotly_chart(fig_region, use_container_width=True)
        
        with col_right:
            # Gráfico por cargo
            if 'cargo' in filtered_df.columns:
                cargo_counts = filtered_df['cargo'].value_counts().head(10)
                fig_cargo = px.bar(
                    x=cargo_counts.values,
                    y=cargo_counts.index,
                    orientation='h',
                    title="🏛️ Top 10 Cargos"
                )
                fig_cargo.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_cargo, use_container_width=True)
        
        # Top 10 mais votadas
        if 'votes_received' in filtered_df.columns and 'ballot_name' in filtered_df.columns:
            st.markdown("---")
            st.subheader("🏆 Top 10 Candidatas Mais Votadas")
            
            top_10 = filtered_df.nlargest(10, 'votes_received')
            
            # Tabela
            display_cols = ['ballot_name', 'state', 'region', 'cargo', 'votes_received']
            if 'vote_percentage' in top_10.columns:
                display_cols.append('vote_percentage')
            
            available_cols = [col for col in display_cols if col in top_10.columns]
            st.dataframe(
                top_10[available_cols],
                use_container_width=True,
                column_config={
                    "votes_received": st.column_config.NumberColumn(
                        "🗳️ Votos",
                        format="%d"
                    ),
                    "vote_percentage": st.column_config.NumberColumn(
                        "📊 %",
                        format="%.4f%%"
                    )
                }
            )
            
            # Gráfico das Top 10
            fig_top = px.bar(
                top_10.head(10),
                x='ballot_name',
                y='votes_received',
                color='region',
                title="🏆 Top 10 Candidatas Mais Votadas",
                hover_data=['state', 'cargo']
            )
            fig_top.update_layout(xaxis_tickangle=45)
            st.plotly_chart(fig_top, use_container_width=True)
        
        # Análise por educação vs votação
        if 'education' in filtered_df.columns and 'votes_received' in filtered_df.columns:
            st.markdown("---")
            st.subheader("🎓 Análise: Educação vs Votação")
            
            edu_stats = filtered_df.groupby('education').agg({
                'votes_received': ['count', 'sum', 'mean'],
                'diversity_score': 'mean' if 'diversity_score' in filtered_df.columns else lambda x: 0
            }).round(2)
            
            edu_stats.columns = ['Candidatas', 'Total Votos', 'Média Votos', 'Score Médio']
            edu_stats = edu_stats.reset_index().sort_values('Total Votos', ascending=False)
            
            st.dataframe(edu_stats, use_container_width=True)
        
        # Informações dos filtros ativos
        st.markdown("---")
        st.subheader("🎯 Filtros Ativos")
        
        active_filters = []
        if selected_states:
            active_filters.append(f"**Estados**: {', '.join(selected_states)}")
        if selected_regions:
            active_filters.append(f"**Regiões**: {', '.join(selected_regions)}")
        if selected_cargos:
            active_filters.append(f"**Cargos**: {', '.join(selected_cargos[:3])}{'...' if len(selected_cargos) > 3 else ''}")
        if selected_education:
            active_filters.append(f"**Educação**: {len(selected_education)} selecionados")
        if min_votes and min_votes > 0:
            active_filters.append(f"**Votos Mínimos**: {min_votes:,}")
        
        if active_filters:
            for filter_text in active_filters:
                st.info(filter_text)
        else:
            st.info("🔍 **Nenhum filtro ativo** - Mostrando todos os dados")
        
        # Amostra dos dados filtrados
        st.markdown("---")
        st.subheader("📋 Amostra dos Dados Filtrados")
        st.dataframe(filtered_df.head(20), use_container_width=True)
        
        # Botão de download
        if st.button("📥 Baixar Dados Filtrados"):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f'candidatas_filtradas_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                mime='text/csv'
            )
    
    else:
        st.warning("⚠️ Nenhuma candidata encontrada com os filtros aplicados")
        st.info("💡 Tente ajustar ou remover alguns filtros")

else:
    st.info("📊 **Clique no botão acima para carregar os dados e começar a usar os filtros!**")
    st.markdown("""
    ### 🎯 O que você poderá fazer:
    - **🗺️ Filtrar por Estados** - Selecione SP, RJ, MG, etc.
    - **🌎 Filtrar por Regiões** - Sudeste, Nordeste, Norte, etc.
    - **🏛️ Filtrar por Cargos** - Deputado, Governador, Senador, etc.
    - **🎓 Filtrar por Educação** - Superior, Pós-graduação, etc.
    - **🗳️ Filtrar por Votação** - Candidatas com X votos ou mais
    
    ### 📊 Métricas que serão exibidas:
    - Total de candidatas e votos
    - Percentual de minorias raciais  
    - Nível educacional das candidatas
    - Rankings e comparações
    - Gráficos interativos
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>🎯 <strong>Dashboard com Filtros Interativos</strong> - Eleições 2026 Analytics</p>
    <p>Filtre por estado, região, cargo, educação e votação | Métricas em tempo real</p>
</div>
""", unsafe_allow_html=True)
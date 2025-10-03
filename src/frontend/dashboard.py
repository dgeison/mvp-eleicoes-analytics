"""
Dashboard Streamlit para visualização dos dados eleitorais
Foco em análise de candidaturas femininas
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
from datetime import datetime
from pathlib import Path
import numpy as np

# Configuração simples sem dependência de settings
API_BASE_URL = "http://api:8000"

# Configuração da página
st.set_page_config(
    page_title="Eleições 2026 - Analytics Feminino",
    page_icon="👩‍💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #1f77b4;
    }
    .women-focus {
        background: linear-gradient(90deg, #ff6b9d, #c44569);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .insight-box {
        background-color: #e8f4fd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #0066cc;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


class ElectionDashboard:
    """Classe principal do dashboard"""
    
    def __init__(self):
        self.api_base_url = API_BASE_URL + "/api/v1"
    
    def load_data_from_api(self):
        """Carrega dados da API"""
        try:
            response = requests.get(f"{self.api_base_url}/candidates?limit=1000")
            if response.status_code == 200:
                data = response.json()
                return pd.DataFrame(data['data'])
            else:
                st.error(f"Erro ao carregar dados: {response.status_code}")
                return pd.DataFrame()
        except Exception as e:
            st.error(f"Erro de conexão com a API: {str(e)}")
            return pd.DataFrame()
    
    def create_overview_metrics(self, df):
        """Cria métricas de overview"""
        if df.empty:
            return
        
        st.markdown('<h2 class="main-header">📊 Panorama Geral das Eleições</h2>', unsafe_allow_html=True)
        
        # Métricas principais
        col1, col2, col3, col4, col5 = st.columns(5)
        
        total_candidates = len(df)
        women_candidates = len(df[df['IS_WOMAN'] == True])
        women_percentage = (women_candidates / total_candidates) * 100 if total_candidates > 0 else 0
        minority_candidates = len(df[df['IS_MINORITY_RACE'] == True])
        avg_diversity = df['DIVERSITY_SCORE'].mean() if 'DIVERSITY_SCORE' in df.columns else 0
        
        with col1:
            st.metric(
                label="Total de Candidatos",
                value=f"{total_candidates:,}",
                delta=None
            )
        
        with col2:
            st.metric(
                label="Candidatas Mulheres",
                value=f"{women_candidates:,}",
                delta=f"{women_percentage:.1f}%"
            )
        
        with col3:
            st.metric(
                label="Candidatos de Minorias",
                value=f"{minority_candidates:,}",
                delta=f"{(minority_candidates/total_candidates)*100:.1f}%" if total_candidates > 0 else "0%"
            )
        
        with col4:
            st.metric(
                label="Score Médio de Diversidade",
                value=f"{avg_diversity:.2f}",
                delta=None
            )
        
        with col5:
            years_covered = df['ANO_ELEICAO'].nunique() if 'ANO_ELEICAO' in df.columns else 0
            st.metric(
                label="Anos Cobertos",
                value=years_covered,
                delta=None
            )
    
    def create_women_analysis_section(self, df):
        """Seção específica de análise feminina"""
        st.markdown('<div class="women-focus"><h2>👩‍💼 Análise Específica: Candidaturas Femininas</h2></div>', unsafe_allow_html=True)
        
        if df.empty:
            st.warning("Nenhum dado disponível para análise")
            return
        
        women_df = df[df['IS_WOMAN'] == True].copy()
        
        if women_df.empty:
            st.warning("Nenhuma candidata encontrada nos dados")
            return
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            selected_years = st.multiselect(
                "Selecione os Anos",
                options=sorted(df['ANO_ELEICAO'].unique()) if 'ANO_ELEICAO' in df.columns else [],
                default=sorted(df['ANO_ELEICAO'].unique()) if 'ANO_ELEICAO' in df.columns else []
            )
        
        with col2:
            selected_regions = st.multiselect(
                "Selecione as Regiões",
                options=sorted(df['REGIAO'].unique()) if 'REGIAO' in df.columns else [],
                default=sorted(df['REGIAO'].unique()) if 'REGIAO' in df.columns else []
            )
        
        with col3:
            selected_cargos = st.multiselect(
                "Selecione Categorias de Cargo",
                options=sorted(df['CARGO_CATEGORY'].unique()) if 'CARGO_CATEGORY' in df.columns else [],
                default=sorted(df['CARGO_CATEGORY'].unique()) if 'CARGO_CATEGORY' in df.columns else []
            )
        
        # Aplicar filtros
        filtered_women = women_df.copy()
        if selected_years and 'ANO_ELEICAO' in filtered_women.columns:
            filtered_women = filtered_women[filtered_women['ANO_ELEICAO'].isin(selected_years)]
        if selected_regions and 'REGIAO' in filtered_women.columns:
            filtered_women = filtered_women[filtered_women['REGIAO'].isin(selected_regions)]
        if selected_cargos and 'CARGO_CATEGORY' in filtered_women.columns:
            filtered_women = filtered_women[filtered_women['CARGO_CATEGORY'].isin(selected_cargos)]
        
        # Visualizações
        self.create_women_visualizations(filtered_women)
    
    def create_women_visualizations(self, women_df):
        """Cria visualizações específicas para mulheres"""
        if women_df.empty:
            st.warning("Nenhum dado após aplicar filtros")
            return
        
        # Row 1: Distribuições básicas
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribuição por raça/cor
            if 'COR_RACA' in women_df.columns:
                race_counts = women_df['COR_RACA'].value_counts()
                fig_race = px.pie(
                    values=race_counts.values,
                    names=race_counts.index,
                    title="Distribuição por Cor/Raça",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_race.update_layout(height=400)
                st.plotly_chart(fig_race, use_container_width=True)
        
        with col2:
            # Distribuição por região
            if 'REGIAO' in women_df.columns:
                region_counts = women_df['REGIAO'].value_counts()
                fig_region = px.bar(
                    x=region_counts.index,
                    y=region_counts.values,
                    title="Candidatas por Região",
                    color=region_counts.values,
                    color_continuous_scale="viridis"
                )
                fig_region.update_layout(height=400)
                st.plotly_chart(fig_region, use_container_width=True)
        
        # Row 2: Análise temporal
        if 'ANO_ELEICAO' in women_df.columns:
            st.subheader("📈 Evolução Temporal")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Evolução do número de candidatas
                yearly_counts = women_df.groupby('ANO_ELEICAO').size().reset_index(name='count')
                fig_timeline = px.line(
                    yearly_counts,
                    x='ANO_ELEICAO',
                    y='count',
                    title="Evolução do Número de Candidatas",
                    markers=True
                )
                fig_timeline.update_layout(height=400)
                st.plotly_chart(fig_timeline, use_container_width=True)
            
            with col2:
                # Evolução do potencial de marketing
                if 'MARKETING_POTENTIAL' in women_df.columns:
                    yearly_potential = women_df.groupby('ANO_ELEICAO')['MARKETING_POTENTIAL'].mean().reset_index()
                    fig_potential = px.bar(
                        yearly_potential,
                        x='ANO_ELEICAO',
                        y='MARKETING_POTENTIAL',
                        title="Potencial Médio de Marketing por Ano",
                        color='MARKETING_POTENTIAL',
                        color_continuous_scale="blues"
                    )
                    fig_potential.update_layout(height=400)
                    st.plotly_chart(fig_potential, use_container_width=True)
        
        # Row 3: Análise de potencial
        st.subheader("🎯 Análise de Potencial para Marketing")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Score de potencial feminino
            if 'WOMEN_POTENTIAL_SCORE' in women_df.columns:
                fig_potential_dist = px.histogram(
                    women_df,
                    x='WOMEN_POTENTIAL_SCORE',
                    title="Distribuição do Score de Potencial",
                    nbins=20,
                    color_discrete_sequence=['#ff6b9d']
                )
                fig_potential_dist.update_layout(height=350)
                st.plotly_chart(fig_potential_dist, use_container_width=True)
        
        with col2:
            # Score de diversidade
            if 'DIVERSITY_SCORE' in women_df.columns:
                fig_diversity = px.histogram(
                    women_df,
                    x='DIVERSITY_SCORE',
                    title="Distribuição do Score de Diversidade",
                    nbins=20,
                    color_discrete_sequence=['#74b9ff']
                )
                fig_diversity.update_layout(height=350)
                st.plotly_chart(fig_diversity, use_container_width=True)
        
        with col3:
            # Potencial de marketing
            if 'MARKETING_POTENTIAL' in women_df.columns:
                fig_marketing = px.histogram(
                    women_df,
                    x='MARKETING_POTENTIAL',
                    title="Distribuição do Potencial de Marketing",
                    nbins=20,
                    color_discrete_sequence=['#00b894']
                )
                fig_marketing.update_layout(height=350)
                st.plotly_chart(fig_marketing, use_container_width=True)
    
    def create_potential_candidates_section(self, df):
        """Seção de candidatas com alto potencial"""
        st.markdown("## 🌟 Candidatas com Alto Potencial")
        
        if df.empty:
            st.warning("Nenhum dado disponível")
            return
        
        women_df = df[df['IS_WOMAN'] == True].copy()
        
        if 'WOMEN_POTENTIAL_SCORE' in women_df.columns:
            # Filtro de potencial mínimo
            min_potential = st.slider(
                "Score Mínimo de Potencial",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1
            )
            
            high_potential = women_df[women_df['WOMEN_POTENTIAL_SCORE'] >= min_potential].copy()
            
            if not high_potential.empty:
                # Ordenar por potencial
                high_potential = high_potential.sort_values('WOMEN_POTENTIAL_SCORE', ascending=False)
                
                st.info(f"Encontradas {len(high_potential)} candidatas com potencial ≥ {min_potential}")
                
                # Top 20 candidatas
                top_candidates = high_potential.head(20)
                
                # Preparar dados para exibição
                display_data = top_candidates[[
                    'NM_CANDIDATO', 'NM_UE', 'REGIAO', 'CARGO_CATEGORY',
                    'WOMEN_POTENTIAL_SCORE', 'MARKETING_POTENTIAL', 'DIVERSITY_SCORE'
                ]].copy()
                
                display_data.columns = [
                    'Nome', 'Município', 'Região', 'Categoria do Cargo',
                    'Score de Potencial', 'Potencial de Marketing', 'Score de Diversidade'
                ]
                
                # Formatar números
                for col in ['Score de Potencial', 'Potencial de Marketing', 'Score de Diversidade']:
                    display_data[col] = display_data[col].round(3)
                
                st.dataframe(
                    display_data,
                    use_container_width=True,
                    height=600
                )
                
                # Botão para download
                csv = display_data.to_csv(index=False)
                st.download_button(
                    label="📥 Baixar Lista de Candidatas (CSV)",
                    data=csv,
                    file_name=f"candidatas_alto_potencial_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning(f"Nenhuma candidata encontrada com potencial ≥ {min_potential}")
    
    def create_insights_section(self, df):
        """Seção de insights para marketing"""
        st.markdown("## 💡 Insights para Marketing Político")
        
        if df.empty:
            return
        
        women_df = df[df['IS_WOMAN'] == True].copy()
        
        # Insights baseados nos dados
        insights = []
        
        # 1. Região com maior potencial
        if 'REGIAO' in women_df.columns and 'MARKETING_POTENTIAL' in women_df.columns:
            region_potential = women_df.groupby('REGIAO')['MARKETING_POTENTIAL'].mean().sort_values(ascending=False)
            if not region_potential.empty:
                top_region = region_potential.index[0]
                insights.append(f"🌍 **Região com maior potencial**: {top_region} (score médio: {region_potential.iloc[0]:.3f})")
        
        # 2. Cargo com maior diversidade
        if 'CARGO_CATEGORY' in women_df.columns and 'DIVERSITY_SCORE' in women_df.columns:
            cargo_diversity = women_df.groupby('CARGO_CATEGORY')['DIVERSITY_SCORE'].mean().sort_values(ascending=False)
            if not cargo_diversity.empty:
                top_cargo = cargo_diversity.index[0]
                insights.append(f"🏛️ **Cargo mais diverso**: {top_cargo} (score médio: {cargo_diversity.iloc[0]:.3f})")
        
        # 3. Tendência temporal
        if 'ANO_ELEICAO' in women_df.columns:
            yearly_counts = women_df.groupby('ANO_ELEICAO').size()
            if len(yearly_counts) > 1:
                trend = "crescente" if yearly_counts.iloc[-1] > yearly_counts.iloc[0] else "decrescente"
                insights.append(f"📈 **Tendência temporal**: Número de candidatas mulheres está em tendência {trend}")
        
        # 4. Potencial não explorado
        if 'WOMEN_POTENTIAL_SCORE' in women_df.columns:
            high_potential_count = len(women_df[women_df['WOMEN_POTENTIAL_SCORE'] > 0.7])
            total_women = len(women_df)
            percentage = (high_potential_count / total_women) * 100 if total_women > 0 else 0
            insights.append(f"⭐ **Potencial não explorado**: {high_potential_count} candidatas ({percentage:.1f}%) têm alto potencial de marketing")
        
        # Exibir insights
        for insight in insights:
            st.markdown(f'<div class="insight-box">{insight}</div>', unsafe_allow_html=True)
        
        # Recomendações estratégicas
        st.markdown("### 🎯 Recomendações Estratégicas")
        
        recommendations = [
            "**Foque em regiões com maior potencial**: Concentre recursos de marketing nas regiões identificadas como de alto potencial.",
            "**Diversifique o portfólio**: Invista em candidatas de diferentes backgrounds raciais para maximizar o apelo eleitoral.",
            "**Aproveite o momentum digital**: Candidatas jovens e com boa educação tendem a ter melhor performance em redes sociais.",
            "**Monitore tendências**: Acompanhe a evolução temporal para identificar oportunidades emergentes."
        ]
        
        for rec in recommendations:
            st.markdown(f"• {rec}")
    
    def create_data_quality_section(self):
        """Seção de qualidade dos dados"""
        st.markdown("## 📊 Qualidade dos Dados")
        
        # Verificar arquivos de qualidade
        quality_files = list(self.silver_path.glob("*_quality_report.json"))
        
        if not quality_files:
            st.warning("Nenhum relatório de qualidade encontrado")
            return
        
        quality_data = []
        for file_path in quality_files:
            try:
                with open(file_path, 'r') as f:
                    report = json.load(f)
                    report['dataset'] = file_path.stem.replace('_quality_report', '')
                    quality_data.append(report)
            except Exception as e:
                st.error(f"Erro ao ler {file_path}: {e}")
        
        if quality_data:
            # Métricas gerais
            total_records = sum(q['total_records'] for q in quality_data)
            valid_records = sum(q['valid_records'] for q in quality_data)
            avg_quality = sum(q['quality_score'] for q in quality_data) / len(quality_data)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total de Registros", f"{total_records:,}")
            
            with col2:
                st.metric("Registros Válidos", f"{valid_records:,}", 
                         delta=f"{(valid_records/total_records)*100:.1f}%" if total_records > 0 else "0%")
            
            with col3:
                st.metric("Score Médio de Qualidade", f"{avg_quality:.3f}")
            
            # Tabela detalhada
            quality_df = pd.DataFrame(quality_data)
            st.dataframe(quality_df, use_container_width=True)


def main():
    """Função principal do dashboard"""
    # Header
    st.markdown('<h1 class="main-header">🗳️ Analytics Eleições 2026 - Foco em Candidaturas Femininas</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/300x100/1f77b4/ffffff?text=Eleições+2026", width=300)
        st.markdown("### 📋 Navegação")
        
        page = st.selectbox(
            "Selecione uma seção",
            [
                "📊 Panorama Geral",
                "👩‍💼 Análise Feminina",
                "🌟 Alto Potencial",
                "💡 Insights de Marketing",
                "📈 Qualidade dos Dados"
            ]
        )
        
        st.markdown("---")
        st.markdown("### ℹ️ Sobre")
        st.markdown("""
        Este dashboard analisa dados eleitorais brasileiros com foco especial em candidaturas femininas,
        identificando oportunidades para aumentar a representatividade política das mulheres.
        """)
        
        st.markdown("### 📈 Última Atualização")
        st.text(datetime.now().strftime("%d/%m/%Y %H:%M"))
    
    # Inicializar dashboard
    dashboard = ElectionDashboard()
    
    # Carregar dados
    with st.spinner("Carregando dados..."):
        df = dashboard.load_data_from_api()
    
    if df.empty:
        st.error("❌ Nenhum dado encontrado. Verifique se a API está funcionando.")
        st.info("Execute: `docker compose up -d api` para iniciar a API.")
        return
    
    # Navegação por páginas
    if page == "📊 Panorama Geral":
        dashboard.create_overview_metrics(df)
        dashboard.create_women_analysis_section(df)
    
    elif page == "👩‍💼 Análise Feminina":
        dashboard.create_women_analysis_section(df)
    
    elif page == "🌟 Alto Potencial":
        dashboard.create_potential_candidates_section(df)
    
    elif page == "💡 Insights de Marketing":
        dashboard.create_insights_section(df)
    
    elif page == "📈 Qualidade dos Dados":
        dashboard.create_data_quality_section()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        💻 Desenvolvido para análise estratégica de candidaturas femininas - Eleições 2026<br>
        🔗 Conecte com Power BI através da API: <code>http://localhost:8000/api/v1/powerbi/</code>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
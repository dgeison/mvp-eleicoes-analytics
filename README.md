# MVP - Plataforma de Analytics Eleitorais 2026

## 🎯 Objetivo
Desenvolver uma plataforma robusta de análise de dados eleitorais brasileiros com foco em insights para candidaturas femininas, utilizando dados do TSE e integração com redes sociais.

## 🏗️ Arquitetura

### Camadas de Dados (Medallion Architecture)
- **Bronze**: Dados brutos do TSE, redes sociais e fontes externas
- **Silver**: Dados limpos, validados e enriquecidos
- **Gold**: Dados agregados e prontos para análise/dashboard

### Stack Tecnológica
- **Backend**: Python, PySpark, FastAPI
- **Banco de Dados**: PostgreSQL, Apache Spark
- **ETL/ELT**: Apache Airflow
- **Frontend**: React/Next.js, Streamlit
- **Visualização**: Power BI, Plotly
- **Infraestrutura**: Docker, Apache Kafka

## 📊 Fontes de Dados

### Principais
- [TSE - Dados Abertos](https://dadosabertos.tse.jus.br/dataset/)
- [TSE - Estatísticas](https://www.tse.jus.br/eleicoes/estatisticas/estatisticas)
- APIs Instagram/Facebook
- Dados demográficos IBGE

### Eleições Cobertas
- 4 últimas eleições majoritárias (2022, 2018, 2014, 2010)
- 4 últimas eleições estaduais/municipais

## 🎯 Objetivos de Análise

### Demografia Eleitoral
- Distribuição por gênero, raça/cor
- Análise de candidaturas femininas
- Perfil socioeconômico dos candidatos

### Insights para Marketing Político
- Identificação de potenciais candidatas mulheres
- Análise de performance eleitoral por perfil
- Estratégias de posicionamento digital

### KPIs Principais
- Taxa de candidaturas femininas por região
- Performance eleitoral por demografia
- Engajamento em redes sociais
- Potencial eleitoral não explorado

## 🚀 Roadmap

### Fase 1 - MVP (4 semanas)
- [ ] Setup da infraestrutura base
- [ ] Ingestão de dados TSE (Bronze)
- [ ] Pipeline de limpeza (Silver)
- [ ] Dashboard básico (Gold)

### Fase 2 - Enriquecimento (6 semanas)
- [ ] Integração redes sociais
- [ ] APIs de dados demográficos
- [ ] ML para identificação de potenciais candidatas
- [ ] Dashboard avançado Power BI

### Fase 3 - Produção (4 semanas)
- [ ] Otimização performance
- [ ] Testes automatizados
- [ ] Deploy cloud
- [ ] Monitoramento

## 📁 Estrutura do Projeto

```
mvp_eleicoes_analytics/
├── data/
│   ├── bronze/          # Dados brutos
│   ├── silver/          # Dados processados
│   └── gold/            # Dados para análise
├── src/
│   ├── ingestion/       # Scripts de ingestão
│   ├── processing/      # ETL/ELT pipelines
│   ├── api/            # APIs FastAPI
│   ├── models/         # Modelos ML
│   └── utils/          # Utilitários
├── frontend/           # Interface web
├── dashboards/         # Templates Power BI
├── notebooks/          # Jupyter notebooks
├── tests/             # Testes automatizados
├── docker/            # Containers
└── deployment/        # Scripts deploy
```

## 📈 Métricas de Sucesso
- Cobertura de 100% das eleições target
- Dashboard com <2s de carregamento
- Identificação de 500+ potenciais candidatas
- 95% de precisão nos dados processados

## 🔧 Como Executar
```bash
# Clone o repositório
git clone <repo-url>

# Setup do ambiente
make setup

# Inicie os serviços
make run-dev

# Acesse o dashboard
http://localhost:8000
```

## 📞 Contato
Desenvolvido para análise estratégica de candidaturas femininas nas eleições brasileiras 2026.
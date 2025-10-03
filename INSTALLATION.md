# Guia de Instalação e Uso - MVP Eleições Analytics

## 🚀 Início Rápido

### Pré-requisitos
- Python 3.11+
- Docker e Docker Compose
- Git
- 8GB RAM (recomendado)
- 10GB espaço em disco

### 1. Clonagem e Setup Inicial
```bash
# Clone o projeto (substitua pela URL real)
git clone <repo-url> mvp_eleicoes_analytics
cd mvp_eleicoes_analytics

# Copie e configure o arquivo de ambiente
cp .env.example .env
# Edite o .env conforme necessário

# Inicialize o projeto completo
make init-project
```

### 2. Acesso às Aplicações
Após a inicialização, acesse:
- **API**: http://localhost:8000/docs
- **Dashboard**: http://localhost:8501
- **Jupyter Lab**: http://localhost:8888

## 📊 Estrutura do Projeto

```
mvp_eleicoes_analytics/
├── data/                    # Dados (Bronze, Silver, Gold)
│   ├── bronze/             # Dados brutos do TSE
│   ├── silver/             # Dados processados e limpos
│   └── gold/               # Dados agregados para BI
├── src/                    # Código fonte
│   ├── ingestion/          # Scripts de ingestão
│   ├── processing/         # Processamento de dados
│   ├── api/                # FastAPI application
│   ├── frontend/           # Dashboard Streamlit
│   └── models/             # Modelos ML
├── notebooks/              # Jupyter notebooks
├── dashboards/             # Templates Power BI
├── docker/                 # Configurações Docker
└── tests/                  # Testes automatizados
```

## 🔄 Pipeline de Dados

### Camada Bronze (Dados Brutos)
```bash
# Ingere dados do TSE
make data-ingest
```

### Camada Silver (Dados Processados)
```bash
# Processa e limpa dados
make data-process
```

### Camada Gold (Dados para BI)
```bash
# Pipeline completo
make data-pipeline
```

## 📈 Análise de Dados

### Dashboard Interativo
```bash
# Inicia dashboard Streamlit
make run-dashboard
```

### Jupyter Notebooks
```bash
# Inicia Jupyter Lab
make run-jupyter
```

### Análise Completa
```bash
# Executa análise exploratória completa
make analyze
```

## 🔌 API REST

### Endpoints Principais

#### Candidatos
```bash
# Buscar candidatos
curl "http://localhost:8000/api/v1/candidates?gender=F&year=2022"

# Candidatos com alto potencial
curl "http://localhost:8000/api/v1/potential-candidates?min_score=0.7"
```

#### Análise de Mulheres
```bash
# Estatísticas de candidaturas femininas
curl "http://localhost:8000/api/v1/women-analysis?year=2022"

# Dados para Power BI
curl "http://localhost:8000/api/v1/powerbi/women-dashboard"
```

## 📊 Integração Power BI

### Conectar ao Power BI
1. Abra o Power BI Desktop
2. Selecione "Obter Dados" > "Web"
3. Use as URLs dos endpoints:
   - `http://localhost:8000/api/v1/powerbi/women-dashboard`
   - `http://localhost:8000/api/v1/powerbi/diversity-metrics`

### Datasets Prontos
Os arquivos CSV na pasta `data/gold/` podem ser importados diretamente.

## 🛠️ Comandos Úteis

### Desenvolvimento
```bash
make run-dev          # Ambiente de desenvolvimento
make run-api          # Apenas API
make run-dashboard    # Apenas dashboard
make test             # Executar testes
make lint             # Verificar código
```

### Dados
```bash
make data-pipeline    # Pipeline completo
make export-csv       # Exportar para CSV
make export-powerbi   # Dados para Power BI
make backup-data      # Backup dos dados
```

### Docker
```bash
make docker-build     # Build das imagens
make docker-up        # Subir serviços
make docker-down      # Parar serviços
make docker-logs      # Ver logs
```

### Banco de Dados
```bash
make db-init          # Inicializar banco
make db-reset         # Resetar banco (cuidado!)
make backup-db        # Backup do banco
```

## 📋 Monitoramento

### Health Check
```bash
make health-check     # Verificar saúde dos serviços
make status           # Status dos containers
make logs             # Logs da aplicação
```

### Qualidade dos Dados
Acesse: http://localhost:8000/api/v1/data-quality

## 🔧 Personalização

### Adicionando Novos Anos
Edite o arquivo `.env`:
```
ELECTION_YEARS_MAJOR=2022,2018,2014,2010,2026
ELECTION_YEARS_LOCAL=2020,2016,2012,2008,2024
```

### Configurando APIs de Redes Sociais
1. Obtenha credenciais do Facebook/Instagram
2. Configure no arquivo `.env`:
```
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret
INSTAGRAM_ACCESS_TOKEN=your_token
```

### Adicionando Novos Filtros
Modifique `src/api/main.py` para adicionar novos endpoints ou filtros.

## 📚 Documentação da API

Acesse a documentação interativa em: http://localhost:8000/docs

## 🎯 Casos de Uso

### 1. Identificar Candidatas Potenciais
```python
import requests

response = requests.get(
    "http://localhost:8000/api/v1/potential-candidates",
    params={"min_score": 0.8, "region": "SUDESTE", "limit": 50}
)
candidatas = response.json()
```

### 2. Análise Regional
```python
response = requests.get(
    "http://localhost:8000/api/v1/women-analysis",
    params={"region": "NORDESTE", "year": 2022}
)
analise = response.json()
```

### 3. Estatísticas Gerais
```python
response = requests.get(
    "http://localhost:8000/api/v1/election-stats",
    params={"year": 2022}
)
stats = response.json()
```

## 🚨 Solução de Problemas

### Erro de Memória
- Reduza `BATCH_SIZE` no `.env`
- Aumente memória do Docker
- Use `MAX_WORKERS=2` para menos paralelismo

### Dados Não Carregando
```bash
# Verifique logs
make logs

# Reinicie pipeline
make clean
make data-pipeline
```

### API Não Responde
```bash
# Verifique status
make health-check

# Reinicie serviços
make docker-down
make docker-up
```

## 📞 Suporte

Para problemas ou dúvidas:
1. Verifique os logs: `make logs`
2. Execute health check: `make health-check`
3. Consulte a documentação da API: http://localhost:8000/docs

## 🔄 Atualizações

```bash
# Atualizar dependências
make update

# Aplicar migrations
make db-migrate

# Verificar segurança
make security-scan
```

## 🎉 Próximos Passos

1. **Produção**: Configure variáveis de ambiente para produção
2. **Monitoramento**: Implemente logging e métricas avançadas
3. **ML**: Desenvolva modelos preditivos para identificação de candidatas
4. **Redes Sociais**: Configure APIs do Facebook/Instagram
5. **Power BI**: Desenvolva dashboards avançados

## 📈 Métricas de Sucesso

- ✅ Cobertura de 100% das eleições target
- ✅ Dashboard com <2s de carregamento
- ✅ Identificação de 500+ potenciais candidatas
- ✅ 95% de precisão nos dados processados
- ✅ API com 99.9% uptime
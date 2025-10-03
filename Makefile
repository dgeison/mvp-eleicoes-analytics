.PHONY: help setup install clean run-dev run-prod test docs

# Variables
PYTHON = python3
PIP = pip3
DOCKER_COMPOSE = docker-compose
PROJECT_NAME = mvp_eleicoes_analytics

# Colors for output
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m # No Color

help: ## Show this help message
	@echo "$(GREEN)MVP Eleições Analytics - Makefile Commands$(NC)"
	@echo "================================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

setup: ## Initial project setup (install dependencies, create directories)
	@echo "$(GREEN)🚀 Setting up MVP Eleições Analytics...$(NC)"
	@mkdir -p data/bronze data/silver data/gold logs
	@mkdir -p src/ingestion src/processing src/api src/models src/utils
	@mkdir -p notebooks dashboards frontend tests
	@$(PIP) install --upgrade pip
	@$(PIP) install -r requirements.txt
	@echo "$(GREEN)✅ Setup completed!$(NC)"

install: ## Install Python dependencies
	@echo "$(GREEN)📦 Installing dependencies...$(NC)"
	@$(PIP) install -r requirements.txt
	@echo "$(GREEN)✅ Dependencies installed!$(NC)"

install-dev: ## Install development dependencies
	@echo "$(GREEN)🛠️ Installing development dependencies...$(NC)"
	@$(PIP) install -r requirements.txt
	@$(PIP) install pytest black flake8 jupyter ipykernel pre-commit
	@pre-commit install
	@echo "$(GREEN)✅ Development environment ready!$(NC)"

clean: ## Clean temporary files and caches
	@echo "$(GREEN)🧹 Cleaning up...$(NC)"
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type d -name "*.egg-info" -exec rm -rf {} +
	@find . -type f -name ".coverage" -delete
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@rm -rf logs/*.log
	@echo "$(GREEN)✅ Cleanup completed!$(NC)"

# Data Pipeline Commands
data-ingest: ## Run TSE data ingestion
	@echo "$(GREEN)📥 Starting data ingestion...$(NC)"
	@$(PYTHON) -m src.ingestion.tse_ingester
	@echo "$(GREEN)✅ Data ingestion completed!$(NC)"

data-process: ## Process raw data (Bronze → Silver)
	@echo "$(GREEN)⚙️ Processing data...$(NC)"
	@$(PYTHON) -m src.processing.data_processor
	@echo "$(GREEN)✅ Data processing completed!$(NC)"

data-pipeline: ## Run complete data pipeline (ingest + process)
	@echo "$(GREEN)🔄 Running complete data pipeline...$(NC)"
	@$(MAKE) data-ingest
	@$(MAKE) data-process
	@echo "$(GREEN)✅ Complete pipeline finished!$(NC)"

# Database Commands
db-init: ## Initialize database
	@echo "$(GREEN)🗄️ Initializing database...$(NC)"
	@$(PYTHON) -c "from src.api.database import init_database; init_database()"
	@echo "$(GREEN)✅ Database initialized!$(NC)"

db-reset: ## Reset database (WARNING: Deletes all data)
	@echo "$(RED)⚠️ WARNING: This will delete all database data!$(NC)"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ]
	@$(PYTHON) -c "from src.api.database import reset_database; reset_database()"
	@echo "$(GREEN)✅ Database reset completed!$(NC)"

db-migrate: ## Run database migrations
	@echo "$(GREEN)🔄 Running database migrations...$(NC)"
	@alembic upgrade head
	@echo "$(GREEN)✅ Migrations completed!$(NC)"

# Development Commands
run-api: ## Run FastAPI development server
	@echo "$(GREEN)🚀 Starting FastAPI server...$(NC)"
	@uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

run-dashboard: ## Run Streamlit dashboard
	@echo "$(GREEN)📊 Starting Streamlit dashboard...$(NC)"
	@streamlit run src/frontend/dashboard.py --server.port 8501 --server.address 0.0.0.0

run-jupyter: ## Start Jupyter Lab
	@echo "$(GREEN)📓 Starting Jupyter Lab...$(NC)"
	@jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root

run-dev: ## Start all development services
	@echo "$(GREEN)🚀 Starting all development services...$(NC)"
	@$(DOCKER_COMPOSE) up -d postgres redis minio
	@echo "$(YELLOW)⏳ Waiting for services to start...$(NC)"
	@sleep 10
	@$(MAKE) db-init
	@echo "$(GREEN)✅ Development environment ready!$(NC)"
	@echo "$(YELLOW)📡 API: http://localhost:8000$(NC)"
	@echo "$(YELLOW)📊 Dashboard: http://localhost:8501$(NC)"
	@echo "$(YELLOW)📓 Jupyter: http://localhost:8888$(NC)"

run-prod: ## Start production services
	@echo "$(GREEN)🚀 Starting production services...$(NC)"
	@$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✅ Production services started!$(NC)"

# Docker Commands
docker-build: ## Build Docker images
	@echo "$(GREEN)🐳 Building Docker images...$(NC)"
	@$(DOCKER_COMPOSE) build
	@echo "$(GREEN)✅ Docker images built!$(NC)"

docker-up: ## Start Docker services
	@echo "$(GREEN)🐳 Starting Docker services...$(NC)"
	@$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✅ Docker services started!$(NC)"

docker-down: ## Stop Docker services
	@echo "$(GREEN)🐳 Stopping Docker services...$(NC)"
	@$(DOCKER_COMPOSE) down
	@echo "$(GREEN)✅ Docker services stopped!$(NC)"

docker-logs: ## Show Docker logs
	@$(DOCKER_COMPOSE) logs -f

docker-clean: ## Clean Docker resources
	@echo "$(GREEN)🧹 Cleaning Docker resources...$(NC)"
	@$(DOCKER_COMPOSE) down -v --rmi all --remove-orphans
	@docker system prune -f
	@echo "$(GREEN)✅ Docker cleanup completed!$(NC)"

# Testing Commands
test: ## Run all tests
	@echo "$(GREEN)🧪 Running tests...$(NC)"
	@$(PYTHON) -m pytest tests/ -v
	@echo "$(GREEN)✅ Tests completed!$(NC)"

test-api: ## Run API tests
	@echo "$(GREEN)🧪 Running API tests...$(NC)"
	@$(PYTHON) -m pytest tests/test_api/ -v

test-processing: ## Run data processing tests
	@echo "$(GREEN)🧪 Running processing tests...$(NC)"
	@$(PYTHON) -m pytest tests/test_processing/ -v

test-coverage: ## Run tests with coverage
	@echo "$(GREEN)🧪 Running tests with coverage...$(NC)"
	@$(PYTHON) -m pytest tests/ --cov=src --cov-report=html --cov-report=term
	@echo "$(GREEN)📊 Coverage report: htmlcov/index.html$(NC)"

# Code Quality Commands
lint: ## Run code linting
	@echo "$(GREEN)🔍 Running linting...$(NC)"
	@flake8 src/ --max-line-length=100
	@echo "$(GREEN)✅ Linting completed!$(NC)"

format: ## Format code with Black
	@echo "$(GREEN)🎨 Formatting code...$(NC)"
	@black src/ tests/ --line-length=100
	@echo "$(GREEN)✅ Code formatted!$(NC)"

check: ## Run all code quality checks
	@echo "$(GREEN)🔍 Running code quality checks...$(NC)"
	@$(MAKE) lint
	@$(MAKE) format
	@$(MAKE) test
	@echo "$(GREEN)✅ All checks passed!$(NC)"

# Analysis Commands
analyze: ## Run complete data analysis
	@echo "$(GREEN)📊 Running complete data analysis...$(NC)"
	@$(PYTHON) -c "import subprocess; subprocess.run(['jupyter', 'nbconvert', '--execute', '--to', 'html', 'notebooks/analise_exploratoria_candidaturas_femininas.ipynb'])"
	@echo "$(GREEN)✅ Analysis completed! Check notebooks/ for HTML report.$(NC)"

generate-insights: ## Generate marketing insights
	@echo "$(GREEN)💡 Generating marketing insights...$(NC)"
	@$(PYTHON) -c "from src.processing.data_processor import process_all_data; process_all_data()"
	@echo "$(GREEN)✅ Insights generated!$(NC)"

# Data Export Commands
export-csv: ## Export data to CSV files
	@echo "$(GREEN)📤 Exporting data to CSV...$(NC)"
	@$(PYTHON) -c "from pathlib import Path; import pandas as pd; [pd.read_parquet(f).to_csv(f.with_suffix('.csv'), index=False) for f in Path('data/gold/').glob('*.parquet')]"
	@echo "$(GREEN)✅ Data exported to CSV!$(NC)"

export-powerbi: ## Generate Power BI ready datasets
	@echo "$(GREEN)📊 Generating Power BI datasets...$(NC)"
	@curl -X GET "http://localhost:8000/api/v1/powerbi/women-dashboard" > data/gold/powerbi_women_dashboard.json
	@curl -X GET "http://localhost:8000/api/v1/powerbi/diversity-metrics" > data/gold/powerbi_diversity_metrics.json
	@echo "$(GREEN)✅ Power BI datasets ready!$(NC)"

# Monitoring Commands
health-check: ## Check application health
	@echo "$(GREEN)❤️ Checking application health...$(NC)"
	@curl -f http://localhost:8000/health || echo "$(RED)❌ API not responding$(NC)"
	@curl -f http://localhost:8501/ || echo "$(RED)❌ Dashboard not responding$(NC)"

status: ## Show service status
	@echo "$(GREEN)📊 Service Status:$(NC)"
	@$(DOCKER_COMPOSE) ps

logs: ## Show application logs
	@$(DOCKER_COMPOSE) logs -f api dashboard

# Documentation Commands
docs: ## Generate documentation
	@echo "$(GREEN)📚 Generating documentation...$(NC)"
	@mkdir -p docs
	@$(PYTHON) -c "import pdoc; pdoc.pdoc('src', output_dir='docs')"
	@echo "$(GREEN)✅ Documentation generated in docs/$(NC)"

# Backup Commands
backup-data: ## Backup data files
	@echo "$(GREEN)💾 Backing up data...$(NC)"
	@mkdir -p backups
	@tar -czf backups/data_backup_$(shell date +%Y%m%d_%H%M%S).tar.gz data/
	@echo "$(GREEN)✅ Data backup completed!$(NC)"

backup-db: ## Backup database
	@echo "$(GREEN)💾 Backing up database...$(NC)"
	@mkdir -p backups
	@$(DOCKER_COMPOSE) exec postgres pg_dump -U postgres eleicoes_analytics > backups/db_backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✅ Database backup completed!$(NC)"

# Complete workflows
init-project: ## Initialize complete project (first time setup)
	@echo "$(GREEN)🎉 Initializing MVP Eleições Analytics project...$(NC)"
	@$(MAKE) setup
	@$(MAKE) docker-build
	@$(MAKE) run-dev
	@$(MAKE) data-pipeline
	@echo "$(GREEN)🎉 Project initialization completed!$(NC)"
	@echo "$(YELLOW)🔗 Access the application:$(NC)"
	@echo "  📡 API Documentation: http://localhost:8000/docs"
	@echo "  📊 Dashboard: http://localhost:8501"
	@echo "  📓 Jupyter Lab: http://localhost:8888"

demo: ## Run demo with sample data
	@echo "$(GREEN)🎬 Starting demo...$(NC)"
	@$(MAKE) run-dev
	@$(MAKE) data-pipeline
	@$(MAKE) analyze
	@echo "$(GREEN)🎬 Demo ready! Check the dashboard and API.$(NC)"

# Maintenance Commands
update: ## Update dependencies
	@echo "$(GREEN)🔄 Updating dependencies...$(NC)"
	@$(PIP) install --upgrade -r requirements.txt
	@echo "$(GREEN)✅ Dependencies updated!$(NC)"

security-scan: ## Run security scan
	@echo "$(GREEN)🔒 Running security scan...$(NC)"
	@$(PIP) install safety bandit
	@safety check
	@bandit -r src/
	@echo "$(GREEN)✅ Security scan completed!$(NC)"

# Help is default
.DEFAULT_GOAL := help
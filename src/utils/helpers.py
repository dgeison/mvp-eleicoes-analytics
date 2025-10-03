"""
Utilitários gerais para o projeto
"""
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
import json
from datetime import datetime


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """Configura logging para a aplicação"""
    
    # Criar diretório de logs se não existir
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configurar formato
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Logger principal
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler para arquivo se especificado
    if log_file:
        file_handler = logging.FileHandler(log_dir / log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def validate_data_schema(df: pd.DataFrame, required_columns: List[str]) -> Dict[str, Any]:
    """Valida schema de um DataFrame"""
    
    validation_result = {
        "is_valid": True,
        "missing_columns": [],
        "extra_columns": [],
        "data_types": {},
        "null_counts": {},
        "total_rows": len(df)
    }
    
    # Verificar colunas obrigatórias
    missing_cols = set(required_columns) - set(df.columns)
    if missing_cols:
        validation_result["is_valid"] = False
        validation_result["missing_columns"] = list(missing_cols)
    
    # Colunas extras
    extra_cols = set(df.columns) - set(required_columns)
    validation_result["extra_columns"] = list(extra_cols)
    
    # Tipos de dados
    validation_result["data_types"] = df.dtypes.to_dict()
    
    # Contagem de nulos
    validation_result["null_counts"] = df.isnull().sum().to_dict()
    
    return validation_result


def save_json_report(data: Dict[str, Any], filepath: Path, indent: int = 2):
    """Salva relatório em formato JSON"""
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False, default=str)


def load_json_config(filepath: Path) -> Dict[str, Any]:
    """Carrega configuração de arquivo JSON"""
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def ensure_directory(path: Path) -> Path:
    """Garante que um diretório existe"""
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_size_mb(filepath: Path) -> float:
    """Retorna tamanho do arquivo em MB"""
    if filepath.exists():
        return filepath.stat().st_size / (1024 * 1024)
    return 0.0


def format_number(number: int) -> str:
    """Formata número com separadores de milhares"""
    return f"{number:,}"


def calculate_percentage(part: int, total: int) -> float:
    """Calcula percentual com segurança"""
    if total == 0:
        return 0.0
    return (part / total) * 100


def create_timestamp() -> str:
    """Cria timestamp formatado"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Divisão segura que evita divisão por zero"""
    if denominator == 0:
        return default
    return numerator / denominator


class DataQualityChecker:
    """Classe para verificação de qualidade de dados"""
    
    def __init__(self):
        self.checks = []
    
    def check_completeness(self, df: pd.DataFrame, column: str, threshold: float = 0.95) -> Dict[str, Any]:
        """Verifica completude de uma coluna"""
        
        total_rows = len(df)
        non_null_rows = df[column].notna().sum()
        completeness = non_null_rows / total_rows if total_rows > 0 else 0
        
        result = {
            "column": column,
            "completeness": completeness,
            "threshold": threshold,
            "passed": completeness >= threshold,
            "total_rows": total_rows,
            "non_null_rows": int(non_null_rows),
            "null_rows": total_rows - int(non_null_rows)
        }
        
        self.checks.append(result)
        return result
    
    def check_uniqueness(self, df: pd.DataFrame, column: str) -> Dict[str, Any]:
        """Verifica unicidade de uma coluna"""
        
        total_rows = len(df)
        unique_values = df[column].nunique()
        duplicates = total_rows - unique_values
        
        result = {
            "column": column,
            "total_rows": total_rows,
            "unique_values": unique_values,
            "duplicates": duplicates,
            "uniqueness_ratio": unique_values / total_rows if total_rows > 0 else 0
        }
        
        self.checks.append(result)
        return result
    
    def check_data_types(self, df: pd.DataFrame, expected_types: Dict[str, str]) -> Dict[str, Any]:
        """Verifica tipos de dados"""
        
        type_issues = {}
        
        for column, expected_type in expected_types.items():
            if column in df.columns:
                actual_type = str(df[column].dtype)
                if expected_type not in actual_type:
                    type_issues[column] = {
                        "expected": expected_type,
                        "actual": actual_type
                    }
        
        result = {
            "type_issues": type_issues,
            "passed": len(type_issues) == 0
        }
        
        self.checks.append(result)
        return result
    
    def get_summary(self) -> Dict[str, Any]:
        """Retorna resumo de todas as verificações"""
        
        total_checks = len(self.checks)
        passed_checks = sum(1 for check in self.checks if check.get("passed", False))
        
        return {
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": total_checks - passed_checks,
            "overall_score": passed_checks / total_checks if total_checks > 0 else 0,
            "checks": self.checks
        }


class ProgressTracker:
    """Classe para acompanhar progresso de operações"""
    
    def __init__(self, total_steps: int, description: str = "Processing"):
        self.total_steps = total_steps
        self.current_step = 0
        self.description = description
        self.start_time = datetime.now()
    
    def update(self, step_description: str = ""):
        """Atualiza progresso"""
        self.current_step += 1
        percentage = (self.current_step / self.total_steps) * 100
        
        elapsed_time = datetime.now() - self.start_time
        
        print(f"\r{self.description}: {percentage:.1f}% ({self.current_step}/{self.total_steps}) - {step_description}", end="")
        
        if self.current_step >= self.total_steps:
            print(f"\n✅ Completed in {elapsed_time}")
    
    def finish(self):
        """Finaliza tracking"""
        elapsed_time = datetime.now() - self.start_time
        print(f"\n✅ {self.description} completed in {elapsed_time}")


# Constantes úteis
FEMALE_NAMES_INDICATORS = [
    'ana', 'maria', 'joana', 'carla', 'paula', 'lucia', 'cristina',
    'adriana', 'fernanda', 'patricia', 'sandra', 'monica', 'claudia',
    'rita', 'julia', 'vera', 'rosa', 'angela', 'regina', 'sonia'
]

BRAZILIAN_REGIONS = {
    'NORTE': ['AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO'],
    'NORDESTE': ['AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE'],
    'SUDESTE': ['ES', 'MG', 'RJ', 'SP'],
    'SUL': ['PR', 'RS', 'SC'],
    'CENTRO_OESTE': ['DF', 'GO', 'MT', 'MS']
}

def get_region_by_state(uf: str) -> str:
    """Retorna região baseada na UF"""
    for region, states in BRAZILIAN_REGIONS.items():
        if uf in states:
            return region
    return 'OUTROS'
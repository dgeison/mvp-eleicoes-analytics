"""
Configurações da aplicação MVP Eleições Analytics
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configurações da aplicação"""
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres123@localhost:5432/eleicoes_analytics"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # MinIO/S3
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin123"
    MINIO_BUCKET: str = "eleicoes-data"
    
    # Spark
    SPARK_MASTER_URL: str = "spark://localhost:7077"
    SPARK_APP_NAME: str = "Eleicoes_Analytics"
    
    # APIs External
    TSE_BASE_URL: str = "https://dadosabertos.tse.jus.br"
    IBGE_BASE_URL: str = "https://servicodados.ibge.gov.br/api/v1"
    
    # Social Media APIs
    FACEBOOK_APP_ID: Optional[str] = None
    FACEBOOK_APP_SECRET: Optional[str] = None
    INSTAGRAM_ACCESS_TOKEN: Optional[str] = None
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
    
    # Data paths
    DATA_PATH: str = "/app/data"
    BRONZE_PATH: str = "/app/data/bronze"
    SILVER_PATH: str = "/app/data/silver"
    GOLD_PATH: str = "/app/data/gold"
    
    # Processing
    BATCH_SIZE: int = 1000
    MAX_WORKERS: int = 4
    
    # Elections years to process
    ELECTION_YEARS_MAJOR: str = "2022,2018,2014,2010"  # Majoritárias
    ELECTION_YEARS_LOCAL: str = "2020,2016,2012,2008"  # Municipais
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Singleton instance
settings = Settings()

# Data schemas for validation
TSE_DATA_SCHEMAS = {
    "candidatos": {
        "required_columns": [
            "NM_CANDIDATO", "NM_URNA_CANDIDATO", "SG_UE", "NM_UE", 
            "CD_CARGO", "DS_CARGO", "DS_GENERO", "DS_COR_RACA",
            "DS_GRAU_INSTRUCAO", "VR_DESPESA_MAX_CAMPANHA"
        ]
    },
    "votacao": {
        "required_columns": [
            "NM_CANDIDATO", "NM_URNA_CANDIDATO", "SG_UE", "NM_UE",
            "QT_VOTOS_NOMINAIS", "ST_VOTO_EM_TRANSITO"
        ]
    },
    "prestacao_contas": {
        "required_columns": [
            "NM_CANDIDATO", "SG_UE", "VR_RECEITA", "VR_DESPESA",
            "DS_ORIGEM_RECEITA", "DS_ESPECIE_RECEITA"
        ]
    }
}

# Social media analysis keywords for women candidates identification
WOMEN_KEYWORDS = [
    "mulher", "feminina", "liderança feminina", "empoderamento",
    "igualdade de gênero", "direitos da mulher", "mãe", "esposa",
    "profissional", "empresária", "advogada", "médica", "professora"
]

# Demographic mapping
DEMOGRAPHIC_MAPPING = {
    "genero": {
        "FEMININO": "F",
        "MASCULINO": "M"
    },
    "cor_raca": {
        "BRANCA": "branca",
        "PRETA": "preta", 
        "PARDA": "parda",
        "AMARELA": "amarela",
        "INDÍGENA": "indigena",
        "NÃO INFORMADO": "nao_informado"
    }
}
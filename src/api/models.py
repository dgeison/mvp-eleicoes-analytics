"""
Modelos Pydantic para validação de dados da API
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum


class Gender(str, Enum):
    """Enum para gênero"""
    FEMALE = "F"
    MALE = "M"
    NOT_INFORMED = "NI"


class Race(str, Enum):
    """Enum para cor/raça"""
    BRANCA = "branca"
    PRETA = "preta"
    PARDA = "parda"
    AMARELA = "amarela"
    INDIGENA = "indigena"
    NAO_INFORMADO = "nao_informado"


class Region(str, Enum):
    """Enum para regiões"""
    NORTE = "NORTE"
    NORDESTE = "NORDESTE"
    SUDESTE = "SUDESTE"
    SUL = "SUL"
    CENTRO_OESTE = "CENTRO_OESTE"


class CargoCategory(str, Enum):
    """Enum para categorias de cargo"""
    EXECUTIVO_FEDERAL = "EXECUTIVO_FEDERAL"
    EXECUTIVO_ESTADUAL = "EXECUTIVO_ESTADUAL"
    EXECUTIVO_MUNICIPAL = "EXECUTIVO_MUNICIPAL"
    LEGISLATIVO_FEDERAL = "LEGISLATIVO_FEDERAL"
    LEGISLATIVO_ESTADUAL = "LEGISLATIVO_ESTADUAL"
    LEGISLATIVO_MUNICIPAL = "LEGISLATIVO_MUNICIPAL"
    OUTROS = "OUTROS"


# MODELS BASE

class BaseResponse(BaseModel):
    """Modelo base para respostas da API"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True
    )


class CandidateBase(BaseModel):
    """Modelo base para candidato"""
    name: str = Field(..., description="Nome do candidato")
    ballot_name: Optional[str] = Field(None, description="Nome de urna")
    gender: Optional[Gender] = Field(None, description="Gênero")
    race: Optional[Race] = Field(None, description="Cor/Raça")
    education: Optional[str] = Field(None, description="Grau de instrução")
    cargo: Optional[str] = Field(None, description="Cargo")
    cargo_category: Optional[CargoCategory] = Field(None, description="Categoria do cargo")
    state: Optional[str] = Field(None, description="Estado (UF)")
    city: Optional[str] = Field(None, description="Município")
    region: Optional[Region] = Field(None, description="Região")
    election_year: Optional[int] = Field(None, description="Ano da eleição")


class CandidateResponse(CandidateBase):
    """Resposta completa de candidato"""
    is_woman: Optional[bool] = Field(None, description="É mulher")
    is_minority_race: Optional[bool] = Field(None, description="É minoria racial")
    diversity_score: Optional[float] = Field(None, ge=0, le=1, description="Score de diversidade")
    women_potential_score: Optional[float] = Field(None, ge=0, le=1, description="Score de potencial feminino")
    marketing_potential: Optional[float] = Field(None, ge=0, le=1, description="Potencial de marketing")
    success_indicator: Optional[int] = Field(None, description="Indicador de sucesso")
    age: Optional[int] = Field(None, ge=0, le=150, description="Idade")
    age_group: Optional[str] = Field(None, description="Faixa etária")
    campaign_budget: Optional[float] = Field(None, ge=0, description="Orçamento de campanha")
    votes_received: Optional[int] = Field(None, ge=0, description="Votos recebidos")
    vote_percentage: Optional[float] = Field(None, ge=0, le=100, description="Percentual de votos")


# ANÁLISE DE MULHERES

class WomenStatistics(BaseModel):
    """Estatísticas de candidaturas femininas"""
    total_women_candidates: int = Field(..., ge=0, description="Total de candidatas")
    by_race: Dict[str, int] = Field(..., description="Distribuição por raça")
    by_region: Dict[str, int] = Field(..., description="Distribuição por região")
    by_cargo: Dict[str, int] = Field(..., description="Distribuição por cargo")
    avg_marketing_potential: float = Field(..., ge=0, le=1, description="Potencial médio de marketing")
    high_potential_candidates: int = Field(..., ge=0, description="Candidatas com alto potencial")
    diversity_score_avg: float = Field(..., ge=0, le=1, description="Score médio de diversidade")


class TopCandidate(BaseModel):
    """Candidata com alto potencial"""
    name: str = Field(..., description="Nome da candidata")
    location: str = Field(..., description="Local")
    cargo_category: str = Field(..., description="Categoria do cargo")
    potential_score: float = Field(..., ge=0, le=1, description="Score de potencial")
    marketing_potential: float = Field(..., ge=0, le=1, description="Potencial de marketing")


class MarketingInsights(BaseModel):
    """Insights para marketing"""
    regioes_com_maior_potencial: Dict[str, float] = Field(..., description="Regiões com maior potencial")
    cargos_com_maior_diversidade: Dict[str, float] = Field(..., description="Cargos com maior diversidade")
    faixas_etarias_predominantes: Dict[str, int] = Field(..., description="Faixas etárias predominantes")


class WomenAnalysisResponse(BaseResponse):
    """Resposta da análise de mulheres"""
    statistics: WomenStatistics
    top_candidates: List[TopCandidate]
    marketing_insights: MarketingInsights
    analysis_timestamp: str = Field(..., description="Timestamp da análise")
    filters_applied: Dict[str, Any] = Field(..., description="Filtros aplicados")


# ESTATÍSTICAS ELEITORAIS

class FinancialStatistics(BaseModel):
    """Estatísticas financeiras"""
    avg_campaign_budget: float = Field(..., ge=0, description="Orçamento médio de campanha")
    median_campaign_budget: float = Field(..., ge=0, description="Orçamento mediano de campanha")
    total_declared_wealth: float = Field(..., ge=0, description="Patrimônio total declarado")


class ElectionStatsResponse(BaseResponse):
    """Estatísticas gerais de eleição"""
    year: int = Field(..., description="Ano da eleição")
    total_candidates: int = Field(..., ge=0, description="Total de candidatos")
    women_percentage: float = Field(..., ge=0, le=100, description="Percentual de mulheres")
    minority_percentage: float = Field(..., ge=0, le=100, description="Percentual de minorias")
    gender_distribution: Dict[str, int] = Field(..., description="Distribuição por gênero")
    race_distribution: Dict[str, int] = Field(..., description="Distribuição por raça")
    cargo_distribution: Dict[str, int] = Field(..., description="Distribuição por cargo")
    region_distribution: Dict[str, int] = Field(..., description="Distribuição por região")
    financial_statistics: FinancialStatistics
    generated_at: str = Field(..., description="Timestamp da geração")


# CANDIDATAS POTENCIAIS

class PotentialCandidate(BaseModel):
    """Candidata com potencial"""
    name: str = Field(..., description="Nome")
    location: str = Field(..., description="Localização")
    region: str = Field(..., description="Região")
    cargo_category: str = Field(..., description="Categoria do cargo")
    potential_score: float = Field(..., ge=0, le=1, description="Score de potencial")
    marketing_potential: float = Field(..., ge=0, le=1, description="Potencial de marketing")
    diversity_score: float = Field(..., ge=0, le=1, description="Score de diversidade")
    race: str = Field(..., description="Cor/Raça")
    age_group: str = Field(..., description="Faixa etária")
    education: str = Field(..., description="Escolaridade")
    last_election_year: Union[int, str] = Field(..., description="Último ano de eleição")


class PotentialCandidatesResponse(BaseResponse):
    """Resposta de candidatas potenciais"""
    candidates: List[PotentialCandidate]
    total: int = Field(..., ge=0, description="Total de candidatas")
    filters: Dict[str, Any] = Field(..., description="Filtros aplicados")
    analysis_date: str = Field(..., description="Data da análise")


# QUALIDADE DOS DADOS

class DatasetQuality(BaseModel):
    """Qualidade de um dataset"""
    dataset: str = Field(..., description="Nome do dataset")
    total_records: int = Field(..., ge=0, description="Total de registros")
    valid_records: int = Field(..., ge=0, description="Registros válidos")
    invalid_records: int = Field(..., ge=0, description="Registros inválidos")
    missing_values: Dict[str, int] = Field(..., description="Valores faltantes por campo")
    duplicates: int = Field(..., ge=0, description="Registros duplicados")
    quality_score: float = Field(..., ge=0, le=1, description="Score de qualidade")
    issues: List[str] = Field(..., description="Problemas identificados")
    processed_at: str = Field(..., description="Data do processamento")


class OverallQuality(BaseModel):
    """Qualidade geral dos dados"""
    total_records: int = Field(..., ge=0, description="Total de registros")
    valid_records: int = Field(..., ge=0, description="Registros válidos")
    average_quality_score: float = Field(..., ge=0, le=1, description="Score médio de qualidade")
    data_completeness: float = Field(..., ge=0, le=100, description="Completude dos dados (%)")


class DataQualityResponse(BaseResponse):
    """Resposta do relatório de qualidade"""
    overall_quality: OverallQuality
    by_dataset: List[DatasetQuality]
    generated_at: str = Field(..., description="Timestamp da geração")


# POWER BI MODELS

class PowerBIWomenDashboard(BaseModel):
    """Dados para dashboard do Power BI - Mulheres"""
    women_by_year: Dict[str, int] = Field(..., description="Mulheres por ano")
    women_by_region: Dict[str, int] = Field(..., description="Mulheres por região")
    women_by_race: Dict[str, int] = Field(..., description="Mulheres por raça")
    women_by_cargo: Dict[str, int] = Field(..., description="Mulheres por cargo")
    avg_potential_by_region: Dict[str, float] = Field(..., description="Potencial médio por região")
    high_potential_count: int = Field(..., ge=0, description="Candidatas com alto potencial")
    total_women: int = Field(..., ge=0, description="Total de mulheres")
    last_updated: str = Field(..., description="Última atualização")


class PowerBIDiversityMetrics(BaseModel):
    """Métricas de diversidade para Power BI"""
    diversity_by_year: Dict[str, float] = Field(..., description="Diversidade por ano")
    women_percentage_by_year: Dict[str, float] = Field(..., description="Percentual de mulheres por ano")
    minority_percentage_by_year: Dict[str, float] = Field(..., description="Percentual de minorias por ano")
    diversity_score_distribution: Dict[str, float] = Field(..., description="Distribuição do score de diversidade")
    top_diverse_regions: Dict[str, float] = Field(..., description="Regiões mais diversas")
    generated_at: str = Field(..., description="Timestamp da geração")


# REQUEST MODELS

class CandidateSearchRequest(BaseModel):
    """Modelo para busca de candidatos"""
    year: Optional[int] = Field(None, description="Ano da eleição")
    gender: Optional[Gender] = Field(None, description="Gênero")
    race: Optional[Race] = Field(None, description="Cor/Raça")
    region: Optional[Region] = Field(None, description="Região")
    cargo_category: Optional[CargoCategory] = Field(None, description="Categoria do cargo")
    min_potential_score: Optional[float] = Field(None, ge=0, le=1, description="Score mínimo de potencial")
    limit: int = Field(100, ge=1, le=1000, description="Limite de resultados")
    offset: int = Field(0, ge=0, description="Offset para paginação")


class WomenAnalysisRequest(BaseModel):
    """Modelo para análise de mulheres"""
    year: Optional[int] = Field(None, description="Ano da eleição")
    region: Optional[Region] = Field(None, description="Região")
    cargo_category: Optional[CargoCategory] = Field(None, description="Categoria do cargo")
    min_marketing_potential: Optional[float] = Field(None, ge=0, le=1, description="Potencial mínimo de marketing")


# ERROR MODELS

class ErrorResponse(BaseModel):
    """Modelo para respostas de erro"""
    error: str = Field(..., description="Mensagem de erro")
    detail: Optional[str] = Field(None, description="Detalhes do erro")
    timestamp: str = Field(..., description="Timestamp do erro")
    path: Optional[str] = Field(None, description="Endpoint que gerou o erro")


class ValidationError(BaseModel):
    """Modelo para erros de validação"""
    field: str = Field(..., description="Campo com erro")
    message: str = Field(..., description="Mensagem de erro")
    value: Any = Field(..., description="Valor inválido")


class ValidationErrorResponse(BaseModel):
    """Resposta para erros de validação"""
    error: str = Field(..., description="Tipo do erro")
    validation_errors: List[ValidationError] = Field(..., description="Erros de validação")
    timestamp: str = Field(..., description="Timestamp do erro")


# HEALTH CHECK

class HealthResponse(BaseModel):
    """Resposta do health check"""
    status: str = Field(..., description="Status da aplicação")
    database: Optional[str] = Field(None, description="Status do banco de dados")
    data_available: Optional[bool] = Field(None, description="Dados disponíveis")
    timestamp: str = Field(..., description="Timestamp da verificação")


# METADATA

class APIMetadata(BaseModel):
    """Metadados da API"""
    version: str = Field(..., description="Versão da API")
    description: str = Field(..., description="Descrição da API")
    available_years: List[int] = Field(..., description="Anos disponíveis")
    supported_regions: List[str] = Field(..., description="Regiões suportadas")
    supported_cargo_categories: List[str] = Field(..., description="Categorias de cargo suportadas")
    last_data_update: str = Field(..., description="Última atualização dos dados")


# PAGINATION

class PaginationInfo(BaseModel):
    """Informações de paginação"""
    page: int = Field(..., ge=1, description="Página atual")
    per_page: int = Field(..., ge=1, description="Itens por página")
    total: int = Field(..., ge=0, description="Total de itens")
    total_pages: int = Field(..., ge=0, description="Total de páginas")
    has_next: bool = Field(..., description="Tem próxima página")
    has_prev: bool = Field(..., description="Tem página anterior")


class PaginatedResponse(BaseModel):
    """Resposta paginada genérica"""
    data: List[Any] = Field(..., description="Dados da página")
    pagination: PaginationInfo = Field(..., description="Informações de paginação")
    filters_applied: Dict[str, Any] = Field(..., description="Filtros aplicados")
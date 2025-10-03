"""
API Principal - FastAPI
Endpoints para acesso aos dados e análises
"""
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional, Any
from datetime import datetime
import pandas as pd
from pathlib import Path

from ..config import settings
from .models import (
    CandidateResponse, 
    WomenAnalysisResponse, 
    ElectionStatsResponse,
    DataQualityResponse
)
from .database import get_db, SessionLocal, Candidate
from sqlalchemy.orm import Session
from ..processing.data_processor import DataProcessor


# Inicialização da aplicação
app = FastAPI(
    title="MVP Eleições Analytics",
    description="API para análise de dados eleitorais com foco em candidaturas femininas",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicialização do processador
processor = DataProcessor()


@app.get("/", tags=["Health"])
async def root():
    """Endpoint de saúde da API"""
    return {
        "message": "MVP Eleições Analytics API",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health", tags=["Health"])
async def health_check(db: Session = Depends(get_db)):
    """Verificação de saúde completa"""
    try:
        # Verificar quantidade de dados no banco
        candidate_count = db.query(Candidate).count()
        data_available = candidate_count > 0
        
        return {
            "status": "healthy",
            "database": "connected",
            "data_available": data_available,
            "candidate_count": candidate_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


# ENDPOINTS DE DADOS GERAIS

@app.get("/api/v1/elections/years", tags=["Elections"])
async def get_available_years():
    """Retorna anos de eleições disponíveis"""
    major_years = [int(year) for year in settings.ELECTION_YEARS_MAJOR.split(',')]
    local_years = [int(year) for year in settings.ELECTION_YEARS_LOCAL.split(',')]
    
    return {
        "major_elections": major_years,
        "local_elections": local_years,
        "all_years": sorted(major_years + local_years, reverse=True)
    }


@app.get("/api/v1/candidates", tags=["Candidates"])
async def get_candidates(
    year: Optional[int] = Query(None, description="Ano da eleição"),
    gender: Optional[str] = Query(None, description="Gênero (F/M)"),
    race: Optional[str] = Query(None, description="Cor/Raça"),
    cargo: Optional[str] = Query(None, description="Cargo"),
    state: Optional[str] = Query(None, description="Estado (UF)"),
    limit: int = Query(100, description="Limite de resultados"),
    offset: int = Query(0, description="Offset para paginação"),
    db: Session = Depends(get_db)
):
    """Busca candidatos com filtros"""
    try:
        # Query base
        query = db.query(Candidate)
        
        # Aplicar filtros
        if year:
            query = query.filter(Candidate.election_year == year)
        if gender:
            query = query.filter(Candidate.gender == gender.upper())
        if race:
            query = query.filter(Candidate.race == race.lower())
        if cargo:
            query = query.filter(Candidate.cargo.ilike(f"%{cargo}%"))
        if state:
            query = query.filter(Candidate.state == state.upper())
        
        # Contar total
        total = query.count()
        
        # Aplicar paginação
        candidates = query.offset(offset).limit(limit).all()
        
        # Converter para dicionários
        result = []
        for candidate in candidates:
            result.append({
                "id": candidate.id,
                "name": candidate.name,
                "ballot_name": candidate.ballot_name,
                "cpf": candidate.cpf,
                "gender": candidate.gender,
                "race": candidate.race,
                "education": candidate.education,
                "occupation": candidate.occupation,
                "cargo": candidate.cargo,
                "cargo_category": candidate.cargo_category,
                "state": candidate.state,
                "city": candidate.city,
                "region": candidate.region,
                "election_year": candidate.election_year,
                "is_woman": candidate.is_woman,
                "is_minority_race": candidate.is_minority_race,
                "diversity_score": candidate.diversity_score
            })
        
        return {
            "data": result,
            "total": total,
            "page": offset // limit + 1,
            "per_page": limit,
            "filters_applied": {
                "year": year,
                "gender": gender,
                "race": race,
                "cargo": cargo,
                "state": state
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@app.get("/api/v1/women-analysis", response_model=WomenAnalysisResponse, tags=["Women Analysis"])
async def get_women_analysis(
    year: Optional[int] = Query(None, description="Ano da eleição"),
    region: Optional[str] = Query(None, description="Região"),
    cargo: Optional[str] = Query(None, description="Categoria do cargo")
):
    """Análise específica de candidaturas femininas"""
    try:
        silver_path = Path(settings.SILVER_PATH)
        
        # Carregar dados processados
        if year:
            data_files = list(silver_path.glob(f"candidatos_{year}_processed.parquet"))
        else:
            data_files = list(silver_path.glob("candidatos_*_processed.parquet"))
        
        if not data_files:
            raise HTTPException(status_code=404, detail="Dados não encontrados")
        
        # Processar análise de mulheres
        all_women_data = []
        
        for file_path in data_files:
            df = pd.read_parquet(file_path)
            women_df = df[df['IS_WOMAN'] == True].copy()
            
            # Aplicar filtros
            if region:
                women_df = women_df[women_df['REGIAO'] == region.upper()]
            
            if cargo:
                women_df = women_df[women_df['CARGO_CATEGORY'].str.contains(cargo.upper(), na=False)]
            
            all_women_data.append(women_df)
        
        if not all_women_data:
            raise HTTPException(status_code=404, detail="Nenhuma candidata encontrada")
        
        combined_women_df = pd.concat(all_women_data, ignore_index=True)
        
        # Calcular estatísticas
        stats = {
            "total_women_candidates": len(combined_women_df),
            "by_race": combined_women_df['COR_RACA'].value_counts().to_dict(),
            "by_region": combined_women_df['REGIAO'].value_counts().to_dict(),
            "by_cargo": combined_women_df['CARGO_CATEGORY'].value_counts().to_dict(),
            "avg_marketing_potential": float(combined_women_df['MARKETING_POTENTIAL'].mean()),
            "high_potential_candidates": len(combined_women_df[combined_women_df['MARKETING_POTENTIAL'] > 0.7]),
            "diversity_score_avg": float(combined_women_df['DIVERSITY_SCORE'].mean())
        }
        
        # Top candidatas com maior potencial
        top_candidates = combined_women_df.nlargest(10, 'WOMEN_POTENTIAL_SCORE')[
            ['NM_CANDIDATO', 'SG_UE', 'CARGO_CATEGORY', 'WOMEN_POTENTIAL_SCORE', 'MARKETING_POTENTIAL']
        ].to_dict('records')
        
        # Insights para marketing
        marketing_insights = {
            "regioes_com_maior_potencial": combined_women_df.groupby('REGIAO')['MARKETING_POTENTIAL'].mean().nlargest(3).to_dict(),
            "cargos_com_maior_diversidade": combined_women_df.groupby('CARGO_CATEGORY')['DIVERSITY_SCORE'].mean().nlargest(3).to_dict(),
            "faixas_etarias_predominantes": combined_women_df['FAIXA_ETARIA'].value_counts().head(3).to_dict() if 'FAIXA_ETARIA' in combined_women_df.columns else {}
        }
        
        return {
            "statistics": stats,
            "top_candidates": top_candidates,
            "marketing_insights": marketing_insights,
            "analysis_timestamp": datetime.now().isoformat(),
            "filters_applied": {
                "year": year,
                "region": region,
                "cargo": cargo
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise: {str(e)}")


@app.get("/api/v1/election-stats", response_model=ElectionStatsResponse, tags=["Statistics"])
async def get_election_statistics(year: int = Query(..., description="Ano da eleição")):
    """Estatísticas gerais de uma eleição"""
    try:
        silver_path = Path(settings.SILVER_PATH)
        file_path = silver_path / f"candidatos_{year}_processed.parquet"
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Dados para {year} não encontrados")
        
        df = pd.read_parquet(file_path)
        
        # Estatísticas gerais
        total_candidates = len(df)
        women_candidates = len(df[df['IS_WOMAN'] == True])
        minority_candidates = len(df[df['IS_MINORITY_RACE'] == True])
        
        # Por gênero
        gender_stats = df['GENERO'].value_counts().to_dict()
        
        # Por raça/cor
        race_stats = df['COR_RACA'].value_counts().to_dict()
        
        # Por cargo
        cargo_stats = df['CARGO_CATEGORY'].value_counts().to_dict()
        
        # Por região
        region_stats = df['REGIAO'].value_counts().to_dict()
        
        # Estatísticas financeiras
        financial_stats = {
            "avg_campaign_budget": float(df['VR_DESPESA_MAX_CAMPANHA'].mean()) if 'VR_DESPESA_MAX_CAMPANHA' in df.columns else 0,
            "median_campaign_budget": float(df['VR_DESPESA_MAX_CAMPANHA'].median()) if 'VR_DESPESA_MAX_CAMPANHA' in df.columns else 0,
            "total_declared_wealth": float(df['VR_BEM_CANDIDATO'].sum()) if 'VR_BEM_CANDIDATO' in df.columns else 0
        }
        
        return {
            "year": year,
            "total_candidates": total_candidates,
            "women_percentage": (women_candidates / total_candidates) * 100,
            "minority_percentage": (minority_candidates / total_candidates) * 100,
            "gender_distribution": gender_stats,
            "race_distribution": race_stats,
            "cargo_distribution": cargo_stats,
            "region_distribution": region_stats,
            "financial_statistics": financial_stats,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular estatísticas: {str(e)}")


@app.get("/api/v1/potential-candidates", tags=["Analysis"])
async def get_potential_women_candidates(
    min_score: float = Query(0.7, description="Score mínimo de potencial"),
    region: Optional[str] = Query(None, description="Região"),
    limit: int = Query(50, description="Limite de resultados")
):
    """Identifica mulheres com alto potencial para candidatura"""
    try:
        silver_path = Path(settings.SILVER_PATH)
        data_files = list(silver_path.glob("candidatos_*_processed.parquet"))
        
        if not data_files:
            raise HTTPException(status_code=404, detail="Dados não encontrados")
        
        # Carregar e filtrar dados
        all_potential = []
        
        for file_path in data_files:
            df = pd.read_parquet(file_path)
            
            # Filtrar por score de potencial
            high_potential_df = df[
                (df['WOMEN_POTENTIAL_SCORE'] >= min_score) & 
                (df['IS_WOMAN'] == True)
            ].copy()
            
            # Aplicar filtro de região se especificado
            if region:
                high_potential_df = high_potential_df[high_potential_df['REGIAO'] == region.upper()]
            
            all_potential.append(high_potential_df)
        
        if not all_potential:
            return {"candidates": [], "total": 0}
        
        combined_df = pd.concat(all_potential, ignore_index=True)
        
        # Ordenar por score de potencial
        top_potential = combined_df.nlargest(limit, 'WOMEN_POTENTIAL_SCORE')
        
        # Preparar resposta
        candidates = []
        for _, row in top_potential.iterrows():
            candidate = {
                "name": row['NM_CANDIDATO'],
                "location": row['NM_UE'],
                "region": row['REGIAO'],
                "cargo_category": row['CARGO_CATEGORY'],
                "potential_score": float(row['WOMEN_POTENTIAL_SCORE']),
                "marketing_potential": float(row['MARKETING_POTENTIAL']),
                "diversity_score": float(row['DIVERSITY_SCORE']),
                "race": row['COR_RACA'],
                "age_group": row.get('FAIXA_ETARIA', 'N/A'),
                "education": row.get('DS_GRAU_INSTRUCAO', 'N/A'),
                "last_election_year": row.get('ANO_ELEICAO', 'N/A')
            }
            candidates.append(candidate)
        
        return {
            "candidates": candidates,
            "total": len(candidates),
            "filters": {
                "min_score": min_score,
                "region": region,
                "limit": limit
            },
            "analysis_date": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na busca: {str(e)}")


@app.get("/api/v1/data-quality", response_model=DataQualityResponse, tags=["Data Quality"])
async def get_data_quality():
    """Relatório de qualidade dos dados"""
    try:
        silver_path = Path(settings.SILVER_PATH)
        quality_files = list(silver_path.glob("*_quality_report.json"))
        
        if not quality_files:
            raise HTTPException(status_code=404, detail="Relatórios de qualidade não encontrados")
        
        import json
        reports = []
        
        for file_path in quality_files:
            with open(file_path, 'r') as f:
                report = json.load(f)
                report['dataset'] = file_path.stem.replace('_quality_report', '')
                reports.append(report)
        
        # Calcular qualidade geral
        total_records = sum(r['total_records'] for r in reports)
        valid_records = sum(r['valid_records'] for r in reports)
        avg_quality_score = sum(r['quality_score'] for r in reports) / len(reports)
        
        return {
            "overall_quality": {
                "total_records": total_records,
                "valid_records": valid_records,
                "average_quality_score": avg_quality_score,
                "data_completeness": (valid_records / total_records) * 100 if total_records > 0 else 0
            },
            "by_dataset": reports,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no relatório: {str(e)}")


# ENDPOINTS PARA POWER BI

@app.get("/api/v1/powerbi/women-dashboard", tags=["Power BI"])
async def powerbi_women_dashboard():
    """Dados formatados para dashboard do Power BI - Mulheres"""
    try:
        silver_path = Path(settings.SILVER_PATH)
        data_files = list(silver_path.glob("candidatos_*_processed.parquet"))
        
        if not data_files:
            raise HTTPException(status_code=404, detail="Dados não encontrados")
        
        # Carregar e processar dados para Power BI
        dfs = []
        for file_path in data_files:
            df = pd.read_parquet(file_path)
            women_df = df[df['IS_WOMAN'] == True].copy()
            dfs.append(women_df)
        
        combined_df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
        
        # Formato para Power BI
        powerbi_data = {
            "women_by_year": combined_df.groupby('ANO_ELEICAO').size().to_dict(),
            "women_by_region": combined_df.groupby('REGIAO').size().to_dict(),
            "women_by_race": combined_df.groupby('COR_RACA').size().to_dict(),
            "women_by_cargo": combined_df.groupby('CARGO_CATEGORY').size().to_dict(),
            "avg_potential_by_region": combined_df.groupby('REGIAO')['WOMEN_POTENTIAL_SCORE'].mean().to_dict(),
            "high_potential_count": len(combined_df[combined_df['WOMEN_POTENTIAL_SCORE'] > 0.7]),
            "total_women": len(combined_df),
            "last_updated": datetime.now().isoformat()
        }
        
        return powerbi_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no dashboard: {str(e)}")


@app.get("/api/v1/powerbi/diversity-metrics", tags=["Power BI"])
async def powerbi_diversity_metrics():
    """Métricas de diversidade para Power BI"""
    try:
        silver_path = Path(settings.SILVER_PATH)
        data_files = list(silver_path.glob("candidatos_*_processed.parquet"))
        
        all_data = []
        for file_path in data_files:
            df = pd.read_parquet(file_path)
            all_data.append(df)
        
        combined_df = pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()
        
        # Métricas de diversidade
        metrics = {
            "diversity_by_year": combined_df.groupby('ANO_ELEICAO')['DIVERSITY_SCORE'].mean().to_dict(),
            "women_percentage_by_year": combined_df.groupby('ANO_ELEICAO')['IS_WOMAN'].mean().multiply(100).to_dict(),
            "minority_percentage_by_year": combined_df.groupby('ANO_ELEICAO')['IS_MINORITY_RACE'].mean().multiply(100).to_dict(),
            "diversity_score_distribution": combined_df['DIVERSITY_SCORE'].describe().to_dict(),
            "top_diverse_regions": combined_df.groupby('REGIAO')['DIVERSITY_SCORE'].mean().nlargest(5).to_dict(),
            "generated_at": datetime.now().isoformat()
        }
        
        return metrics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro nas métricas: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
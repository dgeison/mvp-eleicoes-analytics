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

# Funções auxiliares
def get_age_category(age: int) -> str:
    """Categoriza idade em faixas etárias"""
    if age < 25:
        return "18-24"
    elif age < 35:
        return "25-34"
    elif age < 45:
        return "35-44"
    elif age < 55:
        return "45-54"
    elif age < 65:
        return "55-64"
    else:
        return "65+"

def calculate_marketing_potential(candidate) -> float:
    """Calcula potencial de marketing baseado em fatores diversos"""
    score = 0.5  # Base score
    
    # Bonus por diversidade
    if candidate.diversity_score:
        score += candidate.diversity_score * 0.3
    
    # Bonus por minoria racial
    if candidate.is_minority_race:
        score += 0.2
    
    # Bonus por ser mulher
    if candidate.gender == 'F':
        score += 0.1
    
    return min(1.0, max(0.0, score))

def group_by_field(candidates, field_name: str) -> dict:
    """Agrupa candidatos por um campo específico"""
    groups = {}
    for candidate in candidates:
        value = getattr(candidate, field_name, None) or "Não informado"
        groups[value] = groups.get(value, 0) + 1
    return groups
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


@app.get("/api/v1/women-analysis", tags=["Women Analysis"])
async def get_women_analysis(
    year: Optional[int] = Query(None, description="Ano da eleição"),
    region: Optional[str] = Query(None, description="Região"),
    cargo: Optional[str] = Query(None, description="Categoria do cargo"),
    db: Session = Depends(get_db)
):
    """Análise específica de candidaturas femininas"""
    try:
        # Query base - apenas mulheres
        query = db.query(Candidate).filter(Candidate.gender == 'F')
        
        # Aplicar filtros
        if year:
            query = query.filter(Candidate.election_year == year)
        if region:
            query = query.filter(Candidate.region == region.upper())
        if cargo:
            query = query.filter(Candidate.cargo.ilike(f"%{cargo}%"))
            
        women_candidates = query.all()
        
        if not women_candidates:
            return {
                "message": "Nenhuma candidata encontrada com os filtros especificados",
                "total_women_candidates": 0
            }
        
        # Calcular estatísticas
        races = {}
        states = {}
        cargos = {}
        total_diversity = 0
        
        for candidate in women_candidates:
            # Contagem por raça
            race = candidate.race or "não informado"
            races[race] = races.get(race, 0) + 1
            
            # Contagem por estado
            state = candidate.state or "não informado"
            states[state] = states.get(state, 0) + 1
            
            # Contagem por cargo
            cargo_name = candidate.cargo or "não informado"
            cargos[cargo_name] = cargos.get(cargo_name, 0) + 1
            
            # Somar scores de diversidade
            total_diversity += candidate.diversity_score or 0
        
        # Candidatas com maior potencial (top 5)
        top_candidates = sorted(
            women_candidates, 
            key=lambda x: x.diversity_score or 0, 
            reverse=True
        )[:5]
        
        top_list = [
            {
                "name": c.name,
                "state": c.state,
                "cargo": c.cargo,
                "race": c.race,
                "diversity_score": c.diversity_score or 0
            }
            for c in top_candidates
        ]
        
        return {
            "total_women_candidates": len(women_candidates),
            "statistics": {
                "by_race": races,
                "by_state": states,
                "by_cargo": cargos,
                "avg_diversity_score": total_diversity / len(women_candidates) if women_candidates else 0,
                "minority_percentage": sum(1 for c in women_candidates if c.is_minority_race) / len(women_candidates) * 100
            },
            "top_candidates": top_list,
            "insights": {
                "most_common_race": max(races.items(), key=lambda x: x[1])[0] if races else "N/A",
                "most_active_state": max(states.items(), key=lambda x: x[1])[0] if states else "N/A",
                "most_disputed_cargo": max(cargos.items(), key=lambda x: x[1])[0] if cargos else "N/A"
            },
            "filters_applied": {
                "year": year,
                "region": region,
                "cargo": cargo
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise: {str(e)}")


@app.get("/api/v1/potential-candidates", tags=["Women Analysis"])
async def get_potential_candidates(
    limit: int = Query(10, description="Número de candidatas a retornar"),
    min_score: float = Query(0.5, description="Score mínimo de diversidade"),
    cargo: Optional[str] = Query(None, description="Filtrar por cargo"),
    state: Optional[str] = Query(None, description="Estado (sigla)"),
    db: Session = Depends(get_db)
):
    """Candidatas com maior potencial eleitoral"""
    try:
        # Query base - apenas mulheres
        query = db.query(Candidate).filter(Candidate.gender == 'F')
        
        # Aplicar filtros
        if min_score:
            query = query.filter(Candidate.diversity_score >= min_score)
        if cargo:
            query = query.filter(Candidate.cargo.ilike(f"%{cargo}%"))
        if state:
            query = query.filter(Candidate.state == state.upper())
        
        # Ordenar por score de diversidade (decrescente) e limitar
        candidates = query.order_by(Candidate.diversity_score.desc()).limit(limit).all()
        
        if not candidates:
            return {
                "message": "Nenhuma candidata encontrada com os critérios especificados",
                "total_found": 0,
                "criteria": {
                    "min_score": min_score,
                    "cargo": cargo,
                    "state": state
                }
            }
        
        # Formatar dados das candidatas
        potential_candidates = []
        for candidate in candidates:
            potential_candidates.append({
                "id": candidate.id,
                "name": candidate.name,
                "state": candidate.state,
                "cargo": candidate.cargo,
                "race": candidate.race,
                "age": "N/A",  # Campo não disponível
                "diversity_score": candidate.diversity_score or 0,
                "is_minority": candidate.is_minority_race,
                "election_year": candidate.election_year,
                "region": candidate.region,
                "potential_rating": "Alto" if (candidate.diversity_score or 0) > 0.8 else "Médio" if (candidate.diversity_score or 0) > 0.6 else "Regular"
            })
        
        # Estatísticas do grupo
        avg_score = sum(c.diversity_score or 0 for c in candidates) / len(candidates)
        minority_count = sum(1 for c in candidates if c.is_minority_race)
        
        return {
            "total_found": len(candidates),
            "candidates": potential_candidates,
            "group_statistics": {
                "average_diversity_score": round(avg_score, 3),
                "minority_candidates": minority_count,
                "minority_percentage": round((minority_count / len(candidates)) * 100, 1),
                "age_range": "Dados de idade não disponíveis no modelo atual"
            },
            "filters_applied": {
                "limit": limit,
                "min_score": min_score,
                "cargo": cargo,
                "state": state
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na busca: {str(e)}")


@app.get("/api/v1/data-quality", tags=["Analytics"])
async def get_data_quality(db: Session = Depends(get_db)):
    """Relatório de qualidade dos dados"""
    try:
        # Buscar todos os candidatos
        candidates = db.query(Candidate).all()
        
        if not candidates:
            return {
                "message": "Nenhum candidato encontrado no banco de dados",
                "total_records": 0
            }
        
        total_candidates = len(candidates)
        
        # Verificar campos obrigatórios
        missing_data = {
            "name": sum(1 for c in candidates if not c.name or c.name.strip() == ""),
            "gender": sum(1 for c in candidates if not c.gender),
            "state": sum(1 for c in candidates if not c.state),
            "cargo": sum(1 for c in candidates if not c.cargo),
            "election_year": sum(1 for c in candidates if not c.election_year),
            "race": sum(1 for c in candidates if not c.race)
        }
        
        # Calcular percentuais de completude
        completeness = {}
        for field, missing_count in missing_data.items():
            completeness[field] = round(((total_candidates - missing_count) / total_candidates) * 100, 2)
        
        # Identificar duplicatas potenciais (mesmo nome + estado)
        name_state_pairs = {}
        for candidate in candidates:
            key = f"{candidate.name}_{candidate.state}"
            name_state_pairs[key] = name_state_pairs.get(key, 0) + 1
        
        potential_duplicates = sum(1 for count in name_state_pairs.values() if count > 1)
        
        # Verificar consistência de dados
        invalid_years = sum(1 for c in candidates if c.election_year and (c.election_year < 2000 or c.election_year > 2030))
        
        # Score geral de qualidade (0-100)
        avg_completeness = sum(completeness.values()) / len(completeness)
        consistency_score = 100 - (invalid_years / total_candidates * 100)
        uniqueness_score = 100 - (potential_duplicates / total_candidates * 100)
        
        overall_quality = round((avg_completeness + consistency_score + uniqueness_score) / 3, 1)
        
        return {
            "summary": {
                "total_records": total_candidates,
                "overall_quality_score": overall_quality,
                "quality_rating": "Excelente" if overall_quality >= 90 else "Boa" if overall_quality >= 75 else "Regular" if overall_quality >= 60 else "Ruim"
            },
            "completeness": {
                "fields": completeness,
                "average_completeness": round(avg_completeness, 1)
            },
            "consistency": {
                "invalid_years": invalid_years,
                "consistency_score": round(consistency_score, 1)
            },
            "uniqueness": {
                "potential_duplicates": potential_duplicates,
                "uniqueness_score": round(uniqueness_score, 1)
            },
            "recommendations": [
                f"Preencher dados faltantes em {min(missing_data, key=missing_data.get)}" if missing_data else "Dados completos",
                "Verificar duplicatas potenciais" if potential_duplicates > 0 else "Sem duplicatas detectadas",
                "Verificar anos eleitorais" if invalid_years > 0 else "Anos consistentes"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise de qualidade: {str(e)}")


# Power BI Endpoints
@app.get("/api/v1/powerbi/women-dashboard", tags=["Power BI"])
async def get_powerbi_women_dashboard(db: Session = Depends(get_db)):
    """Dados formatados para dashboard de mulheres no Power BI"""
    try:
        # Buscar apenas candidatas mulheres
        women_candidates = db.query(Candidate).filter(Candidate.gender == 'F').all()
        
        if not women_candidates:
            return {
                "message": "Nenhuma candidata encontrada",
                "total_women": 0,
                "data": []
            }
        
        # Formatar dados para Power BI
        dashboard_data = []
        for candidate in women_candidates:
            dashboard_data.append({
                "ID": candidate.id,
                "Nome": candidate.name,
                "Estado": candidate.state,
                "Regiao": candidate.region,
                "Cargo": candidate.cargo,
                "Raca": candidate.race or "Não informado",
                "Idade": "N/A",  # Campo não disponível no modelo atual
                "Ano_Eleicao": candidate.election_year,
                "Score_Diversidade": candidate.diversity_score or 0,
                "Minoria_Racial": candidate.is_minority_race or False,
                "Categoria_Idade": "N/A",  # Campo idade não disponível
                "Potencial_Marketing": calculate_marketing_potential(candidate),
                "Data_Processamento": datetime.now().isoformat()
            })
        
        # Estatísticas de resumo para o dashboard
        summary_stats = {
            "total_candidatas": len(women_candidates),
            "por_regiao": group_by_field(women_candidates, "region"),
            "por_raca": group_by_field(women_candidates, "race"),
            "por_cargo": group_by_field(women_candidates, "cargo"),
            "score_medio": sum(c.diversity_score or 0 for c in women_candidates) / len(women_candidates),
            "percentual_minoria": sum(1 for c in women_candidates if c.is_minority_race) / len(women_candidates) * 100
        }
        
        return {
            "metadata": {
                "total_records": len(dashboard_data),
                "last_updated": datetime.now().isoformat(),
                "data_source": "MVP Eleições 2026"
            },
            "summary": summary_stats,
            "data": dashboard_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no dashboard: {str(e)}")


@app.get("/api/v1/powerbi/diversity-metrics", tags=["Power BI"])
async def get_powerbi_diversity_metrics(db: Session = Depends(get_db)):
    """Métricas de diversidade formatadas para Power BI"""
    try:
        # Buscar todos os candidatos
        all_candidates = db.query(Candidate).all()
        
        if not all_candidates:
            return {
                "message": "Nenhum candidato encontrado",
                "data": []
            }
        
        # Métricas por estado
        state_metrics = {}
        for candidate in all_candidates:
            state = candidate.state or "N/A"
            if state not in state_metrics:
                state_metrics[state] = {
                    "total": 0,
                    "women": 0,
                    "minorities": 0,
                    "diversity_scores": []
                }
            
            state_metrics[state]["total"] += 1
            if candidate.gender == 'F':
                state_metrics[state]["women"] += 1
            if candidate.is_minority_race:
                state_metrics[state]["minorities"] += 1
            if candidate.diversity_score:
                state_metrics[state]["diversity_scores"].append(candidate.diversity_score)
        
        # Formatar dados para Power BI
        diversity_data = []
        for state, metrics in state_metrics.items():
            avg_score = sum(metrics["diversity_scores"]) / len(metrics["diversity_scores"]) if metrics["diversity_scores"] else 0
                
            diversity_data.append({
                "Estado": state,
                "Total_Candidatos": metrics["total"],
                "Total_Mulheres": metrics["women"],
                "Total_Minorias": metrics["minorities"],
                "Percentual_Mulheres": round((metrics["women"] / metrics["total"]) * 100, 2) if metrics["total"] > 0 else 0,
                "Percentual_Minorias": round((metrics["minorities"] / metrics["total"]) * 100, 2) if metrics["total"] > 0 else 0,
                "Score_Diversidade_Medio": round(avg_score, 3),
                "Data_Processamento": datetime.now().isoformat()
            })
        
        return {
            "metadata": {
                "total_records": len(diversity_data),
                "last_updated": datetime.now().isoformat(),
                "data_source": "MVP Eleições 2026"
            },
            "data": diversity_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro nas métricas: {str(e)}")


@app.get("/api/v1/election-stats", tags=["Analytics"])
async def get_election_stats(
    year: Optional[int] = Query(None, description="Ano da eleição"),
    cargo: Optional[str] = Query(None, description="Filtrar por cargo"),
    state: Optional[str] = Query(None, description="Estado (sigla)"),
    db: Session = Depends(get_db)
):
    """Estatísticas eleitorais gerais"""
    try:
        # Query base
        query = db.query(Candidate)
        
        # Aplicar filtros
        if year:
            query = query.filter(Candidate.election_year == year)
        if cargo:
            query = query.filter(Candidate.cargo.ilike(f"%{cargo}%"))
        if state:
            query = query.filter(Candidate.state == state.upper())
            
        candidates = query.all()
        
        if not candidates:
            return {
                "message": "Nenhum candidato encontrado com os filtros especificados",
                "total_candidates": 0
            }
        
        # Estatísticas gerais
        total_candidates = len(candidates)
        women_count = sum(1 for c in candidates if c.gender == 'F')
        men_count = sum(1 for c in candidates if c.gender == 'M')
        
        # Estatísticas por raça
        race_stats = {}
        for candidate in candidates:
            race = candidate.race or "não informado"
            race_stats[race] = race_stats.get(race, 0) + 1
        
        # Estatísticas por idade - vamos simular baseado no ano
        age_groups = {
            "jovens (estimado)": 0,
            "adultos (estimado)": 0,
            "experientes (estimado)": 0
        }
        
        # Simulação básica de distribuição etária
        total_for_age = len(candidates)
        age_groups["jovens (estimado)"] = int(total_for_age * 0.25)  # 25%
        age_groups["adultos (estimado)"] = int(total_for_age * 0.55)  # 55%
        age_groups["experientes (estimado)"] = total_for_age - age_groups["jovens (estimado)"] - age_groups["adultos (estimado)"]
        
        # Top 5 estados com mais candidatos
        state_counts = {}
        for candidate in candidates:
            state_name = candidate.state or "não informado"
            state_counts[state_name] = state_counts.get(state_name, 0) + 1
        
        top_states = sorted(state_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "summary": {
                "total_candidates": total_candidates,
                "women_candidates": women_count,
                "men_candidates": men_count,
                "women_percentage": (women_count / total_candidates * 100) if total_candidates > 0 else 0,
                "average_age": "Dados de idade não disponíveis"
            },
            "demographics": {
                "by_race": race_stats,
                "by_age_group": age_groups,
                "minority_candidates": sum(1 for c in candidates if c.is_minority_race),
                "minority_percentage": sum(1 for c in candidates if c.is_minority_race) / total_candidates * 100 if total_candidates > 0 else 0
            },
            "geographic": {
                "top_states": [{"state": state, "count": count} for state, count in top_states],
                "states_represented": len(state_counts)
            },
            "filters_applied": {
                "year": year,
                "cargo": cargo,
                "state": state
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro nas estatísticas: {str(e)}")


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


@app.post("/api/candidates/bulk_update", tags=["Candidates"])
async def bulk_update_candidates(data: dict):
    """
    Atualização em massa de candidatas com dados do TSE
    
    Body:
        {
            "candidates": [...],
            "source": "TSE",
            "update_mode": "replace"
        }
    """
    try:
        candidates_data = data.get('candidates', [])
        source = data.get('source', 'Unknown')
        update_mode = data.get('update_mode', 'append')
        
        if not candidates_data:
            raise HTTPException(status_code=400, detail="Nenhuma candidata fornecida")
        
        db = SessionLocal()
        
        try:
            # Se modo replace, limpar dados existentes
            if update_mode == 'replace':
                db.query(Candidate).delete()
                db.commit()
            
            # Inserir novas candidatas
            updated_count = 0
            
            for candidate_data in candidates_data:
                # Verificar se candidata já existe (por nome)
                existing = db.query(Candidate).filter(
                    Candidate.name == candidate_data.get('name')
                ).first()
                
                if existing and update_mode != 'replace':
                    # Atualizar candidata existente
                    for key, value in candidate_data.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                else:
                    # Criar nova candidata
                    new_candidate = Candidate(
                        name=candidate_data.get('name', ''),
                        age=candidate_data.get('age', 0),
                        education=candidate_data.get('education', ''),
                        political_experience=candidate_data.get('political_experience', ''),
                        region=candidate_data.get('region', ''),
                        diversity_score=candidate_data.get('diversity_score', 0.0),
                        social_media_engagement=candidate_data.get('social_media_engagement', 0),
                        policy_areas=",".join(candidate_data.get('policy_areas', [])),
                        is_woman=True,  # Assumindo que só inserimos mulheres
                        is_minority_race=candidate_data.get('raw_data', {}).get('race', '') in ['PRETA', 'PARDA', 'INDÍGENA']
                    )
                    db.add(new_candidate)
                
                updated_count += 1
            
            db.commit()
            
            return {
                "status": "success",
                "updated_count": updated_count,
                "source": source,
                "update_mode": update_mode,
                "timestamp": datetime.now().isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na atualização: {str(e)}")


# ========== ENDPOINTS OTIMIZADOS PARA PERFORMANCE ==========

@app.get("/analytics/summary")
async def get_summary_stats(db = Depends(get_db)):
    """Endpoint otimizado para estatísticas resumidas"""
    try:
        from sqlalchemy import func, distinct
        
        # Consultas agregadas otimizadas
        total_candidates = db.query(func.count(Candidate.id)).scalar()
        
        states_covered = db.query(func.count(distinct(Candidate.state))).scalar()
        
        avg_diversity_score = db.query(func.avg(Candidate.diversity_score)).scalar() or 0
        
        # Contagem por fonte
        tse_count = db.query(func.count(Candidate.id)).filter(Candidate.source == 'TSE').scalar()
        
        # Taxa de diversidade
        minority_count = db.query(func.count(Candidate.id)).filter(Candidate.is_minority_race == True).scalar()
        diversity_rate = (minority_count / total_candidates * 100) if total_candidates > 0 else 0
        
        return {
            "total_candidates": total_candidates,
            "states_covered": states_covered,
            "avg_diversity_score": round(avg_diversity_score, 3),
            "diversity_rate": round(diversity_rate, 1),
            "tse_candidates": tse_count,
            "manual_candidates": total_candidates - tse_count,
            "last_updated": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar estatísticas: {str(e)}")


@app.get("/analytics/regional")
async def get_regional_stats(db = Depends(get_db)):
    """Endpoint otimizado para dados regionais agregados"""
    try:
        from sqlalchemy import func
        
        # Query agregada por região
        regional_data = db.query(
            Candidate.region,
            func.count(Candidate.id).label('total_candidates'),
            func.avg(Candidate.diversity_score).label('avg_diversity_score'),
            func.count(func.distinct(Candidate.state)).label('states_in_region')
        ).group_by(Candidate.region).all()
        
        result = []
        for row in regional_data:
            result.append({
                "region": row.region,
                "total_candidates": row.total_candidates,
                "avg_diversity_score": round(row.avg_diversity_score or 0, 3),
                "states_in_region": row.states_in_region
            })
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar dados regionais: {str(e)}")


@app.get("/candidates/paginated")
async def get_candidates_paginated(
    limit: int = Query(100, ge=1, le=2000),
    skip: int = Query(0, ge=0),
    region: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None, ge=0, le=1),
    cargo: Optional[str] = Query(None),
    db = Depends(get_db)
):
    """Endpoint paginado otimizado com filtros"""
    try:
        # Base query
        query = db.query(Candidate)
        
        # Aplicar filtros
        if region and region != "Todas":
            query = query.filter(Candidate.region == region)
        
        if source and source != "Todas":
            query = query.filter(Candidate.source == source)
        
        if min_score is not None:
            query = query.filter(Candidate.diversity_score >= min_score)
        
        if cargo and cargo != "Todos":
            query = query.filter(Candidate.cargo == cargo)
        
        # Total count (otimizado)
        total_count = query.count()
        
        # Fetch com limit/offset
        candidates = query.offset(skip).limit(limit).all()
        
        # Converter para dicionário (otimizado)
        candidates_data = []
        for candidate in candidates:
            candidates_data.append({
                "id": candidate.id,
                "name": candidate.name,
                "ballot_name": candidate.ballot_name,
                "state": candidate.state,
                "region": candidate.region,
                "cargo": candidate.cargo,
                "education": candidate.education,
                "diversity_score": candidate.diversity_score,
                "source": candidate.source,
                "is_minority_race": candidate.is_minority_race
            })
        
        return {
            "candidates": candidates_data,
            "total_count": total_count,
            "page_size": limit,
            "current_skip": skip,
            "has_next": (skip + limit) < total_count
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na consulta paginada: {str(e)}")


@app.get("/health")
async def health_check(db = Depends(get_db)):
    """Health check otimizado"""
    try:
        from sqlalchemy import func
        
        # Test database connection
        db.execute("SELECT 1")
        
        # Basic stats
        total_candidates = db.query(func.count(Candidate.id)).scalar()
        
        return {
            "status": "healthy",
            "database": "connected", 
            "total_candidates": total_candidates,
            "timestamp": datetime.now().isoformat(),
            "version": "1.2.0-optimized"
        }
    
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
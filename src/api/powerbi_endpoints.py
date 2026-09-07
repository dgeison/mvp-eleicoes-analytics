"""
Endpoints específicos para integração com PowerBI
"""
from fastapi import APIRouter, Query, HTTPException, Response
from typing import Optional, List
import pandas as pd
from sqlalchemy.orm import Session
from ..database.connection import get_db
from ..models.candidate import Candidate
import json
import csv
import io

router = APIRouter(prefix="/powerbi", tags=["PowerBI Integration"])

@router.get("/candidates/csv")
async def export_candidates_csv(
    db: Session = next(get_db()),
    limit: Optional[int] = Query(None, description="Limite de registros"),
    states: Optional[str] = Query(None, description="Estados separados por vírgula"),
    regions: Optional[str] = Query(None, description="Regiões separadas por vírgula"),
    cargos: Optional[str] = Query(None, description="Cargos separados por vírgula")
):
    """
    Export de candidatas em formato CSV para PowerBI
    """
    try:
        query = db.query(Candidate)
        
        # Aplicar filtros se fornecidos
        if states:
            state_list = [s.strip() for s in states.split(',')]
            query = query.filter(Candidate.state.in_(state_list))
            
        if regions:
            region_list = [r.strip() for r in regions.split(',')]
            query = query.filter(Candidate.region.in_(region_list))
            
        if cargos:
            cargo_list = [c.strip() for c in cargos.split(',')]
            query = query.filter(Candidate.cargo.in_(cargo_list))
        
        if limit:
            query = query.limit(limit)
            
        candidates = query.all()
        
        # Converter para DataFrame
        data = []
        for candidate in candidates:
            data.append({
                'id': candidate.id,
                'nome': candidate.name,
                'nome_urna': candidate.ballot_name,
                'estado': candidate.state,
                'regiao': candidate.region,
                'cargo': candidate.cargo,
                'educacao': candidate.education,
                'raca': candidate.race,
                'score_diversidade': candidate.diversity_score,
                'votos_recebidos': candidate.votes_received,
                'percentual_votos': candidate.vote_percentage,
                'eh_minoria_racial': candidate.is_minority_race,
                'fonte': candidate.source
            })
        
        df = pd.DataFrame(data)
        
        # Criar CSV em memória
        output = io.StringIO()
        df.to_csv(output, index=False, encoding='utf-8')
        csv_content = output.getvalue()
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=candidatas_eleicoes_2026.csv"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar CSV: {str(e)}")

@router.get("/candidates/excel")
async def export_candidates_excel(
    db: Session = next(get_db()),
    limit: Optional[int] = Query(None, description="Limite de registros"),
    states: Optional[str] = Query(None, description="Estados separados por vírgula"),
    regions: Optional[str] = Query(None, description="Regiões separadas por vírgula"),
    cargos: Optional[str] = Query(None, description="Cargos separados por vírgula")
):
    """
    Export de candidatas em formato Excel para PowerBI
    """
    try:
        query = db.query(Candidate)
        
        # Aplicar filtros
        if states:
            state_list = [s.strip() for s in states.split(',')]
            query = query.filter(Candidate.state.in_(state_list))
            
        if regions:
            region_list = [r.strip() for r in regions.split(',')]
            query = query.filter(Candidate.region.in_(region_list))
            
        if cargos:
            cargo_list = [c.strip() for c in cargos.split(',')]
            query = query.filter(Candidate.cargo.in_(cargo_list))
        
        if limit:
            query = query.limit(limit)
            
        candidates = query.all()
        
        # Converter para DataFrame
        data = []
        for candidate in candidates:
            data.append({
                'ID': candidate.id,
                'Nome Completo': candidate.name,
                'Nome na Urna': candidate.ballot_name,
                'Estado': candidate.state,
                'Região': candidate.region,
                'Cargo': candidate.cargo,
                'Educação': candidate.education,
                'Raça/Cor': candidate.race,
                'Score Diversidade': candidate.diversity_score,
                'Votos Recebidos': candidate.votes_received,
                'Percentual Votos': candidate.vote_percentage,
                'É Minoria Racial': candidate.is_minority_race,
                'Fonte dos Dados': candidate.source
            })
        
        df = pd.DataFrame(data)
        
        # Criar Excel em memória
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Candidatas', index=False)
            
            # Adicionar formatação
            workbook = writer.book
            worksheet = writer.sheets['Candidatas']
            
            # Formato para números
            num_format = workbook.add_format({'num_format': '#,##0'})
            pct_format = workbook.add_format({'num_format': '0.00%'})
            
            # Aplicar formatos
            worksheet.set_column('I:I', 15, num_format)  # Votos
            worksheet.set_column('J:J', 15, pct_format)  # Percentual
            
        excel_content = output.getvalue()
        
        return Response(
            content=excel_content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=candidatas_eleicoes_2026.xlsx"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar Excel: {str(e)}")

@router.get("/candidates/powerbi-json")
async def get_candidates_powerbi_format(
    db: Session = next(get_db()),
    limit: Optional[int] = Query(10000, description="Limite de registros"),
    skip: Optional[int] = Query(0, description="Registros para pular")
):
    """
    Dados formatados especificamente para PowerBI Web API
    """
    try:
        query = db.query(Candidate).offset(skip).limit(limit)
        candidates = query.all()
        
        # Formato otimizado para PowerBI
        powerbi_data = {
            "value": [
                {
                    "ID": candidate.id,
                    "Nome": candidate.name,
                    "NomeUrna": candidate.ballot_name,
                    "Estado": candidate.state,
                    "Regiao": candidate.region,
                    "Cargo": candidate.cargo,
                    "Educacao": candidate.education,
                    "Raca": candidate.race,
                    "ScoreDiversidade": float(candidate.diversity_score) if candidate.diversity_score else 0,
                    "VotosRecebidos": int(candidate.votes_received) if candidate.votes_received else 0,
                    "PercentualVotos": float(candidate.vote_percentage) if candidate.vote_percentage else 0,
                    "EhMinoriaRacial": bool(candidate.is_minority_race),
                    "Fonte": candidate.source
                }
                for candidate in candidates
            ],
            "@odata.count": db.query(Candidate).count()
        }
        
        return powerbi_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar dados PowerBI: {str(e)}")

@router.get("/metadata")
async def get_powerbi_metadata():
    """
    Metadados das colunas para PowerBI
    """
    return {
        "tables": [
            {
                "name": "Candidatas",
                "columns": [
                    {"name": "ID", "type": "Int64", "description": "ID único da candidata"},
                    {"name": "Nome", "type": "String", "description": "Nome completo"},
                    {"name": "NomeUrna", "type": "String", "description": "Nome na urna"},
                    {"name": "Estado", "type": "String", "description": "Estado (UF)"},
                    {"name": "Regiao", "type": "String", "description": "Região do Brasil"},
                    {"name": "Cargo", "type": "String", "description": "Cargo disputado"},
                    {"name": "Educacao", "type": "String", "description": "Nível de escolaridade"},
                    {"name": "Raca", "type": "String", "description": "Raça/Cor autodeclarada"},
                    {"name": "ScoreDiversidade", "type": "Double", "description": "Score de diversidade (0-1)"},
                    {"name": "VotosRecebidos", "type": "Int64", "description": "Total de votos recebidos"},
                    {"name": "PercentualVotos", "type": "Double", "description": "Percentual de votos"},
                    {"name": "EhMinoriaRacial", "type": "Boolean", "description": "Se é minoria racial"},
                    {"name": "Fonte", "type": "String", "description": "Fonte dos dados"}
                ]
            }
        ],
        "measures": [
            {
                "name": "TotalCandidatas",
                "expression": "COUNT(Candidatas[ID])",
                "description": "Total de candidatas"
            },
            {
                "name": "TotalVotos",
                "expression": "SUM(Candidatas[VotosRecebidos])",
                "description": "Total de votos"
            },
            {
                "name": "MediaVotos",
                "expression": "AVERAGE(Candidatas[VotosRecebidos])",
                "description": "Média de votos por candidata"
            },
            {
                "name": "PercentualMinorias",
                "expression": "DIVIDE(COUNTROWS(FILTER(Candidatas, Candidatas[EhMinoriaRacial] = TRUE)), COUNTROWS(Candidatas))",
                "description": "Percentual de candidatas de minorias raciais"
            }
        ]
    }

@router.get("/database-connection-info")
async def get_database_connection_info():
    """
    Informações para conexão direta do PowerBI ao PostgreSQL
    """
    return {
        "connection_type": "PostgreSQL",
        "server": "localhost",
        "port": 5432,
        "database": "eleicoes_analytics",
        "table": "candidates",
        "connection_string_template": "Host=localhost;Port=5432;Database=eleicoes_analytics;Username=your_user;Password=your_password",
        "sql_query_example": """
        SELECT 
            id as "ID",
            name as "Nome",
            ballot_name as "Nome na Urna",
            state as "Estado",
            region as "Região",
            cargo as "Cargo",
            education as "Educação",
            race as "Raça",
            diversity_score as "Score Diversidade",
            votes_received as "Votos Recebidos",
            vote_percentage as "Percentual Votos",
            is_minority_race as "É Minoria Racial",
            source as "Fonte"
        FROM candidates
        WHERE state IS NOT NULL
        ORDER BY votes_received DESC
        """,
        "notes": [
            "Use a conexão direta para melhor performance",
            "Configure refresh automático no PowerBI Service",
            "Considere criar views no PostgreSQL para queries otimizadas"
        ]
    }
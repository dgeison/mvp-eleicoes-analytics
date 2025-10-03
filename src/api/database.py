"""
Configuração do banco de dados
"""
from sqlalchemy import create_engine, MetaData, Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import pandas as pd
from typing import Generator

from ..config import settings

# Configuração do SQLAlchemy
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
metadata = MetaData()


# Models de banco de dados
class Candidate(Base):
    """Tabela de candidatos"""
    __tablename__ = "candidates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    ballot_name = Column(String(255), index=True)
    cpf = Column(String(11), unique=True, index=True)
    gender = Column(String(1), index=True)
    race = Column(String(50), index=True)
    education = Column(String(100))
    occupation = Column(String(100))
    cargo = Column(String(100), index=True)
    cargo_category = Column(String(50), index=True)
    state = Column(String(2), index=True)
    city = Column(String(255), index=True)
    region = Column(String(20), index=True)
    election_year = Column(Integer, index=True)
    
    # Campos calculados
    is_woman = Column(Boolean, default=False, index=True)
    is_minority_race = Column(Boolean, default=False, index=True)
    diversity_score = Column(Float, default=0.0)
    women_potential_score = Column(Float, default=0.0)
    marketing_potential = Column(Float, default=0.0)
    
    # Campos financeiros
    campaign_budget = Column(Float)
    declared_wealth = Column(Float)
    
    # Campos de votação
    votes_received = Column(Integer)
    vote_percentage = Column(Float)
    
    # Metadados
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class Election(Base):
    """Tabela de eleições"""
    __tablename__ = "elections"
    
    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False, unique=True, index=True)
    type = Column(String(50), nullable=False)  # 'MUNICIPAL', 'ESTADUAL', 'FEDERAL'
    description = Column(Text)
    total_candidates = Column(Integer)
    women_candidates = Column(Integer)
    minority_candidates = Column(Integer)
    created_at = Column(DateTime)


class DataQuality(Base):
    """Tabela de qualidade dos dados"""
    __tablename__ = "data_quality"
    
    id = Column(Integer, primary_key=True, index=True)
    dataset_name = Column(String(100), nullable=False, index=True)
    election_year = Column(Integer, index=True)
    total_records = Column(Integer)
    valid_records = Column(Integer)
    invalid_records = Column(Integer)
    duplicates = Column(Integer)
    quality_score = Column(Float)
    issues = Column(Text)  # JSON string
    processed_at = Column(DateTime)


class SocialMediaProfile(Base):
    """Tabela de perfis de redes sociais"""
    __tablename__ = "social_media_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, index=True)  # FK to candidates
    platform = Column(String(50), nullable=False, index=True)
    profile_url = Column(String(500))
    username = Column(String(100))
    followers_count = Column(Integer)
    posts_count = Column(Integer)
    engagement_rate = Column(Float)
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class WomenAnalysis(Base):
    """Tabela de análises específicas de mulheres"""
    __tablename__ = "women_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    election_year = Column(Integer, nullable=False, index=True)
    region = Column(String(20), index=True)
    total_women = Column(Integer)
    high_potential_women = Column(Integer)
    avg_marketing_potential = Column(Float)
    avg_diversity_score = Column(Float)
    top_performing_region = Column(String(20))
    analysis_date = Column(DateTime)


# Dependency para obter sessão do banco
def get_db() -> Generator[Session, None, None]:
    """Dependency que fornece uma sessão do banco de dados"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session():
    """Context manager para sessão do banco"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Funções utilitárias
def create_tables():
    """Cria todas as tabelas no banco de dados"""
    Base.metadata.create_all(bind=engine)
    print("✅ Tabelas criadas com sucesso!")


def drop_tables():
    """Remove todas as tabelas do banco de dados"""
    Base.metadata.drop_all(bind=engine)
    print("🗑️ Tabelas removidas!")


def reset_database():
    """Reseta o banco de dados (remove e recria todas as tabelas)"""
    drop_tables()
    create_tables()


class DatabaseManager:
    """Gerenciador de operações do banco de dados"""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def bulk_insert_candidates(self, df: pd.DataFrame) -> int:
        """Insere candidatos em lote"""
        with get_db_session() as db:
            # Converter DataFrame para dicionários
            records = df.to_dict('records')
            
            # Preparar dados para inserção
            candidates_data = []
            for record in records:
                candidate_data = {
                    'name': record.get('NM_CANDIDATO'),
                    'ballot_name': record.get('NM_URNA_CANDIDATO'),
                    'gender': record.get('GENERO'),
                    'race': record.get('COR_RACA'),
                    'education': record.get('DS_GRAU_INSTRUCAO'),
                    'cargo': record.get('DS_CARGO'),
                    'cargo_category': record.get('CARGO_CATEGORY'),
                    'state': record.get('SG_UF'),
                    'city': record.get('NM_UE'),
                    'region': record.get('REGIAO'),
                    'election_year': record.get('ANO_ELEICAO'),
                    'is_woman': record.get('IS_WOMAN', False),
                    'is_minority_race': record.get('IS_MINORITY_RACE', False),
                    'diversity_score': record.get('DIVERSITY_SCORE', 0.0),
                    'women_potential_score': record.get('WOMEN_POTENTIAL_SCORE', 0.0),
                    'marketing_potential': record.get('MARKETING_POTENTIAL', 0.0),
                    'campaign_budget': record.get('VR_DESPESA_MAX_CAMPANHA'),
                    'votes_received': record.get('QT_VOTOS_NOMINAIS'),
                    'vote_percentage': record.get('PERCENTUAL_VOTOS')
                }
                candidates_data.append(candidate_data)
            
            # Inserir em lote
            db.bulk_insert_mappings(Candidate, candidates_data)
            db.commit()
            
            return len(candidates_data)
    
    def get_candidates_by_filters(self, 
                                year: int = None,
                                gender: str = None,
                                region: str = None,
                                cargo_category: str = None,
                                limit: int = 100,
                                offset: int = 0) -> list:
        """Busca candidatos com filtros"""
        with get_db_session() as db:
            query = db.query(Candidate)
            
            if year:
                query = query.filter(Candidate.election_year == year)
            if gender:
                query = query.filter(Candidate.gender == gender)
            if region:
                query = query.filter(Candidate.region == region)
            if cargo_category:
                query = query.filter(Candidate.cargo_category == cargo_category)
            
            return query.offset(offset).limit(limit).all()
    
    def get_women_statistics(self, year: int = None) -> dict:
        """Obtém estatísticas de candidaturas femininas"""
        with get_db_session() as db:
            query = db.query(Candidate).filter(Candidate.is_woman == True)
            
            if year:
                query = query.filter(Candidate.election_year == year)
            
            candidates = query.all()
            
            if not candidates:
                return {}
            
            # Calcular estatísticas
            stats = {
                'total_women': len(candidates),
                'by_region': {},
                'by_race': {},
                'by_cargo': {},
                'avg_potential': sum(c.women_potential_score or 0 for c in candidates) / len(candidates),
                'high_potential_count': sum(1 for c in candidates if (c.women_potential_score or 0) > 0.7)
            }
            
            # Distribuições
            for candidate in candidates:
                # Por região
                region = candidate.region or 'UNKNOWN'
                stats['by_region'][region] = stats['by_region'].get(region, 0) + 1
                
                # Por raça
                race = candidate.race or 'UNKNOWN'
                stats['by_race'][race] = stats['by_race'].get(race, 0) + 1
                
                # Por cargo
                cargo = candidate.cargo_category or 'UNKNOWN'
                stats['by_cargo'][cargo] = stats['by_cargo'].get(cargo, 0) + 1
            
            return stats
    
    def save_quality_report(self, dataset_name: str, year: int, quality_data: dict):
        """Salva relatório de qualidade no banco"""
        with get_db_session() as db:
            quality_record = DataQuality(
                dataset_name=dataset_name,
                election_year=year,
                total_records=quality_data.get('total_records', 0),
                valid_records=quality_data.get('valid_records', 0),
                invalid_records=quality_data.get('invalid_records', 0),
                duplicates=quality_data.get('duplicates', 0),
                quality_score=quality_data.get('quality_score', 0.0),
                issues=str(quality_data.get('issues', [])),
                processed_at=pd.Timestamp.now()
            )
            
            db.add(quality_record)
            db.commit()
    
    def get_election_summary(self, year: int) -> dict:
        """Obtém resumo de uma eleição"""
        with get_db_session() as db:
            candidates = db.query(Candidate).filter(Candidate.election_year == year).all()
            
            if not candidates:
                return {}
            
            total = len(candidates)
            women = sum(1 for c in candidates if c.is_woman)
            minorities = sum(1 for c in candidates if c.is_minority_race)
            
            return {
                'year': year,
                'total_candidates': total,
                'women_count': women,
                'women_percentage': (women / total) * 100 if total > 0 else 0,
                'minority_count': minorities,
                'minority_percentage': (minorities / total) * 100 if total > 0 else 0,
                'avg_diversity_score': sum(c.diversity_score or 0 for c in candidates) / total if total > 0 else 0
            }


# Instância global do gerenciador
db_manager = DatabaseManager()


# Função para inicializar o banco
def init_database():
    """Inicializa o banco de dados"""
    try:
        create_tables()
        print("✅ Banco de dados inicializado com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao inicializar banco de dados: {e}")
        return False


# Função para verificar conexão
def check_database_connection() -> bool:
    """Verifica se a conexão com o banco está funcionando"""
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"❌ Erro de conexão com banco: {e}")
        return False


if __name__ == "__main__":
    # Teste de conexão
    if check_database_connection():
        print("✅ Conexão com banco de dados OK!")
        init_database()
    else:
        print("❌ Falha na conexão com banco de dados!")
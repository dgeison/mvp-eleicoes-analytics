#!/usr/bin/env python3
"""
Script para gerar dados de votação sintéticos baseados no diversity_score
Simula dados realísticos de votação para demonstração
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def conectar_bd():
    """Conectar ao banco PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            port='5432',
            database='eleicoes_analytics',
            user='postgres',
            password='postgres123'
        )
        return conn
    except Exception as e:
        logger.error(f"Erro ao conectar ao BD: {e}")
        return None

def gerar_dados_votacao():
    """Gerar dados de votação sintéticos baseados no diversity_score"""
    conn = conectar_bd()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Buscar candidatas TSE sem dados de votação
        cursor.execute("""
            SELECT id, name, ballot_name, state, cargo, race, education, 
                   diversity_score, source
            FROM candidates 
            WHERE source = 'TSE' 
            AND (votes_received IS NULL OR votes_received = 0)
            ORDER BY diversity_score DESC
        """)
        
        candidatas = cursor.fetchall()
        logger.info(f"Encontradas {len(candidatas)} candidatas para gerar dados de votação")
        
        if not candidatas:
            logger.warning("Nenhuma candidata encontrada sem dados de votação")
            return True
        
        # Configurar seed para reprodutibilidade
        np.random.seed(2022)
        
        total_atualizadas = 0
        total_votos_gerados = 0
        
        # Fatores baseados no cargo (simulando competitividade real)
        fatores_cargo = {
            'DEPUTADO FEDERAL': {'base': 50000, 'variacao': 40000},
            'DEPUTADO ESTADUAL': {'base': 25000, 'variacao': 20000},
            'DEPUTADO DISTRITAL': {'base': 15000, 'variacao': 12000},
            'SENADOR': {'base': 1000000, 'variacao': 500000},
            'GOVERNADOR': {'base': 2000000, 'variacao': 1000000},
            'PRESIDENTE': {'base': 50000000, 'variacao': 20000000},
            'PREFEITO': {'base': 10000, 'variacao': 15000},
            'VEREADOR': {'base': 500, 'variacao': 1000}
        }
        
        for candidata in candidatas:
            # Obter fatores do cargo
            cargo = candidata['cargo'] or 'DEPUTADO ESTADUAL'
            fator = fatores_cargo.get(cargo, fatores_cargo['DEPUTADO ESTADUAL'])
            
            # Calcular votos baseados no diversity_score
            score = candidata['diversity_score'] or 0.5
            
            # Base de votos influenciada pelo score
            base_votos = fator['base'] * (0.3 + score * 1.4)  # Score alto = mais votos
            
            # Adicionar variação aleatória
            variacao = np.random.normal(0, fator['variacao'] * 0.5)
            votos = int(max(0, base_votos + variacao))
            
            # Adicionar fatores adicionais
            # Bonus para minorias raciais (simula políticas de inclusão)
            if candidata['race'] in ['PRETA', 'PARDA', 'INDÍGENA', 'AMARELA']:
                votos = int(votos * np.random.uniform(1.1, 1.3))
            
            # Bonus para educação superior
            if candidata['education'] and ('SUPERIOR' in candidata['education'] or 'PÓS' in candidata['education']):
                votos = int(votos * np.random.uniform(1.05, 1.2))
            
            # Variação por estado (alguns estados são mais populosos)
            estados_grandes = ['SP', 'RJ', 'MG', 'BA', 'PR', 'RS', 'PE', 'CE', 'PA', 'SC']
            if candidata['state'] in estados_grandes:
                votos = int(votos * np.random.uniform(1.2, 1.5))
            
            # Garantir valores mínimos realísticos
            if cargo == 'VEREADOR':
                votos = max(votos, np.random.randint(50, 500))
            elif cargo in ['DEPUTADO ESTADUAL', 'DEPUTADO FEDERAL']:
                votos = max(votos, np.random.randint(1000, 5000))
            else:
                votos = max(votos, np.random.randint(100, 1000))
            
            total_votos_gerados += votos
            
            # Atualizar no banco
            cursor.execute("""
                UPDATE candidates 
                SET votes_received = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (votos, candidata['id']))
            
            total_atualizadas += 1
            
            if total_atualizadas % 1000 == 0:
                logger.info(f"Processadas {total_atualizadas} candidatas...")
        
        # Calcular percentuais baseados no total de votos
        cursor.execute("""
            UPDATE candidates 
            SET vote_percentage = (
                votes_received::float / (
                    SELECT SUM(votes_received) 
                    FROM candidates 
                    WHERE source = 'TSE' AND votes_received > 0
                ) * 100
            )
            WHERE source = 'TSE' AND votes_received > 0
        """)
        
        conn.commit()
        
        logger.info(f"✅ Dados de votação gerados com sucesso!")
        logger.info(f"   - Candidatas atualizadas: {total_atualizadas:,}")
        logger.info(f"   - Total de votos gerados: {total_votos_gerados:,}")
        
        # Estatísticas finais
        cursor.execute("""
            SELECT 
                COUNT(*) as total_candidatas,
                COUNT(votes_received) FILTER (WHERE votes_received > 0) as com_votos,
                SUM(votes_received) as total_votos,
                AVG(votes_received) as media_votos,
                MAX(votes_received) as max_votos,
                MIN(votes_received) FILTER (WHERE votes_received > 0) as min_votos
            FROM candidates 
            WHERE source = 'TSE'
        """)
        
        stats = cursor.fetchone()
        logger.info(f"📊 Estatísticas finais:")
        logger.info(f"   - Total de candidatas: {stats['total_candidatas']:,}")
        logger.info(f"   - Com dados de votação: {stats['com_votos']:,}")
        logger.info(f"   - Total de votos: {stats['total_votos']:,}")
        logger.info(f"   - Média de votos: {stats['media_votos']:,.0f}")
        logger.info(f"   - Máximo de votos: {stats['max_votos']:,}")
        logger.info(f"   - Mínimo de votos: {stats['min_votos']:,}")
        
        # Top 10 mais votadas
        cursor.execute("""
            SELECT name, ballot_name, state, cargo, votes_received, vote_percentage
            FROM candidates 
            WHERE source = 'TSE' AND votes_received > 0
            ORDER BY votes_received DESC
            LIMIT 10
        """)
        
        top_10 = cursor.fetchall()
        logger.info(f"\n🏆 Top 10 candidatas mais votadas:")
        for i, candidata in enumerate(top_10, 1):
            logger.info(f"   {i}. {candidata['ballot_name']} ({candidata['state']}) - {candidata['votes_received']:,} votos ({candidata['vote_percentage']:.4f}%)")
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao gerar dados de votação: {e}")
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def verificar_dados_existentes():
    """Verificar se já existem dados de votação"""
    conn = conectar_bd()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(votes_received) FILTER (WHERE votes_received > 0) as com_votos
            FROM candidates 
            WHERE source = 'TSE'
        """)
        
        result = cursor.fetchone()
        
        logger.info(f"Status atual: {result['com_votos']}/{result['total']} candidatas com dados de votação")
        
        return result['com_votos'] > 0
        
    except Exception as e:
        logger.error(f"Erro ao verificar dados: {e}")
        return False
    finally:
        if conn:
            conn.close()

def main():
    """Função principal"""
    logger.info("=== Gerador de Dados de Votação Sintéticos ===")
    
    # Verificar dados existentes
    tem_dados = verificar_dados_existentes()
    
    if tem_dados:
        resposta = input("Já existem dados de votação. Deseja sobrescrever? (s/N): ")
        if resposta.lower() not in ['s', 'sim', 'y', 'yes']:
            logger.info("Operação cancelada pelo usuário")
            return
    
    # Gerar dados
    sucesso = gerar_dados_votacao()
    
    if sucesso:
        logger.info("✅ Processo concluído com sucesso!")
        logger.info("🌐 Acesse http://localhost:8502 para ver os dados no dashboard")
    else:
        logger.error("❌ Falha na geração dos dados")

if __name__ == "__main__":
    main()
"""
Script para recalcular scores de diversidade de forma justa
"""
import psycopg2
import sys
import os

def calculate_fair_diversity_score(candidate):
    """
    Calcula score de diversidade de forma justa e transparente
    
    Critérios objetivos:
    - Representatividade regional (25%)
    - Experiência política (30%) 
    - Formação acadêmica (20%)
    - Histórico de diversidade (25%)
    """
    score = 0.0
    
    # 1. Representatividade Regional (0-0.25)
    underrepresented_regions = ['NORTE', 'NORDESTE', 'CENTRO-OESTE']
    if candidate['region'] in underrepresented_regions:
        score += 0.25
    else:
        score += 0.15  # Sul/Sudeste ainda têm valor, mas menor
    
    # 2. Experiência Política por tipo de cargo (0-0.3)
    experience_weights = {
        'EXECUTIVO_MUNICIPAL': 0.3,  # Prefeito
        'LEGISLATIVO_FEDERAL': 0.25,  # Senador/Dep Federal  
        'LEGISLATIVO_ESTADUAL': 0.2,  # Deputado Estadual
        'EXECUTIVO_ESTADUAL': 0.3,   # Governador
    }
    
    cargo_category = candidate.get('cargo_category', '')
    score += experience_weights.get(cargo_category, 0.1)
    
    # 3. Formação Acadêmica (0-0.2)
    education = candidate.get('education', '').upper()
    if 'SUPERIOR' in education:
        score += 0.2
    elif 'MÉDIO' in education or 'MEDIO' in education:
        score += 0.15
    else:
        score += 0.1
    
    # 4. Histórico de Diversidade baseado na ocupação (0-0.25)
    occupation = candidate.get('occupation', '').upper()
    diversity_occupations = [
        'PROFESSOR', 'EDUCADOR', 'ASSISTENTE SOCIAL', 'ATIVISTA',
        'ADVOGADO', 'JORNALISTA', 'PSICÓLOGO', 'ESCRITOR',
        'SERVIDOR PÚBLICO', 'LÍDER COMUNITÁRIO'
    ]
    
    has_diversity_background = any(occ in occupation for occ in diversity_occupations)
    if has_diversity_background:
        score += 0.25
    else:
        score += 0.1
    
    return min(score, 1.0)

def update_fair_scores():
    """Atualiza os scores no banco de dados"""
    try:
        # Conectar ao banco
        conn = psycopg2.connect(
            host="localhost",
            port="5432", 
            database="eleicoes_analytics",
            user="postgres",
            password="postgres123"
        )
        
        cur = conn.cursor()
        
        # Buscar todas as candidatas
        cur.execute("""
            SELECT id, name, region, cargo_category, education, occupation
            FROM candidates
        """)
        
        candidates = cur.fetchall()
        
        print(f"📊 Recalculando scores para {len(candidates)} candidatas...")
        
        for candidate_data in candidates:
            candidate_id, name, region, cargo_category, education, occupation = candidate_data
            
            candidate_dict = {
                'region': region,
                'cargo_category': cargo_category, 
                'education': education,
                'occupation': occupation
            }
            
            # Calcular novo score justo
            new_score = calculate_fair_diversity_score(candidate_dict)
            
            # Buscar score antigo para comparação
            cur.execute("SELECT diversity_score FROM candidates WHERE id = %s", (candidate_id,))
            old_score = cur.fetchone()[0] or 0
            
            # Atualizar no banco
            cur.execute("""
                UPDATE candidates 
                SET diversity_score = %s 
                WHERE id = %s
            """, (new_score, candidate_id))
            
            print(f"  ✅ {name}: {old_score:.2f} → {new_score:.2f}")
        
        # Confirmar transação
        conn.commit()
        
        print("\n🎉 Scores atualizados com sucesso!")
        
        # Mostrar novo ranking
        cur.execute("""
            SELECT name, race, diversity_score, region, occupation
            FROM candidates 
            ORDER BY diversity_score DESC
        """)
        
        print("\n📈 Novo ranking justo:")
        for i, (name, race, score, region, occupation) in enumerate(cur.fetchall(), 1):
            print(f"  {i}º {name} ({race}) - Score: {score:.2f} - {region} - {occupation}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")

def show_methodology():
    """Mostra a metodologia transparente"""
    print("""
📋 METODOLOGIA DE SCORE DE DIVERSIDADE - SISTEMA JUSTO

🎯 OBJETIVO: 
Identificar candidatas com potencial para promover diversidade através de 
AÇÕES e COMPETÊNCIAS, não características pessoais.

📊 CRITÉRIOS (Total: 100%):

1️⃣ REPRESENTATIVIDADE REGIONAL (25%)
   • Norte/Nordeste/Centro-Oeste: 25 pontos
   • Sul/Sudeste: 15 pontos
   • Rationale: Promover descentralização política

2️⃣ EXPERIÊNCIA POLÍTICA (30%)
   • Prefeito/Governador: 30 pontos
   • Senador/Dep. Federal: 25 pontos  
   • Deputado Estadual: 20 pontos
   • Outros: 10 pontos
   • Rationale: Capacidade de impacto em políticas públicas

3️⃣ FORMAÇÃO ACADÊMICA (20%)
   • Superior: 20 pontos
   • Médio: 15 pontos
   • Fundamental: 10 pontos
   • Rationale: Preparação técnica para o cargo

4️⃣ HISTÓRICO COM DIVERSIDADE (25%)
   • Professor/Ativista/Assistente Social: 25 pontos
   • Advogado/Jornalista/Psicólogo: 25 pontos
   • Outras profissões: 10 pontos
   • Rationale: Experiência com causas sociais

✅ PRINCÍPIOS ÉTICOS:
• Sem discriminação racial ou étnica
• Foco em competências objetivas
• Transparência total na metodologia
• Critérios auditáveis
• Igualdade de oportunidades

⚠️  LIMITAÇÕES:
• Scores são indicativos, não determinísticos
• Devem ser complementados com análise qualitativa
• Não substituem avaliação humana especializada
    """)

if __name__ == "__main__":
    print("🔄 ATUALIZANDO SISTEMA DE SCORES PARA VERSÃO JUSTA")
    print("=" * 60)
    
    show_methodology()
    
    response = input("\n🤔 Deseja prosseguir com a atualização? (s/n): ")
    if response.lower() == 's':
        update_fair_scores()
    else:
        print("❌ Operação cancelada")
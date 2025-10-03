"""
Sistema de Pontuação Justo e Transparente para Candidaturas
"""

def calculate_fair_diversity_score(candidate):
    """
    Calcula score de diversidade de forma transparente e justa
    
    Critérios objetivos (sem viés racial):
    - Representatividade regional (20%)
    - Experiência política (30%) 
    - Formação acadêmica (20%)
    - Propostas de diversidade (30%)
    """
    score = 0.0
    
    # 1. Representatividade Regional (0-0.2)
    underrepresented_regions = ['NORTE', 'NORDESTE', 'CENTRO-OESTE']
    if candidate.region in underrepresented_regions:
        score += 0.2
    else:
        score += 0.1
    
    # 2. Experiência Política (0-0.3)
    experience_mapping = {
        'PREFEITO': 0.3,
        'SENADOR': 0.25,
        'DEPUTADO_FEDERAL': 0.2,
        'DEPUTADO_ESTADUAL': 0.15
    }
    score += experience_mapping.get(candidate.cargo, 0.1)
    
    # 3. Formação Acadêmica (0-0.2)
    if candidate.education == 'Superior':
        score += 0.2
    elif candidate.education == 'Médio':
        score += 0.15
    else:
        score += 0.1
    
    # 4. Histórico de Diversidade (0-0.3)
    # Baseado em ações concretas, não características pessoais
    diversity_occupations = ['Ativista', 'Educadora', 'Defensora']
    if candidate.occupation in diversity_occupations:
        score += 0.3
    elif candidate.occupation in ['Professora', 'Assistente Social']:
        score += 0.2
    else:
        score += 0.1
    
    return min(score, 1.0)

def create_transparent_methodology():
    """
    Metodologia transparente para cálculo de scores
    """
    return {
        "metodologia": {
            "objetivo": "Identificar candidatas com potencial para promover diversidade através de AÇÕES, não características pessoais",
            "criterios": {
                "representatividade_regional": {
                    "peso": "20%",
                    "descrição": "Candidatas de regiões sub-representadas",
                    "valores": {
                        "Norte/Nordeste/Centro-Oeste": 0.2,
                        "Sul/Sudeste": 0.1
                    }
                },
                "experiencia_politica": {
                    "peso": "30%", 
                    "descrição": "Experiência em cargos que impactam políticas públicas",
                    "valores": {
                        "Prefeito": 0.3,
                        "Senador": 0.25,
                        "Deputado Federal": 0.2,
                        "Deputado Estadual": 0.15
                    }
                },
                "formacao_academica": {
                    "peso": "20%",
                    "descrição": "Preparação técnica para exercer o cargo",
                    "valores": {
                        "Superior": 0.2,
                        "Médio": 0.15,
                        "Fundamental": 0.1
                    }
                },
                "historico_diversidade": {
                    "peso": "30%",
                    "descrição": "Histórico de trabalho com causas de diversidade e inclusão",
                    "valores": {
                        "Ativista/Educadora": 0.3,
                        "Professora/Assistente Social": 0.2,
                        "Outras profissões": 0.1
                    }
                }
            }
        },
        "principios_eticos": [
            "Não discriminação racial ou étnica",
            "Foco em ações e competências, não características pessoais",
            "Transparência total na metodologia",
            "Critérios objetivos e auditáveis",
            "Igualdade de oportunidades"
        ],
        "limitacoes": [
            "Scores são indicativos, não determinísticos",
            "Devem ser complementados com análise qualitativa",
            "Não substituem avaliação humana especializada"
        ]
    }

# Exemplo de recálculo justo
def demonstrate_fair_scoring():
    """Exemplo de como seria o cálculo justo"""
    candidates_examples = [
        {
            "name": "Sônia Guajajara",
            "region": "SUDESTE", 
            "cargo": "DEPUTADO_FEDERAL",
            "education": "Superior",
            "occupation": "Ativista",
            "fair_score": 0.1 + 0.2 + 0.2 + 0.3,  # 0.8
            "current_biased_score": 0.95
        },
        {
            "name": "Ana Santos",
            "region": "SUDESTE",
            "cargo": "DEPUTADO_ESTADUAL", 
            "education": "Superior",
            "occupation": "Advogada",
            "fair_score": 0.1 + 0.15 + 0.2 + 0.1,  # 0.55
            "current_biased_score": 0.0
        }
    ]
    
    return candidates_examples
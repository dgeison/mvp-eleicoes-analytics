-- Script SQL para atualizar scores de diversidade de forma justa

-- Criar função para calcular score justo
CREATE OR REPLACE FUNCTION calculate_fair_diversity_score(
    p_region VARCHAR,
    p_cargo_category VARCHAR, 
    p_education VARCHAR,
    p_occupation VARCHAR
) RETURNS DECIMAL(3,2) AS $$
DECLARE
    score DECIMAL(3,2) := 0.0;
BEGIN
    -- 1. Representatividade Regional (25%)
    IF p_region IN ('NORTE', 'NORDESTE', 'CENTRO-OESTE') THEN
        score := score + 0.25;
    ELSE
        score := score + 0.15;
    END IF;
    
    -- 2. Experiência Política (30%)
    CASE 
        WHEN p_cargo_category = 'EXECUTIVO_MUNICIPAL' THEN score := score + 0.30;
        WHEN p_cargo_category = 'LEGISLATIVO_FEDERAL' THEN score := score + 0.25;
        WHEN p_cargo_category = 'LEGISLATIVO_ESTADUAL' THEN score := score + 0.20;
        WHEN p_cargo_category = 'EXECUTIVO_ESTADUAL' THEN score := score + 0.30;
        ELSE score := score + 0.10;
    END CASE;
    
    -- 3. Formação Acadêmica (20%)
    IF UPPER(p_education) LIKE '%SUPERIOR%' THEN
        score := score + 0.20;
    ELSIF UPPER(p_education) LIKE '%MÉDIO%' OR UPPER(p_education) LIKE '%MEDIO%' THEN
        score := score + 0.15;
    ELSE
        score := score + 0.10;
    END IF;
    
    -- 4. Histórico de Diversidade (25%)
    IF UPPER(p_occupation) ~ '(PROFESSOR|EDUCADOR|ASSISTENTE SOCIAL|ATIVISTA|ADVOGADO|JORNALISTA|PSICÓLOGO|ESCRITOR|SERVIDOR PÚBLICO)' THEN
        score := score + 0.25;
    ELSE
        score := score + 0.10;
    END IF;
    
    -- Garantir que o score não exceda 1.0
    RETURN LEAST(score, 1.0);
END;
$$ LANGUAGE plpgsql;

-- Mostrar scores atuais
SELECT 
    'SCORES ATUAIS (SISTEMA TENDENCIOSO)' as status,
    name, 
    race,
    region,
    occupation,
    diversity_score as score_atual
FROM candidates 
ORDER BY diversity_score DESC;

-- Atualizar todos os scores com o novo algoritmo justo
UPDATE candidates 
SET diversity_score = calculate_fair_diversity_score(region, cargo_category, education, occupation);

-- Mostrar novos scores
SELECT 
    'NOVOS SCORES (SISTEMA JUSTO)' as status,
    name,
    race, 
    region,
    occupation,
    diversity_score as novo_score
FROM candidates 
ORDER BY diversity_score DESC;

-- Comparação lado a lado
WITH old_scores AS (
    SELECT 
        name,
        CASE 
            WHEN name = 'Sônia Guajajara' THEN 0.95
            WHEN name = 'Conceição Evaristo' THEN 0.90
            WHEN name = 'Tabata Amaral' THEN 0.85
            WHEN name = 'Manuela D''Ávila' THEN 0.75
            WHEN name = 'Luiza Helena' THEN 0.70
            ELSE 0.0
        END as score_antigo
    FROM candidates
)
SELECT 
    c.name,
    c.race,
    o.score_antigo,
    c.diversity_score as score_novo,
    ROUND((c.diversity_score - o.score_antigo), 2) as diferenca,
    CASE 
        WHEN c.diversity_score > o.score_antigo THEN '⬆️ SUBIU'
        WHEN c.diversity_score < o.score_antigo THEN '⬇️ DESCEU' 
        ELSE '➡️ IGUAL'
    END as mudanca
FROM candidates c
JOIN old_scores o ON c.name = o.name
ORDER BY c.diversity_score DESC;

-- Estatísticas finais
SELECT 
    '📊 ESTATÍSTICAS DO NOVO SISTEMA' as info,
    ROUND(AVG(diversity_score), 3) as score_medio,
    ROUND(MIN(diversity_score), 3) as score_minimo,
    ROUND(MAX(diversity_score), 3) as score_maximo,
    ROUND(STDDEV(diversity_score), 3) as desvio_padrao
FROM candidates;
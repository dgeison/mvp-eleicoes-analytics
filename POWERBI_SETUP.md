# 🚀 Como Conectar PowerBI aos Dados Eleitorais

## 📊 Opções de Conexão Disponíveis

### 1. 🔗 **Conexão Direta ao PostgreSQL** (RECOMENDADO)
**Melhor performance e atualizações automáticas**

**Configuração no PowerBI Desktop:**
1. Abra PowerBI Desktop
2. Clique em "Obter Dados" → "Banco de Dados" → "PostgreSQL"
3. Configure:
   - **Servidor:** `localhost:5432`
   - **Banco de dados:** `eleicoes_analytics`
   - **Usuário:** `postgres`
   - **Senha:** (conforme configurado no docker-compose)

**Query SQL Recomendada:**
```sql
SELECT 
    id as "ID",
    name as "Nome Completo",
    ballot_name as "Nome na Urna",
    state as "Estado", 
    region as "Região",
    cargo as "Cargo",
    education as "Educação",
    race as "Raça/Cor",
    diversity_score as "Score Diversidade",
    votes_received as "Votos Recebidos",
    vote_percentage as "Percentual Votos",
    is_minority_race as "É Minoria Racial",
    source as "Fonte"
FROM candidates 
WHERE state IS NOT NULL
ORDER BY votes_received DESC NULLS LAST;
```

---

### 2. 📁 **Exportação de Arquivos** (MAIS FÁCIL)
**Para análises pontuais ou quando não há acesso direto ao banco**

#### CSV Export
**URL:** `http://localhost:8000/powerbi/candidates/csv`

**Parâmetros opcionais:**
- `states=SP,RJ,MG` - Filtrar por estados específicos
- `regions=SUDESTE,SUL` - Filtrar por regiões
- `cargos=DEPUTADO FEDERAL,SENADOR` - Filtrar por cargos
- `limit=5000` - Limitar número de registros

**Exemplo completo:**
```
http://localhost:8000/powerbi/candidates/csv?states=SP,RJ&limit=1000
```

#### Excel Export (Formatado)
**URL:** `http://localhost:8000/powerbi/candidates/excel`

**Inclui:**
- ✅ Dados principais formatados
- ✅ Resumos por estado e cargo
- ✅ Metadados da exportação
- ✅ Formatação de números e percentuais

---

### 3. 🔄 **API REST** (PARA DESENVOLVEDORES)
**Para integrações personalizadas**

**Endpoint Principal:**
`http://localhost:8000/powerbi/quick-data`

**Retorna JSON com:**
- Dados das candidatas
- Resumos estatísticos
- Metadados

---

## 🎯 Configuração Recomendada no PowerBI

### 1. Medidas DAX Essenciais
```dax
// Total de Candidatas
Total Candidatas = COUNTROWS(candidatas)

// Total de Votos
Total Votos = SUM(candidatas[Votos Recebidos])

// Média de Votos
Média Votos = AVERAGE(candidatas[Votos Recebidos])

// Percentual de Minorias
% Minorias = 
DIVIDE(
    COUNTROWS(FILTER(candidatas, candidatas[É Minoria Racial] = TRUE)), 
    COUNTROWS(candidatas), 
    0
)

// Score Diversidade Médio
Score Diversidade Médio = AVERAGE(candidatas[Score Diversidade])

// Candidatas com Mais de 50mil Votos
Candidatas 50k+ Votos = 
COUNTROWS(FILTER(candidatas, candidatas[Votos Recebidos] > 50000))
```

### 2. Filtros Sugeridos
- 🗺️ **Estado** (Slicer com múltipla seleção)
- 🌎 **Região** (Botões ou Slicer)
- 🏛️ **Cargo** (Dropdown)
- 🎓 **Educação** (Hierarquia)
- 🗳️ **Faixa de Votos** (Slider numérico)

### 3. Visualizações Recomendadas

#### Dashboard Principal
- **Cartões KPI:** Total de candidatas, votos totais, média
- **Gráfico de Barras:** Top 10 candidatas mais votadas
- **Mapa:** Distribuição por estado
- **Pizza:** Distribuição racial
- **Coluna:** Candidatas por nível educacional

#### Análise de Diversidade
- **Scatter Plot:** Score Diversidade vs Votos Recebidos
- **Treemap:** Estados por diversidade
- **Barras Empilhadas:** Raça por região
- **Linha:** Evolução da diversidade (se dados históricos)

---

## 🛠️ Passos Detalhados

### PowerBI Desktop

1. **Baixar dados via Excel** (Mais fácil para começar)
   ```
   http://localhost:8000/powerbi/candidates/excel
   ```

2. **Abrir PowerBI Desktop**

3. **Obter Dados → Excel**
   - Selecionar arquivo baixado
   - Importar aba "Candidatas"

4. **Criar Medidas DAX** (copiar códigos acima)

5. **Montar Dashboard:**
   - Adicionar slicers para filtros
   - Criar visualizações principais
   - Aplicar tema personalizado

6. **Publicar no PowerBI Service**
   - Configurar refresh automático (se usando conexão direta)

### Conexão Direta (Avançado)

1. **Obter Dados → PostgreSQL**

2. **Configurar conexão:**
   ```
   Servidor: localhost:5432
   Banco: eleicoes_analytics
   Modo: DirectQuery (para grandes volumes)
   ```

3. **Usar query SQL personalizada** (ver acima)

4. **Configurar refresh automático**

---

## 📈 Análises Sugeridas

### 1. **Análise Eleitoral**
- Candidatas mais votadas por estado
- Efetividade por faixa de investimento
- Correlação educação vs performance

### 2. **Análise de Diversidade**
- Representatividade racial por região
- Score de diversidade vs sucesso eleitoral
- Gaps de oportunidade

### 3. **Análise Geográfica**
- Heatmap de candidaturas por estado
- Performance regional
- Oportunidades de expansão

### 4. **Análise Educacional**
- Distribuição de escolaridade
- Performance por nível educacional
- Tendências e padrões

---

## 🔧 Solução de Problemas

### Conexão PostgreSQL não funciona
- Verificar se o Docker está rodando: `docker-compose ps`
- Testar conectividade: `curl http://localhost:8000/health`
- Verificar credenciais no docker-compose.yml

### Performance lenta
- Usar filtros na query SQL
- Considerar DirectQuery para grandes volumes
- Implementar agregações no banco

### Dados não atualizando
- Configurar refresh automático
- Verificar conexão de rede
- Testar endpoints da API manualmente

---

## 📞 Suporte

**Endpoints de teste:**
- Health Check: `http://localhost:8000/health`
- Dados rápidos: `http://localhost:8000/powerbi/quick-data?limit=100`
- Metadados: `http://localhost:8000/powerbi/database-info`

**Documentação da API:**
`http://localhost:8000/docs`

---

## 🎉 Vantagens do PowerBI

✅ **Filtros interativos nativos** - Exatamente o que você queria!
✅ **Performance superior** - Renderização otimizada
✅ **Funcionalidades avançadas** - Drill-down, cross-filtering
✅ **Compartilhamento fácil** - PowerBI Service
✅ **Mobile friendly** - Apps nativas
✅ **Integração Microsoft** - Excel, Teams, SharePoint
✅ **Visualizações ricas** - Mapas, gráficos interativos

O PowerBI vai resolver todos os problemas de performance e filtros que estávamos tendo! 🚀
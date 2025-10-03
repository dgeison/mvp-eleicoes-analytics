"""
🧪 GUIA DE TESTE - DOCUMENTAÇÃO SWAGGER
======================================

COMO USAR A DOCUMENTAÇÃO INTERATIVA:

1. ABRIR A DOCUMENTAÇÃO
   📍 URL: http://localhost:8000/docs
   
2. ESTRUTURA DA PÁGINA
   👁️ O que você verá:
   - Título "MVP Eleições Analytics" 
   - Lista de endpoints com cores:
     🟢 GET (buscar dados)
     🔵 POST (enviar dados)
     🟡 PUT (atualizar dados)
     🔴 DELETE (deletar dados)

3. TESTANDO UM ENDPOINT (passo a passo):
   
   3.1. ESCOLHA UM ENDPOINT
   - Clique em qualquer linha (ex: GET /api/v1/candidates)
   - A linha se expande mostrando detalhes
   
   3.2. ATIVAR TESTE
   - Clique no botão "Try it out" (canto direito)
   - Os campos ficam editáveis
   
   3.3. PREENCHER PARÂMETROS (opcional)
   - Se houver campos, você pode preenchê-los
   - Exemplo: gender = F, state = SP
   - Deixe vazio para buscar tudo
   
   3.4. EXECUTAR TESTE
   - Clique no botão azul "Execute"
   - Aguarde a resposta
   
   3.5. VER RESULTADO
   - Seção "Response body": dados retornados
   - Seção "Response headers": informações técnicas
   - Status code: 200 = sucesso, 400+ = erro

4. TESTES RECOMENDADOS PARA VOCÊ:

   TESTE A: Health Check ✅
   ----------------------
   - Endpoint: GET /health
   - Parâmetros: nenhum
   - Resultado esperado: {"status": "healthy"}
   
   TESTE B: Listar Candidatas ✅
   ----------------------------
   - Endpoint: GET /api/v1/candidates
   - Parâmetros: deixe vazio
   - Resultado esperado: 7 candidatas
   
   TESTE C: Filtrar por Gênero ✅
   -----------------------------
   - Endpoint: GET /api/v1/candidates
   - Parâmetro: gender = F
   - Resultado esperado: todas mulheres
   
   TESTE D: Filtrar por Estado ✅
   -----------------------------
   - Endpoint: GET /api/v1/candidates
   - Parâmetro: state = SP
   - Resultado esperado: candidatas de São Paulo
   
   TESTE E: Filtro Combinado ✅
   ---------------------------
   - Endpoint: GET /api/v1/candidates
   - Parâmetros: gender = F, state = SP
   - Resultado esperado: mulheres de SP
   
   TESTE F: Anos de Eleições ✅
   ---------------------------
   - Endpoint: GET /api/v1/elections/years
   - Parâmetros: nenhum
   - Resultado esperado: lista de anos

5. INTERPRETANDO RESPOSTAS:

   SUCESSO (Status 200):
   {
     "data": [...],      // Lista de resultados
     "total": 7,         // Total de registros
     "page": 1,          // Página atual
     "per_page": 100     // Itens por página
   }
   
   ERRO (Status 4xx/5xx):
   {
     "detail": "Mensagem do erro"
   }

6. DICAS IMPORTANTES:

   ✅ Sempre teste o /health primeiro
   ✅ Comece sem filtros, depois adicione
   ✅ Observe o status code (200 = ok)
   ✅ Leia as mensagens de erro
   ✅ Teste diferentes combinações
   
   ❌ Não use valores inválidos (ex: state = 999)
   ❌ Não deixe campos obrigatórios vazios
   ❌ Não ignore mensagens de erro

7. SE ALGO DER ERRADO:

   🔧 API não responde:
   - Verifique se containers estão rodando
   - docker compose ps
   
   🔧 Erro 500:
   - Problema interno da API
   - Verifique logs: docker compose logs api
   
   🔧 Erro 404:
   - Endpoint não existe
   - Verifique se digitou corretamente
   
   🔧 Erro 422:
   - Parâmetros inválidos
   - Verifique os valores dos filtros

DIVIRTA-SE TESTANDO! 🎉
"""
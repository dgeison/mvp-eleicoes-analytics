"""
Script para integrar dados reais do TSE ao sistema
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import json
import requests
from src.ingestion.tse_connector_enhanced import TSEConnector
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TSEIntegration:
    """Classe para integrar dados TSE ao sistema"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.tse_connector = TSEConnector()
        self.api_base_url = api_base_url
    
    def test_api_connection(self) -> bool:
        """Testa conexão com a API"""
        try:
            response = requests.get(f"{self.api_base_url}/health")
            if response.status_code == 200:
                logger.info("✅ API está funcionando")
                return True
            else:
                logger.error(f"❌ API retornou status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Erro na conexão com API: {e}")
            return False
    
    def backup_current_data(self) -> bool:
        """Faz backup dos dados atuais"""
        try:
            response = requests.get(f"{self.api_base_url}/api/candidates")
            if response.status_code == 200:
                backup_data = response.json()
                with open('data/backup_candidates.json', 'w') as f:
                    json.dump(backup_data, f, indent=2)
                logger.info(f"✅ Backup criado: {len(backup_data.get('candidates', []))} candidatas salvas")
                return True
            else:
                logger.error(f"❌ Erro no backup: status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Erro no backup: {e}")
            return False
    
    def fetch_and_process_tse_data(self, year: int = 2022, limit: int = 500) -> list:
        """
        Busca e processa dados do TSE
        
        Args:
            year: Ano da eleição
            limit: Limite de candidatas para processar
            
        Returns:
            Lista de candidatas processadas
        """
        try:
            logger.info(f"🔍 Iniciando busca de dados TSE {year}...")
            
            # Buscar dados brutos do TSE
            tse_data = self.tse_connector.fetch_real_data(year=year, limit=limit)
            
            if tse_data.empty:
                logger.error("❌ Nenhum dado encontrado no TSE")
                return []
            
            logger.info(f"📊 Dados TSE carregados: {len(tse_data)} registros")
            
            # Converter para formato da API
            candidates = self.tse_connector.export_to_api_format(tse_data)
            
            if not candidates:
                logger.error("❌ Falha na conversão dos dados")
                return []
            
            logger.info(f"✅ Dados convertidos: {len(candidates)} candidatas")
            
            # Aplicar processamento adicional com nosso sistema justo
            processed_candidates = []
            for candidate in candidates:
                # Recalcular score usando nosso algoritmo justo
                fair_score = self._calculate_enhanced_score(candidate)
                candidate['diversity_score'] = fair_score
                candidate['processing_source'] = 'TSE_Enhanced'
                processed_candidates.append(candidate)
            
            # Ordenar por score
            processed_candidates.sort(key=lambda x: x['diversity_score'], reverse=True)
            
            logger.info(f"🎯 Candidatas processadas com scores justos")
            
            return processed_candidates
            
        except Exception as e:
            logger.error(f"❌ Erro no processamento TSE: {e}")
            return []
    
    def _calculate_enhanced_score(self, candidate: dict) -> float:
        """
        Calcula score aprimorado usando critérios justos
        """
        try:
            score = 0.0
            
            # 1. Experiência Política (30%)
            experience = candidate.get('political_experience', '').upper()
            if 'DEPUTADO FEDERAL' in experience or 'SENADOR' in experience:
                score += 0.30
            elif 'DEPUTADO ESTADUAL' in experience:
                score += 0.25
            elif 'PREFEITO' in experience or 'VEREADOR' in experience:
                score += 0.20
            else:
                score += 0.10
            
            # 2. Educação (25%)
            education = candidate.get('education', '').upper()
            if 'PÓS-GRADUAÇÃO' in education or 'MESTRADO' in education or 'DOUTORADO' in education:
                score += 0.25
            elif 'SUPERIOR' in education:
                score += 0.20
            elif 'MÉDIO' in education:
                score += 0.15
            else:
                score += 0.10
            
            # 3. Representatividade Regional (25%)
            region = candidate.get('region', '').upper()
            if region in ['NORTE', 'NORDESTE', 'CENTRO-OESTE']:
                score += 0.25  # Regiões sub-representadas
            elif region in ['SUL']:
                score += 0.20
            elif region in ['SUDESTE']:
                score += 0.15
            else:
                score += 0.10
            
            # 4. Diversidade e Inclusão (20%)
            raw_data = candidate.get('raw_data', {})
            race = raw_data.get('race', '').upper()
            occupation = raw_data.get('occupation', '').upper()
            
            # Raça/etnia
            if any(term in race for term in ['PRETA', 'PARDA', 'INDÍGENA']):
                score += 0.10
            else:
                score += 0.05
            
            # Ocupação em áreas de inclusão
            inclusion_areas = ['PROFESSOR', 'ASSISTENTE SOCIAL', 'ADVOGADO', 'MÉDICO', 'JORNALISTA']
            if any(area in occupation for area in inclusion_areas):
                score += 0.10
            else:
                score += 0.05
            
            return min(score, 1.0)  # Máximo 1.0
            
        except Exception as e:
            logger.error(f"❌ Erro no cálculo de score: {e}")
            return 0.5
    
    def update_database_with_tse_data(self, candidates: list) -> bool:
        """
        Atualiza base de dados com candidatas do TSE
        """
        try:
            logger.info(f"📝 Atualizando base com {len(candidates)} candidatas TSE...")
            
            # Preparar dados para inserção
            insert_data = {
                "candidates": candidates,
                "source": "TSE",
                "update_mode": "replace"  # Substituir dados existentes
            }
            
            # Enviar para API
            response = requests.post(
                f"{self.api_base_url}/api/candidates/bulk_update",
                json=insert_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Base atualizada com sucesso: {result.get('updated_count', 0)} registros")
                return True
            else:
                logger.error(f"❌ Erro na atualização: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro na atualização da base: {e}")
            return False
    
    def run_full_integration(self, year: int = 2022, limit: int = 200) -> bool:
        """
        Executa integração completa TSE
        
        Args:
            year: Ano da eleição
            limit: Limite de candidatas
            
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            logger.info("🚀 Iniciando integração completa TSE...")
            
            # 1. Verificar conexões
            if not self.test_api_connection():
                logger.error("❌ API não está disponível")
                return False
            
            if not self.tse_connector.test_tse_connection():
                logger.error("❌ TSE não está disponível")
                return False
            
            # 2. Backup dos dados atuais
            if not self.backup_current_data():
                logger.warning("⚠️ Falha no backup - continuando mesmo assim")
            
            # 3. Buscar e processar dados TSE
            candidates = self.fetch_and_process_tse_data(year=year, limit=limit)
            
            if not candidates:
                logger.error("❌ Nenhuma candidata processada")
                return False
            
            # 4. Mostrar preview dos dados
            logger.info("\n📋 Preview das candidatas TSE:")
            for i, candidate in enumerate(candidates[:5]):
                logger.info(f"   {i+1}. {candidate['name']} - Score: {candidate['diversity_score']:.2f} - {candidate['region']}")
            
            if len(candidates) > 5:
                logger.info(f"   ... e mais {len(candidates) - 5} candidatas")
            
            # 5. Confirmar integração
            logger.info(f"\n🤔 Integrar {len(candidates)} candidatas TSE ao sistema? (dados atuais serão substituídos)")
            
            # Para automação, assumir 'sim'
            confirm = True
            
            if confirm:
                # 6. Atualizar base de dados
                if self.update_database_with_tse_data(candidates):
                    logger.info("🎉 Integração TSE concluída com sucesso!")
                    
                    # 7. Testar API atualizada
                    response = requests.get(f"{self.api_base_url}/api/candidates")
                    if response.status_code == 200:
                        api_data = response.json()
                        logger.info(f"✅ API atualizada: {len(api_data.get('candidates', []))} candidatas disponíveis")
                    
                    return True
                else:
                    logger.error("❌ Falha na atualização da base")
                    return False
            else:
                logger.info("⚠️ Integração cancelada pelo usuário")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro na integração: {e}")
            return False

def main():
    """Função principal"""
    print("🗳️ Integração de Dados TSE - Eleições 2026")
    print("=" * 50)
    
    # Inicializar integração
    integration = TSEIntegration()
    
    # Executar integração
    success = integration.run_full_integration(year=2022, limit=100)
    
    if success:
        print("\n🎉 Integração TSE concluída com sucesso!")
        print("📊 Sistema agora usa dados reais do Tribunal Superior Eleitoral")
        print("🌐 Acesse o dashboard em: http://localhost:8501")
    else:
        print("\n❌ Falha na integração TSE")
        print("🔧 Verifique os logs para mais detalhes")

if __name__ == "__main__":
    main()
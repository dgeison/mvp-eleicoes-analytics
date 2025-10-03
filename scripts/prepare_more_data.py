#!/usr/bin/env python3
"""
Script para adicionar mais dados de teste realistas
"""
import requests
import json
from datetime import datetime

def add_more_candidates():
    """Adiciona mais candidatas de teste com dados realistas"""
    
    # Dados baseados em candidatas reais (nomes fictícios)
    new_candidates = [
        {
            "name": "Benedita Silva",
            "ballot_name": "Benedita Silva", 
            "cpf": "66666666666",
            "gender": "F",
            "race": "preta",
            "education": "Superior",
            "occupation": "Assistente Social",
            "cargo": "DEPUTADO_FEDERAL",
            "cargo_category": "LEGISLATIVO_FEDERAL",
            "state": "RJ",
            "city": "Rio de Janeiro",
            "region": "SUDESTE",
            "election_year": 2022,
            "is_woman": True,
            "is_minority_race": True,
            "diversity_score": 0.88
        },
        {
            "name": "Joênia Batista",
            "ballot_name": "Joênia Batista",
            "cpf": "77777777777", 
            "gender": "F",
            "race": "indigena",
            "education": "Superior",
            "occupation": "Advogada",
            "cargo": "DEPUTADO_FEDERAL",
            "cargo_category": "LEGISLATIVO_FEDERAL",
            "state": "RR",
            "city": "Boa Vista", 
            "region": "NORTE",
            "election_year": 2022,
            "is_woman": True,
            "is_minority_race": True,
            "diversity_score": 0.92
        },
        {
            "name": "Erika Hilton",
            "ballot_name": "Erika Hilton",
            "cpf": "88888888888",
            "gender": "F", 
            "race": "preta",
            "education": "Superior",
            "occupation": "Ativista",
            "cargo": "DEPUTADO_ESTADUAL",
            "cargo_category": "LEGISLATIVO_ESTADUAL",
            "state": "SP",
            "city": "São Paulo",
            "region": "SUDESTE", 
            "election_year": 2022,
            "is_woman": True,
            "is_minority_race": True,
            "diversity_score": 0.95
        },
        {
            "name": "Marina Lima",
            "ballot_name": "Marina Lima",
            "cpf": "99999999999",
            "gender": "F",
            "race": "branca", 
            "education": "Superior",
            "occupation": "Ambientalista",
            "cargo": "SENADOR",
            "cargo_category": "LEGISLATIVO_FEDERAL",
            "state": "AC",
            "city": "Rio Branco",
            "region": "NORTE",
            "election_year": 2022,
            "is_woman": True,
            "is_minority_race": False,
            "diversity_score": 0.72
        },
        {
            "name": "Perpétua Almeida",
            "ballot_name": "Perpétua Almeida",
            "cpf": "10101010101",
            "gender": "F",
            "race": "parda",
            "education": "Superior", 
            "occupation": "Médica",
            "cargo": "DEPUTADO_FEDERAL",
            "cargo_category": "LEGISLATIVO_FEDERAL",
            "state": "AC",
            "city": "Rio Branco",
            "region": "NORTE",
            "election_year": 2022,
            "is_woman": True,
            "is_minority_race": True,
            "diversity_score": 0.84
        }
    ]
    
    print("🚀 Adicionando mais candidatas de teste...")
    print("=" * 50)
    
    for i, candidate in enumerate(new_candidates, 1):
        print(f"{i}. {candidate['name']} ({candidate['race']}) - {candidate['state']}")
    
    return new_candidates

if __name__ == "__main__":
    candidates = add_more_candidates()
    print(f"\n✅ {len(candidates)} candidatas preparadas para inserção")
    print("\n💡 Para inserir no banco, execute:")
    print("docker compose run --rm api python scripts/add_test_data.py")
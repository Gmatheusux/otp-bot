import pytest
from ai.fuzzy_engine import FuzzyUtilityEngine

def test_critical_hp_massive_monsters():
    engine = FuzzyUtilityEngine()
    scores = engine.evaluate(current_hp=20, current_monsters=8)
    
    assert scores['stress'] > 70.0
    assert scores['utility_heal'] > 70.0
    assert scores['utility_attack'] < 50.0

def test_healthy_hp_isolated_monsters():
    engine = FuzzyUtilityEngine()
    scores = engine.evaluate(current_hp=100, current_monsters=0)
    
    assert scores['stress'] < 40.0
    assert scores['utility_heal'] < 40.0
    assert scores['utility_attack'] < 40.0

def test_healthy_hp_massive_monsters():
    engine = FuzzyUtilityEngine()
    scores = engine.evaluate(current_hp=90, current_monsters=8)
    
    assert scores['utility_attack'] > 70.0
    assert scores['utility_heal'] < 40.0

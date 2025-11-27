"""
Behaviour Tree Nodes for Dungeon Game

Defines condition and action nodes that interface with the game engine.
"""

from abc import ABC, abstractmethod
from typing import Optional
from .game_engine import GameState, ActionType


class BTNodeResult:
    """Result of BT node execution"""
    SUCCESS = "success"
    FAILURE = "failure"
    RUNNING = "running"


class BTCondition(ABC):
    """Base class for condition nodes"""
    
    @abstractmethod
    def evaluate(self, state: GameState) -> bool:
        """Evaluate condition against game state"""
        pass


class BTAction(ABC):
    """Base class for action nodes"""
    
    @abstractmethod
    def execute(self, state: GameState) -> ActionType:
        """Execute action and return the ActionType to perform"""
        pass


# ============================================================================
# CONDITION NODES
# ============================================================================

class IsPlayerHPLow(BTCondition):
    """Check if player HP is below threshold percentage"""
    
    def __init__(self, threshold: int = 30):
        self.threshold = threshold
    
    def evaluate(self, state: GameState) -> bool:
        return state.player.hp_percentage() < self.threshold
    
    def __repr__(self):
        return f"IsPlayerHPLow({self.threshold})"


class IsPlayerHPHigh(BTCondition):
    """Check if player HP is above threshold percentage"""
    
    def __init__(self, threshold: int = 70):
        self.threshold = threshold
    
    def evaluate(self, state: GameState) -> bool:
        return state.player.hp_percentage() > self.threshold
    
    def __repr__(self):
        return f"IsPlayerHPHigh({self.threshold})"


class IsEnemyHPLow(BTCondition):
    """Check if enemy HP is below threshold percentage"""
    
    def __init__(self, threshold: int = 30):
        self.threshold = threshold
    
    def evaluate(self, state: GameState) -> bool:
        if not state.enemy:
            return False
        return state.enemy.hp_percentage() < self.threshold
    
    def __repr__(self):
        return f"IsEnemyHPLow({self.threshold})"


class IsEnemyHPHigh(BTCondition):
    """Check if enemy HP is above threshold percentage"""
    
    def __init__(self, threshold: int = 70):
        self.threshold = threshold
    
    def evaluate(self, state: GameState) -> bool:
        if not state.enemy:
            return False
        return state.enemy.hp_percentage() > self.threshold
    
    def __repr__(self):
        return f"IsEnemyHPHigh({self.threshold})"


class CanHeal(BTCondition):
    """Check if heal is available (not on cooldown)"""
    
    def evaluate(self, state: GameState) -> bool:
        return state.heal_cooldown == 0
    
    def __repr__(self):
        return "CanHeal()"


class IsDefending(BTCondition):
    """Check if player is currently defending"""
    
    def evaluate(self, state: GameState) -> bool:
        return state.is_defending
    
    def __repr__(self):
        return "IsDefending()"


class HasComboReady(BTCondition):
    """Check if a specific combo pattern is one action away"""
    
    def __init__(self, combo_name: str = "TripleLight"):
        self.combo_name = combo_name
    
    def evaluate(self, state: GameState) -> bool:
        history = state.action_history
        
        if self.combo_name == "TripleLight":
            # Need 2 light attacks in a row
            return (len(history) >= 2 and 
                   history[-2:] == [ActionType.LIGHT_ATTACK, ActionType.LIGHT_ATTACK])
        
        elif self.combo_name == "HeavyFinisher":
            # Need 2 light attacks in a row (next heavy will trigger)
            return (len(history) >= 2 and 
                   history[-2:] == [ActionType.LIGHT_ATTACK, ActionType.LIGHT_ATTACK])
        
        elif self.combo_name == "CounterStrike":
            # Need to have just defended
            return len(history) >= 1 and history[-1] == ActionType.DEFEND
        
        return False
    
    def __repr__(self):
        return f"HasComboReady({self.combo_name})"


class IsFloorBoss(BTCondition):
    """Check if current floor is a boss floor (5 or 10)"""
    
    def evaluate(self, state: GameState) -> bool:
        return state.current_floor % 5 == 0
    
    def __repr__(self):
        return "IsFloorBoss()"


class IsTurnEarly(BTCondition):
    """Check if it's early in the fight (low turn count)"""
    
    def __init__(self, threshold: int = 3):
        self.threshold = threshold
    
    def evaluate(self, state: GameState) -> bool:
        return state.turn_count <= self.threshold
    
    def __repr__(self):
        return f"IsTurnEarly({self.threshold})"


# ============================================================================
# ACTION NODES
# ============================================================================

class LightAttack(BTAction):
    """Execute light attack"""
    
    def execute(self, state: GameState) -> ActionType:
        return ActionType.LIGHT_ATTACK
    
    def __repr__(self):
        return "LightAttack()"


class HeavyAttack(BTAction):
    """Execute heavy attack"""
    
    def execute(self, state: GameState) -> ActionType:
        return ActionType.HEAVY_ATTACK
    
    def __repr__(self):
        return "HeavyAttack()"


class Defend(BTAction):
    """Execute defend action"""
    
    def execute(self, state: GameState) -> ActionType:
        return ActionType.DEFEND
    
    def __repr__(self):
        return "Defend()"


class Heal(BTAction):
    """Execute heal action"""
    
    def execute(self, state: GameState) -> ActionType:
        return ActionType.HEAL
    
    def __repr__(self):
        return "Heal()"


# ============================================================================
# NODE FACTORY
# ============================================================================

def create_condition_node(node_type: str, param: Optional[str] = None) -> BTCondition:
    """Factory function to create condition nodes from DSL"""
    
    # Parse parameter if exists
    threshold = None
    combo_name = None
    
    if param:
        # Remove parentheses and parse
        param = param.strip('()')
        if param.isdigit():
            threshold = int(param)
        else:
            combo_name = param
    
    # Create appropriate node
    if node_type == "IsPlayerHPLow":
        return IsPlayerHPLow(threshold if threshold else 30)
    elif node_type == "IsPlayerHPHigh":
        return IsPlayerHPHigh(threshold if threshold else 70)
    elif node_type == "IsEnemyHPLow":
        return IsEnemyHPLow(threshold if threshold else 30)
    elif node_type == "IsEnemyHPHigh":
        return IsEnemyHPHigh(threshold if threshold else 70)
    elif node_type == "CanHeal":
        return CanHeal()
    elif node_type == "IsDefending":
        return IsDefending()
    elif node_type == "HasComboReady":
        return HasComboReady(combo_name if combo_name else "TripleLight")
    elif node_type == "IsFloorBoss":
        return IsFloorBoss()
    elif node_type == "IsTurnEarly":
        return IsTurnEarly(threshold if threshold else 3)
    else:
        raise ValueError(f"Unknown condition node type: {node_type}")


def create_action_node(node_type: str) -> BTAction:
    """Factory function to create action nodes from DSL"""
    
    if node_type == "LightAttack":
        return LightAttack()
    elif node_type == "HeavyAttack":
        return HeavyAttack()
    elif node_type == "Defend":
        return Defend()
    elif node_type == "Heal":
        return Heal()
    else:
        raise ValueError(f"Unknown action node type: {node_type}")

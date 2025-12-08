"""
Behaviour Tree Nodes for Enhanced Combat System

Defines condition and action nodes for:
- 8 Player actions
- Elemental system checks
- Resource (TP/MP) checks
- Enemy type detection
- Status ailment checks
"""

from abc import ABC, abstractmethod
from typing import Optional
from .game_engine import GameState, PlayerAction, Element, EnemyType, StatusAilment


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
    def execute(self, state: GameState) -> Optional[PlayerAction]:
        """Execute action and return the PlayerAction to perform"""
        pass


# ============================================================================
# CONDITION NODES - HP Checks
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


# ============================================================================
# CONDITION NODES - Resource Checks
# ============================================================================

class HasTP(BTCondition):
    """Check if player has enough TP"""
    
    def __init__(self, threshold: int = 30):
        self.threshold = threshold
    
    def evaluate(self, state: GameState) -> bool:
        return state.player_resources.tp >= self.threshold
    
    def __repr__(self):
        return f"HasTP({self.threshold})"


class HasMP(BTCondition):
    """Check if player has enough MP"""
    
    def __init__(self, threshold: int = 20):
        self.threshold = threshold
    
    def evaluate(self, state: GameState) -> bool:
        return state.player_resources.mp >= self.threshold
    
    def __repr__(self):
        return f"HasMP({self.threshold})"


class IsTPLow(BTCondition):
    """Check if player TP is below threshold"""
    
    def __init__(self, threshold: int = 30):
        self.threshold = threshold
    
    def evaluate(self, state: GameState) -> bool:
        return state.player_resources.tp < self.threshold
    
    def __repr__(self):
        return f"IsTPLow({self.threshold})"


class IsMPLow(BTCondition):
    """Check if player MP is below threshold"""
    
    def __init__(self, threshold: int = 30):
        self.threshold = threshold
    
    def evaluate(self, state: GameState) -> bool:
        return state.player_resources.mp < self.threshold
    
    def __repr__(self):
        return f"IsMPLow({self.threshold})"


# ============================================================================
# CONDITION NODES - Enemy Type & Elemental
# ============================================================================

class IsEnemy(BTCondition):
    """Check if current enemy matches specific type"""
    
    def __init__(self, enemy_name: str):
        self.enemy_name = enemy_name.strip()
        # Map string to EnemyType
        enemy_map = {
            "FireGolem": EnemyType.FIRE_GOLEM,
            "IceWraith": EnemyType.ICE_WRAITH,
            "ThunderDrake": EnemyType.THUNDER_DRAKE
        }
        self.enemy_type = enemy_map.get(self.enemy_name)
    
    def evaluate(self, state: GameState) -> bool:
        if not state.enemy_type or not self.enemy_type:
            return False
        return state.enemy_type == self.enemy_type
    
    def __repr__(self):
        return f"IsEnemy({self.enemy_name})"


class EnemyWeakTo(BTCondition):
    """Check if enemy is weak to specific element"""
    
    def __init__(self, element: str):
        self.element_str = element.strip()
        # Map string to Element
        element_map = {
            "Fire": Element.FIRE,
            "Ice": Element.ICE,
            "Lightning": Element.LIGHTNING
        }
        self.element = element_map.get(self.element_str)
    
    def evaluate(self, state: GameState) -> bool:
        if not state.enemy or not self.element:
            return False
        
        # Check weakness
        from .game_engine import ELEMENTAL_WEAKNESS
        weakness = ELEMENTAL_WEAKNESS.get(state.enemy.element)
        return weakness == self.element
    
    def __repr__(self):
        return f"EnemyWeakTo({self.element_str})"


class EnemyResistantTo(BTCondition):
    """Check if enemy is resistant to specific element"""
    
    def __init__(self, element: str):
        self.element_str = element.strip()
        element_map = {
            "Fire": Element.FIRE,
            "Ice": Element.ICE,
            "Lightning": Element.LIGHTNING
        }
        self.element = element_map.get(self.element_str)
    
    def evaluate(self, state: GameState) -> bool:
        if not state.enemy or not self.element:
            return False
        
        # Enemy is resistant to its own element
        return state.enemy.element == self.element
    
    def __repr__(self):
        return f"EnemyResistantTo({self.element_str})"


class HasScannedEnemy(BTCondition):
    """Check if enemy has been scanned"""
    
    def evaluate(self, state: GameState) -> bool:
        return state.scanned
    
    def __repr__(self):
        return "HasScannedEnemy()"


# ============================================================================
# CONDITION NODES - Status Ailments
# ============================================================================

class HasAilment(BTCondition):
    """Check if player has specific status ailment"""
    
    def __init__(self, ailment_name: str):
        self.ailment_str = ailment_name.strip()
        ailment_map = {
            "Burn": StatusAilment.BURN,
            "Freeze": StatusAilment.FREEZE,
            "Paralyze": StatusAilment.PARALYZE,
            "AttackDown": StatusAilment.ATTACK_DOWN,
            "Defending": StatusAilment.DEFENDING
        }
        self.ailment = ailment_map.get(self.ailment_str)
    
    def evaluate(self, state: GameState) -> bool:
        if not self.ailment:
            return False
        return state.has_status("player", self.ailment)
    
    def __repr__(self):
        return f"HasAilment({self.ailment_str})"


class EnemyHasBuff(BTCondition):
    """Check if enemy has specific buff"""
    
    def __init__(self, buff_name: str):
        self.buff_str = buff_name.strip()
        buff_map = {
            "RageBuff": StatusAilment.RAGE_BUFF,
            "Enrage": StatusAilment.ENRAGE,
            "StormCharge": StatusAilment.STORM_CHARGE,
            "FrostAura": StatusAilment.FROST_AURA
        }
        self.buff = buff_map.get(self.buff_str)
    
    def evaluate(self, state: GameState) -> bool:
        if not self.buff:
            return False
        return state.has_status("enemy", self.buff)
    
    def __repr__(self):
        return f"EnemyHasBuff({self.buff_str})"


class IsFrozen(BTCondition):
    """Check if player is frozen"""
    
    def evaluate(self, state: GameState) -> bool:
        return state.has_status("player", StatusAilment.FREEZE)
    
    def __repr__(self):
        return "IsFrozen()"


class IsParalyzed(BTCondition):
    """Check if player is paralyzed"""
    
    def evaluate(self, state: GameState) -> bool:
        return state.has_status("player", StatusAilment.PARALYZE)
    
    def __repr__(self):
        return "IsParalyzed()"


# ============================================================================
# CONDITION NODES - Tactical
# ============================================================================

class CanHeal(BTCondition):
    """Check if heal is available (not on cooldown and has MP)"""
    
    def evaluate(self, state: GameState) -> bool:
        return state.heal_cooldown == 0 and state.player_resources.mp >= 30
    
    def __repr__(self):
        return "CanHeal()"


class EnemyInPhase(BTCondition):
    """Check if enemy is in specific HP phase"""
    
    def __init__(self, phase: str):
        self.phase = phase.strip()
    
    def evaluate(self, state: GameState) -> bool:
        if not state.enemy:
            return False
        
        hp_pct = state.enemy.hp_percentage()
        
        if self.phase == "Healthy":
            return hp_pct > 60
        elif self.phase == "Wounded":
            return 30 < hp_pct <= 60
        elif self.phase == "Critical":
            return hp_pct <= 30
        
        return False
    
    def __repr__(self):
        return f"EnemyInPhase({self.phase})"


class EnemyIsTelegraphing(BTCondition):
    """Check if enemy is telegraphing a specific action"""
    
    def __init__(self, action: str):
        self.action = action.strip()
    
    def evaluate(self, state: GameState) -> bool:
        if not state.telegraphed_action:
            return False
        return self.action in state.telegraphed_action
    
    def __repr__(self):
        return f"EnemyIsTelegraphing({self.action})"


class IsTurnEarly(BTCondition):
    """Check if turn count is early (within threshold)"""
    
    def __init__(self, threshold: int = 3):
        self.threshold = threshold
    
    def evaluate(self, state: GameState) -> bool:
        return state.turn_count <= self.threshold
    
    def __repr__(self):
        return f"IsTurnEarly({self.threshold})"


class EnemyLastAction(BTCondition):
    """Check if enemy's last action matches specific action"""
    
    def __init__(self, action: str):
        self.action = action.strip()
    
    def evaluate(self, state: GameState) -> bool:
        if not state.last_enemy_action:
            return False
        return self.action in state.last_enemy_action
    
    def __repr__(self):
        return f"EnemyLastAction({self.action})"


class EnemyUsedRecently(BTCondition):
    """Check if enemy used specific action in recent history (last 5 turns)"""
    
    def __init__(self, action: str):
        self.action = action.strip()
    
    def evaluate(self, state: GameState) -> bool:
        if not state.action_history:
            return False
        return self.action in state.action_history
    
    def __repr__(self):
        return f"EnemyUsedRecently({self.action})"


# ============================================================================
# ACTION NODES
# ============================================================================

class Attack(BTAction):
    """Execute basic attack (free, builds TP)"""
    
    def execute(self, state: GameState) -> Optional[PlayerAction]:
        return PlayerAction.ATTACK
    
    def __repr__(self):
        return "Attack()"


class PowerStrike(BTAction):
    """Execute power strike (30 TP, high damage)"""
    
    def execute(self, state: GameState) -> Optional[PlayerAction]:
        return PlayerAction.POWER_STRIKE
    
    def __repr__(self):
        return "PowerStrike()"


class FireSpell(BTAction):
    """Execute fire spell (20 MP, fire element)"""
    
    def execute(self, state: GameState) -> Optional[PlayerAction]:
        return PlayerAction.FIRE_SPELL
    
    def __repr__(self):
        return "FireSpell()"


class IceSpell(BTAction):
    """Execute ice spell (20 MP, ice element)"""
    
    def execute(self, state: GameState) -> Optional[PlayerAction]:
        return PlayerAction.ICE_SPELL
    
    def __repr__(self):
        return "IceSpell()"


class LightningSpell(BTAction):
    """Execute lightning spell (20 MP, lightning element)"""
    
    def execute(self, state: GameState) -> Optional[PlayerAction]:
        return PlayerAction.LIGHTNING_SPELL
    
    def __repr__(self):
        return "LightningSpell()"


class Defend(BTAction):
    """Execute defend (free, -50% damage, +20 TP)"""
    
    def execute(self, state: GameState) -> Optional[PlayerAction]:
        return PlayerAction.DEFEND
    
    def __repr__(self):
        return "Defend()"


class Heal(BTAction):
    """Execute heal (30 MP, 45 HP, 3 turn cooldown)"""
    
    def execute(self, state: GameState) -> Optional[PlayerAction]:
        return PlayerAction.HEAL
    
    def __repr__(self):
        return "Heal()"


class Scan(BTAction):
    """Execute scan (15 MP, reveal enemy weakness)"""
    
    def execute(self, state: GameState) -> Optional[PlayerAction]:
        return PlayerAction.SCAN
    
    def __repr__(self):
        return "Scan()"


# ============================================================================
# Legacy Compatibility (for old BT files)
# ============================================================================

# Map old action names to new ones
LightAttack = Attack
HeavyAttack = PowerStrike

# Old condition nodes (still supported)
class IsPlayerHPLevel(BTCondition):
    """Check if player HP matches a specific level (Low/Mid/High)"""
    
    def __init__(self, level: str = "Low"):
        self.level = level.strip()
    
    def evaluate(self, state: GameState) -> bool:
        hp_pct = state.player.hp_percentage()
        
        if self.level == "Low":
            return hp_pct < 33.33
        elif self.level == "Mid":
            return 33.33 <= hp_pct < 66.67
        elif self.level == "High":
            return hp_pct >= 66.67
        
        return False
    
    def __repr__(self):
        return f"IsPlayerHPLevel({self.level})"


class IsEnemyHPLevel(BTCondition):
    """Check if enemy HP matches a specific level (Low/Mid/High)"""
    
    def __init__(self, level: str = "Low"):
        self.level = level.strip()
    
    def evaluate(self, state: GameState) -> bool:
        if not state.enemy:
            return False
        
        hp_pct = state.enemy.hp_percentage()
        
        if self.level == "Low":
            return hp_pct < 33.33
        elif self.level == "Mid":
            return 33.33 <= hp_pct < 66.67
        elif self.level == "High":
            return hp_pct >= 66.67
        
        return False
    
    def __repr__(self):
        return f"IsEnemyHPLevel({self.level})"


# ============================================================================
# FACTORY FUNCTIONS (for BT parser)
# ============================================================================

def create_condition_node(node_type: str, param: Optional[str] = None) -> BTCondition:
    """Factory function to create condition nodes from string names"""
    
    # Resource conditions
    if node_type == "HasTP":
        return HasTP(int(param) if param else 30)
    elif node_type == "HasMP":
        return HasMP(int(param) if param else 20)
    elif node_type == "IsTPLow":
        return IsTPLow(int(param) if param else 30)
    elif node_type == "IsMPLow":
        return IsMPLow(int(param) if param else 30)
    
    # HP conditions
    elif node_type == "IsPlayerHPLow":
        return IsPlayerHPLow(int(param) if param else 30)
    elif node_type == "IsPlayerHPHigh":
        return IsPlayerHPHigh(int(param) if param else 70)
    elif node_type == "IsEnemyHPLow":
        return IsEnemyHPLow(int(param) if param else 30)
    elif node_type == "IsEnemyHPHigh":
        return IsEnemyHPHigh(int(param) if param else 70)
    elif node_type == "IsPlayerHPLevel":
        return IsPlayerHPLevel(param if param else "Low")
    elif node_type == "IsEnemyHPLevel":
        return IsEnemyHPLevel(param if param else "Low")
    
    # Enemy type conditions
    elif node_type == "IsEnemy":
        return IsEnemy(param if param else "FireGolem")
    elif node_type == "EnemyWeakTo":
        return EnemyWeakTo(param if param else "Fire")
    elif node_type == "EnemyResistantTo":
        return EnemyResistantTo(param if param else "Fire")
    elif node_type == "HasScannedEnemy":
        return HasScannedEnemy()
    
    # Status ailment conditions
    elif node_type == "HasAilment":
        return HasAilment(param if param else "Burn")
    elif node_type == "EnemyHasBuff":
        return EnemyHasBuff(param if param else "RageBuff")
    elif node_type == "IsFrozen":
        return IsFrozen()
    elif node_type == "IsParalyzed":
        return IsParalyzed()
    
    # Tactical conditions
    elif node_type == "CanHeal":
        return CanHeal()
    elif node_type == "EnemyInPhase":
        return EnemyInPhase(param if param else "Healthy")
    elif node_type == "EnemyIsTelegraphing":
        return EnemyIsTelegraphing(param if param else "HeavySlam")
    elif node_type == "IsTurnEarly":
        return IsTurnEarly(int(param) if param else 3)
    elif node_type == "EnemyLastAction":
        return EnemyLastAction(param if param else "Slam")
    elif node_type == "EnemyUsedRecently":
        return EnemyUsedRecently(param if param else "RageBuff")
    
    else:
        raise ValueError(f"Unknown condition node type: {node_type}")


def create_action_node(action_type: str) -> BTAction:
    """Factory function to create action nodes from string names"""
    
    # New action names
    if action_type == "Attack":
        return Attack()
    elif action_type == "PowerStrike":
        return PowerStrike()
    elif action_type == "FireSpell":
        return FireSpell()
    elif action_type == "IceSpell":
        return IceSpell()
    elif action_type == "LightningSpell":
        return LightningSpell()
    elif action_type == "Defend":
        return Defend()
    elif action_type == "Heal":
        return Heal()
    elif action_type == "Scan":
        return Scan()
    
    # Legacy action names (backwards compatibility)
    elif action_type == "LightAttack":
        return Attack()
    elif action_type == "HeavyAttack":
        return PowerStrike()
    
    else:
        raise ValueError(f"Unknown action node type: {action_type}")


"""
Game Engine for 10-Floor Turn-Based Dungeon Crawler

This module implements the core game logic including:
- Turn-based combat system
- Player actions (Light Attack, Heavy Attack, Defend, Heal)
- Combo pattern detection and execution
- Enemy AI behaviors
- Floor progression with difficulty scaling
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum


class ActionType(Enum):
    """Player action types"""
    LIGHT_ATTACK = "LightAttack"
    HEAVY_ATTACK = "HeavyAttack"
    DEFEND = "Defend"
    HEAL = "Heal"


class CombatResult(Enum):
    """Combat outcome types"""
    CONTINUE = "continue"
    PLAYER_WIN = "player_win"
    PLAYER_DEATH = "player_death"
    FLOOR_CLEARED = "floor_cleared"
    TURN_LIMIT_EXCEEDED = "turn_limit_exceeded"


@dataclass
class CombatStats:
    """Combat statistics for player or enemy"""
    max_hp: int
    current_hp: int
    base_attack: int
    defense: int
    
    def is_alive(self) -> bool:
        return self.current_hp > 0
    
    def hp_percentage(self) -> float:
        return (self.current_hp / self.max_hp) * 100 if self.max_hp > 0 else 0
    
    def take_damage(self, damage: int) -> int:
        """Apply damage and return actual damage taken"""
        actual_damage = max(0, damage - self.defense)
        self.current_hp = max(0, self.current_hp - actual_damage)
        return actual_damage
    
    def heal(self, amount: int) -> int:
        """Heal and return actual amount healed"""
        old_hp = self.current_hp
        self.current_hp = min(self.max_hp, self.current_hp + amount)
        return self.current_hp - old_hp


@dataclass
class GameState:
    """Complete game state"""
    current_floor: int = 1
    turn_count: int = 0
    floor_turn_count: int = 0  # Turns on current floor only
    player: CombatStats = field(default_factory=lambda: CombatStats(
        max_hp=100,
        current_hp=100,
        base_attack=15,
        defense=5
    ))
    enemy: Optional[CombatStats] = None
    action_history: List[ActionType] = field(default_factory=list)
    heal_used_this_floor: bool = False  # Track if heal was used on current floor
    is_defending: bool = False  # Player is in defend stance
    used_heavy_attack_this_turn: bool = False  # Track if heavy attack was used this turn (take 2x damage immediately)
    
    def reset_for_new_floor(self, floor: int):
        """Reset state for new floor (keep player HP)"""
        self.current_floor = floor
        self.turn_count = 0
        self.floor_turn_count = 0  # Reset floor turn counter
        self.enemy = self._create_enemy_for_floor(floor)
        self.action_history = []
        self.is_defending = False
        self.heal_used_this_floor = False  # Reset heal availability for new floor
        self.used_heavy_attack_this_turn = False  # Reset heavy attack penalty
    
    def _create_enemy_for_floor(self, floor: int) -> CombatStats:
        """Create enemy with stats scaled to floor difficulty"""
        # Boss floors (5, 10) have stronger enemies
        is_boss = floor % 5 == 0
        multiplier = 1.5 if is_boss else 1.0
        
        base_hp = 50 + (floor * 10)
        base_attack = 10 + (floor * 2)
        base_defense = 2 + floor
        
        return CombatStats(
            max_hp=int(base_hp * multiplier),
            current_hp=int(base_hp * multiplier),
            base_attack=int(base_attack * multiplier),
            defense=int(base_defense * multiplier)
        )


class ComboPattern:
    """Defines a combo pattern and its effect"""
    def __init__(self, name: str, pattern: List[ActionType], damage_multiplier: float):
        self.name = name
        self.pattern = pattern
        self.damage_multiplier = damage_multiplier
    
    def matches(self, action_history: List[ActionType]) -> bool:
        """Check if recent actions match this combo pattern"""
        if len(action_history) < len(self.pattern):
            return False
        recent = action_history[-len(self.pattern):]
        return recent == self.pattern


class CombatEngine:
    """Handles combat mechanics and turn resolution"""
    
    # Define combo patterns
    COMBOS = [
        ComboPattern("Triple Light", 
                    [ActionType.LIGHT_ATTACK, ActionType.LIGHT_ATTACK, ActionType.LIGHT_ATTACK],
                    4.0),  # 4x damage on final hit
        ComboPattern("Heavy Finisher",
                    [ActionType.LIGHT_ATTACK, ActionType.LIGHT_ATTACK, ActionType.HEAVY_ATTACK],
                    3.0),  # 3x damage on heavy
        ComboPattern("Counter Strike",
                    [ActionType.DEFEND, ActionType.HEAVY_ATTACK],
                    2.5),  # 2.5x damage after defend
    ]
    
    HEAL_PERCENTAGE = 0.25  # Heal 25% of max HP
    DEFEND_DAMAGE_REDUCTION = 0.5  # Reduce damage by 50% when defending
    TURN_LIMIT = 30  # Maximum turns per floor
    
    def __init__(self, game_state: GameState):
        self.state = game_state
    
    def execute_player_action(self, action: ActionType) -> Tuple[str, int, Optional[str]]:
        """
        Execute player action and return (description, value, combo_name)
        Returns: (action description, damage/heal amount, combo triggered or None)
        """
        self.state.action_history.append(action)
        combo_triggered = None
        
        if action == ActionType.LIGHT_ATTACK:
            damage = self.state.player.base_attack
            
            # Check for combo
            for combo in self.COMBOS:
                if combo.matches(self.state.action_history):
                    damage = int(damage * combo.damage_multiplier)
                    combo_triggered = combo.name
                    break
            
            actual_damage = self.state.enemy.take_damage(damage)
            self.state.is_defending = False
            return f"Light Attack", actual_damage, combo_triggered
        
        elif action == ActionType.HEAVY_ATTACK:
            damage = int(self.state.player.base_attack * 1.5)  # 1.5x damage
            
            # Check for combo
            for combo in self.COMBOS:
                if combo.matches(self.state.action_history):
                    damage = int(damage * combo.damage_multiplier)
                    combo_triggered = combo.name
                    break
            
            actual_damage = self.state.enemy.take_damage(damage)
            self.state.is_defending = False
            self.state.used_heavy_attack_this_turn = True  # Mark for 2x damage penalty THIS turn
            return f"Heavy Attack", actual_damage, combo_triggered
        
        elif action == ActionType.DEFEND:
            # Defending reduces incoming damage by 50%
            self.state.is_defending = True
            return "Defend", 0, None
        
        elif action == ActionType.HEAL:
            if self.state.heal_used_this_floor:
                return "Heal (Failed - Already Used This Floor)", 0, None
            
            heal_amount = int(self.state.player.max_hp * self.HEAL_PERCENTAGE)
            actual_heal = self.state.player.heal(heal_amount)
            self.state.heal_used_this_floor = True
            self.state.is_defending = False
            return "Heal", actual_heal, None
        
        return "Unknown Action", 0, None
    
    def execute_enemy_turn(self) -> Tuple[str, int]:
        """
        Execute enemy AI turn
        Returns: (action description, damage dealt)
        """
        if not self.state.enemy or not self.state.enemy.is_alive():
            return "No Action", 0
        
        # Simple AI: attack more aggressively when player HP is low
        player_hp_pct = self.state.player.hp_percentage()
        enemy_hp_pct = self.state.enemy.hp_percentage()
        
        # Enemy uses heavy attack if player is low or enemy is desperate
        if player_hp_pct < 30 or enemy_hp_pct < 20:
            damage = self.state.enemy.base_attack * 2
            action = "Heavy Attack"
        else:
            damage = self.state.enemy.base_attack
            action = "Light Attack"
        
        # Apply player defense
        actual_damage = max(0, damage - self.state.player.defense)
        
        # If defending, reduce damage by 50%
        if self.state.is_defending:
            actual_damage = int(actual_damage * self.DEFEND_DAMAGE_REDUCTION)
        
        # If player used heavy attack THIS turn, take 2x damage
        if self.state.used_heavy_attack_this_turn:
            actual_damage = int(actual_damage * 2)
        
        self.state.player.current_hp = max(0, self.state.player.current_hp - actual_damage)
        
        # Reset defend state after enemy turn
        self.state.is_defending = False
        # Reset heavy attack penalty after taking the damage
        self.state.used_heavy_attack_this_turn = False
        
        return action, actual_damage
    
    def process_turn(self, player_action: ActionType) -> Tuple[CombatResult, Optional[str]]:
        """
        Process a complete turn (player then enemy)
        Returns (combat result status, combo name if triggered)
        """
        self.state.turn_count += 1
        self.state.floor_turn_count += 1
        
        # Check turn limit BEFORE processing the turn
        if self.state.floor_turn_count > self.TURN_LIMIT:
            return CombatResult.TURN_LIMIT_EXCEEDED, None
        
        # Player turn
        player_desc, player_value, combo = self.execute_player_action(player_action)
        
        # Check if enemy defeated
        if not self.state.enemy.is_alive():
            if self.state.current_floor >= 10:
                return CombatResult.PLAYER_WIN, combo
            else:
                return CombatResult.FLOOR_CLEARED, combo
        
        # Enemy turn
        enemy_desc, enemy_damage = self.execute_enemy_turn()
        
        # Check if player defeated
        if not self.state.player.is_alive():
            return CombatResult.PLAYER_DEATH, combo
        
        return CombatResult.CONTINUE, combo


class DungeonGame:
    """Main game controller for the 10-floor dungeon"""
    
    def __init__(self):
        self.state = GameState()
        self.state.reset_for_new_floor(1)
        self.engine = CombatEngine(self.state)
        self.game_over = False
        self.victory = False
    
    def take_action(self, action: ActionType) -> dict:
        """
        Execute a player action and return the result
        Returns a dict with turn information
        """
        if self.game_over:
            return {"error": "Game is over"}
        
        old_player_hp = self.state.player.current_hp
        old_enemy_hp = self.state.enemy.current_hp if self.state.enemy else 0
        
        result, combo = self.engine.process_turn(action)
        
        turn_info = {
            "floor": self.state.current_floor,
            "turn": self.state.turn_count,
            "action": action.value,
            "player_hp": self.state.player.current_hp,
            "player_hp_change": self.state.player.current_hp - old_player_hp,
            "enemy_hp": self.state.enemy.current_hp if self.state.enemy else 0,
            "enemy_hp_change": (self.state.enemy.current_hp if self.state.enemy else 0) - old_enemy_hp,
            "result": result.value,
            "combo": combo,  # Add combo info
            "game_over": False,
            "victory": False
        }
        
        # Handle combat results
        if result == CombatResult.FLOOR_CLEARED:
            next_floor = self.state.current_floor + 1
            self.state.reset_for_new_floor(next_floor)
            self.engine = CombatEngine(self.state)
            turn_info["floor_cleared"] = True
        
        elif result == CombatResult.PLAYER_WIN:
            self.game_over = True
            self.victory = True
            turn_info["game_over"] = True
            turn_info["victory"] = True
        
        elif result == CombatResult.PLAYER_DEATH:
            self.game_over = True
            self.victory = False
            turn_info["game_over"] = True
            turn_info["victory"] = False
        
        elif result == CombatResult.TURN_LIMIT_EXCEEDED:
            self.game_over = True
            self.victory = False
            turn_info["game_over"] = True
            turn_info["victory"] = False
            turn_info["defeat_reason"] = "turn_limit_exceeded"
        
        return turn_info
    
    def get_state_snapshot(self) -> dict:
        """Get current game state as a dictionary"""
        return {
            "floor": self.state.current_floor,
            "turn": self.state.turn_count,
            "player_hp": self.state.player.current_hp,
            "player_max_hp": self.state.player.max_hp,
            "enemy_hp": self.state.enemy.current_hp if self.state.enemy else 0,
            "enemy_max_hp": self.state.enemy.max_hp if self.state.enemy else 0,
            "heal_used_this_floor": self.state.heal_used_this_floor,
            "is_defending": self.state.is_defending,
            "game_over": self.game_over,
            "victory": self.victory
        }

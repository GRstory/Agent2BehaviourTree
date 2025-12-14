"""
Enhanced Combat System - RPG Maker Style

Single-floor turn-based combat with:
- 3 Element types (Fire, Ice, Lightning) with rock-paper-scissors
- 8 Player actions (2 neutral, 3 elemental, 3 support)
- 3 Distinct enemy types with unique AI patterns
- TP/MP resource management
- Status ailment system
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
from enum import Enum
import random

# Element Types
class Element(Enum):
    """Elemental types"""
    FIRE = "Fire"
    ICE = "Ice"
    NEUTRAL = "Neutral"


# Player Action Types
class PlayerAction(Enum):
    """Player action types"""
    # Neutral Attacks
    ATTACK = "Attack"
    CHARGE = "Charge"
    
    # Elemental Magic
    FIRE_SPELL = "FireSpell"
    ICE_SPELL = "IceSpell"
    
    # Support
    DEFEND = "Defend"
    HEAL = "Heal"
    SCAN = "Scan"
    CLEANSE = "Cleanse"


# Status Ailments
class StatusAilment(Enum):
    """Status ailment types"""
    BURN = "Burn"              # 10 dmg/turn, 3 turns
    FREEZE = "Freeze"          # Skip 1 turn
    PARALYZE = "Paralyze"      # 50% miss chance, 2 turns
    ATTACK_DOWN = "AttackDown" # -20% attack, 3 turns
    DEFENDING = "Defending"    # -50% damage taken, 1 turn
    RAGE_BUFF = "RageBuff"     # +40% attack, 3 turns
    ENRAGE = "Enrage"          # +50% attack, permanent
    FROST_AURA = "FrostAura"   # 30% freeze on attack, passive
    CHARGED = "Charged"        # Next attack 2x damage, 1 turn
    POWER_BOOST = "PowerBoost" # +10% damage, 1 turn


# Enemy Types
class EnemyType(Enum):
    """2 Distinct enemy types"""
    FIRE_GOLEM = "FireGolem"
    ICE_WRAITH = "IceWraith"


# Combat Result
class CombatResult(Enum):
    """Combat outcome types"""
    CONTINUE = "continue"
    PLAYER_WIN = "player_win"
    PLAYER_DEATH = "player_death"
    TURN_LIMIT = "turn_limit"


@dataclass
class StatusEffect:
    """Status effect instance"""
    ailment: StatusAilment
    duration: int
    value: int = 0  # For DoT or stat changes


@dataclass
class Resources:
    """MP resource pool"""
    mp: int = 100
    max_mp: int = 100
    mp_regen: int = 5
    
    def regenerate(self):
        """Regenerate MP per turn"""
        self.mp = min(self.max_mp, self.mp + self.mp_regen)
    
    def spend_mp(self, amount: int) -> bool:
        """Try to spend MP, return success"""
        if self.mp >= amount:
            self.mp -= amount
            return True
        return False


@dataclass
class CombatStats:
    """Combat statistics"""
    max_hp: int
    current_hp: int
    base_attack: int
    defense: int
    element: Element = Element.NEUTRAL
    
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
    turn_count: int = 0
    player: CombatStats = field(default_factory=lambda: CombatStats(
        max_hp=100,
        current_hp=100,
        base_attack=15,
        defense=6,
        element=Element.NEUTRAL
    ))
    player_resources: Resources = field(default_factory=Resources)
    player_status: List[StatusEffect] = field(default_factory=list)
    
    enemy: Optional[CombatStats] = None
    enemy_type: Optional[EnemyType] = None
    enemy_resources: Resources = field(default_factory=Resources)
    enemy_status: List[StatusEffect] = field(default_factory=list)
    
    heal_cooldown: int = 0
    scanned: bool = False
    telegraphed_action: Optional[str] = None
    
    # Action history tracking
    last_enemy_action: Optional[str] = None
    action_history: List[str] = field(default_factory=list)  # Recent 5 actions
    
    # Dynamic element system
    enemy_element_duration: int = 0  # Turns remaining for current element
    
    def has_status(self, target: str, ailment: StatusAilment) -> bool:
        """Check if target has status ailment"""
        status_list = self.player_status if target == "player" else self.enemy_status
        return any(s.ailment == ailment for s in status_list)
    
    def add_status(self, target: str, effect: StatusEffect):
        """Add status effect to target"""
        status_list = self.player_status if target == "player" else self.enemy_status
        # Remove existing same ailment
        status_list[:] = [s for s in status_list if s.ailment != effect.ailment]
        status_list.append(effect)
    
    def remove_status(self, target: str, ailment: StatusAilment):
        """Remove status effect from target"""
        status_list = self.player_status if target == "player" else self.enemy_status
        status_list[:] = [s for s in status_list if s.ailment != ailment]
    
    def tick_status_effects(self, target: str) -> List[Tuple[StatusAilment, int]]:
        """Tick down status effects, return DoT damage"""
        status_list = self.player_status if target == "player" else self.enemy_status
        damage_events = []
        
        for effect in status_list[:]:
            # Apply DoT (use effect.value for damage amount)
            if effect.ailment == StatusAilment.BURN:
                damage_amount = effect.value if effect.value > 0 else 5
                damage_events.append((StatusAilment.BURN, damage_amount))
            
            # Decrease duration
            effect.duration -= 1
            if effect.duration <= 0:
                status_list.remove(effect)
        
        return damage_events


# Elemental weakness system
ELEMENTAL_WEAKNESS = {
    Element.FIRE: Element.ICE,      # Fire weak to Ice
    Element.ICE: Element.FIRE,      # Ice weak to Fire
    Element.NEUTRAL: None
}

def calculate_elemental_multiplier(attack_element: Element, target_element: Element) -> float:
    """Calculate damage multiplier based on elemental matchup"""
    if attack_element == Element.NEUTRAL or target_element == Element.NEUTRAL:
        return 1.0
    
    # Super effective
    if ELEMENTAL_WEAKNESS.get(target_element) == attack_element:
        return 1.5
    
    # Resisted
    if ELEMENTAL_WEAKNESS.get(attack_element) == target_element:
        return 0.5
    
    # Neutral
    return 1.0


class CombatEngine:
    """Handles combat mechanics"""
    
    TURN_LIMIT = 35
    
    def __init__(self, state: GameState):
        self.state = state
    
    def execute_player_action(self, action: PlayerAction) -> Dict:
        """Execute player action and return result info"""
        result = {
            'action': action.value,
            'success': False,
            'damage': 0,
            'heal': 0,
            
            'cost_mp': 0,
            'status_applied': None,
            'message': ''
        }
        
        # Check if frozen
        if self.state.has_status("player", StatusAilment.FREEZE):
            result['message'] = "Player is frozen! Turn skipped."
            self.state.remove_status("player", StatusAilment.FREEZE)
            return result
        
        # Execute action
        if action == PlayerAction.ATTACK:
            result['success'] = True
            result['damage'] = self._calculate_damage(20, Element.NEUTRAL, "player")
            result['message'] = f"Attack dealt {result['damage']} damage"
        
        elif action == PlayerAction.CHARGE:
            if self.state.player_resources.spend_mp(15):
                result['success'] = True
                result['cost_mp'] = 15
                result['damage'] = self._calculate_damage(7, Element.NEUTRAL, "player")
                # Apply CHARGED buff for next turn
                self.state.add_status("player", StatusEffect(StatusAilment.CHARGED, 1))
                result['message'] = f"Charging! Dealt {result['damage']} damage, next attack will be doubled!"
            else:
                result['message'] = "Not enough MP!"
        
        elif action == PlayerAction.FIRE_SPELL:
            if self.state.player_resources.spend_mp(20):
                result['success'] = True
                result['cost_mp'] = 20
                result['damage'] = self._calculate_damage(10, Element.FIRE, "player")
                # 25% chance to burn
                if random.random() < 0.25:
                    self.state.add_status("enemy", StatusEffect(StatusAilment.BURN, 3, 5))
                    result['status_applied'] = "Burn"
                result['message'] = f"Fire Spell dealt {result['damage']} damage"
            else:
                result['message'] = "Not enough MP!"
        
        elif action == PlayerAction.ICE_SPELL:
            if self.state.player_resources.spend_mp(20):
                result['success'] = True
                result['cost_mp'] = 20
                result['damage'] = self._calculate_damage(14, Element.ICE, "player")
                # 25% chance to freeze
                if random.random() < 0.25:
                    self.state.add_status("enemy", StatusEffect(StatusAilment.FREEZE, 1))
                    result['status_applied'] = "Freeze"
                result['message'] = f"Ice Spell dealt {result['damage']} damage"
            else:
                result['message'] = "Not enough MP!"
        

        
        elif action == PlayerAction.DEFEND:
            result['success'] = True
            self.state.add_status("player", StatusEffect(StatusAilment.DEFENDING, 1))
            result['message'] = "Defending! Damage reduced by 50%, gained 20 TP"
        
        elif action == PlayerAction.HEAL:
            if self.state.heal_cooldown > 0:
                result['message'] = f"Heal on cooldown ({self.state.heal_cooldown} turns left)"
            elif self.state.player_resources.spend_mp(30):
                result['success'] = True
                result['cost_mp'] = 30
                result['heal'] = self.state.player.heal(45)
                self.state.heal_cooldown = 3
                result['message'] = f"Healed {result['heal']} HP"
            else:
                result['message'] = "Not enough MP!"
        
        elif action == PlayerAction.SCAN:
            if self.state.player_resources.spend_mp(15):
                result['success'] = True
                result['cost_mp'] = 15
                self.state.scanned = True
                result['message'] = f"Scanned! Enemy is {self.state.enemy_type.value} (Weak to {self._get_enemy_weakness()})"
            else:
                result['message'] = "Not enough MP!"
        
        elif action == PlayerAction.CLEANSE:
            if self.state.player_resources.spend_mp(25):
                result['success'] = True
                result['cost_mp'] = 25
                # Remove Burn and AttackDown
                removed = []
                if self.state.has_status("player", StatusAilment.BURN):
                    self.state.remove_status("player", StatusAilment.BURN)
                    removed.append("Burn")
                if self.state.has_status("player", StatusAilment.ATTACK_DOWN):
                    self.state.remove_status("player", StatusAilment.ATTACK_DOWN)
                    removed.append("AttackDown")
                # Grant Power Boost (+10% damage for 1 turn)
                self.state.add_status("player", StatusEffect(StatusAilment.POWER_BOOST, 1))
                removed_str = ", ".join(removed) if removed else "none"
                result['message'] = f"Cleansed! Removed: {removed_str}. Gained Power Boost (+10% damage)!"
            else:
                result['message'] = "Not enough MP!"
        
        # Apply damage to enemy
        if result['damage'] > 0 and self.state.enemy:
            actual_damage = self.state.enemy.take_damage(result['damage'])
            result['damage'] = actual_damage
        
        return result
    
    def _calculate_damage(self, base_damage: int, element: Element, attacker: str) -> int:
        """Calculate final damage with all modifiers"""
        damage = base_damage
        
        # Apply attacker's attack stat
        if attacker == "player":
            attack_stat = self.state.player.base_attack
            # Apply attack down debuff
            if self.state.has_status("player", StatusAilment.ATTACK_DOWN):
                attack_stat = int(attack_stat * 0.8)
            # Apply power boost
            if self.state.has_status("player", StatusAilment.POWER_BOOST):
                attack_stat = int(attack_stat * 1.1)
        else:
            attack_stat = self.state.enemy.base_attack
            # Apply enemy buffs
            if self.state.has_status("enemy", StatusAilment.RAGE_BUFF):
                attack_stat = int(attack_stat * 1.4)
            if self.state.has_status("enemy", StatusAilment.ENRAGE):
                attack_stat = int(attack_stat * 1.5)
        
        # Scale with attack stat
        damage = int(damage * (attack_stat / 15))
        
        # Apply elemental multiplier
        if attacker == "player" and self.state.enemy:
            multiplier = calculate_elemental_multiplier(element, self.state.enemy.element)
            damage = int(damage * multiplier)
        elif attacker == "enemy":
            multiplier = calculate_elemental_multiplier(element, self.state.player.element)
            damage = int(damage * multiplier)
        
        # Apply paralyze miss chance
        if attacker == "player" and self.state.has_status("player", StatusAilment.PARALYZE):
            if random.random() < 0.5:
                return 0  # Miss!
        
        return max(0, damage)
    
    def _get_enemy_weakness(self) -> str:
        """Get enemy's elemental weakness"""
        if not self.state.enemy:
            return "None"
        weakness = ELEMENTAL_WEAKNESS.get(self.state.enemy.element)
        return weakness.value if weakness else "None"
    
    def telegraph_enemy_action(self) -> str:
        """Telegraph enemy's next action (decision phase) - only heavy/special attacks"""
        if not self.state.enemy or not self.state.enemy.is_alive():
            return ""
        
        # Check if frozen - will skip turn
        if self.state.has_status("enemy", StatusAilment.FREEZE):
            self.state.telegraphed_action = "Frozen"
            return "Frozen"
        
        # Select action based on enemy type and HP
        action = self._select_enemy_action()
        
        # Only telegraph heavy attacks and special abilities
        TELEGRAPHED_ACTIONS = [
            'HeavySlam', 'ThunderStrike', 'StormCharge',  # Heavy attacks
            'RageBuff', 'Heal', 'Debuff', 'FrostAura'      # Special abilities
        ]
        
        if action in TELEGRAPHED_ACTIONS:
            self.state.telegraphed_action = action
        else:
            self.state.telegraphed_action = None  # Normal attacks are hidden
        
        return action
    
    def execute_enemy_turn(self) -> Dict:
        """Execute enemy's previously telegraphed action"""
        result = {
            'action': '',
            'damage': 0,
            'heal': 0,
            'status_applied': None,
            'message': '',
            'telegraphed': None
        }
        
        if not self.state.enemy or not self.state.enemy.is_alive():
            return result
        
        # Check if frozen
        if self.state.has_status("enemy", StatusAilment.FREEZE):
            result['message'] = "Enemy is frozen! Turn skipped."
            self.state.remove_status("enemy", StatusAilment.FREEZE)
            self.state.telegraphed_action = None
            return result
        
        # Use previously telegraphed action
        action = self.state.telegraphed_action if self.state.telegraphed_action else self._select_enemy_action()
        result['action'] = action
        
        # Execute action based on enemy type
        if self.state.enemy_type == EnemyType.FIRE_GOLEM:
            result = self._execute_fire_golem_action(action)
        elif self.state.enemy_type == EnemyType.ICE_WRAITH:
            result = self._execute_ice_wraith_action(action)

        # Apply damage to player
        if result['damage'] > 0:
            # Apply defending reduction
            if self.state.has_status("player", StatusAilment.DEFENDING):
                result['damage'] = int(result['damage'] * 0.5)
                result['message'] += " (Reduced by Defend!)"
            
            actual_damage = self.state.player.take_damage(result['damage'])
            result['damage'] = actual_damage
            
            # FireGolem lifesteal: heal based on actual damage dealt (after defense)
            if self.state.enemy_type == EnemyType.FIRE_GOLEM and actual_damage > 0:
                hp_pct = self.state.enemy.hp_percentage()
                lifesteal_rate = 0.20 if hp_pct >= 50 else 0.10
                heal_amount = int(actual_damage * lifesteal_rate)
                if heal_amount > 0:
                    result['heal'] = self.state.enemy.heal(heal_amount)
                    result['message'] += f" [Lifesteal: {result['heal']} HP!]"
        
        # Apply Frost Aura freeze chance
        if self.state.enemy_type == EnemyType.ICE_WRAITH:
            if self.state.has_status("enemy", StatusAilment.FROST_AURA):
                if random.random() < 0.3:
                    self.state.add_status("player", StatusEffect(StatusAilment.FREEZE, 1))
                    result['status_applied'] = "Freeze (Frost Aura)"
        
        # Record action in history
        if action:
            self.state.last_enemy_action = action
            self.state.action_history.append(action)
            # Keep only recent 5 actions
            if len(self.state.action_history) > 5:
                self.state.action_history.pop(0)
        
        # Clear telegraphed action after execution
        self.state.telegraphed_action = None
        
        return result
    
    def _select_enemy_action(self) -> str:
        """Select enemy action based on type and HP phase"""
        hp_pct = self.state.enemy.hp_percentage()
        
        if self.state.enemy_type == EnemyType.FIRE_GOLEM:
            if hp_pct >= 50:
                # Phase 1 (HP >= 50%): Neutral attacks only
                return random.choices(
                    ["Slam", "HeavySlam"],
                    weights=[60, 40]
                )[0]
            else:
                # Phase 2 (HP < 50%): Fire element + FireSpell
                # Activate permanent Fire element if not already
                if self.state.enemy and self.state.enemy.element != Element.FIRE:
                    self.state.enemy.element = Element.FIRE
                    self.state.enemy_element_duration = 999  # Permanent
                
                return random.choices(
                    ["FireSpell", "HeavySlam"],
                    weights=[70, 30]
                )[0]
        
        elif self.state.enemy_type == EnemyType.ICE_WRAITH:
            # Phase 1 (HP > 60%): Only IceSpell and FrostTouch, no Debuff
            if hp_pct > 60:
                return random.choices(
                    ["IceSpell", "FrostTouch"],
                    weights=[60, 40]
                )[0]
            # Phase 2 (30% < HP <= 60%): FrostTouch + 20% Debuff
            elif hp_pct > 30:
                return random.choices(
                    ["FrostTouch", "Debuff"],
                    weights=[80, 20]
                )[0]
            # Phase 3 (HP <= 30%): IceSpell, FrostTouch, Debuff
            else:
                return random.choices(
                    ["IceSpell", "FrostTouch", "Debuff"],
                    weights=[45, 35, 20]
                )[0]
        
        return "Slam"
    
    def _execute_fire_golem_action(self, action: str) -> Dict:
        """Execute Fire Golem specific action"""
        result = {'action': action, 'damage': 0, 'heal': 0, 'status_applied': None, 'message': '', 'telegraphed': None}
        
        if action == "Slam":
            if self.state.enemy_resources.spend_mp(10):
                result['damage'] = self._calculate_damage(21, Element.NEUTRAL, "enemy")
                result['message'] = f"Enemy slams for {result['damage']} damage"
        
        elif action == "HeavySlam":
            if self.state.enemy_resources.spend_mp(30):
                result['damage'] = self._calculate_damage(45, Element.NEUTRAL, "enemy")
                result['message'] = f"Enemy heavy slams for {result['damage']} damage"
                result['telegraphed'] = "Enemy raises its fists!"
        
        elif action == "FireSpell":
            if self.state.enemy_resources.spend_mp(20):
                result['damage'] = self._calculate_damage(15, Element.FIRE, "enemy")
                result['message'] = f"Enemy casts Fire Spell for {result['damage']} damage"
                # Apply Burn DoT (10 dmg/turn for 3 turns)
                self.state.add_status("player", StatusEffect(StatusAilment.BURN, 3, 10))
                result['status_applied'] = "Burn"
                result['message'] += " [Burn: 10 dmg/turn for 3 turns!]"
        
        return result
    
    def _execute_ice_wraith_action(self, action: str) -> Dict:
        """Execute Ice Wraith specific action"""
        result = {'action': action, 'damage': 0, 'heal': 0, 'status_applied': None, 'message': '', 'telegraphed': None}
        
        if action == "FrostTouch":
            if self.state.enemy_resources.spend_mp(10):
                result['damage'] = self._calculate_damage(18, Element.NEUTRAL, "enemy")
                result['message'] = f"Enemy touches for {result['damage']} damage"
        
        elif action == "IceSpell":
            if self.state.enemy_resources.spend_mp(20):
                result['damage'] = self._calculate_damage(28, Element.ICE, "enemy")
                result['message'] = f"Enemy casts Ice Spell for {result['damage']} damage"
                # IceSpell grants Ice element (3 turns)
                if self.state.enemy:
                    self.state.enemy.element = Element.ICE
                    self.state.enemy_element_duration = 3
                    result['message'] += " [Gained ICE element!]"
                # 25% freeze chance
                if random.random() < 0.25:
                    self.state.add_status("player", StatusEffect(StatusAilment.FREEZE, 1))
                    result['status_applied'] = "Freeze"
        
        elif action == "Heal":
            if self.state.enemy_resources.spend_mp(30):
                result['heal'] = self.state.enemy.heal(40)
                result['message'] = f"Enemy heals {result['heal']} HP"
        
        elif action == "Debuff":
            if self.state.enemy_resources.spend_mp(20):
                self.state.add_status("player", StatusEffect(StatusAilment.ATTACK_DOWN, 3))
                result['status_applied'] = "Attack Down"
                result['message'] = "Enemy curses you! Attack -20% for 3 turns"
        
        return result
    
    def process_turn(self, player_action: PlayerAction) -> Tuple[CombatResult, Dict, Dict]:
        """Process complete turn with telegraph-first order"""
        self.state.turn_count += 1
        
        # Check turn limit
        if self.state.turn_count > self.TURN_LIMIT:
            return CombatResult.TURN_LIMIT, {}, {}
        
        # Decrease heal cooldown
        if self.state.heal_cooldown > 0:
            self.state.heal_cooldown -= 1
        
        # Regenerate resources
        self.state.player_resources.regenerate()
        self.state.enemy_resources.regenerate()
        
        # Tick status effects
        player_dots = self.state.tick_status_effects("player")
        enemy_dots = self.state.tick_status_effects("enemy")
        
        # Tick down enemy element duration
        if self.state.enemy_element_duration > 0:
            self.state.enemy_element_duration -= 1
            if self.state.enemy_element_duration == 0:
                # Element expired, return to Neutral
                if self.state.enemy:
                    self.state.enemy.element = Element.NEUTRAL
        
        # Apply DoT damage (bypasses defense)
        for ailment, damage in player_dots:
            self.state.player.current_hp = max(0, self.state.player.current_hp - damage)
        for ailment, damage in enemy_dots:
            self.state.enemy.current_hp = max(0, self.state.enemy.current_hp - damage)
        
        # Player turn (reacts to telegraphed action from previous turn)
        player_result = self.execute_player_action(player_action)
        
        # Check if enemy defeated
        if not self.state.enemy.is_alive():
            return CombatResult.PLAYER_WIN, player_result, {}
        
        # Enemy turn (executes previously telegraphed action)
        enemy_result = self.execute_enemy_turn()
        
        # Check if player defeated
        if not self.state.player.is_alive():
            return CombatResult.PLAYER_DEATH, player_result, enemy_result
        
        # Remove defending status after enemy turn
        self.state.remove_status("player", StatusAilment.DEFENDING)
        
        # Telegraph enemy's NEXT action (for next turn)
        if self.state.enemy and self.state.enemy.is_alive():
            self.telegraph_enemy_action()
        
        return CombatResult.CONTINUE, player_result, enemy_result


def create_enemy(enemy_type: EnemyType) -> CombatStats:
    """Create enemy with type-specific stats"""
    if enemy_type == EnemyType.ICE_WRAITH:
        defense = 8
        max_hp = 200
    elif enemy_type == EnemyType.FIRE_GOLEM:
        defense = 5
        max_hp = 180
        base_attack = 17
    else:
        defense = 6
        max_hp = 180
    
    base_attack_value = base_attack if enemy_type == EnemyType.FIRE_GOLEM else 15
    
    return CombatStats(
        max_hp=max_hp,
        current_hp=max_hp,
        base_attack=base_attack_value,
        defense=defense,
        element=Element.NEUTRAL  # Always starts Neutral!
    )


class DungeonGame:
    """Main game controller for single-floor combat"""
    
    def __init__(self, enemy_type: Optional[EnemyType] = None):
        self.state = GameState()
        
        # Select random enemy if not specified
        if enemy_type is None:
            enemy_type = random.choice(list(EnemyType))
        
        self.state.enemy_type = enemy_type
        self.state.enemy = create_enemy(enemy_type)
        
        # Set enemy resources based on type
        if enemy_type == EnemyType.FIRE_GOLEM:
            self.state.enemy_resources = Resources(mp=40, max_mp=40, mp_regen=8)
        elif enemy_type == EnemyType.ICE_WRAITH:
            self.state.enemy_resources = Resources(mp=100, max_mp=100, mp_regen=15)
        
        self.engine = CombatEngine(self.state)
        self.game_over = False
        self.victory = False
    
    def take_action(self, action: PlayerAction) -> dict:
        """Execute player action and return result"""
        if self.game_over:
            return {"error": "Game is over"}
        
        result, player_info, enemy_info = self.engine.process_turn(action)
        
        turn_info = {
            "turn": self.state.turn_count,
            "action": action.value,
            "player_hp": self.state.player.current_hp,
            "enemy_hp": self.state.enemy.current_hp if self.state.enemy else 0,
            "player_info": player_info,
            "enemy_info": enemy_info,
            "result": result.value,
            "game_over": False,
            "victory": False
        }
        
        if result == CombatResult.PLAYER_WIN:
            self.game_over = True
            self.victory = True
            turn_info["game_over"] = True
            turn_info["victory"] = True
        elif result == CombatResult.PLAYER_DEATH:
            self.game_over = True
            self.victory = False
            turn_info["game_over"] = True
            turn_info["victory"] = False
        elif result == CombatResult.TURN_LIMIT:
            self.game_over = True
            self.victory = False
            turn_info["game_over"] = True
            turn_info["victory"] = False
            turn_info["defeat_reason"] = "turn_limit_exceeded"
        
        return turn_info
    
    def get_state_snapshot(self) -> dict:
        """Get current game state as dictionary"""
        return {
            "turn": self.state.turn_count,
            "player_hp": self.state.player.current_hp,
            "player_max_hp": self.state.player.max_hp,
            "player_tp": self.state.player_resources.tp,
            "player_mp": self.state.player_resources.mp,
            "enemy_hp": self.state.enemy.current_hp if self.state.enemy else 0,
            "enemy_max_hp": self.state.enemy.max_hp if self.state.enemy else 0,
            "enemy_type": self.state.enemy_type.value if self.state.enemy_type else "None",
            "scanned": self.state.scanned,
            "game_over": self.game_over,
            "victory": self.victory
        }


# For backwards compatibility with old ActionType
ActionType = PlayerAction

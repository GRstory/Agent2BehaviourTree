"""
Abstract Logger for LLM-Friendly Game Logs

Converts numerical game data into abstract, natural language descriptions
that are easier for LLMs to understand and analyze.
"""

from typing import List, Dict, Any
from .game_engine import ActionType, GameState, CombatStats


class AbstractionLevel(str):
    """Abstract level descriptors for numerical values"""
    CRITICAL = "Critical"
    VERY_LOW = "Very Low"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    VERY_HIGH = "Very High"
    FULL = "Full"


class AbstractLogger:
    """Converts game events to abstract, LLM-friendly logs"""
    
    def __init__(self):
        self.logs: List[str] = []  # All logs (for debugging)
        self.current_stage_logs: List[str] = []  # Only current stage logs (for LLM)
        self.stage_history: Dict[int, str] = {}  # History of logs per floor
        self.previous_state: Dict[str, Any] = {}
        self.current_floor: int = 1
    
    def start_new_stage(self, floor: int):
        """Start a new stage (floor), clearing previous stage logs"""
        # Save previous stage log if it exists
        if self.current_stage_logs:
            self.stage_history[self.current_floor] = "".join(self.current_stage_logs)
            
        self.current_floor = floor
        self.current_stage_logs = []  # Clear for new stage
    
    def _add_log(self, log_entry: str):
        """Add log entry to both full logs and current stage logs"""
        self.logs.append(log_entry)
        self.current_stage_logs.append(log_entry)
    
    @staticmethod
    def abstract_hp(current: int, maximum: int) -> str:
        """Convert HP to abstract level (Low/Mid/High)"""
        percentage = (current / maximum) * 100 if maximum > 0 else 0
        
        if percentage >= 66.67:
            return "High"  # 66-100%
        elif percentage >= 33.33:
            return "Mid"   # 33-66%
        else:
            return "Low"   # 0-33%
    
    @staticmethod
    def abstract_damage(damage: int, target_max_hp: int) -> str:
        """Convert damage amount to abstract level"""
        percentage = (damage / target_max_hp) * 100 if target_max_hp > 0 else 0
        
        if percentage >= 40:
            return "Massive"
        elif percentage >= 25:
            return "Heavy"
        elif percentage >= 15:
            return "Medium"
        elif percentage >= 5:
            return "Light"
        else:
            return "Minimal"
    
    @staticmethod
    def get_hp_trend(old_hp: int, new_hp: int) -> str:
        """Describe HP change trend"""
        if new_hp > old_hp:
            return "increased"
        elif new_hp < old_hp:
            return "decreased"
        else:
            return "unchanged"
    
    def log_turn_start(self, state: GameState):
        """Log the start of a turn"""
        floor_type = "BOSS FLOOR" if state.current_floor % 5 == 0 else f"Floor {state.current_floor}"
        
        log_entry = f"\n{'='*60}\n"
        log_entry += f"[{floor_type}] Turn {state.turn_count}\n"
        log_entry += f"{'='*60}\n"
        
        # Player status
        player_hp_level = self.abstract_hp(state.player.current_hp, state.player.max_hp)
        log_entry += f"Player HP: {player_hp_level}"
        
        if self.previous_state.get('player_hp'):
            old_hp = self.previous_state['player_hp']
            trend = self.get_hp_trend(old_hp, state.player.current_hp)
            if trend != "unchanged":
                old_level = self.abstract_hp(old_hp, state.player.max_hp)
                log_entry += f" (was {old_level}, {trend})"
        log_entry += "\n"
        
        # Enemy status
        if state.enemy:
            enemy_hp_level = self.abstract_hp(state.enemy.current_hp, state.enemy.max_hp)
            log_entry += f"Enemy HP: {enemy_hp_level}"
            
            if self.previous_state.get('enemy_hp'):
                old_hp = self.previous_state['enemy_hp']
                trend = self.get_hp_trend(old_hp, state.enemy.current_hp)
                if trend != "unchanged":
                    old_level = self.abstract_hp(old_hp, state.enemy.max_hp)
                    log_entry += f" (was {old_level}, {trend})"
            log_entry += "\n"
        
        # Special status
        if state.is_defending:
            log_entry += "Status: DEFENDING (increased defense)\n"
        
        if state.heal_cooldown > 0:
            log_entry += f"Heal Cooldown: {state.heal_cooldown} turn(s) remaining\n"
        else:
            log_entry += "Heal: READY\n"
        
        self._add_log(log_entry)
    
    def log_player_action(self, action: ActionType, value: int, combo: str, state: GameState):
        """Log player action with abstract descriptions"""
        log_entry = f"\n>>> Player Action: {action.value}\n"
        
        if action in [ActionType.LIGHT_ATTACK, ActionType.HEAVY_ATTACK]:
            damage_level = self.abstract_damage(value, state.enemy.max_hp)
            log_entry += f"Result: Hit! Enemy took {damage_level} damage\n"
            
            if combo:
                log_entry += f"[COMBO] {combo} ACTIVATED!\n"
            
            # Tactical observations
            enemy_hp_pct = state.enemy.hp_percentage()
            if enemy_hp_pct < 20:
                log_entry += "Observation: Enemy is nearly defeated!\n"
            elif enemy_hp_pct < 40:
                log_entry += "Observation: Enemy is vulnerable, press the advantage\n"
            
            # Check if close to combo
            recent_actions = state.action_history[-2:] if len(state.action_history) >= 2 else []
            if recent_actions == [ActionType.LIGHT_ATTACK, ActionType.LIGHT_ATTACK]:
                log_entry += "Hint: One more Light Attack will trigger Triple Light combo (4x damage)!\n"
            elif recent_actions == [ActionType.LIGHT_ATTACK, ActionType.LIGHT_ATTACK]:
                log_entry += "Hint: Heavy Attack now will trigger Heavy Finisher combo (3x damage)!\n"
            elif state.is_defending:
                log_entry += "Hint: Heavy Attack after Defend triggers Counter Strike combo (2.5x damage)!\n"
        
        elif action == ActionType.DEFEND:
            log_entry += f"Result: Defense increased by {value}\n"
            log_entry += "Observation: Prepared to reduce incoming damage\n"
        
        elif action == ActionType.HEAL:
            if value > 0:
                heal_level = self.abstract_damage(value, state.player.max_hp)
                log_entry += f"Result: Restored {heal_level} amount of HP\n"
                
                player_hp_pct = state.player.hp_percentage()
                if player_hp_pct > 80:
                    log_entry += "Warning: Heal may have been wasted (HP already high)\n"
            else:
                log_entry += "Result: FAILED - Heal is on cooldown!\n"
                log_entry += f"Warning: Wasted turn! Heal available in {state.heal_cooldown} turn(s)\n"
        
        self._add_log(log_entry)
    
    def log_enemy_action(self, action: str, damage: int, state: GameState):
        """Log enemy action with abstract descriptions"""
        log_entry = f"\n<<< Enemy Action: {action}\n"
        
        if damage > 0:
            damage_level = self.abstract_damage(damage, state.player.max_hp)
            log_entry += f"Result: Player took {damage_level} damage\n"
            
            # Tactical observations
            player_hp_pct = state.player.hp_percentage()
            if player_hp_pct < 20:
                log_entry += "[WARNING] Player HP is CRITICAL!\n"
            elif player_hp_pct < 35:
                log_entry += "Caution: Player HP is getting low, consider healing or defending\n"
        else:
            log_entry += "Result: Attack blocked! (No damage taken)\n"
            log_entry += "Observation: Defending was effective\n"
        
        self._add_log(log_entry)
    
    def log_floor_cleared(self, floor: int):
        """Log floor completion"""
        log_entry = f"\n{'*'*60}\n"
        log_entry += f"[CLEARED] FLOOR {floor} CLEARED!\n"
        log_entry += f"{'*'*60}\n"
        self._add_log(log_entry)
    
    def log_game_over(self, victory: bool, final_floor: int, defeat_reason: str = None):
        """Log game end"""
        log_entry = f"\n{'='*60}\n"
        if victory:
            log_entry += "[VICTORY] All 10 floors cleared!\n"
        else:
            if defeat_reason == "turn_limit_exceeded":
                log_entry += f"[DEFEAT] on Floor {final_floor} - TURN LIMIT EXCEEDED\n"
                log_entry += f"\n[CRITICAL FAILURE] The battle took more than 30 turns!\n"
                log_entry += "This indicates the strategy was too slow or inefficient.\n"
                log_entry += "The agent failed to defeat the enemy quickly enough.\n"
            else:
                log_entry += f"[DEFEAT] on Floor {final_floor}\n"
        log_entry += f"{'='*60}\n"
        self._add_log(log_entry)
        
        # Save final stage log
        if self.current_stage_logs:
            self.stage_history[self.current_floor] = "".join(self.current_stage_logs)
    
    def update_state_snapshot(self, state: GameState):
        """Update previous state for comparison"""
        self.previous_state = {
            'player_hp': state.player.current_hp,
            'enemy_hp': state.enemy.current_hp if state.enemy else 0,
        }
    
    def get_full_log(self) -> str:
        """Get complete log as a single string"""
        return "".join(self.logs)
    
    def get_last_stage_log(self) -> str:
        """Get only the last stage (floor) log for LLM analysis"""
        return "".join(self.current_stage_logs)
    
    def get_stage_history(self) -> Dict[int, str]:
        """Get history of logs for all stages"""
        return self.stage_history
    
    def get_recent_log(self, num_entries: int = 5) -> str:
        """Get recent log entries"""
        return "".join(self.logs[-num_entries:])
    
    def clear_logs(self):
        """Clear all logs"""
        self.logs = []
        self.current_stage_logs = []
        self.stage_history = {}
        self.previous_state = {}
    
    def generate_summary(self, state: GameState, total_turns: int) -> str:
        """Generate a tactical summary of the game"""
        summary = "\n" + "="*60 + "\n"
        summary += "TACTICAL SUMMARY\n"
        summary += "="*60 + "\n\n"
        
        if state.current_floor > 1:
            summary += f"Floors Cleared: {state.current_floor - 1}\n"
        else:
            summary += "Floors Cleared: 0 (Died on first floor)\n"
        
        summary += f"Total Turns: {total_turns}\n"
        
        player_hp_level = self.abstract_hp(state.player.current_hp, state.player.max_hp)
        summary += f"Final Player HP: {player_hp_level}\n\n"
        
        # Analyze action history
        if state.action_history:
            action_counts = {}
            for action in state.action_history:
                action_counts[action.value] = action_counts.get(action.value, 0) + 1
            
            summary += "Action Distribution:\n"
            for action, count in sorted(action_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(state.action_history)) * 100
                summary += f"  - {action}: {count} times ({percentage:.1f}%)\n"
        
        summary += "\n" + "="*60 + "\n"
        
        return summary

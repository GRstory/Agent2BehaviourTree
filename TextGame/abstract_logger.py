"""
Abstract Logger for Enhanced Combat System - Simplified

Compact logging with minimal redundancy for LLM analysis.
"""

from typing import List, Dict, Any, Optional
from .game_engine import PlayerAction, GameState, Element, EnemyType


class AbstractLogger:
    """Converts game events to compact, LLM-friendly logs"""
    
    def __init__(self):
        self.logs: List[str] = []
        self.turn_logs: List[str] = []
        self.combat_start_state: Optional[Dict] = None
    
    def start_combat(self, state: GameState):
        """Log combat start - enemy info only once"""
        self.logs = []
        self.turn_logs = []
        
        log = f"=== COMBAT START ===\n"
        log += f"Enemy: {state.enemy_type.value if state.enemy_type else 'None'} ({state.enemy.element.value if state.enemy else 'None'})\n"
        log += f"Player: {state.player.current_hp} HP\n"
        log += f"Enemy: {state.enemy.current_hp if state.enemy else 0} HP\n\n"
        
        self.logs.append(log)
    
    def log_turn_start(self, state: GameState):
        """Log turn start - compact format"""
        log = f"=== TURN {state.turn_count} ===\n"
        
        # Show enemy's telegraphed action (if any)
        if state.telegraphed_action:
            log += f"[!] ENEMY TELEGRAPHS: {state.telegraphed_action}\n"
        
        # Compact player status
        hp_pct = int(state.player.hp_percentage())
        log += f"Player: HP {hp_pct}%, TP {state.player_resources.tp}, MP {state.player_resources.mp}"
        
        if state.player_status:
            ailments = [s.ailment.value for s in state.player_status]
            log += f", Ailments: {', '.join(ailments)}"
        log += "\n"
        
        # Compact enemy status
        if state.enemy:
            enemy_hp_pct = int(state.enemy.hp_percentage())
            element_str = state.enemy.element.value
            if state.enemy_element_duration > 0:
                log += f"Enemy: HP {enemy_hp_pct}%, Element: {element_str} ({state.enemy_element_duration} turns)"
            else:
                log += f"Enemy: HP {enemy_hp_pct}%, Element: {element_str}"
            
            if state.enemy_status:
                buffs = [s.ailment.value for s in state.enemy_status]
                log += f", Buffs: {', '.join(buffs)}"
            log += "\n"
        
        log += "\n"
        self.turn_logs.append(log)
    
    def log_player_action(self, action: PlayerAction, result: Dict, state: GameState):
        """Log player action - one line"""
        log = f"Action: {action.value}"
        
        # Cost
        if result.get('cost_tp', 0) > 0:
            log += f" (TP -{result['cost_tp']})"
        if result.get('cost_mp', 0) > 0:
            log += f" (MP -{result['cost_mp']})"
        
        # Damage
        if result.get('damage', 0) > 0:
            damage = result['damage']
            log += f" -> {damage} dmg"
            
            # Elemental effectiveness
            if action in [PlayerAction.FIRE_SPELL, PlayerAction.ICE_SPELL, PlayerAction.LIGHTNING_SPELL]:
                element = self._get_action_element(action)
                if state.enemy:
                    multiplier = self._get_elemental_multiplier(element, state.enemy.element)
                    if multiplier == 1.5:
                        log += " [SUPER EFFECTIVE!]"
                    elif multiplier == 0.5:
                        log += " [Not effective]"
        
        # Heal
        if result.get('heal', 0) > 0:
            log += f" -> Healed {result['heal']} HP"
        
        # Status
        if result.get('status_applied'):
            log += f" [{result['status_applied']}]"
        
        log += "\n"
        self.turn_logs.append(log)
    
    def log_enemy_action(self, result: Dict, state: GameState):
        """Log enemy action - one line"""
        log = f"Enemy: {result.get('action', 'None')}"
        
        if result.get('damage', 0) > 0:
            log += f" -> {result['damage']} dmg"
        
        if result.get('heal', 0) > 0:
            log += f" -> Healed {result['heal']} HP"
        
        if result.get('telegraphed'):
            log += f" [TELEGRAPH: {result['telegraphed']}]"
        
        log += "\n\n"
        self.turn_logs.append(log)
    
    def log_turn_end(self, state: GameState):
        """Log turn end summary"""
        # Removed - redundant
        pass
    
    def generate_summary(self, state: GameState, victory: bool, total_turns: int) -> str:
        """Generate combat summary - pure statistics only"""
        summary = "=== COMBAT SUMMARY ===\n\n"
        
        # Result
        summary += f"Result: {'VICTORY' if victory else 'DEFEAT'}\n"
        summary += f"Turns: {total_turns}\n"
        summary += f"Final Player HP: {state.player.current_hp}/{state.player.max_hp} ({int(state.player.hp_percentage())}%)\n"
        if state.enemy:
            summary += f"Final Enemy HP: {state.enemy.current_hp}/{state.enemy.max_hp} ({int(state.enemy.hp_percentage())}%)\n"
        summary += "\n"
        
        # Enemy info (only once)
        if state.enemy_type:
            summary += f"Enemy: {state.enemy_type.value} ({state.enemy.element.value})\n"
            if state.scanned:
                weakness = self._get_weakness_element(state.enemy.element)
                summary += f"Weakness: {weakness} (scanned)\n"
            else:
                summary += f"Weakness: Unknown (not scanned)\n"
            summary += "\n"
        
        # Resource usage
        summary += f"Resources Remaining: TP {state.player_resources.tp}/{state.player_resources.max_tp}, MP {state.player_resources.mp}/{state.player_resources.max_mp}\n"
        
        return summary
    
    def get_full_log(self) -> str:
        """Get complete combat log"""
        return "".join(self.logs) + "".join(self.turn_logs)
    
    def get_turn_log(self) -> str:
        """Get current turn log"""
        return "".join(self.turn_logs)
    
    def generate_critic_log(self, state: GameState, victory: bool, total_turns: int) -> str:
        """Generate log for Critic LLM - hints without answers"""
        log = "=== COMBAT LOG FOR ANALYSIS ===\n\n"
        
        # Add turn-by-turn hints
        log += self.get_full_log()
        
        # Add pattern analysis hints (not in regular log)
        log += "\n=== PATTERN ANALYSIS HINTS ===\n\n"
        
        # Enemy action history
        if state.action_history:
            log += f"Enemy Action History (last 5): {', '.join(state.action_history)}\n"
        
        if state.last_enemy_action:
            log += f"Enemy Last Action: {state.last_enemy_action}\n"
        
        # Element changes (without telling when to exploit)
        log += f"\nFinal Enemy Element: {state.enemy.element.value if state.enemy else 'None'}\n"
        if state.enemy_element_duration > 0:
            log += f"Element Duration Remaining: {state.enemy_element_duration} turns\n"
        
        log += "\n"
        
        # Add summary
        log += self.generate_summary(state, victory, total_turns)
        
        return log
    
    # Helper methods
    
    @staticmethod
    def _get_weakness_element(enemy_element: Element) -> str:
        """Get element that enemy is weak to"""
        from .game_engine import ELEMENTAL_WEAKNESS
        weakness = ELEMENTAL_WEAKNESS.get(enemy_element)
        return weakness.value if weakness else "None"
    
    @staticmethod
    def _get_action_element(action: PlayerAction) -> Element:
        """Get element of player action"""
        if action == PlayerAction.FIRE_SPELL:
            return Element.FIRE
        elif action == PlayerAction.ICE_SPELL:
            return Element.ICE
        elif action == PlayerAction.LIGHTNING_SPELL:
            return Element.LIGHTNING
        else:
            return Element.NEUTRAL
    
    @staticmethod
    def _get_elemental_multiplier(attack_element: Element, target_element: Element) -> float:
        """Get damage multiplier for elemental matchup"""
        from .game_engine import calculate_elemental_multiplier
        return calculate_elemental_multiplier(attack_element, target_element)

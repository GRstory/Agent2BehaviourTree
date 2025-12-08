"""
Test skill-based dynamic element system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from TextGame.game_engine import DungeonGame, PlayerAction, EnemyType
from TextGame.abstract_logger import AbstractLogger

# Create game
game = DungeonGame(enemy_type=EnemyType.FIRE_GOLEM)
logger = AbstractLogger()

logger.start_combat(game.state)

# Pre-telegraph first action
if game.state.enemy:
    game.engine.telegraph_enemy_action()

print("Testing Skill-Based Dynamic Element System\n")
print("="*70)

# Run 10 turns
for turn in range(1, 11):
    logger.log_turn_start(game.state)
    
    # Simple strategy: use IceSpell when enemy has Fire element
    if game.state.enemy and game.state.enemy.element.value == "Fire":
        action = PlayerAction.ICE_SPELL
        print(f"Turn {turn}: Enemy is FIRE! Using IceSpell (1.5x damage)")
    else:
        action = PlayerAction.ATTACK
        print(f"Turn {turn}: Enemy is Neutral, using Attack")
    
    # Execute turn
    result = game.take_action(action)
    
    logger.log_player_action(action, result['player_info'], game.state)
    logger.log_enemy_action(result['enemy_info'], game.state)
    
    if game.game_over:
        print(f"\n{'='*70}")
        print(f"GAME OVER - {'VICTORY' if game.victory else 'DEFEAT'}")
        break

print(f"\n{'='*70}")
print("\nFull Combat Log:")
print(logger.get_full_log())
print(logger.generate_summary(game.state, game.victory, game.state.turn_count))

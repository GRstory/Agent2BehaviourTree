"""
Test critic log generation
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

# Run 5 turns
for turn in range(1, 6):
    logger.log_turn_start(game.state)
    
    # Simple strategy
    if game.state.enemy and game.state.enemy.element.value == "Fire":
        action = PlayerAction.ICE_SPELL
    else:
        action = PlayerAction.ATTACK
    
    result = game.take_action(action)
    
    logger.log_player_action(action, result['player_info'], game.state)
    logger.log_enemy_action(result['enemy_info'], game.state)
    
    if game.game_over:
        break

# Generate critic log
critic_log = logger.generate_critic_log(game.state, game.victory, game.state.turn_count)

print("="*70)
print("CRITIC LOG (What Critic LLM sees)")
print("="*70)
print(critic_log)

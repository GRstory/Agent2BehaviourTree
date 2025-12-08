"""
Test telegraph system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from TextGame.game_engine import DungeonGame, PlayerAction, EnemyType
from TextGame.abstract_logger import AbstractLogger
from TextGame.bt_executor import create_bt_executor_from_dsl

# Load manual BT
with open('examples/manual.txt', 'r', encoding='utf-8') as f:
    bt_dsl = f.read()

# Create game
game = DungeonGame(enemy_type=EnemyType.FIRE_GOLEM)
logger = AbstractLogger()
executor = create_bt_executor_from_dsl(bt_dsl)

logger.start_combat(game.state)

# Pre-telegraph first action
if game.state.enemy:
    game.engine.telegraph_enemy_action()

# Run 3 turns
for turn in range(1, 4):
    print(f"\n{'='*70}")
    print(f"TURN {turn}")
    print(f"{'='*70}")
    
    # Show telegraph
    if game.state.telegraphed_action:
        print(f"[!] ENEMY TELEGRAPHS: {game.state.telegraphed_action}")
    
    # Show state
    print(f"Player HP: {game.state.player.current_hp}/{game.state.player.max_hp}")
    print(f"Enemy HP: {game.state.enemy.current_hp}/{game.state.enemy.max_hp}")
    print(f"Player TP: {game.state.player_resources.tp}, MP: {game.state.player_resources.mp}")
    
    # Execute BT
    action = executor.execute(game.state)
    if not action:
        action = PlayerAction.ATTACK
    
    print(f"\nPlayer chooses: {action.value}")
    
    # Execute turn
    result = game.take_action(action)
    
    print(f"Player action result: {result['player_info'].get('message', 'N/A')}")
    print(f"Enemy action result: {result['enemy_info'].get('message', 'N/A')}")
    
    if game.game_over:
        print(f"\n{'='*70}")
        print(f"GAME OVER - {'VICTORY' if game.victory else 'DEFEAT'}")
        print(f"{'='*70}")
        break

print("\n\nFull combat log:")
print(logger.get_full_log())

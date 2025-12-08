"""
Test if BT reacts to HeavySlam telegraph
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from TextGame.game_engine import DungeonGame, PlayerAction, EnemyType
from TextGame.bt_executor import create_bt_executor_from_dsl

# Load manual BT
with open('examples/manual.txt', 'r', encoding='utf-8') as f:
    bt_dsl = f.read()

# Create game
game = DungeonGame(enemy_type=EnemyType.FIRE_GOLEM)
executor = create_bt_executor_from_dsl(bt_dsl)

# Pre-telegraph first action
if game.state.enemy:
    game.engine.telegraph_enemy_action()

# Run until we see HeavySlam telegraph
for turn in range(1, 20):
    print(f"\n{'='*70}")
    print(f"TURN {turn}")
    
    # Show telegraph
    if game.state.telegraphed_action:
        print(f"[!] ENEMY TELEGRAPHS: {game.state.telegraphed_action}")
        
        # Check if it's HeavySlam
        if "HeavySlam" in game.state.telegraphed_action or "heavy" in game.state.telegraphed_action.lower():
            print(">>> BT should choose Defend() now!")
    
    # Execute BT
    action = executor.execute(game.state)
    if not action:
        action = PlayerAction.ATTACK
    
    print(f"Player chooses: {action.value}")
    
    # Check if BT correctly defended
    if game.state.telegraphed_action and ("HeavySlam" in game.state.telegraphed_action or "heavy" in game.state.telegraphed_action.lower()):
        if action == PlayerAction.DEFEND:
            print("[OK] CORRECT! BT reacted to HeavySlam telegraph!")
        else:
            print("[X] WRONG! BT should have defended!")
    
    # Execute turn
    result = game.take_action(action)
    
    print(f"Enemy action: {result['enemy_info'].get('action', 'N/A')}")
    print(f"Player HP: {result['player_hp']}, Enemy HP: {result['enemy_hp']}")
    
    if game.game_over:
        print(f"\nGAME OVER - {'VICTORY' if game.victory else 'DEFEAT'}")
        break

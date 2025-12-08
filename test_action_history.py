"""
Test selective telegraph and action history tracking
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from TextGame.game_engine import DungeonGame, PlayerAction, EnemyType
from TextGame.bt_executor import create_bt_executor_from_dsl

# Simple BT that uses new conditions
bt_dsl = """
root :
    selector :
        # React to telegraphed heavy attacks
        sequence :
            condition : EnemyIsTelegraphing(HeavySlam)
            task : Defend()
        
        # If enemy used RageBuff recently, be defensive
        sequence :
            condition : EnemyUsedRecently(RageBuff)
            condition : EnemyHasBuff(RageBuff)
            task : Defend()
        
        # If enemy just used Slam, attack aggressively
        sequence :
            condition : EnemyLastAction(Slam)
            task : Attack()
        
        # Default
        task : Attack()
"""

# Create game
game = DungeonGame(enemy_type=EnemyType.FIRE_GOLEM)
executor = create_bt_executor_from_dsl(bt_dsl)

# Pre-telegraph first action
if game.state.enemy:
    game.engine.telegraph_enemy_action()

print("Testing Selective Telegraph & Action History\n")
print("="*70)

# Run 10 turns
for turn in range(1, 11):
    print(f"\n--- TURN {turn} ---")
    
    # Show telegraph (if any)
    if game.state.telegraphed_action:
        print(f"[TELEGRAPH] Enemy will use: {game.state.telegraphed_action}")
    else:
        print(f"[NO TELEGRAPH] Enemy action hidden")
    
    # Show last action
    if game.state.last_enemy_action:
        print(f"[LAST ACTION] Enemy used: {game.state.last_enemy_action}")
    
    # Show recent history
    if game.state.action_history:
        print(f"[HISTORY] Recent actions: {game.state.action_history}")
    
    # Execute BT
    action = executor.execute(game.state)
    if not action:
        action = PlayerAction.ATTACK
    
    print(f"\nPlayer chooses: {action.value}")
    
    # Execute turn
    result = game.take_action(action)
    
    print(f"Enemy executed: {result['enemy_info'].get('action', 'N/A')}")
    print(f"Player HP: {result['player_hp']}, Enemy HP: {result['enemy_hp']}")
    
    if game.game_over:
        print(f"\n{'='*70}")
        print(f"GAME OVER - {'VICTORY' if game.victory else 'DEFEAT'}")
        break

print(f"\n{'='*70}")
print("Test Complete!")
print(f"\nFinal action history: {game.state.action_history}")

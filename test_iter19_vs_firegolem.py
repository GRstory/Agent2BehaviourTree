"""
Test iter19 BT against FireGolem 5 times
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from TextGame.game_engine import DungeonGame, EnemyType, PlayerAction
from TextGame.bt_executor import BTExecutor
from bt_parser import parse_bt_dsl

def run_test():
    bt_path = "generated_bts/20251214_150632/iter19_bt.txt"
    
    print("=" * 80)
    print("Testing iter19 BT vs FireGolem (5 battles)")
    print("=" * 80)
    print()
    
    # Parse BT
    with open(bt_path, 'r', encoding='utf-8') as f:
        bt_text = f.read()
    
    bt_root = parse_bt_dsl(bt_text)
    
    wins = 0
    losses = 0
    results = []
    
    for i in range(5):
        print(f"\n{'='*80}")
        print(f"BATTLE {i+1}/5")
        print(f"{'='*80}\n")
        
        # Create game with FireGolem
        game = DungeonGame(EnemyType.FIRE_GOLEM)
        executor = BTExecutor(bt_root)
        
        # Run combat
        max_turns = 50
        turn = 0
        
        while not game.game_over and turn < max_turns:
            # Get action from BT
            action = executor.execute(game.state)
            
            # If BT returns None, default to Attack
            if action is None:
                action = PlayerAction.ATTACK
            
            # Execute turn
            result = game.take_action(action)
            turn += 1
        
        # Determine result
        if game.state.player.is_alive() and not game.state.enemy.is_alive():
            combat_result = 'VICTORY'
        elif not game.state.player.is_alive():
            combat_result = 'DEFEAT'
        elif turn >= max_turns:
            combat_result = 'TURN_LIMIT'
        else:
            combat_result = 'UNKNOWN'
        
        # Store results
        battle_result = {
            'battle_num': i + 1,
            'result': combat_result,
            'turns': turn,
            'player_hp': game.state.player.current_hp,
            'enemy_hp': game.state.enemy.current_hp,
            'player_hp_pct': game.state.player.hp_percentage(),
            'enemy_hp_pct': game.state.enemy.hp_percentage(),
            'player_max_hp': game.state.player.max_hp,
            'enemy_max_hp': game.state.enemy.max_hp
        }
        results.append(battle_result)
        
        if combat_result == 'VICTORY':
            wins += 1
            print(f"\n[WIN] VICTORY in {turn} turns!")
        else:
            losses += 1
            print(f"\n[LOSS] DEFEAT in {turn} turns")
        
        print(f"Final HP - Player: {battle_result['player_hp']}/{battle_result['player_max_hp']} ({battle_result['player_hp_pct']}%)")
        print(f"Final HP - Enemy: {battle_result['enemy_hp']}/{battle_result['enemy_max_hp']} ({battle_result['enemy_hp_pct']}%)")
    
    # Summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print(f"\nTotal Battles: 5")
    print(f"Wins: {wins} ({wins/5*100:.1f}%)")
    print(f"Losses: {losses} ({losses/5*100:.1f}%)")
    print(f"\nWin Rate: {wins}/5 = {wins/5*100:.1f}%")
    
    print("\n" + "-" * 80)
    print("Battle Details:")
    print("-" * 80)
    for r in results:
        status = "[WIN] " if r['result'] == 'VICTORY' else "[LOSS]"
        print(f"Battle {r['battle_num']}: {status} | {r['turns']} turns | "
              f"Player HP: {r['player_hp_pct']}% | Enemy HP: {r['enemy_hp_pct']}%")
    
    print("\n" + "=" * 80)
    
    # Calculate average turns for wins
    if wins > 0:
        avg_turns_win = sum(r['turns'] for r in results if r['result'] == 'VICTORY') / wins
        avg_hp_win = sum(r['player_hp_pct'] for r in results if r['result'] == 'VICTORY') / wins
        print(f"\nWin Statistics:")
        print(f"  Average Turns: {avg_turns_win:.1f}")
        print(f"  Average Final HP: {avg_hp_win:.1f}%")
    
    if losses > 0:
        avg_turns_loss = sum(r['turns'] for r in results if r['result'] != 'VICTORY') / losses
        avg_enemy_hp_loss = sum(r['enemy_hp_pct'] for r in results if r['result'] != 'VICTORY') / losses
        print(f"\nLoss Statistics:")
        print(f"  Average Turns: {avg_turns_loss:.1f}")
        print(f"  Average Enemy HP Remaining: {avg_enemy_hp_loss:.1f}%")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    run_test()

"""
Test iter12 BT against both enemies
Run 5 battles against IceWraith and 5 against FireGolem
Calculate win rate for each enemy type
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'TextGame'))

from TextGame.game_engine import DungeonGame, EnemyType, PlayerAction
from TextGame.bt_executor import BTExecutor

def run_battle(bt_file: str, enemy_type: EnemyType, battle_num: int) -> dict:
    """Run a single battle and return results"""
    game = DungeonGame(enemy_type=enemy_type)
    
    # Load BT from file
    with open(bt_file, 'r', encoding='utf-8') as f:
        bt_dsl = f.read()
    
    from TextGame.bt_executor import create_bt_executor_from_dsl
    executor = create_bt_executor_from_dsl(bt_dsl)
    
    if not executor:
        raise ValueError(f"Failed to parse BT from {bt_file}")
    
    turn = 0
    max_turns = 35
    
    while turn < max_turns:
        # Get BT decision
        action = executor.execute(game.state)
        
        # Execute turn
        result = game.take_action(action)
        turn += 1
        
        # Check if game over
        if result['game_over']:
            return {
                'enemy_type': enemy_type.value,
                'battle_num': battle_num,
                'victory': result['victory'],
                'turns': turn,
                'final_player_hp': game.state.player.current_hp,
                'final_enemy_hp': game.state.enemy.current_hp if game.state.enemy else 0
            }
    
    # Turn limit reached
    return {
        'enemy_type': enemy_type.value,
        'battle_num': battle_num,
        'victory': False,
        'turns': turn,
        'final_player_hp': game.state.player.current_hp,
        'final_enemy_hp': game.state.enemy.current_hp if game.state.enemy else 0,
        'defeat_reason': 'turn_limit'
    }

def main():
    bt_file = "generated_bts/20251215_024921/iter19_bt.txt"
    
    print("=" * 60)
    print("Testing iter19 BT Win Rate")
    print("=" * 60)
    print(f"BT File: {bt_file}")
    print(f"Tests: 5 vs IceWraith, 5 vs FireGolem (Total: 10)")
    print("=" * 60)
    print()
    
    results = {
        'IceWraith': [],
        'FireGolem': []
    }
    
    # Test against IceWraith (5 battles)
    print("Testing vs IceWraith...")
    for i in range(5):
        result = run_battle(bt_file, EnemyType.ICE_WRAITH, i+1)
        results['IceWraith'].append(result)
        status = "WIN" if result['victory'] else "LOSS"
        print(f"  Battle {i+1}: {status} - {result['turns']} turns")
    
    print()
    
    # Test against FireGolem (5 battles)
    print("Testing vs FireGolem...")
    for i in range(5):
        result = run_battle(bt_file, EnemyType.FIRE_GOLEM, i+1)
        results['FireGolem'].append(result)
        status = "WIN" if result['victory'] else "LOSS"
        print(f"  Battle {i+1}: {status} - {result['turns']} turns")
    
    print()
    print("=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    
    # Calculate win rates
    for enemy_name, battles in results.items():
        wins = sum(1 for b in battles if b['victory'])
        total = len(battles)
        win_rate = (wins / total) * 100
        avg_turns = sum(b['turns'] for b in battles) / total
        
        print(f"\n{enemy_name}:")
        print(f"  Win Rate: {wins}/{total} ({win_rate:.1f}%)")
        print(f"  Avg Turns: {avg_turns:.1f}")
        
        if wins > 0:
            winning_battles = [b for b in battles if b['victory']]
            avg_winning_turns = sum(b['turns'] for b in winning_battles) / len(winning_battles)
            print(f"  Avg Winning Turns: {avg_winning_turns:.1f}")
    
    # Overall stats
    total_wins = sum(1 for enemy_battles in results.values() for b in enemy_battles if b['victory'])
    total_battles = sum(len(battles) for battles in results.values())
    overall_win_rate = (total_wins / total_battles) * 100
    
    print(f"\nOverall Win Rate: {total_wins}/{total_battles} ({overall_win_rate:.1f}%)")
    print("=" * 60)

if __name__ == "__main__":
    main()

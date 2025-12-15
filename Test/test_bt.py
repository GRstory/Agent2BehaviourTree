"""
Clean test script for testing any BT against both enemies
Usage: python test_bt.py <bt_file_path>
"""
import sys
import os
import random

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from TextGame.game_engine import DungeonGame, PlayerAction, EnemyType
from TextGame.bt_executor import create_bt_executor_from_dsl

def test_bt(bt_path, num_tests=20, verbose=False):
    """Test BT against both enemies"""
    try:
        with open(bt_path, 'r', encoding='utf-8') as f:
            bt_dsl = f.read()
    except FileNotFoundError:
        print(f"[ERROR] File not found: {bt_path}")
        return None
    
    print(f"Testing BT: {bt_path}")
    print("="*70)
    
    overall_results = {}
    
    for enemy_type in [EnemyType.FIRE_GOLEM, EnemyType.ICE_WRAITH]:
        results = []
        
        for seed in range(num_tests):
            random.seed(seed)
            game = DungeonGame(enemy_type=enemy_type)
            executor = create_bt_executor_from_dsl(bt_dsl)
            
            if not executor:
                print(f"[ERROR] Failed to parse BT")
                return None
            
            game.engine.telegraph_enemy_action()
            turn = 0
            max_turns = 35
            
            while not game.game_over and turn < max_turns:
                turn += 1
                action = executor.execute(game.state) or PlayerAction.ATTACK
                game.take_action(action)
                
                if verbose and seed == 0:
                    p_hp = game.state.player.current_hp
                    e_hp = game.state.enemy.current_hp
                    print(f"T{turn:2d}: {action.value:12s} | P:{p_hp:3d} E:{e_hp:3d}")
            
            results.append({
                'victory': game.victory,
                'turns': turn,
                'player_hp': game.state.player.current_hp,
                'enemy_hp': game.state.enemy.current_hp
            })
        
        wins = sum(1 for r in results if r['victory'])
        avg_turns = sum(r['turns'] for r in results) / len(results)
        
        overall_results[enemy_type.value] = {
            'wins': wins,
            'total': num_tests,
            'win_rate': wins / num_tests,
            'avg_turns': avg_turns
        }
        
        print(f"\n{enemy_type.value}:")
        print(f"  Win Rate: {wins}/{num_tests} ({wins/num_tests*100:.0f}%)")
        print(f"  Avg Turns: {avg_turns:.1f}")
    
    # Overall stats
    total_wins = sum(r['wins'] for r in overall_results.values())
    total_battles = sum(r['total'] for r in overall_results.values())
    
    print(f"\n{'='*70}")
    print(f"Overall: {total_wins}/{total_battles} ({total_wins/total_battles*100:.0f}%)")
    print(f"{'='*70}")
    
    return overall_results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_bt.py <bt_file_path> [--verbose]")
        print("\nExample:")
        print("  python test_bt.py examples/optimal_bt_final.txt")
        print("  python test_bt.py generated_bts/20251215_225920/iter24_bt.txt --verbose")
        sys.exit(1)
    
    bt_path = sys.argv[1]
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    
    test_bt(bt_path, num_tests=20, verbose=verbose)

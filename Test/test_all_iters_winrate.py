"""
Test all iteration BTs and track win rates against both enemies.
Only tests iterations that resulted in WIN.
Stops when 100% win rate is achieved.
"""

import sys
import os
import re
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from TextGame.game_engine import DungeonGame, EnemyType, PlayerAction
from TextGame.bt_executor import BTExecutor
from TextGame.bt_parser import parse_bt_dsl


def run_battle(bt_root, enemy_type: EnemyType) -> bool:
    """Run a single battle and return True if won."""
    game = DungeonGame(enemy_type)
    executor = BTExecutor(bt_root)
    
    max_turns = 50
    turn = 0
    
    while not game.game_over and turn < max_turns:
        action = executor.execute(game.state)
        if action is None:
            action = PlayerAction.ATTACK
        
        result = game.take_action(action)
        turn += 1
    
    return game.state.player.is_alive() and not game.state.enemy.is_alive()


def test_bt_winrate(bt_path: str, battles_per_enemy: int = 5) -> dict:
    """Test a BT against both enemies and return win rates."""
    with open(bt_path, 'r', encoding='utf-8') as f:
        bt_text = f.read()
    bt_root = parse_bt_dsl(bt_text)
    
    results = {}
    
    for enemy_name, enemy_type in [("FireGolem", EnemyType.FIRE_GOLEM), 
                                     ("IceWraith", EnemyType.ICE_WRAITH)]:
        wins = 0
        for _ in range(battles_per_enemy):
            if run_battle(bt_root, enemy_type):
                wins += 1
        
        results[enemy_name] = {
            'wins': wins,
            'total': battles_per_enemy,
            'win_rate': (wins / battles_per_enemy) * 100
        }
    
    return results


def find_win_iterations(log_dir: str) -> list:
    """Find all iterations that resulted in WIN."""
    win_iters = set()
    
    if not os.path.exists(log_dir):
        return []
    
    for filename in os.listdir(log_dir):
        if filename.endswith('_win.txt'):
            # Extract iteration number from filename like "iter00_FireGolem_win.txt"
            match = re.match(r'iter(\d+)_.*_win\.txt', filename)
            if match:
                iter_num = int(match.group(1))
                win_iters.add(iter_num)
    
    return sorted(list(win_iters))


def main():
    # Find the latest log directory
    log_base = "logs"
    bt_base = "generated_bts"
    
    # Get the latest timestamp directory
    log_dirs = [d for d in os.listdir(log_base) if os.path.isdir(os.path.join(log_base, d))]
    if not log_dirs:
        print("No log directories found!")
        return
    
    latest_timestamp = sorted(log_dirs)[-1]
    log_dir = os.path.join(log_base, latest_timestamp)
    bt_dir = os.path.join(bt_base, latest_timestamp)
    
    print(f"Testing BTs from: {bt_dir}")
    print(f"Using logs from: {log_dir}")
    print("=" * 80)
    
    # Find all WIN iterations
    win_iterations = find_win_iterations(log_dir)
    
    if not win_iterations:
        print("No WIN iterations found in logs!")
        return
    
    print(f"\nFound {len(win_iterations)} WIN iterations: {win_iterations}")
    print("\nTesting each WIN iteration against both enemies (5 battles each)...")
    print("=" * 80)
    
    battles_per_enemy = 5
    
    for iter_num in win_iterations:
        bt_path = os.path.join(bt_dir, f"iter{iter_num:02d}_bt.txt")
        
        if not os.path.exists(bt_path):
            print(f"\n[SKIP] iter{iter_num:02d}: BT file not found")
            continue
        
        print(f"\n[TESTING] iter{iter_num:02d}_bt.txt")
        print("-" * 80)
        
        results = test_bt_winrate(bt_path, battles_per_enemy)
        
        # Format: FIREGOLEM[4/5], ICEWRAITH[3/5]
        fg_wins = results['FireGolem']['wins']
        fg_total = results['FireGolem']['total']
        iw_wins = results['IceWraith']['wins']
        iw_total = results['IceWraith']['total']
        
        status_str = f"FIREGOLEM[{fg_wins}/{fg_total}], ICEWRAITH[{iw_wins}/{iw_total}]"
        
        print(f"Results: {status_str}")
        print(f"  FireGolem: {results['FireGolem']['win_rate']:.0f}% win rate")
        print(f"  IceWraith: {results['IceWraith']['win_rate']:.0f}% win rate")
        
        # Check if 100% win rate achieved
        total_wins = fg_wins + iw_wins
        total_battles = fg_total + iw_total
        overall_rate = (total_wins / total_battles) * 100
        
        print(f"  Overall: {overall_rate:.0f}% ({total_wins}/{total_battles})")
        
        # Update the log file with win rate info
        update_log_with_winrate(log_dir, iter_num, status_str)
        
        if overall_rate == 100.0:
            print("\n" + "=" * 80)
            print(f"🎉 100% WIN RATE ACHIEVED at iter{iter_num:02d}!")
            print(f"BT: {bt_path}")
            print("=" * 80)
            break
    
    print("\n" + "=" * 80)
    print("Testing complete!")
    print("=" * 80)


def update_log_with_winrate(log_dir: str, iter_num: int, status_str: str):
    """Update log files with win rate information."""
    # Find all log files for this iteration
    for filename in os.listdir(log_dir):
        if filename.startswith(f"iter{iter_num:02d}_") and filename.endswith('.txt'):
            log_path = os.path.join(log_dir, filename)
            
            # Read existing content
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if already has win rate info
            if "WIN RATE TEST:" not in content:
                # Append win rate info
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(f"\n\n{'='*80}\n")
                    f.write(f"WIN RATE TEST: {status_str}\n")
                    f.write(f"{'='*80}\n")


if __name__ == "__main__":
    main()

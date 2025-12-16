import sys
sys.path.insert(0, '.')

from runner_mastery import ValidationTester
from TextGame.game_engine import EnemyType

# Load optimal manual BT
with open('examples/optimal_manual.txt', 'r') as f:
    bt_dsl = f.read()

# Test against all enemies
tester = ValidationTester(bt_dsl)
result = tester.run_validation_all_enemies()

# Print results
print("\n" + "="*70)
print("OPTIMAL MANUAL BT TEST RESULTS")
print("="*70)

if result['success']:
    enemy_results = result['enemy_results']
    
    # Use EnemyType enum as keys
    fg = enemy_results[EnemyType.FIRE_GOLEM]
    iw = enemy_results[EnemyType.ICE_WRAITH]
    
    print(f"\nFireGolem: {fg['wins']}/{fg['total']} wins ({fg['win_rate']*100:.0f}%)")
    print(f"  - Avg turns: {fg.get('avg_turns', 0):.1f}")
    print(f"  - Mastered: {'YES' if fg['mastered'] else 'NO'}")

    print(f"\nIceWraith: {iw['wins']}/{iw['total']} wins ({iw['win_rate']*100:.0f}%)")
    print(f"  - Avg turns: {iw.get('avg_turns', 0):.1f}")
    print(f"  - Mastered: {'YES' if iw['mastered'] else 'NO'}")

    total_wins = result['total_wins']
    total_battles = result['total_battles']
    print(f"\nOverall: {total_wins}/{total_battles} wins ({result['overall_win_rate']*100:.1f}%)")
    
    if result['perfect']:
        print("\n🎉 PERFECT SCORE! All enemies mastered!")
    elif result['overall_win_rate'] >= 0.8:
        print("\n⭐ EXCELLENT! Strong performance.")
    elif result['overall_win_rate'] >= 0.6:
        print("\n👍 GOOD! Decent performance.")
    else:
        print("\n⚠️  NEEDS WORK! Performance below expectations.")
        
    # Show some failure details
    print("\n" + "-"*70)
    print("Sample Failures:")
    print("-"*70)
    
    fg_losses = [r for r in fg['results'] if not r['victory']]
    if fg_losses:
        print(f"\nFireGolem failures (showing first 3):")
        for i, loss in enumerate(fg_losses[:3]):
            print(f"  {i+1}. {loss['turns']} turns, Enemy HP: {loss['enemy_hp']}/{180} ({loss['enemy_hp']/180*100:.0f}%)")
    
    iw_losses = [r for r in iw['results'] if not r['victory']]
    if iw_losses:
        print(f"\nIceWraith failures (showing first 3):")
        for i, loss in enumerate(iw_losses[:3]):
            print(f"  {i+1}. {loss['turns']} turns, Enemy HP: {loss['enemy_hp']}/{200} ({loss['enemy_hp']/200*100:.0f}%)")
else:
    print(f"ERROR: {result.get('error', 'Unknown error')}")
    
print("="*70)

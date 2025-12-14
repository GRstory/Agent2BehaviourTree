"""
Test IceWraith rebalance changes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from TextGame.game_engine import DungeonGame, PlayerAction, EnemyType

def test_icewraith_rebalance():
    """Test that IceWraith no longer heals and has damage reduction"""
    print("=" * 70)
    print("TEST: IceWraith Rebalance")
    print("=" * 70)
    
    game = DungeonGame(EnemyType.ICE_WRAITH)
    
    print("\nRunning 20 turns to observe enemy behavior:")
    print("- Checking if enemy uses Heal (should NOT appear)")
    print("- Checking damage reduction (player attacks should deal 75% damage)")
    
    heal_count = 0
    attack_damages = []
    
    for turn in range(20):
        # Player attacks
        result = game.take_action(PlayerAction.ATTACK)
        
        enemy_action = result['enemy_info']['action']
        player_damage = result['player_info']['damage']
        
        # Track if enemy heals
        if enemy_action == "Heal":
            heal_count += 1
            print(f"\n[!] Turn {turn}: Enemy used HEAL - THIS SHOULD NOT HAPPEN!")
        
        # Track player damage to enemy
        if player_damage > 0:
            attack_damages.append(player_damage)
        
        print(f"Turn {turn}: Player dealt {player_damage} dmg, Enemy used {enemy_action}")
        
        if game.game_over:
            break
    
    print(f"\n{'=' * 70}")
    print("RESULTS:")
    print(f"{'=' * 70}")
    print(f"Heal count: {heal_count} (should be 0)")
    print(f"Attack damages: {attack_damages}")
    
    # Calculate expected damage with 25% reduction
    # Normal attack: 7 dmg (base 15 * attack_stat/15)
    # With 25% reduction: 7 * 0.75 = 5.25 -> 5 dmg
    # With AttackDown: 2 * 0.75 = 1.5 -> 1 dmg
    
    if attack_damages:
        avg_damage = sum(attack_damages) / len(attack_damages)
        print(f"Average damage: {avg_damage:.1f}")
        print(f"Expected: ~5 dmg (normal) or ~1 dmg (with AttackDown)")
    
    if heal_count == 0:
        print("\n[OK] IceWraith no longer uses Heal!")
    else:
        print(f"\n[FAIL] IceWraith used Heal {heal_count} times!")
    
    print(f"\nFinal state:")
    print(f"  Player HP: {result['player_hp']}/100")
    print(f"  Enemy HP: {result['enemy_hp']}/180")
    print(f"  Result: {'VICTORY' if game.victory else 'DEFEAT' if game.game_over else 'ONGOING'}")


if __name__ == "__main__":
    test_icewraith_rebalance()

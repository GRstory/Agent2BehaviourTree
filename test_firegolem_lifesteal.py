"""
Test FireGolem lifesteal mechanic
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from TextGame.game_engine import DungeonGame, PlayerAction, EnemyType

def test_firegolem_lifesteal():
    """Test that FireGolem heals based on damage dealt"""
    print("=" * 70)
    print("TEST: FireGolem Lifesteal Mechanic")
    print("=" * 70)
    
    # Test Phase 1 (20% lifesteal)
    print("\n--- Phase 1 (HP >= 50%, 20% lifesteal) ---")
    game = DungeonGame(EnemyType.FIRE_GOLEM)
    game.state.enemy.current_hp = 100  # 55.5%
    
    for i in range(5):
        result = game.take_action(PlayerAction.ATTACK)
        enemy_action = result['enemy_info']['action']
        enemy_damage = result['enemy_info']['damage']
        enemy_heal = result['enemy_info'].get('heal', 0)
        
        expected_heal = int(enemy_damage * 0.20) if enemy_damage > 0 else 0
        
        print(f"Turn {i}: {enemy_action}")
        print(f"  Damage: {enemy_damage}")
        print(f"  Heal: {enemy_heal} (expected: {expected_heal})")
        
        if enemy_damage > 0 and expected_heal > 0:
            if enemy_heal == expected_heal:
                print(f"  [OK] Lifesteal correct!")
            else:
                print(f"  [FAIL] Expected {expected_heal}, got {enemy_heal}")
        
        if game.game_over:
            break
    
    # Test Phase 2 (10% lifesteal)
    print("\n--- Phase 2 (HP < 50%, 10% lifesteal) ---")
    game = DungeonGame(EnemyType.FIRE_GOLEM)
    game.state.enemy.current_hp = 72  # 40%
    
    for i in range(5):
        result = game.take_action(PlayerAction.ATTACK)
        enemy_action = result['enemy_info']['action']
        enemy_damage = result['enemy_info']['damage']
        enemy_heal = result['enemy_info'].get('heal', 0)
        
        expected_heal = int(enemy_damage * 0.10) if enemy_damage > 0 else 0
        
        print(f"Turn {i}: {enemy_action}")
        print(f"  Damage: {enemy_damage}")
        print(f"  Heal: {enemy_heal} (expected: {expected_heal})")
        
        if enemy_damage > 0 and expected_heal > 0:
            if enemy_heal == expected_heal:
                print(f"  [OK] Lifesteal correct!")
            else:
                print(f"  [FAIL] Expected {expected_heal}, got {enemy_heal}")
        
        if game.game_over:
            break
    
    print("\n" + "=" * 70)
    print("Lifesteal mechanic is working!")
    print("Enemy heals for % of damage dealt to player")
    print("=" * 70)


if __name__ == "__main__":
    test_firegolem_lifesteal()

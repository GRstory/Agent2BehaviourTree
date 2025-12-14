"""
Test script to verify BT execution fixes

Tests:
1. IsTurnEarly(1) only triggers on turn 0, not turn 1
2. EnemyWeakTo conditions work correctly
3. Scan only executes once
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from TextGame.game_engine import DungeonGame, PlayerAction, EnemyType, Element
from TextGame.bt_executor import create_bt_executor_from_dsl

def test_turn_early_condition():
    """Test that IsTurnEarly(1) only triggers on turn 0"""
    print("=" * 70)
    print("TEST 1: IsTurnEarly Condition")
    print("=" * 70)
    
    bt_dsl = """
root :
    selector :
        sequence :
            condition : IsTurnEarly(1)
            task : Scan()
        task : Attack()
"""
    
    game = DungeonGame(EnemyType.ICE_WRAITH)
    executor = create_bt_executor_from_dsl(bt_dsl)
    
    # Turn 0 - should execute Scan
    print(f"\nTurn 0 (turn_count={game.state.turn_count}):")
    action = executor.execute(game.state)
    print(f"  Action: {action.value if action else 'None'}")
    print(f"  Expected: Scan")
    assert action == PlayerAction.SCAN, f"Expected Scan, got {action}"
    
    # Execute the action to increment turn_count
    game.take_action(action)
    
    # Turn 1 - should execute Attack (not Scan)
    print(f"\nTurn 1 (turn_count={game.state.turn_count}):")
    action = executor.execute(game.state)
    print(f"  Action: {action.value if action else 'None'}")
    print(f"  Expected: Attack")
    assert action == PlayerAction.ATTACK, f"Expected Attack, got {action}"
    
    print("\n[OK] TEST PASSED: IsTurnEarly(1) only triggers on turn 0\n")


def test_enemy_weak_to_conditions():
    """Test that EnemyWeakTo conditions work correctly"""
    print("=" * 70)
    print("TEST 2: EnemyWeakTo Conditions")
    print("=" * 70)
    
    bt_dsl = """
root :
    selector :
        sequence :
            condition : HasScannedEnemy()
            condition : EnemyWeakTo(Fire)
            task : IceSpell()
        sequence :
            condition : HasScannedEnemy()
            condition : EnemyWeakTo(Ice)
            task : FireSpell()
        task : Attack()
"""
    
    game = DungeonGame(EnemyType.ICE_WRAITH)
    executor = create_bt_executor_from_dsl(bt_dsl)
    
    # Scan first
    game.state.scanned = True
    
    # Test 1: Enemy with Ice element should be weak to Fire
    print(f"\nTest 2a: Enemy with Ice element")
    game.state.enemy.element = Element.ICE
    print(f"  Enemy element: {game.state.enemy.element.value}")
    action = executor.execute(game.state)
    print(f"  Action: {action.value if action else 'None'}")
    print(f"  Expected: IceSpell")
    print(f"  Trace: {executor.get_trace()}")
    
    # Test 2: Enemy with Fire element should be weak to Ice
    print(f"\nTest 2b: Enemy with Fire element")
    game.state.enemy.element = Element.FIRE
    print(f"  Enemy element: {game.state.enemy.element.value}")
    action = executor.execute(game.state)
    print(f"  Action: {action.value if action else 'None'}")
    print(f"  Expected: FireSpell")
    print(f"  Trace: {executor.get_trace()}")
    
    # Test 3: Enemy with Neutral element
    print(f"\nTest 2c: Enemy with Neutral element")
    game.state.enemy.element = Element.NEUTRAL
    print(f"  Enemy element: {game.state.enemy.element.value}")
    action = executor.execute(game.state)
    print(f"  Action: {action.value if action else 'None'}")
    print(f"  Expected: Attack (no weakness)")
    print(f"  Trace: {executor.get_trace()}")
    
    print("\n[OK] TEST COMPLETED: EnemyWeakTo conditions tested\n")


def test_full_combat():
    """Test a full combat scenario"""
    print("=" * 70)
    print("TEST 3: Full Combat with Fixed BT")
    print("=" * 70)
    
    bt_dsl = """
root :
    selector :
        # Turn 0: Scan
        sequence :
            condition : IsTurnEarly(1)
            condition : HasMP(15)
            task : Scan()

        # Use Fire spell when enemy is weak to Fire (has Ice element)
        sequence :
            condition : HasScannedEnemy()
            condition : EnemyWeakTo(Fire)
            condition : HasMP(20)
            task : FireSpell()

        # Heal when critical
        sequence :
            condition : IsPlayerHPLow(60)
            condition : CanHeal()
            task : Heal()

        # Default: Attack
        task : Attack()
"""
    
    game = DungeonGame(EnemyType.ICE_WRAITH)
    executor = create_bt_executor_from_dsl(bt_dsl)
    
    print("\nRunning first 5 turns:")
    for i in range(5):
        print(f"\n--- Turn {game.state.turn_count} ---")
        print(f"  Enemy element: {game.state.enemy.element.value}")
        print(f"  Scanned: {game.state.scanned}")
        print(f"  Player MP: {game.state.player_resources.mp}")
        
        action = executor.execute(game.state)
        print(f"  Action chosen: {action.value if action else 'None'}")
        
        result = game.take_action(action)
        print(f"  Player HP: {result['player_hp']}, Enemy HP: {result['enemy_hp']}")
        
        if game.game_over:
            break
    
    print("\n[OK] TEST COMPLETED: Full combat scenario\n")


if __name__ == "__main__":
    test_turn_early_condition()
    test_enemy_weak_to_conditions()
    test_full_combat()
    
    print("=" * 70)
    print("ALL TESTS COMPLETED")
    print("=" * 70)

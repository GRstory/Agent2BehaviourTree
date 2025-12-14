"""
Test FireGolem two-phase system with passive healing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from TextGame.game_engine import DungeonGame, PlayerAction, EnemyType, Element

def test_firegolem_two_phases():
    """Test FireGolem two-phase system"""
    print("=" * 70)
    print("TEST: FireGolem Two-Phase System")
    print("=" * 70)
    
    # Test Phase 1
    print("\n--- Phase 1 (HP >= 50%) ---")
    game = DungeonGame(EnemyType.FIRE_GOLEM)
    game.state.enemy.current_hp = 100  # 55.5%
    
    phase1_actions = []
    phase1_heals = 0
    
    for i in range(20):
        result = game.take_action(PlayerAction.ATTACK)
        action = result['enemy_info']['action']
        heal = result['enemy_info'].get('heal', 0)
        
        phase1_actions.append(action)
        if heal > 0:
            phase1_heals += 1
            print(f"  Turn {i}: {action} + HEAL ({heal} HP)")
        
        if game.game_over or game.state.enemy.hp_percentage() < 50:
            break
    
    print(f"\nPhase 1 Actions: {set(phase1_actions)}")
    print(f"Heal count: {phase1_heals}/20 (expected ~20% = 4)")
    print(f"FireSpell used: {'FireSpell' in phase1_actions} (should be False)")
    
    # Test Phase 2
    print("\n--- Phase 2 (HP < 50%) ---")
    game = DungeonGame(EnemyType.FIRE_GOLEM)
    game.state.enemy.current_hp = 72  # 40%
    
    phase2_actions = []
    phase2_heals = 0
    element_before = game.state.enemy.element
    
    for i in range(20):
        result = game.take_action(PlayerAction.ATTACK)
        action = result['enemy_info']['action']
        heal = result['enemy_info'].get('heal', 0)
        
        phase2_actions.append(action)
        if heal > 0:
            phase2_heals += 1
            print(f"  Turn {i}: {action} + HEAL ({heal} HP)")
        
        if game.game_over:
            break
    
    element_after = game.state.enemy.element
    
    print(f"\nPhase 2 Actions: {set(phase2_actions)}")
    print(f"Heal count: {phase2_heals}/20 (expected ~10% = 2)")
    print(f"FireSpell used: {'FireSpell' in phase2_actions} (should be True)")
    print(f"Element: {element_before.value} -> {element_after.value} (should be Fire)")
    
    # Summary
    print(f"\n{'=' * 70}")
    print("VERIFICATION:")
    print(f"{'=' * 70}")
    
    # Phase 1 checks
    if 'FireSpell' not in phase1_actions:
        print("[OK] Phase 1: No FireSpell (neutral only)")
    else:
        print("[FAIL] Phase 1: FireSpell was used!")
    
    if 2 <= phase1_heals <= 6:  # 20% ± variance
        print(f"[OK] Phase 1: Heal rate ~{phase1_heals/20*100:.0f}% (expected 20%)")
    else:
        print(f"[WARN] Phase 1: Heal rate {phase1_heals/20*100:.0f}% (expected 20%)")
    
    # Phase 2 checks
    if 'FireSpell' in phase2_actions:
        print("[OK] Phase 2: FireSpell is used")
    else:
        print("[FAIL] Phase 2: No FireSpell!")
    
    if element_after == Element.FIRE:
        print("[OK] Phase 2: Fire element activated")
    else:
        print(f"[FAIL] Phase 2: Element is {element_after.value}, not Fire!")
    
    if 0 <= phase2_heals <= 4:  # 10% ± variance
        print(f"[OK] Phase 2: Heal rate ~{phase2_heals/20*100:.0f}% (expected 10%)")
    else:
        print(f"[WARN] Phase 2: Heal rate {phase2_heals/20*100:.0f}% (expected 10%)")


if __name__ == "__main__":
    test_firegolem_two_phases()

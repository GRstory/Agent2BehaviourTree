"""
Analyze why basic BT wins against IceWraith
"""
import sys
import os
import random

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from TextGame.game_engine import DungeonGame, PlayerAction, EnemyType
from TextGame.bt_executor import create_bt_executor_from_dsl

def detailed_analysis(seed):
    """Detailed turn-by-turn analysis"""
    random.seed(seed)
    
    bt = open('examples/example_bt_balanced.txt').read()
    game = DungeonGame(enemy_type=EnemyType.ICE_WRAITH)
    executor = create_bt_executor_from_dsl(bt)
    
    game.engine.telegraph_enemy_action()
    
    print(f"\n{'='*80}")
    print(f"DETAILED ANALYSIS - Seed {seed}")
    print(f"{'='*80}")
    print(f"Player: 100 HP, 15 ATK, 6 DEF | Enemy: 200 HP, 15 ATK, 8 DEF")
    print(f"Player needs to deal 200 damage, Enemy needs to deal 100 damage")
    print(f"{'='*80}\n")
    
    turn = 0
    player_total_dmg = 0
    enemy_total_dmg = 0
    player_heals = 0
    enemy_debuff_count = 0
    enemy_frosttouch_count = 0
    enemy_icespell_count = 0
    
    while not game.game_over and turn < 35:
        turn += 1
        
        action = executor.execute(game.state) or PlayerAction.ATTACK
        result = game.take_action(action)
        
        p_info = result['player_info']
        e_info = result['enemy_info']
        
        p_dmg = p_info.get('damage', 0)
        e_dmg = e_info.get('damage', 0)
        e_action = e_info.get('action', 'None')
        
        player_total_dmg += p_dmg
        enemy_total_dmg += e_dmg
        
        if action == PlayerAction.HEAL:
            player_heals += 1
        
        if e_action == 'Debuff':
            enemy_debuff_count += 1
        elif e_action == 'FrostTouch':
            enemy_frosttouch_count += 1
        elif e_action == 'IceSpell':
            enemy_icespell_count += 1
        
        player_hp = game.state.player.current_hp
        enemy_hp = game.state.enemy.current_hp
        
        print(f"T{turn:2d}: P:{action.value:10s}({p_dmg:2d}) | E:{e_action:12s}({e_dmg:2d}) | HP P:{player_hp:3d} E:{enemy_hp:3d}")
        
        if game.game_over:
            break
    
    print(f"\n{'='*80}")
    print(f"STATISTICS")
    print(f"{'='*80}")
    print(f"Result: {'VICTORY' if game.victory else 'DEFEAT'} in {turn} turns")
    print(f"Player total damage dealt: {player_total_dmg} (avg {player_total_dmg/turn:.1f}/turn)")
    print(f"Enemy total damage dealt: {enemy_total_dmg} (avg {enemy_total_dmg/turn:.1f}/turn)")
    print(f"Player heals used: {player_heals}")
    print(f"\nEnemy action breakdown:")
    print(f"  Debuff: {enemy_debuff_count} ({enemy_debuff_count/turn*100:.1f}%)")
    print(f"  FrostTouch: {enemy_frosttouch_count} ({enemy_frosttouch_count/turn*100:.1f}%)")
    print(f"  IceSpell: {enemy_icespell_count} ({enemy_icespell_count/turn*100:.1f}%)")
    print(f"\nDamage efficiency:")
    print(f"  Player DPS: {player_total_dmg/turn:.2f}")
    print(f"  Enemy DPS: {enemy_total_dmg/turn:.2f}")
    print(f"  Effective enemy DPS (excluding heals): {(enemy_total_dmg - player_heals*45)/turn:.2f}")
    
    # Calculate theoretical minimum turns needed
    print(f"\nTheoretical analysis:")
    print(f"  Turns to kill enemy at 12 dmg/turn: {200/12:.1f}")
    print(f"  Turns to kill player at 17 dmg/turn (avg FrostTouch+IceSpell): {100/17:.1f}")
    print(f"  Player survival with heals: {100 + player_heals*45} effective HP")

# Analyze winning seeds
winning_seeds = [0, 5, 17]

for seed in winning_seeds:
    detailed_analysis(seed)

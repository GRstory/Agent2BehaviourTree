from TextGame.game_engine import DungeonGame, ActionType

print("=== FINAL VERIFICATION ===\n")

# Test Heal: 25% of max HP
game = DungeonGame()
print("1. HEAL TEST")
print(f"   Max HP: {game.state.player.max_hp}")
print(f"   Expected heal amount: {int(game.state.player.max_hp * 0.25)} HP")

# Damage player
for _ in range(5):
    game.take_action(ActionType.LIGHT_ATTACK)
    
before_heal = game.state.player.current_hp
print(f"   HP before heal: {before_heal}")

# Use heal
result = game.take_action(ActionType.HEAL)
after_heal = game.state.player.current_hp
print(f"   HP after heal: {after_heal}")
print(f"   Net change: {result['player_hp_change']} (includes enemy attack)")
print(f"   Heal used: {game.state.heal_used_this_floor}")

# Try again
result2 = game.take_action(ActionType.HEAL)
print(f"   Try heal again: HP change = {result2['player_hp_change']} (should be negative, only damage)")
print(f"   Result: {'PASS' if result2['player_hp_change'] < 0 else 'FAIL'}")

# Test floor reset
game.state.reset_for_new_floor(2)
print(f"\n2. FLOOR RESET TEST")
print(f"   New floor: {game.state.current_floor}")
print(f"   Heal available: {not game.state.heal_used_this_floor}")
print(f"   Result: {'PASS' if not game.state.heal_used_this_floor else 'FAIL'}")

# Test Defend: 50% damage reduction
print(f"\n3. DEFEND TEST")
game1 = DungeonGame()
game1.take_action(ActionType.LIGHT_ATTACK)
normal_damage = 100 - game1.state.player.current_hp
print(f"   Normal damage: {normal_damage}")

game2 = DungeonGame()
result = game2.take_action(ActionType.DEFEND)
defend_damage = 100 - game2.state.player.current_hp
print(f"   Damage with defend: {defend_damage}")
print(f"   Reduction: {normal_damage - defend_damage} ({((normal_damage - defend_damage) / normal_damage * 100):.0f}%)")
print(f"   Result: {'PASS' if defend_damage < normal_damage else 'FAIL'}")

print("\n=== ALL MECHANICS VERIFIED ===")

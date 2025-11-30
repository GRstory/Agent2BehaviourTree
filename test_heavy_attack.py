from TextGame.game_engine import DungeonGame, ActionType

print("=== HEAVY ATTACK MECHANICS TEST (SAME TURN PENALTY) ===\n")

# Test 1: Heavy attack damage
game1 = DungeonGame()
print("1. HEAVY ATTACK DAMAGE TEST")
print(f"   Player base attack: {game1.state.player.base_attack}")
print(f"   Expected heavy attack damage: ~{int(game1.state.player.base_attack * 1.5)} (1.5x)")

enemy_hp_before = game1.state.enemy.current_hp
game1.take_action(ActionType.HEAVY_ATTACK)
enemy_hp_after = game1.state.enemy.current_hp
damage_dealt = enemy_hp_before - enemy_hp_after

print(f"   Enemy HP: {enemy_hp_before} -> {enemy_hp_after}")
print(f"   Actual damage: {damage_dealt}")
print(f"   Result: {'PASS' if 18 <= damage_dealt <= 24 else 'FAIL'}")

# Test 2: Heavy attack penalty (SAME TURN)
print("\n2. HEAVY ATTACK PENALTY TEST (SAME TURN)")

# Normal damage
game2 = DungeonGame()
game2.take_action(ActionType.LIGHT_ATTACK)
normal_damage = 100 - game2.state.player.current_hp
print(f"   Normal damage taken (light attack turn): {normal_damage}")

# Heavy attack - should take 2x damage in SAME turn
game3 = DungeonGame()
print(f"   Before heavy attack - used_heavy_attack_this_turn: {game3.state.used_heavy_attack_this_turn}")
old_hp = game3.state.player.current_hp
game3.take_action(ActionType.HEAVY_ATTACK)
new_hp = game3.state.player.current_hp
heavy_turn_damage = old_hp - new_hp
print(f"   After heavy attack turn - HP: {old_hp} -> {new_hp}")
print(f"   Damage taken in heavy attack turn: {heavy_turn_damage}")
print(f"   Expected: ~{normal_damage * 2} (2x normal damage)")
print(f"   Result: {'PASS' if heavy_turn_damage >= normal_damage * 1.8 else 'FAIL'}")

# Test 3: Penalty resets after same turn
print("\n3. PENALTY RESET TEST")
game4 = DungeonGame()
game4.take_action(ActionType.HEAVY_ATTACK)
print(f"   After heavy attack turn - used_heavy_attack_this_turn: {game4.state.used_heavy_attack_this_turn}")
print(f"   Result: {'PASS' if not game4.state.used_heavy_attack_this_turn else 'FAIL'}")

# Test 4: Next turn has normal damage
print("\n4. NEXT TURN NORMAL DAMAGE TEST")
game5 = DungeonGame()
game5.take_action(ActionType.HEAVY_ATTACK)  # Turn 1: heavy attack, take 2x damage
hp_after_heavy_turn = game5.state.player.current_hp
game5.take_action(ActionType.LIGHT_ATTACK)  # Turn 2: should take normal damage
hp_after_next_turn = game5.state.player.current_hp
next_turn_damage = hp_after_heavy_turn - hp_after_next_turn
print(f"   Damage in turn after heavy attack: {next_turn_damage}")
print(f"   Expected: ~{normal_damage} (normal damage)")
print(f"   Result: {'PASS' if abs(next_turn_damage - normal_damage) <= 2 else 'FAIL'}")

# Test 5: Defend + Heavy attack interaction
print("\n5. DEFEND + HEAVY ATTACK PENALTY INTERACTION")
game6 = DungeonGame()
game6.take_action(ActionType.DEFEND)
defend_damage = 100 - game6.state.player.current_hp
print(f"   Damage with defend: {defend_damage}")

game7 = DungeonGame()
# Heavy attack with defend - should be 2x then 50% = normal
game7.state.is_defending = True  # Set defend manually before heavy attack
old_hp = game7.state.player.current_hp
game7.take_action(ActionType.HEAVY_ATTACK)
new_hp = game7.state.player.current_hp
combined_damage = old_hp - new_hp
print(f"   Damage with heavy attack penalty (2x) + defend (50%): {combined_damage}")
print(f"   Expected: ~{normal_damage} (2x * 50% = 1x)")
print(f"   Result: {'PASS' if abs(combined_damage - normal_damage) <= 2 else 'FAIL'}")

print("\n=== ALL TESTS COMPLETED ===")

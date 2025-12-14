"""
Step 2: Apply CHARGED 2x damage and update spell status effect probabilities
"""

with open('TextGame/game_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add CHARGED damage multiplier in _calculate_damage
# Find the damage calculation section and add CHARGED check
charged_code = '''
        # Apply CHARGED buff (2x damage)
        if attacker == "player" and self.state.has_status("player", StatusAilment.CHARGED):
            damage = int(damage * 2)
            self.state.remove_status("player", StatusAilment.CHARGED)
'''

# Insert after elemental multiplier calculation
# Find the line with "# Calculate final damage with elemental multiplier"
content = content.replace(
    '        # Calculate final damage with elemental multiplier\n        damage = int(base_damage * elemental_multiplier)',
    '        # Calculate final damage with elemental multiplier\n        damage = int(base_damage * elemental_multiplier)' + charged_code
)

# 2. Update FireSpell burn chance: 30% base, 80% on weakness
old_fire = '''            if self.state.player_resources.spend_mp(20):
                result['success'] = True
                result['cost_mp'] = 20
                result['damage'] = self._calculate_damage(28, Element.FIRE, "player")
                # 30% chance to burn
                if random.random() < 0.3:
                    self.state.add_status("enemy", StatusEffect(StatusAilment.BURN, 3, 5))
                    result['status_applied'] = "Burn"
                result['message'] = f"Fire Spell dealt {result['damage']} damage"'''

new_fire = '''            if self.state.player_resources.spend_mp(20):
                result['success'] = True
                result['cost_mp'] = 20
                result['damage'] = self._calculate_damage(28, Element.FIRE, "player")
                # Burn chance: 20% base, 80% on weakness
                from .game_engine import ELEMENTAL_WEAKNESS
                is_weakness = ELEMENTAL_WEAKNESS.get(self.state.enemy.element) == Element.FIRE
                burn_chance = 0.8 if is_weakness else 0.2
                if random.random() < burn_chance:
                    self.state.add_status("enemy", StatusEffect(StatusAilment.BURN, 3, 5))
                    result['status_applied'] = "Burn"
                result['message'] = f"Fire Spell dealt {result['damage']} damage"'''

content = content.replace(old_fire, new_fire)

# 3. Update IceSpell freeze chance: 30% base, 80% on weakness
old_ice = '''            if self.state.player_resources.spend_mp(20):
                result['success'] = True
                result['cost_mp'] = 20
                result['damage'] = self._calculate_damage(28, Element.ICE, "player")
                # 30% chance to freeze
                if random.random() < 0.3:
                    self.state.add_status("enemy", StatusEffect(StatusAilment.FREEZE, 1))
                    result['status_applied'] = "Freeze"
                result['message'] = f"Ice Spell dealt {result['damage']} damage"'''

new_ice = '''            if self.state.player_resources.spend_mp(20):
                result['success'] = True
                result['cost_mp'] = 20
                result['damage'] = self._calculate_damage(28, Element.ICE, "player")
                # Freeze chance: 20% base, 80% on weakness
                from .game_engine import ELEMENTAL_WEAKNESS
                is_weakness = ELEMENTAL_WEAKNESS.get(self.state.enemy.element) == Element.ICE
                freeze_chance = 0.8 if is_weakness else 0.2
                if random.random() < freeze_chance:
                    self.state.add_status("enemy", StatusEffect(StatusAilment.FREEZE, 1))
                    result['status_applied'] = "Freeze"
                result['message'] = f"Ice Spell dealt {result['damage']} damage"'''

content = content.replace(old_ice, new_ice)

with open('TextGame/game_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Step 2: Applied CHARGED 2x and updated spell probabilities")

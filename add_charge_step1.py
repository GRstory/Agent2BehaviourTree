"""
Step 1: Add CHARGED status and rename PowerStrike to Charge
"""

with open('TextGame/game_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace STORM_CHARGE with CHARGED
content = content.replace('STORM_CHARGE = "StormCharge" # Next spell 2x, 1 use', 'CHARGED = "Charged"        # Next attack 2x damage, 1 turn')

# 2. Rename PowerStrike to Charge in PlayerAction
content = content.replace('POWER_STRIKE = "PowerStrike"', 'CHARGE = "Charge"')

# 3. Update Charge action implementation
old_charge = '''        elif action == PlayerAction.POWER_STRIKE:
            if self.state.player_resources.spend_mp(15):
                result['success'] = True
                result['cost_mp'] = 15
                result['damage'] = self._calculate_damage(45, Element.NEUTRAL, "player")
                result['message'] = f"Power Strike dealt {result['damage']} damage"
            else:
                result['message'] = "Not enough MP!"'''

new_charge = '''        elif action == PlayerAction.CHARGE:
            if self.state.player_resources.spend_mp(15):
                result['success'] = True
                result['cost_mp'] = 15
                result['damage'] = self._calculate_damage(7, Element.NEUTRAL, "player")
                # Apply CHARGED buff for next turn
                self.state.add_status("player", StatusEffect(StatusAilment.CHARGED, 1))
                result['message'] = f"Charging! Dealt {result['damage']} damage, next attack will be doubled!"
            else:
                result['message'] = "Not enough MP!"'''

content = content.replace(old_charge, new_charge)

with open('TextGame/game_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Step 1: Added CHARGED status and renamed to Charge")

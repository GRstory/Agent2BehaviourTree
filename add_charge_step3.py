"""
Step 3: Update bt_nodes.py to use Charge instead of PowerStrike
"""

with open('TextGame/bt_nodes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Rename PowerStrike class to Charge
content = content.replace('class PowerStrike(BTAction):', 'class Charge(BTAction):')
content = content.replace('"""Execute power strike (30 TP, high damage)"""', '"""Execute charge (15 MP, 7 damage + 2x next turn)"""')
content = content.replace('return PlayerAction.POWER_STRIKE', 'return PlayerAction.CHARGE')
content = content.replace('return "PowerStrike()"', 'return "Charge()"')

# 2. Update factory function
content = content.replace('elif action_type == "PowerStrike":', 'elif action_type == "Charge":')
content = content.replace('return PowerStrike()', 'return Charge()')

# 3. Keep legacy support
content = content.replace('# Legacy action names (backwards compatibility)\nLightAttack = Attack\nHeavyAttack = PowerStrike',
                         '# Legacy action names (backwards compatibility)\nLightAttack = Attack\nHeavyAttack = Charge\nPowerStrike = Charge  # Old name support')

with open('TextGame/bt_nodes.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Step 3: Updated bt_nodes.py")

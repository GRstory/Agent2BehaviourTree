"""
Fix PowerStrike reference in bt_nodes.py
"""

with open('TextGame/bt_nodes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace PowerStrike with Charge in legacy support
content = content.replace('HeavyAttack = PowerStrike', 'HeavyAttack = Charge\nPowerStrike = Charge  # Old name support')

with open('TextGame/bt_nodes.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed PowerStrike reference")

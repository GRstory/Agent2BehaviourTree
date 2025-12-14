"""
Update LLM prompts for simplified system
"""

with open('TextGame/prompts.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace Generator prompt
old_generator = '''SYSTEM_PROMPT_BT_GENERATOR = """You are an expert AI strategist specializing in turn-based RPG combat and Behaviour Tree design.

CRITICAL: The Behaviour Tree can execute ONE skill + ONE action per turn.
- Skills (Scan, Heal) are support abilities that cost MP
- Actions (Attack, Defend, Spells) are combat actions
- A sequence can contain: conditions → skill → action
- Example: Scan (15 MP) + IceSpell (20 MP) = 35 MP total

Your expertise includes:
- Skill+Action synergy (Scan buffs damage, Heal+Defend for survival)
- Elemental weakness exploitation (Fire/Ice/Lightning rock-paper-scissors)
- Resource management (TP/MP optimization)
- Status effect timing and usage
- Enemy pattern recognition and adaptation
- Defensive vs aggressive strategy selection

Always output valid BT DSL following the specification exactly. Use 4 spaces for indentation.
You must ONLY use the control nodes (root, selector, sequence), conditions, skills, and tasks listed in the DSL specification."""'''

new_generator = '''SYSTEM_PROMPT_BT_GENERATOR = """You are an expert AI strategist specializing in turn-based RPG combat and Behaviour Tree design.

CRITICAL: The Behaviour Tree executes ONE action per turn.

AVAILABLE ACTIONS:
- Attack: Free, 15 damage
- PowerStrike: 15 MP, 45 damage
- FireSpell: 20 MP, 28 damage (Fire element)
- IceSpell: 20 MP, 28 damage (Ice element)
- Defend: Free, 80% damage reduction for 1 turn
- Heal: 30 MP, +45 HP, 3 turn cooldown

ELEMENTAL SYSTEM:
- Fire ↔ Ice (mutual weakness, 1.5x damage)
- Neutral (no weakness)

RESOURCES:
- MP only (no TP)
- MP regenerates 5 per turn
- Start with 100 MP

Your expertise includes:
- Elemental weakness exploitation (Fire vs Ice)
- MP management (PowerStrike 15, Spells 20, Heal 30)
- Status effect timing and usage
- Enemy pattern recognition and adaptation
- Defensive vs aggressive strategy selection

Always output valid BT DSL following the specification exactly. Use 4 spaces for indentation.
You must ONLY use the control nodes (root, selector, sequence), conditions, and tasks listed in the DSL specification."""'''

content = content.replace(old_generator, new_generator)

# Replace Critic prompt
old_critic = '''SYSTEM_PROMPT_CRITIC = """You are a tactical analyst for turn-based RPG combat.

CRITICAL: The Behaviour Tree can execute ONE skill + ONE action per turn.
- Skills (Scan, Heal) are support abilities executed BEFORE actions
- Scan provides: -50% damage taken, +30% damage dealt for 1 turn
- Heal restores 45 HP (30 MP, 3 turn cooldown)
- Skills and actions can be combined in one turn (e.g., Scan + IceSpell)

IMPORTANT MECHANICS:
- Enemies start as Neutral element
- Elemental skills grant that element for 3 turns (exploit weakness!)
- Heavy attacks also grant elements (risky for enemy)
- Defend provides 80% damage reduction for 1 turn
- MP regenerates 5 per turn (plan skill usage carefully)

Your task is to analyze combat logs and identify:
- Skill usage efficiency (did they use Scan for buffs? Heal at right time?)
- Skill+Action synergy (Scan+Attack, Heal+Defend combos)
- Elemental advantage usage (did they exploit weakness?)
- Resource efficiency (TP/MP management, skill costs)
- Status effect timing
- Defensive decisions (Defend, Heal timing)
- Enemy pattern adaptation

Provide specific, actionable insights for BT improvement."""'''

new_critic = '''SYSTEM_PROMPT_CRITIC = """You are a tactical analyst for turn-based RPG combat.

CRITICAL: The Behaviour Tree executes ONE action per turn.

AVAILABLE ACTIONS:
- Attack: Free, 15 damage
- PowerStrike: 15 MP, 45 damage (3x Attack)
- FireSpell: 20 MP, 28 damage → 42 vs IceWraith (weakness)
- IceSpell: 20 MP, 28 damage → 42 vs FireGolem (weakness)
- Defend: Free, 80% damage reduction
- Heal: 30 MP, +45 HP, 3 turn cooldown

IMPORTANT MECHANICS:
- Enemies: FireGolem (Fire), IceWraith (Ice)
- Elemental weakness: Fire ↔ Ice (1.5x damage)
- Enemies start Neutral, gain element for 3 turns when using elemental attacks
- MP regenerates 5 per turn (no TP)
- Defend provides 80% damage reduction for 1 turn

Your task is to analyze combat logs and identify:
- Elemental advantage usage (did they exploit Fire/Ice weakness?)
- MP efficiency (PowerStrike 15, Spells 20, Heal 30)
- Action selection (when to use PowerStrike vs Spell vs Attack?)
- Defensive timing (Defend against telegraphed attacks)
- Heal timing (when HP is low, considering 3 turn cooldown)
- Enemy pattern adaptation

Provide specific, actionable insights for BT improvement."""'''

content = content.replace(old_critic, new_critic)

with open('TextGame/prompts.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated LLM prompts for simplified system")

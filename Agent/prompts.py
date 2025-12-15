"""
Prompt Templates for Enhanced Combat System LLM Agent

Contains prompts for BT generation and improvement based on combat logs.
"""

import os

DSL_SPEC_PATH = os.path.join(os.path.dirname(__file__), "bt_dsl_spec.md")

def load_dsl_spec() -> str:
    """Load the BT DSL specification"""
    try:
        with open(DSL_SPEC_PATH, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return "[DSL Spec not found]"


# ============================================================================
# SYSTEM PROMPTS
# ============================================================================

SYSTEM_PROMPT_BT_GENERATOR = """You are an expert AI strategist specializing in turn-based RPG combat and Behaviour Tree design.

CRITICAL: The Behaviour Tree executes ONE action per turn.

AVAILABLE ACTIONS (7 total):
- Attack: Free, 9 damage, +10 MP (resource recovery!)
- Charge: 15 MP, 7 damage + next turn all damage x2
- FireSpell: 20 MP, 7 damage (1.5x when enemy has Ice element), Burn 25%
- IceSpell: 20 MP, 10 damage (1.5x when enemy has Fire element), Freeze 25%
- Defend: Free, 50% damage reduction for 1 turn
- Heal: 30 MP, +40 HP, 3 turn cooldown
- Cleanse: 25 MP, removes Burn/AttackDown, +10% damage for 1 turn

ELEMENTAL SYSTEM:
- Fire attacks deal 1.5x damage to Ice element enemies
- Ice attacks deal 1.5x damage to Fire element enemies
- Enemies start as Neutral (no weakness), can gain Fire/Ice element during combat
- **CRITICAL: Player attacks do NOT change enemy element**
- **CRITICAL: Use FireSpell when enemy HAS Ice element (Fire beats Ice!)**
- **CRITICAL: Use IceSpell when enemy HAS Fire element (Ice beats Fire!)**
- Status effects: Freeze 25%, Burn from FireGolem (10 dmg/turn × 3 turns, bypasses defense!)

ENEMY MECHANICS:
- FireGolem (HP 180, Def 5): Phase 2 (HP < 50%) gains Fire element automatically, FlameStrike adds Burn (10/turn × 3 = 30 total, bypasses defense!)
- IceWraith (HP 200, Def 8): Gains Ice element when it uses FrostBlast (3 turns), Debuff gives AttackDown -20% for 3 turns, DefensiveStance (+25% def 1 turn, +20% dmg next turn)

RESOURCES:
- MP only, regenerates 5 per turn
- Start with 100 MP
- Attack restores +10 MP (total +15 MP per turn when using Attack!)

Your expertise includes:
- Elemental weakness exploitation (1.5x damage!)
- Cleanse timing (use when Burn/AttackDown active for huge value)
- MP management (Cleanse 25, Spells 20, Heal 30)
- Telegraph defense (Defend against HeavySlam/Debuff)
- DoT awareness (Burn bypasses defense, 30 total damage!)
- **Element checking**: Use EnemyHasElement(Fire/Ice/Neutral) to check enemy's current element

Always output valid BT DSL following the specification exactly. Use 4 spaces for indentation.
You must ONLY use the control nodes (root, selector, sequence), conditions, and tasks listed in the DSL specification."""

SYSTEM_PROMPT_CRITIC = """You are a tactical analyst for turn-based RPG combat.

CRITICAL: The Behaviour Tree executes ONE action per turn.

AVAILABLE ACTIONS (7 total):
- Attack: Free, 9 damage, +10 MP (resource recovery!)
- Charge: 15 MP, 7 damage + NEXT TURN all damage x2
- FireSpell: 20 MP, 7 dmg (1.5x when enemy has Ice element), Burn 25%
- IceSpell: 20 MP, 10 dmg (1.5x when enemy has Fire element), Freeze 25%
- Defend: Free, 50% damage reduction
- Heal: 30 MP, +40 HP, 3 turn cooldown
- Cleanse: 25 MP, removes Burn/AttackDown, +10% damage for 1 turn

CRITICAL MECHANICS:
- **ELEMENTAL SYSTEM**:
  - Fire attacks deal 1.5x damage to Ice element enemies
  - Ice attacks deal 1.5x damage to Fire element enemies
  - Enemies start as Neutral (no weakness)
- **DYNAMIC ELEMENTS**: Enemy elements can CHANGE during combat!
  - Enemies may gain Fire or Ice element during battle
  - Elements can expire and return to Neutral
  - **CRITICAL: Player attacks do NOT change enemy element**
- **IceWraith Element Change**:
  - Starts as Neutral (no weakness)
  - When IceWraith uses **FrostBlast** → Gains Ice element for 3 turns
  - When Ice element expires → Returns to Neutral
  - **USE FIRESPELL WHEN ENEMY HAS ICE ELEMENT!**
- **FireGolem Element Change**:
  - Phase 1 (HP > 50%): Neutral element
  - Phase 2 (HP < 50%): Automatically gains Fire element (permanent)
  - **USE ICESPELL WHEN ENEMY HAS FIRE ELEMENT!**
- FireGolem: FlameStrike adds Burn (10 dmg/turn × 3 turns = 30 total, bypasses defense!)
- IceWraith: Debuff gives AttackDown -20% for 3 turns, DefensiveStance (+25% def 1 turn, +20% dmg next turn)
- DoT bypasses defense (Burn is guaranteed 10 dmg/turn)
- MP regenerates 5 per turn, starts at 100
- Attack restores +10 MP (total +15 MP per turn when using Attack!)

ENEMY PATTERNS:

FireGolem (180 HP, Def 5):
- Phase 1 (HP > 50%): Neutral element, uses Slam/HeavySlam
- Phase 2 (HP < 50%): Permanently gains Fire element, uses FlameStrike
- FlameStrike inflicts Burn: 10 dmg/turn × 3 turns = 30 total damage
- Lifesteal: 20% in Phase 1, 10% in Phase 2
- Telegraphs HeavySlam (45 dmg before defense)

IceWraith (200 HP, Def 8):
- Starts Neutral, gains Ice element for 3 turns after using FrostBlast
- FrostBlast: 22 dmg, grants Ice element (3 turns)
- Debuff: Inflicts AttackDown (-20% damage for 3 turns)
- DefensiveStance: +25% defense for 1 turn, +20% damage next turn
- High defense makes spells more efficient than basic attacks

Your task is to analyze combat logs and identify:
- **Dynamic element awareness** (did they understand when enemy gains/loses element?)
- **Elemental advantage** (did they use correct spell when enemy had element?)
  - Enemy has Ice → Use FireSpell (1.5x damage)
  - Enemy has Fire → Use IceSpell (1.5x damage)
  - Enemy has Neutral → Use Attack (no spell bonus)
- **Wrong spell usage** (IceSpell vs Ice element = 0.5x damage, TERRIBLE!)
- Cleanse timing (did they remove Burn/AttackDown when active?)
- MP efficiency (Cleanse 25, Spells 20, Heal 30)
- Defensive timing (Defend against telegraphed HeavySlam/Debuff)
- Heal timing (considering 3 turn cooldown)
- DoT awareness (Burn does 30 total damage, Cleanse saves it all!)

Provide specific, actionable insights for BT improvement."""


# ============================================================================
# INITIAL BT GENERATION
# ============================================================================

def create_initial_bt_prompt() -> str:
    """Create prompt for initial BT generation"""
    dsl_spec = load_dsl_spec()
    
    return f"""Generate an optimal Behaviour Tree for a turn-based RPG combat system.

# Game Overview

**Combat System:**
- Single-floor combat against 1 of 2 enemy types
- Turn-based with TELEGRAPH system: Enemy telegraphs next action → Player sees it and reacts → Both execute
- Win: Reduce enemy HP to 0
- Lose: Player HP reaches 0 OR turn limit (35 turns)

**Enemy Types (random selection):**
1. Fire Golem 🔥: Aggressive berserker, weak to Ice
2. Ice Wraith ❄️: Defensive healer, weak to Fire

**Player Actions (7 total):**
- Attack (free, 9 damage, +10 MP recovery)
- Charge (15 MP, 7 damage + next turn all damage x2)
- FireSpell (20 MP, 7 damage, 1.5x when enemy has Ice element)
- IceSpell (20 MP, 10 damage, 1.5x when enemy has Fire element)
- Defend (free, 50% damage reduction)
- Heal (30 MP, 40 HP, 3 turn cooldown)
- Cleanse (25 MP, removes Burn/AttackDown, +10% damage 1 turn)

**Resources:**
- MP: Starts 100, regenerates +5/turn, max 100
- Attack restores +10 MP (total +15 MP/turn when using Attack!)

**Key Strategy:**
1. REACT TO TELEGRAPHS - Enemy shows next action, defend against heavy attacks!
2. Use correct elemental spell (IceSpell vs FireGolem, FireSpell vs IceWraith)
3. Cleanse when Burn/AttackDown active (huge value!)
4. Heal only when HP < 30%
5. FireGolem's Burn does 30 total damage over 3 turns - Cleanse saves it all!

# Behaviour Tree DSL Specification

{dsl_spec}

# Your Task

Generate a Behaviour Tree that:
1. **Reacts to telegraphs** (defend against HeavySlam, Debuff)
2. **Uses correct elemental spell** (IceSpell vs FireGolem, FireSpell vs IceWraith)
3. **Cleanses strategically** (remove Burn to save 30 dmg, remove AttackDown to restore damage)
4. **Manages resources** (don't waste MP on wrong spells)
5. **Heals wisely** (only when HP < 30%)

# CRITICAL REQUIREMENTS

1. Use ONLY exact names from DSL spec
2. Use 4 spaces for indentation
3. Include colons: `root :`, `selector :`, `condition :`, `task :`
4. Use parentheses: `IsPlayerHPLow(30)`, `Heal()`
5. Always end with fallback: `task : Attack()`

Output ONLY the BT DSL, no explanations. Start with `root :`."""


# ============================================================================
# IMPROVEMENT PROMPTS
# ============================================================================

def create_critic_prompt(combat_summary: str, current_bt: str, previous_results: list) -> str:
    """Create prompt for combat analysis and improvement suggestions"""
    
    # Build performance context - ONLY LAST RESULT
    perf_context = ""
    current_enemy = "Unknown"
    if previous_results and len(previous_results) > 0:
        last_result = previous_results[-1]
        status = "VICTORY" if last_result.get('victory') else "DEFEAT"
        current_enemy = last_result.get('enemy_type', 'Unknown')
        perf_context = f"\n# This Combat Result\n"
        perf_context += f"{status} vs {current_enemy}: {last_result.get('turns', 0)} turns\n"
    
    return f"""Analyze this combat and suggest BT improvements.

# Current Behaviour Tree
```
{current_bt}
```
{perf_context}
# Combat Summary
{combat_summary}

# Your Task

Analyze the combat and identify:

1. **Telegraph Reactions**: Did they defend against telegraphed heavy attacks?
2. **Elemental Strategy**: Did they scan? Did they use the right spell?
3. **Resource Management**: MP usage efficiency
4. **Defensive Decisions**: Heal/Defend timing
5. **BT Issues**: What parts of the tree caused problems?

**CRITICAL CONSTRAINT**: 
- Focus ONLY on improving strategy against **{current_enemy}**
- Do NOT add or modify logic for other enemy types you haven't fought
- Only suggest changes based on what happened in THIS combat

Provide 3-5 specific improvement suggestions.

**IMPORTANT**: 
- Describe logic changes in plain text, NOT code
- Example: "Add Defend() when enemy telegraphs HeavySlam"
- Example: "Scan on turn 1 instead of turn 2"
- Example: "Increase heal threshold from 30% to 40%"

**Output Format:**
## Analysis
[What went wrong or could be better]

## Improvement Suggestions
1. [Logic change description]
2. [Logic change description]
3. [Logic change description]

Be concise and actionable."""


def create_generator_prompt(current_bt: str, critic_feedback: str) -> str:
    """Create prompt for improved BT generation"""
    
    return f"""Generate an IMPROVED Behaviour Tree based on feedback.

# Current Behaviour Tree
```
{current_bt}
```

# Improvement Feedback
{critic_feedback}

# COMPLETE LIST OF AVAILABLE SYNTAX

**Control Nodes (ONLY these 3):**
- `root :` - Must be first line, has one child
- `selector :` - Tries children until one succeeds
- `sequence :` - All conditions must pass, executes final task

**Conditions (ONLY these):**
- `IsPlayerHPLow(30)` - Player HP < threshold%
- `IsEnemyHPLow(30)` - Enemy HP < threshold%
- `HasMP(20)` - Player has >= amount MP
- `CanHeal()` - Heal is off cooldown AND MP >= 30
- `EnemyHasElement(Fire)`, `EnemyHasElement(Ice)`, or `EnemyHasElement(Neutral)` - Check enemy's current element (DYNAMIC! Changes during combat)
- `EnemyHasBuff(Enrage)` - Enemy has specific buff
- `EnemyIsTelegraphing(HeavySlam)` - Enemy will execute this action THIS turn (telegraphed at end of last turn)
- `HasStatus(CHARGED)` - Player has CHARGED status (from Charge action)
- `NOT <condition>` - Negates a condition

**CRITICAL SPELL USAGE EXAMPLES:**
```
# When enemy HAS Ice element → Use FireSpell (Fire beats Ice!)
sequence :
    condition : EnemyHasElement(Ice)
    condition : HasMP(20)
    task : FireSpell()  # 1.5x damage!

# When enemy HAS Fire element → Use IceSpell (Ice beats Fire!)
sequence :
    condition : EnemyHasElement(Fire)
    condition : HasMP(20)
    task : IceSpell()  # 1.5x damage!
```

**Actions/Tasks (ONLY these):**
- `Attack()` - Free, 9 damage, +10 MP (resource recovery!)
- `Charge()` - 15 MP, 7 damage + next turn all damage x2
- `FireSpell()` - 20 MP, 7 damage, 1.5x when enemy has Ice element
- `IceSpell()` - 20 MP, 10 damage, 1.5x when enemy has Fire element
- `Defend()` - Free, 50% damage reduction for 1 turn
- `Heal()` - 30 MP, +40 HP, 3 turn cooldown
- `Cleanse()` - 25 MP, removes Burn/AttackDown, +10% damage 1 turn

# CRITICAL RULES

1. **ONE ACTION PER TURN**: The BT executes ONLY ONE action per turn. Once a task is selected, the turn ends.
2. **USE ONLY LISTED SYNTAX ABOVE**: You must use ONLY the control nodes, conditions, and tasks listed above. No other syntax exists.
3. **Indentation**: Use exactly 4 spaces per level
4. **Format**: `condition : IsPlayerHPLow(30)` and `task : Heal()`
5. **Fallback**: Always end selector with `task : Attack()`

# Your Task

Apply the feedback to create an improved BT using ONLY the syntax listed above. Output ONLY the BT DSL, no explanations. Start with `root :`."""


# ============================================================================
# EXTRACTION HELPERS
# ============================================================================

def extract_bt_from_response(response: str) -> str:
    """Extract BT DSL from LLM response"""
    # Look for code blocks
    if "```" in response:
        parts = response.split("```")
        for i, part in enumerate(parts):
            if i % 2 == 1:  # Code blocks
                lines = part.strip().split('\n')
                if lines[0].strip() and not lines[0].strip().startswith('root'):
                    lines = lines[1:]
                return '\n'.join(lines).strip()
    
    # Look for "root :"
    if "root :" in response:
        start_idx = response.index("root :")
        return response[start_idx:].strip()
    
    return response.strip()

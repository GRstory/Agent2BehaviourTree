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

CRITICAL: The Behaviour Tree executes ONLY ONE action per turn. Once an action is selected, the turn ends immediately.

Your expertise includes:
- Elemental weakness exploitation (Fire/Ice/Lightning rock-paper-scissors)
- Resource management (TP/MP optimization)
- Status effect timing and usage
- Enemy pattern recognition and adaptation
- Defensive vs aggressive strategy selection

Always output valid BT DSL following the specification exactly. Use 4 spaces for indentation.
You must ONLY use the control nodes (root, selector, sequence), conditions, and tasks listed in the DSL specification."""

SYSTEM_PROMPT_CRITIC = """You are a tactical analyst for turn-based RPG combat.

CRITICAL: Remember that the Behaviour Tree executes ONLY ONE action per turn. The BT cannot perform multiple actions in a single turn.

Your task is to analyze combat logs and identify:
- Elemental advantage usage (did they exploit weakness?)
- Resource efficiency (TP/MP management)
- Status effect timing
- Defensive decisions (Defend, Heal timing)
- Enemy pattern adaptation

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
- Single-floor combat against 1 of 3 enemy types
- Turn-based with TELEGRAPH system: Enemy telegraphs next action → Player sees it and reacts → Both execute
- Win: Reduce enemy HP to 0
- Lose: Player HP reaches 0 OR turn limit (35 turns)

**Enemy Types (random selection):**
1. Fire Golem 🔥: Aggressive berserker, weak to Ice
2. Ice Wraith ❄️: Defensive healer, weak to Lightning
3. Thunder Drake ⚡: Balanced tactical, weak to Fire

**Player Actions (8 total):**
- Attack (free, builds TP)
- PowerStrike (30 TP, high damage)
- FireSpell, IceSpell, LightningSpell (20 MP each, elemental)
- Defend (free, -50% damage, +20 TP)
- Heal (30 MP, 45 HP, 3 turn cooldown)
- Scan (15 MP, reveals enemy weakness)

**Resources:**
- TP: Starts 50, regenerates +15/turn, max 100
- MP: Starts 100, regenerates +12/turn, max 100

**Key Strategy:**
1. REACT TO TELEGRAPHS - Enemy shows next action, defend against heavy attacks!
2. Scan enemy early (turn 1-2) to identify weakness
3. Spam effective elemental spell (1.5x damage!)
4. Heal only when HP < 30%

# Behaviour Tree DSL Specification

{dsl_spec}

# Your Task

Generate a Behaviour Tree that:
1. **Reacts to telegraphs** (defend against HeavySlam, ThunderStrike, etc.)
2. **Scans early** to identify enemy weakness
3. **Exploits elemental advantage** (1.5x damage is huge!)
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
    
    # Build performance context
    perf_context = ""
    if previous_results:
        victories = sum(1 for r in previous_results if r.get('victory', False))
        total = len(previous_results)
        perf_context = f"\n# Recent Performance\n"
        perf_context += f"Last {total} battles: {victories} victories, {total - victories} defeats\n"
        for i, r in enumerate(previous_results[-3:]):
            status = "WIN " if r.get('victory') else "LOSS"
            perf_context += f"  {status} vs {r.get('enemy_type', 'Unknown')}: {r.get('turns', 0)} turns\n"
    
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
3. **Resource Management**: TP/MP usage efficiency
4. **Defensive Decisions**: Heal/Defend timing
5. **BT Issues**: What parts of the tree caused problems?

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
- `HasTP(30)` - Player has >= amount TP
- `HasMP(20)` - Player has >= amount MP
- `CanHeal()` - Heal is off cooldown AND MP >= 30
- `EnemyWeakTo(Fire)` or `EnemyWeakTo(Ice)` or `EnemyWeakTo(Lightning)` - Enemy weak to element
- `HasScannedEnemy()` - Enemy has been scanned
- `EnemyHasBuff(Enrage)` - Enemy has specific buff
- `EnemyIsTelegraphing(HeavySlam)` - Enemy will execute this action THIS turn (telegraphed at end of last turn)
- `IsTurnEarly(2)` - Turn count <= threshold

**Actions/Tasks (ONLY these):**
- `Attack()` - 0 TP, 15-18 damage, gains +15 TP
- `PowerStrike()` - 30 TP, 40-50 damage
- `FireSpell()` - 20 MP, 25-30 Fire damage, 1.5x vs Ice
- `IceSpell()` - 20 MP, 25-30 Ice damage, 1.5x vs Lightning
- `LightningSpell()` - 20 MP, 25-30 Lightning damage, 1.5x vs Fire
- `Defend()` - 0 TP, -50% damage for 1 turn, gains +20 TP
- `Heal()` - 30 MP, +45 HP, 3 turn cooldown
- `Scan()` - 15 MP, reveals enemy weakness

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

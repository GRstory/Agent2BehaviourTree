# Behaviour Tree DSL Specification

## Overview
This DSL defines Behaviour Trees for controlling a player character in a turn-based dungeon crawler game.

## Basic Structure

```
root :
    <control_node> :
        <child_nodes>
```

### Indentation Rules
- Use **4 spaces** per indentation level
- Each node must be properly indented relative to its parent
- Colons (`:`) are required after node types

## Node Types

### 1. Control Nodes

#### Root Node
```
root :
```
- Must be the first line
- Can have exactly one child (usually a selector or sequence)

#### Selector Node
```
selector :
```
- Tries children in order until one succeeds
- Returns success on first successful child
- Returns failure if all children fail

#### Sequence Node
```
sequence :
```
- Executes children in order until one fails
- Returns success only if all children succeed
- Returns failure on first failed child

### 2. Condition Nodes

Conditions evaluate game state and return true/false. They do NOT execute actions.

#### Player HP Conditions

```
condition : IsPlayerHPLow(threshold)
```
- Returns true if player HP percentage < threshold
- Example: `condition : IsPlayerHPLow(30)` - true if HP < 30%
- Default threshold: 30

```
condition : IsPlayerHPHigh(threshold)
```
- Returns true if player HP percentage > threshold
- Example: `condition : IsPlayerHPHigh(70)` - true if HP > 70%
- Default threshold: 70

#### Enemy HP Conditions

```
condition : IsEnemyHPLow(threshold)
```
- Returns true if enemy HP percentage < threshold
- Example: `condition : IsEnemyHPLow(25)` - true if enemy HP < 25%
- Default threshold: 30

```
condition : IsEnemyHPHigh(threshold)
```
- Returns true if enemy HP percentage > threshold
- Example: `condition : IsEnemyHPHigh(60)` - true if enemy HP > 60%
- Default threshold: 70

#### Ability Conditions

```
condition : CanHeal()
```
- Returns true if Heal ability is off cooldown and can be used
- No parameters

```
condition : IsDefending()
```
- Returns true if player is currently in defend stance
- No parameters

#### Combo Conditions

```
condition : HasComboReady(combo_name)
```
- Returns true if the specified combo is ready to be completed
- Valid combo names:
  - `TripleLight` - Two Light Attacks have been performed, third will trigger combo
  - `HeavyFinisher` - Two Light Attacks have been performed, Heavy Attack will trigger combo
  - `CounterStrike` - Defend has been performed, Heavy Attack will trigger combo
- Example: `condition : HasComboReady(TripleLight)`

#### Floor Conditions

```
condition : IsFloorBoss()
```
- Returns true if current floor is a boss floor (5 or 10)
- No parameters

```
condition : IsTurnEarly(threshold)
```
- Returns true if turn count <= threshold
- Example: `condition : IsTurnEarly(3)` - true for first 3 turns
- Default threshold: 3

### 3. Action/Task Nodes

Actions execute game actions and always succeed. Use `task :` keyword.

```
task : LightAttack()
```
- Performs a Light Attack (base damage)
- Part of combo chains

```
task : HeavyAttack()
```
- Performs a Heavy Attack (2x base damage)
- Can finish combos

```
task : Defend()
```
- Increases defense for this turn and next enemy turn
- Part of Counter Strike combo

```
task : Heal()
```
- Restores 30 HP
- Has 3-turn cooldown
- Fails if on cooldown (but BT continues)

## Complete Example

```
root :
    selector :
        sequence :
            condition : IsPlayerHPLow(30)
            condition : CanHeal()
            task : Heal()
        sequence :
            condition : HasComboReady(TripleLight)
            task : LightAttack()
        sequence :
            condition : IsEnemyHPLow(25)
            task : HeavyAttack()
        sequence :
            condition : IsPlayerHPLow(50)
            task : Defend()
        task : LightAttack()
```

## Important Rules

1. **Always have a fallback action**: The last child of the root selector should be an unconditional action (usually `task : LightAttack()`)

2. **Proper indentation**: Each level must be indented exactly 4 spaces more than its parent

3. **Valid node names**: Only use the condition and action names listed above. Custom names will cause errors.

4. **Combo awareness**: Use `HasComboReady()` conditions to detect when combos can be triggered

5. **Survival first**: Consider healing/defending before aggressive actions

6. **No parameters for actions**: Actions like `LightAttack()` don't take parameters (the parentheses are required but empty)

## Common Mistakes to Avoid

❌ **Wrong**: `condition : isPlayerHP <= 30` (invalid syntax)
✅ **Correct**: `condition : IsPlayerHPLow(30)`

❌ **Wrong**: `action : UseAbility(Heal)` (invalid action name)
✅ **Correct**: `task : Heal()`

❌ **Wrong**: `condition : IsAbilityReady(Heal)` (invalid condition name)
✅ **Correct**: `condition : CanHeal()`

❌ **Wrong**: Using 2 spaces for indentation
✅ **Correct**: Using 4 spaces for indentation

❌ **Wrong**: `task : LightAttack` (missing parentheses)
✅ **Correct**: `task : LightAttack()`

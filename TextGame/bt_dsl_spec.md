# Behaviour Tree DSL Specification

## Overview

This document defines the Domain-Specific Language (DSL) for creating Behaviour Trees that control the player in the dungeon game. The DSL uses indentation-based syntax (4 spaces per level) to define tree structure.

## Syntax Rules

1. **Indentation**: Use 4 spaces per level (no tabs)
2. **Node Format**: `node_type : parameter` or just `node_type`
3. **Root Node**: Must be at indentation level 0
4. **Hierarchy**: Children are indented one level deeper than their parent

## Node Types

### Control Flow Nodes

#### `root`
- The top-level node of the tree
- Must have exactly one child
- No parameters

#### `selector`
- Tries children in order until one succeeds
- Succeeds if any child succeeds
- Fails if all children fail
- No parameters

#### `sequence`
- Executes children in order
- All conditions must pass for sequence to continue
- Returns the action from the final child
- Fails if any condition fails
- No parameters

### Condition Nodes

All condition nodes use the format: `condition : ConditionName(parameter)`

#### `IsPlayerHPLow(threshold)`
- **Parameter**: HP percentage threshold (0-100)
- **Returns**: True if player HP < threshold%
- **Example**: `condition : IsPlayerHPLow(30)` - True when player HP below 30%

#### `IsPlayerHPHigh(threshold)`
- **Parameter**: HP percentage threshold (0-100)
- **Returns**: True if player HP > threshold%
- **Example**: `condition : IsPlayerHPHigh(70)` - True when player HP above 70%

#### `IsEnemyHPLow(threshold)`
- **Parameter**: HP percentage threshold (0-100)
- **Returns**: True if enemy HP < threshold%
- **Example**: `condition : IsEnemyHPLow(25)` - True when enemy HP below 25%

#### `IsEnemyHPHigh(threshold)`
- **Parameter**: HP percentage threshold (0-100)
- **Returns**: True if enemy HP > threshold%
- **Example**: `condition : IsEnemyHPHigh(80)` - True when enemy HP above 80%

#### `CanHeal()`
- **Parameter**: None
- **Returns**: True if heal is not on cooldown
- **Example**: `condition : CanHeal()`

#### `IsDefending()`
- **Parameter**: None
- **Returns**: True if player is currently in defend stance
- **Example**: `condition : IsDefending()`

#### `HasComboReady(combo_name)`
- **Parameter**: Combo name - "TripleLight", "HeavyFinisher", or "CounterStrike"
- **Returns**: True if the combo is one action away from triggering
- **Example**: `condition : HasComboReady(TripleLight)`

#### `IsFloorBoss()`
- **Parameter**: None
- **Returns**: True if current floor is a boss floor (5 or 10)
- **Example**: `condition : IsFloorBoss()`

#### `IsTurnEarly(threshold)`
- **Parameter**: Turn count threshold
- **Returns**: True if turn count <= threshold
- **Example**: `condition : IsTurnEarly(3)` - True in first 3 turns

### Action Nodes

All action nodes use the format: `task : ActionName()`

#### `LightAttack()`
- Executes a light attack (base damage)
- Part of combo chains
- **Example**: `task : LightAttack()`

#### `HeavyAttack()`
- Executes a heavy attack (2x base damage)
- Can be part of combos
- **Example**: `task : HeavyAttack()`

#### `Defend()`
- Increases defense for this turn and the next enemy turn
- Enables Counter Strike combo
- **Example**: `task : Defend()`

#### `Heal()`
- Restores 30 HP
- Has 3-turn cooldown after use
- Fails if on cooldown
- **Example**: `task : Heal()`

## Combo System

### Available Combos

1. **Triple Light** (4x damage multiplier)
   - Pattern: Light Attack → Light Attack → Light Attack
   - The third light attack deals 4x damage
   
2. **Heavy Finisher** (3x damage multiplier)
   - Pattern: Light Attack → Light Attack → Heavy Attack
   - The heavy attack deals 3x damage

3. **Counter Strike** (2.5x damage multiplier)
   - Pattern: Defend → Heavy Attack
   - The heavy attack after defending deals 2.5x damage

### Combo Strategy Tips

- Use `HasComboReady(TripleLight)` to check if 2 light attacks have been performed
- Use `HasComboReady(CounterStrike)` to check if just defended
- Combos significantly increase damage output
- Plan sequences to build up to combos

## Complete Example

```
root :
    selector :
        sequence :
            condition : IsPlayerHPLow(25)
            condition : CanHeal()
            task : Heal()
        sequence :
            condition : IsPlayerHPLow(40)
            condition : IsEnemyHPHigh(70)
            task : Defend()
        sequence :
            condition : HasComboReady(TripleLight)
            task : LightAttack()
        sequence :
            condition : HasComboReady(CounterStrike)
            task : HeavyAttack()
        sequence :
            condition : IsEnemyHPLow(30)
            task : HeavyAttack()
        task : LightAttack()
```

## Strategy Explanation

This example BT implements a balanced strategy:

1. **Emergency Healing**: If HP < 25% and heal available, heal immediately
2. **Defensive Stance**: If HP < 40% and enemy is strong, defend
3. **Combo Execution**: If Triple Light combo is ready, complete it
4. **Counter Attack**: If just defended, use heavy attack for Counter Strike
5. **Finishing Move**: If enemy is weak, use heavy attack to finish
6. **Default Action**: Otherwise, use light attack to build combos

## Best Practices

1. **Always have a fallback**: End selectors with a simple action that always succeeds
2. **Check heal cooldown**: Always pair heal actions with `CanHeal()` condition
3. **Prioritize survival**: Put healing/defending sequences before aggressive ones
4. **Leverage combos**: Use conditions to detect combo opportunities
5. **Adapt to enemy**: Use enemy HP conditions to adjust tactics
6. **Consider floor difficulty**: Use `IsFloorBoss()` for special boss strategies

## Common Mistakes to Avoid

1. ❌ **No fallback action**: Selector with no guaranteed success path
2. ❌ **Healing without checking cooldown**: Wastes turns
3. ❌ **Ignoring combos**: Missing significant damage opportunities
4. ❌ **Too aggressive**: Not healing/defending when HP is low
5. ❌ **Too defensive**: Healing when HP is already high
6. ❌ **Inconsistent indentation**: Must use exactly 4 spaces per level

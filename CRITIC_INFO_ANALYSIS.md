# Critic LLM에게 전달되는 정보

## 📋 현재 전달 내용

### 1. **Current Behaviour Tree** (`current_bt`)
```
현재 사용 중인 BT의 전체 DSL 코드
```

### 2. **Combat Summary** (`combat_log` - 실제로는 summary만!)
```
=== COMBAT SUMMARY ===

Result: VICTORY/DEFEAT
Turns: 5
Final Player HP: 0/100 (0%)
Final Enemy HP: 51/180 (28%)

Enemy: FireGolem (Fire)
Weakness: Ice (scanned)

Resources Remaining: TP 100/100, MP 56/100
```

**문제점**: 턴별 상세 로그가 없음! 단순 요약만 전달됨.

### 3. **Previous Results** (최근 3개 전투)
```python
[
    {
        'victory': False,
        'turns': 5,
        'enemy_type': 'FireGolem'
    },
    ...
]
```

---

## ❌ 전달되지 않는 중요 정보

### 1. **턴별 상세 로그**
```
=== TURN 1 ===
[!] ENEMY TELEGRAPHS: HeavySlam
Player: HP 100%, TP 50, MP 100
Enemy: HP 100%, Element: Fire (3 turns)

Action: Attack -> 7 dmg
Enemy: HeavySlam -> 37 dmg
```

**이게 없으면:**
- Critic이 "왜 방어 안 했는지" 모름
- "어떤 속성일 때 어떤 스킬 썼는지" 모름
- "텔레그래프 반응 여부" 판단 불가

### 2. **적의 속성 변화**
```
Enemy: HP 96%, Element: Fire (3 turns)
Enemy: HP 77%, Element: Fire (2 turns)
Enemy: HP 58%, Element: Neutral
```

**이게 없으면:**
- "적이 Fire일 때 IceSpell 썼는지" 모름
- "속성 약점 활용 여부" 판단 불가

### 3. **행동 히스토리**
```
[LAST ACTION] Enemy used: HeavySlam
[HISTORY] Recent actions: ['HeavySlam', 'RageBuff', 'Slam']
```

**이게 없으면:**
- "적의 패턴 학습 여부" 판단 불가
- "EnemyLastAction 활용 여부" 모름

---

## 🎯 개선 필요

### 현재
```python
combat_log=result['summary']  # 요약만!
```

### 개선안
```python
combat_log=result['combat_log']  # 전체 턴별 로그!
# 또는
combat_log=result['combat_log'] + "\n\n" + result['summary']
```

---

## 📊 실제 예시

### 현재 Critic이 보는 것
```
Result: DEFEAT
Turns: 5
Final Player HP: 0/100 (0%)
Final Enemy HP: 51/180 (28%)
Enemy: FireGolem (Fire)
```

**Critic의 한계:**
- "5턴 동안 뭐했는지 모름"
- "왜 졌는지 모름"
- "어떤 실수했는지 모름"

### 개선 후 Critic이 볼 것
```
=== TURN 1 ===
[!] ENEMY TELEGRAPHS: HeavySlam
Player: HP 100%, TP 50, MP 100
Enemy: HP 100%, Element: Neutral

Action: Attack -> 7 dmg
Enemy: HeavySlam -> 37 dmg [Gained FIRE element!]

=== TURN 2 ===
Player: HP 63%, TP 80, MP 100
Enemy: HP 96%, Element: Fire (3 turns)  ← 약점 노출!

Action: Attack -> 7 dmg  ← IceSpell 안 씀!
Enemy: Slam -> 13 dmg

...
```

**Critic의 분석 가능:**
- "턴 2에서 적이 Fire인데 IceSpell 안 씀!"
- "HeavySlam 텔레그래프 무시함!"
- "속성 약점 활용 안 함!"

---

## 🔧 수정 필요

`runner.py` 199번 줄:
```python
# 현재
combat_log=result['summary']

# 개선
combat_log=result['combat_log'] + "\n\n" + result['summary']
```

이렇게 하면 Critic이 **턴별 상세 정보 + 요약**을 모두 볼 수 있습니다!

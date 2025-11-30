# BT DSL 업데이트 요약

## 변경 사항

### 1. HP 조건을 추상 레벨로 통일

#### 이전 (숫자 기반)
```
condition : IsPlayerHPLow(30)    # HP < 30%
condition : IsEnemyHPHigh(70)    # Enemy HP > 70%
```

#### 변경 후 (추상 레벨)
```
condition : IsPlayerHPLevel(Low)   # HP 0-33%
condition : IsPlayerHPLevel(Mid)   # HP 33-66%
condition : IsPlayerHPLevel(High)  # HP 66-100%

condition : IsEnemyHPLevel(Low)    # Enemy HP 0-33%
condition : IsEnemyHPLevel(Mid)    # Enemy HP 33-66%
condition : IsEnemyHPLevel(High)   # Enemy HP 66-100%
```

#### 장점
- ✅ 로그와 BT가 같은 용어 사용 (일관성)
- ✅ LLM이 이해하기 쉬움 (Low/Mid/High는 직관적)
- ✅ 숫자 임계값 고민 불필요
- ✅ 더 추상적이고 자연스러운 표현

---

### 2. 연속공격(콤보) 자연스럽게 설명

#### 핵심 아이디어
**"콤보를 만들기 위한 특별한 함수가 필요 없다"**

콤보는 **같은 행동을 반복**하면 자동으로 발생합니다!

#### DSL 문서에 추가된 설명

```markdown
💡 COMBO STRATEGY - How to Build Combos:

Combos are built by **repeating the same action**. No special function needed!

- **Want Triple Light (4x damage)?**
  Turn 1: LightAttack()  ← First hit
  Turn 2: LightAttack()  ← Second hit (combo building...)
  Turn 3: LightAttack()  ← BOOM! 4x damage!
  
  Just use `task : LightAttack()` as your default action!

- **Want Heavy Finisher (3x damage)?**
  Turn 1: LightAttack()  ← First hit
  Turn 2: LightAttack()  ← Second hit (combo ready!)
  Turn 3: HeavyAttack()  ← BOOM! 3x damage!
  
  Use `HasComboReady(HeavyFinisher)` to detect when ready

- **Want Counter Strike (2.5x damage)?**
  Turn 1: Defend()       ← Block incoming damage
  Turn 2: HeavyAttack()  ← BOOM! 2.5x damage!
  
  Use `HasComboReady(CounterStrike)` to detect when ready

**Key Insight**: You don't need a special "start combo" function. 
Just use the same attack repeatedly, and combos happen automatically!
```

#### 프롬프트에 추가된 설명

```
**Combo System (CRITICAL FOR VICTORY):**
Combos are built by **repeating the same action**. No special setup needed!

1. **Triple Light** (4x damage): Just use Light Attack 3 times in a row!
   - Turn 1: Light Attack (normal damage)
   - Turn 2: Light Attack (normal damage)
   - Turn 3: Light Attack (BOOM! 4x damage)
   - **Strategy**: Make Light Attack your default action to naturally build this combo
```

---

## LLM이 이해하는 방식

### 이전
```
"콤보를 사용하려면... 음... HasComboReady를 체크하고... 
그런데 콤보를 어떻게 시작하지? 특별한 함수가 있나?"
```

### 변경 후
```
"아! 그냥 약공격을 3번 반복하면 Triple Light 콤보가 되는구나!
기본 행동을 약공격으로 하면 자연스럽게 콤보가 쌓이겠네!"
```

---

## 예제 BT (변경 후)

```
root :
    selector :
        # 생존 우선
        sequence :
            condition : IsPlayerHPLevel(Low)  ← 추상 레벨 사용
            condition : CanHeal()
            task : Heal()
        
        # 콤보 마무리 (자동으로 쌓임)
        sequence :
            condition : HasComboReady(TripleLight)
            task : LightAttack()  ← 3번째 약공격 = 4배!
        
        # 적 처치
        sequence :
            condition : IsEnemyHPLevel(Low)  ← 추상 레벨 사용
            task : HeavyAttack()
        
        # 기본: 약공격 (콤보 자동 축적)
        task : LightAttack()  ← 이것만 반복해도 콤보가 쌓임!
```

---

## 업데이트된 파일

1. ✅ `TextGame/bt_dsl_spec.md` - DSL 문서 완전 재작성
2. ✅ `TextGame/prompts.py` - LLM 프롬프트 업데이트
3. ✅ `README.md` - 콤보 설명 개선

---

## 기대 효과

### 1. 일관성 향상
- 로그: "Player HP: Low"
- BT: `IsPlayerHPLevel(Low)`
- 같은 용어 사용으로 혼란 감소

### 2. 콤보 활용 증가
- LLM이 "그냥 반복하면 된다"는 것을 명확히 이해
- 특별한 함수 없이도 콤보 전략 수립 가능
- 기본 행동을 약공격으로 하면 자연스럽게 Triple Light 발동

### 3. 더 나은 전략
- Low/Mid/High 레벨로 더 명확한 조건 분기
- 콤보를 의도적으로 활용하는 BT 생성 가능
- 숫자 임계값 고민 없이 직관적인 전략 수립

---

## 다음 단계

이제 LLM이 생성하는 BT에서:
- ✅ `IsPlayerHPLevel(Low)` 같은 추상 레벨 사용
- ✅ 기본 행동을 `LightAttack()`으로 설정하여 자연스럽게 콤보 축적
- ✅ `HasComboReady()`로 콤보 타이밍 감지
- ✅ 더 효율적이고 이해하기 쉬운 전략

을 기대할 수 있습니다!

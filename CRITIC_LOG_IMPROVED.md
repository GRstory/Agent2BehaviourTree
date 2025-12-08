# Critic LLM이 받는 정보 (개선 후)

## ✅ 이제 Critic이 볼 수 있는 것

### 1. 턴별 상세 로그
```
=== TURN 1 ===
Player: HP 63%, TP 80, MP 100
Enemy: HP 96%, Element: Fire (3 turns)  ← 속성 정보!

Action: IceSpell (MP -20) -> 34 dmg [SUPER EFFECTIVE!]
Enemy: HeavySlam -> 37 dmg
```

**Critic이 분석 가능:**
- ✅ 각 턴에서 무슨 행동 했는지
- ✅ 적의 속성 변화 (Neutral → Fire)
- ✅ 속성 약점 활용 여부 ([SUPER EFFECTIVE!])
- ✅ 리소스 사용 패턴 (MP 소모)

### 2. 텔레그래프 정보
```
=== TURN 3 ===
[!] ENEMY TELEGRAPHS: HeavySlam  ← 예고!
Player: HP 26%, TP 100, MP 72
Enemy: HP 58%, Element: Fire (3 turns)

Action: IceSpell (MP -20) -> 34 dmg  ← 방어 안 함!
Enemy: HeavySlam -> 37 dmg
```

**Critic이 분석 가능:**
- ✅ 텔레그래프 반응 여부
- ✅ "HeavySlam 예고했는데 Defend 안 씀!"
- ✅ HP 낮은데 방어 안 한 실수 파악

### 3. 패턴 분석 힌트
```
=== PATTERN ANALYSIS HINTS ===

Enemy Action History (last 5): HeavySlam, HeavySlam, HeavySlam
Enemy Last Action: HeavySlam

Final Enemy Element: Fire
Element Duration Remaining: 3 turns
```

**Critic이 분석 가능:**
- ✅ 적이 HeavySlam 3번 연속 사용 (패턴!)
- ✅ "적이 HeavySlam 자주 씀 → Defend 필요"
- ✅ Fire 속성 3턴 남음 → IceSpell 계속 유효

### 4. 전투 요약
```
Result: DEFEAT
Turns: 4
Final Player HP: 0/100 (0%)
Final Enemy HP: 71/180 (39%)

Enemy: FireGolem (Fire)
Weakness: Unknown (not scanned)  ← Scan 안 함!
```

**Critic이 분석 가능:**
- ✅ "Scan 안 해서 약점 모름"
- ✅ "적 HP 39% 남았는데 졌음 → 방어 부족"

---

## 🎯 Critic의 분석 예시

### 이전 (요약만 봤을 때)
```
"5턴 만에 졌네요. 뭐가 문제인지 모르겠어요."
```

### 개선 후 (턴별 로그 + 힌트)
```
분석:
1. 턴 3에서 HeavySlam 텔레그래프 무시 → 37 데미지 받음
2. HP 26%인데 방어 안 하고 공격 선택 → 위험
3. 적이 HeavySlam 3번 연속 → 패턴 학습 필요
4. Fire 속성일 때 IceSpell 잘 사용 (SUPER EFFECTIVE!)
5. Scan 안 해서 공식 약점 확인 못 함

개선 제안:
1. EnemyIsTelegraphing(HeavySlam) → Defend() 추가
2. HP < 30% 일 때 방어 우선순위 높이기
3. EnemyUsedRecently(HeavySlam) → Defend() 고려
4. 턴 1-2에 Scan() 추가
```

---

## 📊 힌트 vs 정답

### ❌ 정답을 알려주는 것 (안 함!)
```
"턴 3에서 Defend()를 써야 했습니다."
"IceSpell을 쓰세요."
```

### ✅ 힌트만 주는 것 (현재)
```
턴별 로그:
- 적 속성: Fire (3 turns)
- 텔레그래프: HeavySlam
- 플레이어 행동: IceSpell
- 결과: 37 데미지 받음

패턴 힌트:
- 적이 HeavySlam 3번 연속
- Fire 속성 3턴 남음
```

**Critic이 스스로 분석:**
- "HeavySlam 텔레그래프 → Defend 필요"
- "Fire 속성 → IceSpell 효과적"
- "HeavySlam 패턴 → 방어 전략 필요"

---

## 🎮 실제 효과

### Critic의 피드백 품질 향상
- **이전**: "더 잘하세요" (구체적이지 않음)
- **개선**: "턴 3 HeavySlam 텔레그래프에 Defend 추가" (구체적!)

### LLM 학습 가능
- 텔레그래프 시스템 이해
- 속성 약점 활용 학습
- 패턴 기반 방어 전략 개발

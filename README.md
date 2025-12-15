# Agent2BehaviourTree

LLM이 전투 로그를 분석하고 Behaviour Tree를 반복적으로 개선하는 시스템

## 빠른 시작

### 1. 설치
```bash
pip install -r requirements.txt
```

### 2. API 키 설정
`.env` 파일 생성:
```
GEMINI_API_KEY=your_api_key_here
```

### 3. 실행

#### Enemy Mastery Mode (권장)
```bash
# Gemini API 사용
python runner_mastery.py --iterations 20

# Mock LLM (테스트용)
python runner_mastery.py --mock --iterations 10

# Hybrid Mode (Ollama Critic + Gemini Generator)
python runner_mastery.py --hybrid --iterations 20
```

#### 단일 BT 테스트
```bash
python test_bt.py examples/optimal_bt_final.txt
```

## 게임 시스템

### 전투 메커니즘
- **턴제 전투**: 플레이어 vs 적 (1:1)
- **Telegraph 시스템**: 적의 다음 행동 미리 공개
- **속성 시스템**: Fire ↔ Ice (1.5배 데미지)
- **동적 속성**: 전투 중 적의 속성 변경 가능

### 플레이어 액션 (8개)
- `Attack`: 무료, 9 데미지
- `Charge`: 15 MP, 7 데미지 + 다음 턴 2배
- `FireSpell`: 20 MP, 7 데미지 (Ice 속성에 1.5배)
- `IceSpell`: 20 MP, 10 데미지 (Fire 속성에 1.5배)
- `Defend`: 무료, 50% 데미지 감소
- `Heal`: 30 MP, 40 HP 회복, 3턴 쿨다운
- `Scan`: 15 MP, 적 약점 공개
- `Cleanse`: 25 MP, Burn/AttackDown 제거 + 10% 데미지 부스트

### 적 타입
1. **FireGolem** (HP 180, Def 5)
   - Phase 1: Neutral 속성
   - Phase 2 (HP < 50%): Fire 속성 (Ice에 약함)
   - 특수: Lifesteal, Burn DoT

2. **IceWraith** (HP 200, Def 8)
   - 동적 속성: IceSpell 사용 시 Ice 속성 획득 (3턴)
   - 특수: AttackDown Debuff, DefensiveStance

## 실행 모드

### 1. Enemy Mastery Mode
적별로 학습하며 BT를 개선:
```bash
python runner_mastery.py --iterations 20
```

### 2. Mock LLM Mode
API 호출 없이 테스트:
```bash
python runner_mastery.py --mock --iterations 10
```

### 3. Hybrid Mode
Ollama (로컬) + Gemini (클라우드) 조합:
```bash
python runner_mastery.py --hybrid --ollama-model gemma3:4b
```

### 4. Manual Mode
수동 BT 편집 및 테스트:
```bash
# 1. examples/manual.txt 편집
# 2. 실행
python runner_mastery.py --manual --iterations 1
```

## BT DSL 문법

### 제어 노드
```
root :
    selector :      # OR 로직 (하나 성공하면 성공)
        sequence :  # AND 로직 (모두 성공해야 성공)
            condition : <조건>
            task : <액션>
```

### 조건 노드
- `IsPlayerHPLow(30)` - 플레이어 HP < 30%
- `IsEnemyHPLow(30)` - 적 HP < 30%
- `HasMP(20)` - MP >= 20
- `CanHeal()` - 힐 사용 가능
- `EnemyWeakTo(Fire)` / `EnemyWeakTo(Ice)` - 적 약점
- `HasScannedEnemy()` - 스캔 완료
- `EnemyIsTelegraphing(HeavySlam)` - 적 행동 예고
- `HasStatus(BURN)` - 상태이상 보유
- `NOT <조건>` - 조건 부정

### 액션 노드
```
task : Attack()
task : Charge()
task : FireSpell()
task : IceSpell()
task : Defend()
task : Heal()
task : Scan()
task : Cleanse()
```

## 출력 파일

- `generated_bts/` - 생성된 BT 파일
- `logs/` - 전투 로그 및 요약
- `llm_logs/` - LLM Critic/Generator 로그

## 문서

- `PROMPTS_KR.md` - CRITIC/GENERATOR LLM 프롬프트 한글 번역
- `MODES.md` - 실행 모드 상세 설명
- `TextGame/bt_dsl_spec.md` - BT DSL 전체 스펙

## 최적 BT

**iter24** (78% 전체 승률):
- FireGolem: 85%
- IceWraith: 70%

위치: `examples/optimal_bt_final.txt`

전략:
1. Turn 1에 Scan으로 약점 파악
2. 속성 약점 공격 (IceSpell vs Fire, FireSpell vs Ice)
3. HeavySlam 방어
4. 60% HP에서 힐

## 테스트

```bash
# BT 테스트
python test_bt.py <bt_file_path>

# 최적 BT 테스트
python test_bt.py examples/optimal_bt_final.txt

# 전체 iteration 테스트
python test_all_iters_winrate.py
```

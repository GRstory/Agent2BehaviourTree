# 실행 모드 가이드

## 1. Enemy Mastery Mode (기본)

### 설명
적별로 학습하며 BT를 개선하는 모드

### 실행
```bash
python runner_mastery.py --iterations 20
```

### 동작 방식
1. 모든 적을 active pool에 추가
2. 랜덤하게 적 선택하여 전투
3. **승리 시**: 해당 적에 대해 5회 검증 테스트
4. **5/5 승리 시**: 해당 적을 "mastered"로 표시하고 pool에서 제거
5. 모든 적을 mastered하거나 max iterations 도달 시 종료

### 옵션
```bash
--iterations N     # 최대 반복 횟수 (기본: 20)
--bt PATH         # 초기 BT 파일 (기본: examples/example_bt_balanced.txt)
--verbose         # 상세 출력
```

### 출력
```
[00] FireGolem WIN (15 turns) | Player: 45/100, Enemy: 0/180 → FIREGOLEM[4/5], ICEWRAITH[3/5]
[01] IceWraith LOSS (22 turns) | Player: 0/100, Enemy: 28/200 → FIREGOLEM[2/5], ICEWRAITH[1/5]
```

---

## 2. Mock LLM Mode

### 설명
API 호출 없이 테스트하는 모드 (간단한 규칙 기반 개선)

### 실행
```bash
python runner_mastery.py --mock --iterations 10
```

### 특징
- API 키 불필요
- 빠른 테스트 가능
- 간단한 휴리스틱으로 BT 개선

---

## 3. Hybrid Mode

### 설명
Ollama (로컬 LLM) + Gemini (클라우드 LLM) 조합

### 실행
```bash
python runner_mastery.py --hybrid --ollama-model gemma3:4b --iterations 20
```

### 역할 분담
- **Ollama (Critic)**: 전투 로그 분석 및 피드백 생성
- **Gemini (Generator)**: 피드백 기반 BT 생성

### 장점
- Critic 비용 절감 (로컬 실행)
- Generator 품질 유지 (Gemini 사용)

### 요구사항
- Ollama 설치: https://ollama.ai/
- 모델 다운로드: `ollama pull gemma3:4b`

---

## 4. Ollama Only Mode

### 설명
완전히 로컬에서 실행 (API 키 불필요)

### 실행
```bash
python runner_mastery.py --ollama --ollama-model gemma3:4b --iterations 20
```

### 특징
- 완전 오프라인 가능
- API 비용 0
- 속도는 느릴 수 있음

---

## 5. Single-Stage LLM Mode

### 설명
Critic과 Generator를 하나의 LLM 호출로 통합 (비용 절감 및 속도 향상)

### 실행
```bash
python runner_mastery.py --single-stage --iterations 20
```

### 특징
- **1회 LLM 호출**: 분석 + BT 생성을 한 번에 처리
- **비용 절감**: 2-stage 대비 ~50% API 비용 절감
- **빠른 속도**: LLM 호출 횟수 감소로 더 빠른 실행
- **Gemini 2.0 Flash 사용**: 고품질 유지

### 장점
- API 비용 절감 (2-stage 대비 절반)
- 더 빠른 iteration 속도
- 여전히 Gemini 품질 유지

### 단점
- 2-stage보다 약간 낮은 분석 깊이
- 복잡한 전략에서는 2-stage가 더 나을 수 있음

---

## 6. Manual Mode

### 설명
수동으로 BT를 편집하고 테스트

### 실행
```bash
# 1. examples/manual.txt 편집
# 2. 실행
python runner_mastery.py --manual --iterations 1
```

### 사용 시나리오
- BT 디버깅
- 특정 전략 테스트
- 학습 목적

---

## 모드 비교

| 모드 | API 필요 | 속도 | 품질 | 비용 |
|------|---------|------|------|------|
| Enemy Mastery | ✅ Gemini | 빠름 | 최고 | 중간 |
| Single-Stage | ✅ Gemini | 빠름 | 높음 | 낮음 |
| Mock LLM | ❌ | 매우 빠름 | 낮음 | 무료 |
| Hybrid | ✅ Gemini (Generator만) | 중간 | 높음 | 낮음 |
| Ollama Only | ❌ | 느림 | 중간 | 무료 |
| Manual | ❌ | 즉시 | 사용자 의존 | 무료 |

---

## 권장 사용법

### 개발/테스트
```bash
python runner_mastery.py --mock --iterations 5
```

### 실제 학습 (비용 효율)
```bash
python runner_mastery.py --single-stage --iterations 20
```

### 실제 학습 (하이브리드)
```bash
python runner_mastery.py --hybrid --iterations 20
```

### 최고 품질
```bash
python runner_mastery.py --iterations 30
```

### 완전 오프라인
```bash
python runner_mastery.py --ollama --ollama-model gemma3:4b --iterations 20
```

---

## 출력 파일 구조

```
generated_bts/
  20251215_225920/
    iter00_bt.txt
    iter01_bt.txt
    ...

logs/
  20251215_225920/
    iter00_FireGolem_win.txt
    iter01_IceWraith_loss.txt
    ...

llm_logs/
  20251215_225920/
    iter00_critic_20251215_225925.txt
    iter00_generator_20251215_225928.txt
    ...
```

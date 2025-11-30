# PORTAL-Inspired Dungeon Game with LLM Behaviour Tree Agent

10층 던전 게임을 클리어하기 위해 LLM이 Behaviour Tree를 반복적으로 개선하는 시스템입니다.

## 빠른 시작

### 1. 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. 실행

```bash
# Mock LLM으로 테스트 (API 키 불필요)
python main.py --mock --iterations 3

# Gemini API 사용 (API 키 필요)
python main.py --iterations 5
```

## Gemini API 키 설정

1. `.env.example`을 `.env`로 복사
2. `.env` 파일에 API 키 입력:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```
3. API 키 발급: https://makersuite.google.com/app/apikey

## 모델 설정

`config.py`에서 모델 변경:
```python
model: str = "gemini-1.5-flash"  # 또는 gemini-1.5-pro
```

## 게임 규칙

- **10층 던전**: 5층, 10층은 보스
- **4가지 행동**: 
  - 약공격: 기본 데미지
  - 강공격: 1.5배 데미지, 다음 턴 받는 데미지 2배
  - 방어: 받는 데미지 50% 감소
  - 힐: 최대 HP의 25% 회복 (층당 1번 제한)
- **콤보 시스템**: 
  - Triple Light (4배): 약→약→약 (같은 공격 3번 반복!)
  - Heavy Finisher (3배): 약→약→강 (약공격 2번 후 강공격)
  - Counter Strike (2.5배): 방어→강 (방어 후 반격)

## Behaviour Tree 조건 노드

### 추상적 체력 조건 (권장)
- `IsPlayerHPLevel(Low)` - 플레이어 HP 0-33%
- `IsPlayerHPLevel(Mid)` - 플레이어 HP 33-66%
- `IsPlayerHPLevel(High)` - 플레이어 HP 66-100%
- `IsEnemyHPLevel(Low)` - 적 HP 0-33%
- `IsEnemyHPLevel(Mid)` - 적 HP 33-66%
- `IsEnemyHPLevel(High)` - 적 HP 66-100%

### 숫자 기반 체력 조건 (레거시)
- `IsPlayerHPLow(threshold)` - 플레이어 HP < threshold%
- `IsPlayerHPHigh(threshold)` - 플레이어 HP > threshold%
- `IsEnemyHPLow(threshold)` - 적 HP < threshold%
- `IsEnemyHPHigh(threshold)` - 적 HP > threshold%

### 기타 조건
- `CanHeal()` - 힐 사용 가능 여부
- `HasComboReady(combo_name)` - 콤보 준비 상태
- `IsFloorBoss()` - 보스층 여부
- `IsTurnEarly(threshold)` - 초반 턴 여부

## 명령어 옵션

```bash
python main.py [OPTIONS]

옵션:
  --iterations N    반복 횟수 (기본값: 5)
  --mock           Mock LLM 사용 (API 호출 없음)
  --bt PATH        초기 BT 파일 경로
  --no-save        로그/BT 저장 안 함
  --quiet          최소 출력
```

## 출력 파일

- `generated_bts/` - 생성된 모든 BT
- `logs/` - 게임플레이 로그 및 Critic 피드백

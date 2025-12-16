# OpenAI API 사용 예시

## 환경 변수 설정

`.env` 파일에 OpenAI API 키 추가:
```
GEMINI_API_KEY=your_gemini_key_here
OPENAI_API_KEY=your_openai_key_here
```

## 실행 예시

### 1. 기본 OpenAI 모드
```bash
python runner_mastery.py --openai --iterations 20
```
- Generator: `gpt-4o` (고성능)
- Critic: `gpt-4o-mini` (빠르고 저렴)

### 2. 커스텀 모델 지정
```bash
# o1-preview 사용 (고급 전략 분석)
python runner_mastery.py --openai --openai-model o1-preview --openai-critic-model gpt-4o-mini

# 모두 gpt-4o-mini 사용 (저비용)
python runner_mastery.py --openai --openai-model gpt-4o-mini --openai-critic-model gpt-4o-mini
```

### 3. 비용 예측

20 iterations 기준:
- **gpt-4o + gpt-4o-mini**: 약 $0.50
- **gpt-4o-mini only**: 약 $0.04
- **o1-preview + gpt-4o-mini**: 약 $2.00

## 지원 모델

| 모델 | 용도 | 특징 |
|------|------|------|
| gpt-4o | Generator | 고성능, 창의적 전략 |
| gpt-4o-mini | Critic | 빠르고 저렴 |
| o1-preview | Generator | 고급 추론 능력 |

## 성능 비교

Gemini vs OpenAI 성능 비교를 위해 동일한 조건으로 실행:

```bash
# Gemini 모드
python runner_mastery.py --iterations 20

# OpenAI 모드
python runner_mastery.py --openai --iterations 20
```

결과는 `logs/` 및 `generated_bts/` 디렉토리에서 확인 가능.

"""
PORTAL-Inspired Dungeon Game with LLM Behaviour Tree Agent

간단한 실행 방법:
    python main.py --mock --iterations 3  # Mock LLM (API 키 불필요)
    python main.py --iterations 5         # Gemini API 사용

API 키 설정:
    1. .env.example을 .env로 복사
    2. GEMINI_API_KEY=your_api_key_here 입력
    3. API 키 발급: https://makersuite.google.com/app/apikey

모델 설정:
    config.py에서 모델 변경 가능:
    - gemini-1.5-pro: 고성능 (느림, 비쌈)
    - gemini-1.5-flash: 빠르고 저렴 (기본값, 권장)
    - gemini-2.0-flash-exp: 실험적 최신 모델
"""

if __name__ == "__main__":
    # Import runner and execute
    from runner import main
    main()
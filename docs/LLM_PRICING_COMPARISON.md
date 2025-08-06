# DungeonTalk LLM 제공업체별 가격 비교 가이드

## 지원하는 LLM 제공업체

현재 DungeonTalk에서 지원하는 LLM 제공업체와 모델:

### 1. DeepSeek API
- **DeepSeek Chat** (기본)
- **DeepSeek Reasoner (R1)** (고급 추론)

### 2. OpenAI API  
- **GPT-4o** (권장)
- **GPT-4o Mini** (경제형)

### 3. Anthropic Claude API
- **Claude Sonnet 4** (균형형)
- **Claude Opus 4.1** (프리미엄)

### 4. Ollama (로컬)
- **Llama 3.2** (무료, 로컬 실행)

## 가격 비교표 (2024-2025)

| 제공업체 | 모델 | 입력 토큰/1M | 출력 토큰/1M | 특징 |
|---------|------|-------------|-------------|------|
| **DeepSeek** | Chat | $0.27 | $1.10 | 🔥 **최저가**, 50-75% 할인 시간대 |
| | Reasoner (R1) | $0.55 | $2.19 | 고급 추론, 할인 시간대 |
| **OpenAI** | GPT-4o | $3.00 | $10.00 | 균형잡힌 성능/가격 |
| | GPT-4o Mini | $0.15 | $0.60 | 🔥 **경제형 최저가** |
| **Anthropic** | Claude Sonnet 4 | $3.00 | $15.00 | 캐시 90% 할인 가능 |
| | Claude Opus 4.1 | $15.00 | $75.00 | 💎 **최고 성능** |
| **Ollama** | Llama 3.2 | 무료 | 무료 | 로컬 실행, GPU/CPU 필요 |

## 임베딩 모델 가격

| 모델 | 가격/1K 토큰 | 설명 |
|------|------------|------|
| **OpenAI text-embedding-3-small** | $0.00002 | 원격 임베딩 (권장) |
| **HuggingFace multilingual-e5-large** | 무료 | 로컬 실행 (기본값) |

## 실제 비용 계산 (100번 질문 기준)

### 가정
- **평균 입력**: 200 토큰 (질문 + 컨텍스트)
- **평균 출력**: 300 토큰 (GM 응답)
- **100번 질문**: 20,000 입력 토큰 + 30,000 출력 토큰

### 제공업체별 100번 질문 비용

| 모델 | 입력 비용 | 출력 비용 | **총 비용** | 특징 |
|------|----------|----------|-----------|------|
| **DeepSeek Chat** | $0.005 | $0.033 | **$0.038** | 🔥 할인시간 $0.02 |
| **DeepSeek R1** | $0.011 | $0.066 | **$0.077** | 할인시간 $0.04 |
| **GPT-4o Mini** | $0.003 | $0.018 | **$0.021** | 🔥 **가장 저렴** |
| **GPT-4o** | $0.060 | $0.300 | **$0.360** | 균형형 |
| **Claude Sonnet 4** | $0.060 | $0.450 | **$0.510** | 캐시 활용시 50% 절감 |
| **Claude Opus 4.1** | $0.300 | $2.250 | **$2.550** | 최고 성능 |
| **Ollama Llama 3.2** | $0.000 | $0.000 | **무료** | 로컬 리소스 필요 |

### 임베딩 비용 (문서 처리)

| 시나리오 | OpenAI 임베딩 | 로컬 임베딩 | 설명 |
|---------|-------------|-----------|------|
| **초기 문서 임베딩** (100만 토큰) | $0.020 | 무료 | 최초 1회 |
| **월별 추가 문서** (10만 토큰) | $0.002 | 무료 | 지속적 추가 |

## 연간 비용 예측 (사용량별)

### 개인/소규모 (월 500번 질문)

| 모델 | 월 비용 | 연 비용 |
|------|---------|---------|
| **GPT-4o Mini** | $0.11 | **$1.32** |
| **DeepSeek Chat** | $0.19 | **$2.28** |
| **GPT-4o** | $1.80 | **$21.60** |
| **Claude Sonnet 4** | $2.55 | **$30.60** |

### 중형 서비스 (월 5,000번 질문)

| 모델 | 월 비용 | 연 비용 |
|------|---------|---------|
| **GPT-4o Mini** | $1.05 | **$12.60** |
| **DeepSeek Chat** | $1.90 | **$22.80** |
| **GPT-4o** | $18.00 | **$216.00** |
| **Claude Sonnet 4** | $25.50 | **$306.00** |

### 대형 서비스 (월 50,000번 질문)

| 모델 | 월 비용 | 연 비용 |
|------|---------|---------|
| **GPT-4o Mini** | $10.50 | **$126.00** |
| **DeepSeek Chat** | $19.00 | **$228.00** |
| **GPT-4o** | $180.00 | **$2,160.00** |
| **Claude Sonnet 4** | $255.00 | **$3,060.00** |

## 비용 최적화 팁

### 1. 시간대 할인 활용
- **DeepSeek**: UTC 16:30-00:30 (한국시간 01:30-09:30) 50-75% 할인
- 새벽 시간대 배치 처리로 비용 절감

### 2. 캐시 활용
- **Claude**: 프롬프트 캐싱으로 최대 90% 절감
- **DeepSeek**: 반복 입력시 캐시 히트 74% 할인

### 3. 모델 선택 전략
- **개발/테스트**: GPT-4o Mini 또는 DeepSeek Chat
- **프로덕션**: GPT-4o 또는 Claude Sonnet 4
- **고품질 필요시**: Claude Opus 4.1
- **예산 제한**: Ollama 로컬 실행

### 4. 하이브리드 구성
```bash
# 경제형 설정
LLM_PROVIDER=deepseek
USE_REMOTE_EMBEDDINGS=false  # 로컬 임베딩

# 성능 우선 설정  
LLM_PROVIDER=claude
USE_REMOTE_EMBEDDINGS=true   # OpenAI 임베딩
```

## 환경 변수 설정

### DeepSeek 사용
```bash
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_key
DEEPSEEK_MODEL=deepseek-chat  # 또는 deepseek-reasoner
```

### OpenAI 사용
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4o-mini  # 또는 gpt-4o
USE_REMOTE_EMBEDDINGS=true
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

### Claude 사용
```bash
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=your_key
CLAUDE_MODEL=claude-3-5-sonnet-20241022
```

### 로컬 Ollama 사용
```bash
LLM_PROVIDER=ollama
USE_REMOTE_EMBEDDINGS=false
```

## 권장 구성

### 🥇 비용 효율성 1위
- **모델**: GPT-4o Mini
- **임베딩**: 로컬 HuggingFace
- **예상 비용**: 100번 질문당 $0.021

### 🥈 균형형 추천
- **모델**: DeepSeek Chat
- **임베딩**: OpenAI text-embedding-3-small  
- **예상 비용**: 100번 질문당 $0.040

### 🥉 고품질 권장
- **모델**: Claude Sonnet 4
- **임베딩**: OpenAI text-embedding-3-small
- **예상 비용**: 100번 질문당 $0.512

## 참고사항

1. **토큰 수**: 한국어는 영어 대비 약 1.5-2배 토큰 소모
2. **컨텍스트 길이**: 이전 대화 기록이 많을수록 입력 토큰 증가
3. **문서 임베딩**: 초기 구축 비용은 1회성, 이후 유지비용은 미미
4. **환율 변동**: USD 기준 가격이므로 환율 변동 고려 필요

---

*마지막 업데이트: 2025년 1월*
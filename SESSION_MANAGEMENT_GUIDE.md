# DungeonTalk 세션 관리 시스템

## 세션 구현 방식

### 1. 세션 관리 구조
- **메모리 기반**: `SessionManager` 클래스로 세션별 대화 기록을 RAM에 저장
- **세션 식별**: `session_id` 문자열로 각 세션을 구분
- **공통 벡터스토어**: 모든 세션이 동일한 문서 검색 DB 공유
- **독립적 대화 기록**: 각 세션마다 별도의 대화 내역 유지

### 2. 세션 제한 및 용량

| 항목 | 기본값 | 설정 방법 |
|------|--------|-----------|
| **최대 세션 수** | 100개 | `MAX_SESSIONS` 환경변수 |
| **세션당 최대 대화** | 50개 | 하드코딩 |
| **대화 기록 유지** | 최근 30개 | 50개 초과시 자동 정리 |
| **컨텍스트 사용** | 최근 5개 | `RECENT_CHAT_COUNT` 환경변수 |

### 3. 메모리 사용량 추정 (100번 질문 기준)

```
단일 세션 100번 질문시:
- 질문 + 답변: 평균 500자 × 100번 = 50,000자
- JSON 메타데이터: 약 10,000자
- 총 메모리: 약 60KB per 세션

전체 시스템 (100개 세션 × 100번):
- 총 메모리 사용량: 약 6MB
- 실제 유지: 30개만 유지되므로 약 1.8MB
```

## HTTP API 사용법

### 1. 채팅 요청
```http
POST http://localhost:8000/chat
Content-Type: application/json

{
  "session_id": "room_001",
  "user_name": "플레이어1", 
  "message": "던전으로 들어간다"
}
```

**응답:**
```json
{
  "response": "던전 입구에서 차가운 바람이...",
  "sources": ["관련 문서 조각들..."],
  "session_id": "room_001"
}
```

### 2. 세션 정보 조회
```http
GET http://localhost:8000/sessions
```

**응답:**
```json
{
  "total_sessions": 3,
  "max_sessions": 100,
  "sessions": {
    "room_001": {
      "message_count": 15,
      "users": ["플레이어1", "플레이어2"],
      "last_activity": 12345
    }
  }
}
```

### 3. 특정 세션 대화 기록
```http
GET http://localhost:8000/sessions/room_001/history
```

### 4. 문서 업로드
```http
POST http://localhost:8000/upload
Content-Type: multipart/form-data

file: [선택한 파일]
```

### 5. 문서 재스캔
```http
POST http://localhost:8000/rescan
```

### 6. 서버 상태 확인
```http
GET http://localhost:8000/health
```

## 다중 사용자 시나리오

### 같은 세션 내 여러 플레이어
```bash
# 플레이어 1
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"party_alpha", "user_name":"전사", "message":"검을 든다"}'

# 플레이어 2  
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"party_alpha", "user_name":"마법사", "message":"파이어볼을 준비한다"}'
```

### 독립적인 세션들
```bash
# 세션 1
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"dungeon_001", "user_name":"모험가", "message":"동굴 탐험"}'

# 세션 2  
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"town_002", "user_name":"상인", "message":"아이템 판매"}'
```

## 환경 설정

```bash
# .env 파일
MAX_SESSIONS=100           # 최대 세션 수
RECENT_CHAT_COUNT=5        # 컨텍스트로 사용할 최근 대화 수
API_PORT=8000             # 서버 포트
API_HOST=0.0.0.0          # 서버 호스트
```

## 주요 특징

- **실시간 멀티플레이어**: 같은 `session_id`로 여러 플레이어가 동시 참여 가능
- **세션 독립성**: 각 세션은 완전히 독립적인 게임 진행
- **메모리 효율성**: 자동 대화 기록 정리로 메모리 사용량 최적화
- **컨텍스트 인식**: 이전 대화를 바탕으로 일관성 있는 게임 진행
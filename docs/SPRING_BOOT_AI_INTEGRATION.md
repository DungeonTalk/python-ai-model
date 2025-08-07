# Spring Boot AI 서비스 연동 가이드 v2.0

## 🎯 개요

던전톡 Python AI 서비스가 **완전한 마이크로서비스**로 전환되었습니다. 이제 Spring Boot와의 연동이 간소화되고, 각 서비스의 책임이 명확히 분리되었습니다.

## 🌟 새로운 아키텍처의 장점

### 🚀 **성능 & 확장성**
- **독립적 스케일링**: AI 서비스와 게임 서비스를 각각 필요에 따라 확장
- **전문화된 최적화**: Python은 AI/ML에, Spring Boot는 웹/게임 로직에 최적화
- **병렬 처리**: 여러 AI 요청을 동시에 처리 가능
- **포트 분리**: 8001(AI), 8080(게임)로 트래픽 분산

### 🛡️ **안정성 & 복원력**
- **장애 격리**: 한 서비스 문제가 다른 서비스에 영향 없음
- **독립적 배포**: 각 서비스를 별도로 업데이트 및 재시작 가능
- **Circuit Breaker**: AI 서비스 장애 시 자동 복구 메커니즘
- **Graceful Degradation**: AI 서비스 다운 시에도 채팅은 계속 가능

### 🔧 **개발 & 유지보수**
- **명확한 책임 분리**: 
  - Python: AI 응답 생성만 담당
  - Spring Boot: 게임 로직, 실시간 통신, 세션 관리
- **독립적 개발**: AI 팀과 백엔드 팀이 병렬로 개발 가능
- **기술 스택 최적화**: 각 서비스가 가장 적합한 기술 사용
- **테스트 용이성**: 각 서비스를 독립적으로 테스트

### 🎮 **게임 특화 기능**
- **실시간 성능**: WebSocket은 Spring Boot에서 최적화
- **턴 기반 게임**: Spring Boot에서 복잡한 게임 상태 관리
- **다중 플레이어**: 세션 동기화 및 상태 관리 효율화
- **확장 가능한 구조**: 새로운 게임 기능 추가 용이

### 💰 **비용 효율성**
- **리소스 최적화**: 각 서비스가 필요한 만큼만 리소스 사용
- **AI 모델 공유**: 하나의 AI 서비스로 여러 게임 방 처리
- **클라우드 친화적**: 컨테이너화 및 자동 스케일링 지원
- **개발 속도**: 마이크로서비스로 빠른 기능 추가

### 🔌 **통합 & 확장성**
- **API 기반**: RESTful API로 다른 시스템과 쉽게 통합
- **다중 프론트엔드**: 웹, 모바일, 데스크톱 앱 모두 지원 가능  
- **써드파티 연동**: Discord 봇, Slack 봇 등으로 확장 가능
- **모니터링**: 각 서비스별 독립적인 성능 모니터링

### 📊 **운영 & 모니터링**
- **세밀한 로깅**: 각 서비스별 전문화된 로그
- **성능 추적**: AI 응답 시간, 게임 서버 성능 별도 측정
- **알림 시스템**: 서비스별 장애 알림 및 대응
- **버전 관리**: 독립적인 버전 관리 및 롤백 가능

## 🏗️ 새로운 아키텍처

```
┌─────────────────┐    HTTP API     ┌─────────────────┐
│   Spring Boot   │ ◄────────────► │  Python FastAPI │
│   (게임 서버)    │   /ai-response  │   (AI 서버)     │
│   Port: 8080    │                │   Port: 8001    │
└─────────────────┘                └─────────────────┘
        │                                    │
        ▼                                    ▼
┌─────────────────┐                ┌─────────────────┐
│   게임 DB       │                │   Vector DB     │
│ (PostgreSQL)    │                │(PostgreSQL)    │
│ - 세션 관리     │                │ - 문서 임베딩   │
│ - 채팅 기록     │                │ - 벡터 검색     │
│ - 게임 상태     │                │ - AI 컨텍스트   │
└─────────────────┘                └─────────────────┘
```

## 🚀 주요 변경사항

### ✅ **Python AI 서비스 (v2.0)**
- **세션 관리 완전 제거** - PostgreSQLSessionManager 삭제
- **새로운 전용 엔드포인트** - `/ai-response`
- **포트 분리** - 8001번 포트 사용
- **성능 측정** - 응답 시간 모니터링
- **구조화된 데이터 모델** - Spring Boot와 완벽 호환

### 🎮 **Spring Boot의 새로운 역할**
- **세션 관리** - 사용자 인증, 방 관리
- **실시간 통신** - WebSocket 채팅
- **게임 로직** - 턴 관리, 상태 저장
- **AI 서비스 호출** - HTTP 클라이언트 역할

## 📋 API 명세서

### 🤖 **AI 응답 생성 API**

**엔드포인트**: `POST http://localhost:8001/ai-response`

#### 요청 데이터 구조

```json
{
  "game_id": "game_12345",
  "ai_game_room_id": "room_67890", 
  "current_user": "플레이어1",
  "current_message": "던전에 들어갑니다",
  "turn_number": 5,
  "context_messages": [
    {
      "messageType": "USER",
      "senderNickname": "플레이어1", 
      "content": "안녕하세요",
      "turnNumber": 1,
      "messageOrder": 1
    },
    {
      "messageType": "AI",
      "senderNickname": "GM",
      "content": "던전 입구에 도착했습니다...",
      "turnNumber": 2, 
      "messageOrder": 2
    }
  ]
}
```

#### 응답 데이터 구조

```json
{
  "content": "어둠 속에서 차가운 바람이 불어옵니다. 앞으로 두 갈래 길이 보입니다...",
  "response_time": 2340,
  "sources": [
    "던전_입구_설명.txt...",
    "몬스터_정보.txt..."
  ]
}
```

#### 데이터 모델 설명

| 필드 | 타입 | 설명 |
|------|------|------|
| `game_id` | String | 게임 세션 고유 ID |
| `ai_game_room_id` | String | AI 방 식별자 |
| `current_user` | String | 현재 발언하는 플레이어명 |
| `current_message` | String | 플레이어의 새로운 메시지 |
| `turn_number` | Integer | 현재 턴 번호 |
| `context_messages` | Array | 이전 대화 기록 배열 |

**ContextMessage 구조:**
- `messageType`: "USER", "AI", "SYSTEM" 중 하나
- `senderNickname`: 발송자 닉네임
- `content`: 메시지 내용
- `turnNumber`: 메시지가 발생한 턴
- `messageOrder`: 턴 내 메시지 순서

## 💻 Spring Boot 구현 예제

### 1. **의존성 설정 (pom.xml)**

```xml
<dependencies>
    <!-- Web & WebSocket -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-websocket</artifactId>
    </dependency>
    
    <!-- HTTP Client -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-webflux</artifactId>
    </dependency>
    
    <!-- Database -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-data-jpa</artifactId>
    </dependency>
</dependencies>
```

### 2. **설정 파일 (application.yml)**

```yaml
server:
  port: 8080

spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/dungeontalk_game
    username: postgres
    password: 1234
    
# AI 서비스 설정
ai-service:
  base-url: http://localhost:8001
  timeout: 30000
  retry-count: 3
```

### 3. **AI 서비스 클라이언트**

```java
@Service
public class AiServiceClient {
    
    @Autowired
    private WebClient webClient;
    
    @Value("${ai-service.base-url}")
    private String aiServiceBaseUrl;
    
    public AiResponseResult generateResponse(AiResponseRequest request) {
        return webClient.post()
            .uri(aiServiceBaseUrl + "/ai-response")
            .body(Mono.just(request), AiResponseRequest.class)
            .retrieve()
            .bodyToMono(AiResponseResult.class)
            .timeout(Duration.ofSeconds(30))
            .retry(2)
            .block();
    }
}
```

### 4. **데이터 모델 클래스들**

```java
// 요청 데이터
@Data
public class AiResponseRequest {
    private String gameId;
    private String aiGameRoomId;
    private String currentUser;
    private String currentMessage;
    private Integer turnNumber;
    private List<ContextMessage> contextMessages = new ArrayList<>();
}

// 컨텍스트 메시지
@Data 
public class ContextMessage {
    private String messageType; // USER, AI, SYSTEM
    private String senderNickname;
    private String content;
    private Integer turnNumber;
    private Integer messageOrder;
}

// 응답 데이터
@Data
public class AiResponseResult {
    private String content;
    private Integer responseTime;
    private List<String> sources;
}
```

### 5. **게임 서비스 구현**

```java
@Service
@Transactional
public class GameService {
    
    @Autowired
    private AiServiceClient aiServiceClient;
    
    @Autowired
    private MessageRepository messageRepository;
    
    @Autowired
    private SimpMessagingTemplate messagingTemplate;
    
    public void processPlayerMessage(String gameRoomId, String playerNickname, String message) {
        
        // 1. 사용자 메시지 저장
        GameMessage userMessage = saveMessage(gameRoomId, playerNickname, message, "USER");
        
        // 2. 컨텍스트 메시지 조회 (최근 10개)
        List<ContextMessage> contextMessages = getContextMessages(gameRoomId, 10);
        
        // 3. AI 응답 요청 구성
        AiResponseRequest aiRequest = AiResponseRequest.builder()
            .gameId(findGameByRoomId(gameRoomId).getId())
            .aiGameRoomId(gameRoomId)
            .currentUser(playerNickname)
            .currentMessage(message)
            .turnNumber(getCurrentTurn(gameRoomId))
            .contextMessages(contextMessages)
            .build();
        
        try {
            // 4. AI 서비스 호출
            AiResponseResult aiResponse = aiServiceClient.generateResponse(aiRequest);
            
            // 5. AI 응답 저장
            GameMessage aiMessage = saveMessage(gameRoomId, "GM", aiResponse.getContent(), "AI");
            
            // 6. WebSocket으로 실시간 전송
            messagingTemplate.convertAndSend("/topic/room/" + gameRoomId, aiMessage);
            
            // 7. 응답 시간 로깅
            log.info("AI 응답 생성 완료 - 방:{}, 시간:{}ms", gameRoomId, aiResponse.getResponseTime());
            
        } catch (Exception e) {
            log.error("AI 응답 생성 실패", e);
            // 에러 메시지 전송
            GameMessage errorMessage = createErrorMessage(gameRoomId, "AI 응답 생성에 실패했습니다.");
            messagingTemplate.convertAndSend("/topic/room/" + gameRoomId, errorMessage);
        }
    }
    
    private List<ContextMessage> getContextMessages(String gameRoomId, int limit) {
        return messageRepository.findByGameRoomIdOrderByCreatedAtDesc(gameRoomId, PageRequest.of(0, limit))
            .stream()
            .map(this::toContextMessage)
            .collect(Collectors.toList());
    }
    
    private ContextMessage toContextMessage(GameMessage message) {
        return ContextMessage.builder()
            .messageType(message.getMessageType())
            .senderNickname(message.getSenderNickname())
            .content(message.getContent())
            .turnNumber(message.getTurnNumber())
            .messageOrder(message.getMessageOrder())
            .build();
    }
}
```

### 6. **WebSocket 채팅 컨트롤러**

```java
@Controller
public class ChatController {
    
    @Autowired
    private GameService gameService;
    
    @MessageMapping("/chat.sendMessage")
    @SendTo("/topic/room/{roomId}")
    public void sendMessage(@DestinationVariable String roomId, ChatMessage chatMessage) {
        // 비동기로 AI 응답 처리
        gameService.processPlayerMessage(roomId, chatMessage.getSender(), chatMessage.getContent());
    }
    
    @MessageMapping("/chat.joinRoom")
    @SendTo("/topic/room/{roomId}")
    public ChatMessage joinRoom(@DestinationVariable String roomId, ChatMessage chatMessage) {
        return ChatMessage.builder()
            .type(ChatMessage.MessageType.JOIN)
            .sender(chatMessage.getSender())
            .content(chatMessage.getSender() + "님이 입장했습니다.")
            .build();
    }
}
```

## 🔧 환경 설정

### **Python AI 서비스 (.env)**
```env
# 포트 변경
AI_SERVICE_PORT=8001
AI_SERVICE_HOST=0.0.0.0

# LLM 설정
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your-api-key

# PostgreSQL 벡터 DB
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=dungeondb
POSTGRES_USER=root
POSTGRES_PASSWORD=1234
```

### **Spring Boot (application.yml)**
```yaml
server:
  port: 8080

ai-service:
  base-url: http://localhost:8001
  timeout: 30000

spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/dungeontalk_game
    username: postgres
    password: 1234
```

## 🚀 실행 방법

### 1. **Python AI 서비스 실행**
```bash
cd C:\stuyd\dungeontalk-mvp
uv run python main.py
```
**출력 예시:**
```
[INFO] 환경변수 검증 완료 - LLM Provider: deepseek
[INFO] OpenAI 원격 임베딩 사용
[INFO] PostgreSQL PGVector 벡터스토어 사용
[INFO] AI 서비스 시작 - 0.0.0.0:8001
[INFO] Spring Boot와 연동되는 AI 응답 전용 서비스
```

### 2. **Spring Boot 게임 서버 실행**
```bash
mvn spring-boot:run
```

### 3. **연동 테스트**
```bash
# AI 서비스 상태 확인
curl http://localhost:8001/health

# AI 응답 테스트
curl -X POST http://localhost:8001/ai-response \
  -H "Content-Type: application/json" \
  -d '{
    "game_id": "test_game",
    "ai_game_room_id": "test_room",
    "current_user": "테스트유저",
    "current_message": "던전에 들어갑니다",
    "turn_number": 1,
    "context_messages": []
  }'
```

## 📊 모니터링 및 로깅

### **Python AI 서비스 로그**
```
[INFO] AI 응답 생성 요청 - 게임방: room_12345, 사용자: 플레이어1, 턴: 5
[INFO] AI 응답 생성 완료 - 응답시간: 2340ms, 소스: 3개
```

### **Spring Boot 로그**
```java
@Slf4j
public class GameService {
    public void processPlayerMessage(...) {
        log.info("플레이어 메시지 처리 시작 - 방:{}, 플레이어:{}", gameRoomId, playerNickname);
        // AI 서비스 호출
        log.info("AI 응답 생성 완료 - 방:{}, 시간:{}ms", gameRoomId, aiResponse.getResponseTime());
    }
}
```

## 🛡️ 에러 처리 및 복원력

### **타임아웃 및 재시도**
```java
@Service
public class AiServiceClient {
    
    public AiResponseResult generateResponse(AiResponseRequest request) {
        return webClient.post()
            .uri(aiServiceBaseUrl + "/ai-response")
            .body(Mono.just(request), AiResponseRequest.class)
            .retrieve()
            .onStatus(HttpStatus::is5xxServerError, response -> 
                Mono.error(new AiServiceException("AI 서비스 오류")))
            .bodyToMono(AiResponseResult.class)
            .timeout(Duration.ofSeconds(30))
            .retryWhen(Retry.fixedDelay(2, Duration.ofSeconds(1)))
            .onErrorReturn(createFallbackResponse("현재 AI 서비스를 이용할 수 없습니다."))
            .block();
    }
}
```

### **Circuit Breaker 패턴**
```java
@Component
public class AiServiceCircuitBreaker {
    
    private final CircuitBreaker circuitBreaker = CircuitBreaker.ofDefaults("aiService");
    
    public AiResponseResult callWithCircuitBreaker(AiResponseRequest request) {
        Supplier<AiResponseResult> decoratedSupplier = CircuitBreaker
            .decorateSupplier(circuitBreaker, () -> aiServiceClient.generateResponse(request));
            
        return decoratedSupplier.get();
    }
}
```

## 📈 성능 최적화

### **비동기 처리**
```java
@Service
public class AsyncGameService {
    
    @Async
    public CompletableFuture<Void> processPlayerMessageAsync(String gameRoomId, String playerNickname, String message) {
        // AI 응답 생성을 비동기로 처리
        gameService.processPlayerMessage(gameRoomId, playerNickname, message);
        return CompletableFuture.completedFuture(null);
    }
}
```

### **캐싱 전략**
```java
@Service
public class ContextCacheService {
    
    @Cacheable(value = "contextMessages", key = "#gameRoomId")
    public List<ContextMessage> getContextMessages(String gameRoomId, int limit) {
        // 컨텍스트 메시지 캐싱
    }
    
    @CacheEvict(value = "contextMessages", key = "#gameRoomId")
    public void evictContextCache(String gameRoomId) {
        // 새 메시지 추가시 캐시 무효화
    }
}
```

## 🔗 추가 엔드포인트

### **문서 관리 API**
```bash
# 문서 업로드 (게임 설정 파일)
POST http://localhost:8001/upload

# 문서 재스캔 (새로운 파일 임베딩)
POST http://localhost:8001/rescan

# 서비스 정보
GET http://localhost:8001/
```

## 🎯 다음 단계

1. **Spring Boot 프로젝트 생성**
2. **데이터베이스 스키마 설계**
3. **WebSocket 채팅 구현**
4. **AI 서비스 클라이언트 구현**
5. **통합 테스트 및 성능 튜닝**

---

**이제 Python AI 서비스는 완전한 마이크로서비스가 되었습니다! Spring Boot에서 이 가이드를 따라 구현하면 완벽한 TRPG 시스템이 완성됩니다.** 🎮✨
# 🌱 Spring Boot 연동 가이드

던전톡 Python AI 서버와 Spring Boot 백엔드 연동 방법

---

## 📋 개요

**아키텍처:**
```
사용자 → Spring Boot → Python FastAPI → AI 응답
                   ↓
               세션 관리
```

**역할 분담:**
- **Spring Boot**: 사용자 인증, 세션 관리, 비즈니스 로직
- **Python FastAPI**: AI/RAG 처리, 문서 검색, 응답 생성

---

## 🚀 Python API 서버 준비

### 1. 서버 실행
```bash
# 환경변수 설정
cp .env.example .env
# .env 파일에 API 키 설정

# 서버 시작 (포트 8000)
python main.py
```

### 2. API 엔드포인트 확인
- **채팅**: `POST /chat`
- **헬스체크**: `GET /health`
- **세션 목록**: `GET /sessions`
- **세션 기록**: `GET /sessions/{session_id}/history`

---

## 🔧 Spring Boot 구현

### 1. 의존성 추가 (build.gradle)
```gradle
dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-web'
    implementation 'org.springframework.boot:spring-boot-starter-webflux' // WebClient용
    // 기타 필요한 의존성...
}
```

### 2. AI 서비스 클래스 생성

```java
@Service
public class DungeonTalkAIService {
    
    private final WebClient webClient;
    
    @Value("${dungeontalk.ai.base-url:http://localhost:8000}")
    private String aiBaseUrl;
    
    public DungeonTalkAIService(WebClient.Builder webClientBuilder) {
        this.webClient = webClientBuilder.baseUrl(aiBaseUrl).build();
    }
    
    /**
     * AI와 채팅
     */
    public Mono<ChatResponse> chat(String sessionId, String userName, String message) {
        ChatRequest request = new ChatRequest(sessionId, userName, message);
        
        return webClient.post()
                .uri("/chat")
                .bodyValue(request)
                .retrieve()
                .bodyToMono(ChatResponse.class)
                .timeout(Duration.ofSeconds(30)); // 타임아웃 설정
    }
    
    /**
     * 서버 상태 체크
     */
    public Mono<Boolean> checkHealth() {
        return webClient.get()
                .uri("/health")
                .retrieve()
                .bodyToMono(Map.class)
                .map(response -> "healthy".equals(response.get("status")))
                .onErrorReturn(false);
    }
}
```

### 3. 요청/응답 DTO

```java
// 요청 DTO
@Data
@AllArgsConstructor
@NoArgsConstructor
public class ChatRequest {
    private String sessionId;
    private String userName;  
    private String message;
}

// 응답 DTO
@Data
@NoArgsConstructor
public class ChatResponse {
    private String response;
    private List<String> sources;
    private String sessionId;
}
```

### 4. 컨트롤러 구현

```java
@RestController 
@RequestMapping("/api/trpg")
@Slf4j
public class TRPGController {
    
    private final DungeonTalkAIService aiService;
    private final SessionService sessionService; // 세션 관리 서비스
    
    public TRPGController(DungeonTalkAIService aiService, SessionService sessionService) {
        this.aiService = aiService;
        this.sessionService = sessionService;
    }
    
    /**
     * TRPG 채팅
     */
    @PostMapping("/chat")
    public Mono<ResponseEntity<ChatResponse>> chat(
            @RequestBody Map<String, String> request,
            HttpSession httpSession) {
        
        // 세션 정보 추출
        String sessionId = sessionService.getOrCreateSessionId(httpSession);
        String userName = sessionService.getUserName(httpSession);
        String message = request.get("message");
        
        log.info("TRPG 채팅 요청 - 세션: {}, 사용자: {}", sessionId, userName);
        
        return aiService.chat(sessionId, userName, message)
                .map(ResponseEntity::ok)
                .onErrorResume(error -> {
                    log.error("AI 서비스 오류", error);
                    return Mono.just(ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                            .body(new ChatResponse("죄송합니다. 일시적인 오류가 발생했습니다.", List.of(), sessionId)));
                });
    }
    
    /**
     * 새 게임 세션 시작
     */
    @PostMapping("/sessions/new")
    public ResponseEntity<Map<String, String>> createNewSession(HttpSession httpSession) {
        String sessionId = sessionService.createNewGameSession();
        String userName = sessionService.getUserName(httpSession);
        
        // 세션 정보 저장
        httpSession.setAttribute("game_session_id", sessionId);
        
        return ResponseEntity.ok(Map.of(
            "sessionId", sessionId,
            "userName", userName,
            "message", "새로운 게임 세션이 생성되었습니다."
        ));
    }
}
```

### 5. 세션 관리 서비스

```java
@Service
public class SessionService {
    
    /**
     * 게임 세션 ID 조회 또는 생성
     */
    public String getOrCreateSessionId(HttpSession httpSession) {
        String sessionId = (String) httpSession.getAttribute("game_session_id");
        if (sessionId == null) {
            sessionId = createNewGameSession();
            httpSession.setAttribute("game_session_id", sessionId);
        }
        return sessionId;
    }
    
    /**
     * 새 게임 세션 ID 생성
     */
    public String createNewGameSession() {
        return "room_" + UUID.randomUUID().toString().substring(0, 8);
    }
    
    /**
     * 사용자명 조회 (로그인 정보 기반)
     */
    public String getUserName(HttpSession httpSession) {
        // 실제 구현시 로그인된 사용자 정보에서 가져오기
        String userName = (String) httpSession.getAttribute("user_name");
        if (userName == null) {
            userName = "플레이어" + UUID.randomUUID().toString().substring(0, 4);
            httpSession.setAttribute("user_name", userName);
        }
        return userName;
    }
}
```

---

## 🎮 멀티플레이어 구현

### 1. 방 참가 기능

```java
@PostMapping("/sessions/{sessionId}/join")
public ResponseEntity<Map<String, Object>> joinSession(
        @PathVariable String sessionId,
        HttpSession httpSession,
        @RequestParam String userName) {
    
    // 세션 유효성 검사
    if (!isValidSessionId(sessionId)) {
        return ResponseEntity.badRequest()
                .body(Map.of("error", "유효하지 않은 세션 ID입니다."));
    }
    
    // 사용자를 해당 세션에 참가
    httpSession.setAttribute("game_session_id", sessionId);
    httpSession.setAttribute("user_name", userName);
    
    return ResponseEntity.ok(Map.of(
        "sessionId", sessionId,
        "userName", userName,
        "message", userName + "님이 게임에 참가했습니다."
    ));
}
```

### 2. 세션 정보 조회

```java
@GetMapping("/sessions/{sessionId}/info")
public Mono<ResponseEntity<Map<String, Object>>> getSessionInfo(@PathVariable String sessionId) {
    
    return aiService.getSessionHistory(sessionId)
            .map(history -> ResponseEntity.ok(Map.of(
                "sessionId", sessionId,
                "messageCount", history.getMessageCount(),
                "users", history.getUsers()
            )))
            .onErrorReturn(ResponseEntity.notFound().build());
}
```

---

## ⚙️ 설정 파일

### application.yml
```yaml
dungeontalk:
  ai:
    base-url: http://localhost:8000
    timeout: 30s
    
server:
  port: 8080
  
logging:
  level:
    com.yourcompany.trpg: DEBUG
```

---

## 🔄 실시간 업데이트 (선택사항)

### WebSocket 또는 SSE를 사용한 실시간 동기화

```java
@Controller
public class TRPGWebSocketController {
    
    @MessageMapping("/trpg/{sessionId}")
    @SendTo("/topic/trpg/{sessionId}")
    public ChatResponse handleMessage(
            @DestinationVariable String sessionId,
            ChatRequest request) {
        
        // AI 서비스 호출 후 모든 참가자에게 브로드캐스트
        return aiService.chat(sessionId, request.getUserName(), request.getMessage())
                .block(); // 실제로는 비동기 처리 권장
    }
}
```

---

## 🧪 테스트 코드

```java
@SpringBootTest
@AutoConfigureMockMvc
class TRPGControllerTest {
    
    @Autowired
    private MockMvc mockMvc;
    
    @MockBean
    private DungeonTalkAIService aiService;
    
    @Test
    void testChat() throws Exception {
        // Given
        ChatResponse mockResponse = new ChatResponse("테스트 응답", List.of(), "room_test");
        when(aiService.chat(any(), any(), any())).thenReturn(Mono.just(mockResponse));
        
        // When & Then
        mockMvc.perform(post("/api/trpg/chat")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"message\": \"테스트 메시지\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.response").value("테스트 응답"));
    }
}
```

---

## 🚨 주의사항

### 1. 에러 처리
- Python 서버 다운시 대체 응답 제공
- 타임아웃 설정 (30초 권장)
- 재시도 로직 구현

### 2. 보안
```java
@Configuration
public class WebConfig implements WebMvcConfigurer {
    
    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
                .allowedOrigins("http://localhost:3000") // 프론트엔드 주소
                .allowedMethods("GET", "POST")
                .allowCredentials(true);
    }
}
```

### 3. 모니터링
```java
@Component
public class AIServiceHealthIndicator implements HealthIndicator {
    
    private final DungeonTalkAIService aiService;
    
    @Override
    public Health health() {
        try {
            boolean isHealthy = aiService.checkHealth().block(Duration.ofSeconds(5));
            return isHealthy ? Health.up().build() : Health.down().build();
        } catch (Exception e) {
            return Health.down().withException(e).build();
        }
    }
}
```

---

## 📱 프론트엔드 연동

### JavaScript 예시
```javascript
// TRPG 채팅
async function sendMessage(message) {
    const response = await fetch('/api/trpg/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: message})
    });
    
    const data = await response.json();
    displayMessage(data.response);
}

// 새 게임 시작
async function startNewGame() {
    const response = await fetch('/api/trpg/sessions/new', {method: 'POST'});
    const data = await response.json();
    console.log('새 게임 세션:', data.sessionId);
}
```

---

## 🎯 요약

1. **Python 서버를 8000번 포트에서 실행**
2. **Spring Boot에서 WebClient로 Python API 호출**
3. **세션 ID와 사용자명을 Spring Boot에서 관리** 
4. **멀티플레이어는 같은 세션 ID 공유**
5. **에러 처리와 타임아웃 설정 필수**

이 가이드대로 구현하면 Spring Boot와 Python AI 서버가 완벽하게 연동됩니다! 🚀
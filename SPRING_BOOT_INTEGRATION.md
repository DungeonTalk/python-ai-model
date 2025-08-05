# 🌱 Spring Boot 연동 완벽 가이드

던전톡 Python AI 서버와 Spring Boot 백엔드 연동을 위한 단계별 가이드

---

## 📋 전체 구조

```
사용자 ← → Spring Boot ← → Python FastAPI ← → AI (Claude/DeepSeek)
              ↓                    ↓
          세션/사용자 관리        RAG/문서 검색
```

**역할 분담:**
- **Spring Boot**: 사용자 인증, 세션 관리, 비즈니스 로직, 프론트엔드 API
- **Python FastAPI**: AI/RAG 처리, 문서 검색, 응답 생성, 세션별 대화 기록

---

## 🚀 1단계: Python 서버 준비

### 1.1 서버 실행
```bash
# 1. 환경 설정
cp .env.example .env

# 2. API 키 설정 (.env 파일)
ANTHROPIC_API_KEY=sk-ant-api03-your-api-key-here
LLM_PROVIDER=claude

# 3. 서버 시작
python main.py
# 또는 uv 사용시: uv run python main.py
```

### 1.2 서버 상태 확인
```bash
# 헬스체크
curl http://localhost:8000/health
# 응답: {"status":"healthy"}

# 세션 목록 확인
curl http://localhost:8000/sessions
# 응답: {"total_sessions":0,"max_sessions":100,"sessions":{}}
```

---

## 🔧 2단계: Spring Boot 프로젝트 설정

### 2.1 의존성 추가 (build.gradle)
```gradle
dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-web'
    implementation 'org.springframework.boot:spring-boot-starter-webflux' // WebClient
    implementation 'org.springframework.boot:spring-boot-starter-data-jpa' // 선택사항
    implementation 'org.springframework.boot:spring-boot-starter-security' // 선택사항
    
    // JSON 처리
    implementation 'com.fasterxml.jackson.core:jackson-core'
    implementation 'com.fasterxml.jackson.core:jackson-databind'
    
    // 로깅
    implementation 'org.springframework.boot:spring-boot-starter-logging'
    
    testImplementation 'org.springframework.boot:spring-boot-starter-test'
}
```

### 2.2 application.yml 설정
```yaml
server:
  port: 8080

# Python AI 서버 설정
dungeontalk:
  ai:
    base-url: http://localhost:8000
    timeout: 60s # AI 응답 대기 시간
    
# 로깅 설정
logging:
  level:
    com.yourcompany.trpg: DEBUG
    org.springframework.web.reactive.function.client: DEBUG
    
# 세션 설정
server:
  servlet:
    session:
      timeout: 30m # 세션 타임아웃
```

---

## 📦 3단계: DTO 클래스 작성

### 3.1 요청 DTO
```java
package com.yourcompany.trpg.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class ChatRequest {
    @JsonProperty("session_id")
    private String sessionId;
    
    @JsonProperty("user_name")
    private String userName;
    
    @JsonProperty("message")  
    private String message;
}
```

### 3.2 응답 DTO
```java
package com.yourcompany.trpg.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.util.List;

@Data
@NoArgsConstructor
public class ChatResponse {
    @JsonProperty("response")
    private String response;
    
    @JsonProperty("sources")
    private List<String> sources;
    
    @JsonProperty("session_id")
    private String sessionId;
}
```

### 3.3 세션 정보 DTO
```java
package com.yourcompany.trpg.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import java.util.List;
import java.util.Map;

@Data
public class SessionInfo {
    @JsonProperty("total_sessions")
    private int totalSessions;
    
    @JsonProperty("max_sessions")
    private int maxSessions;
    
    @JsonProperty("sessions")
    private Map<String, SessionDetail> sessions;
    
    @Data
    public static class SessionDetail {
        @JsonProperty("message_count")
        private int messageCount;
        
        @JsonProperty("users")
        private List<String> users;
        
        @JsonProperty("last_activity")
        private Long lastActivity;
    }
}
```

---

## 🔗 4단계: AI 서비스 클래스

### 4.1 WebClient 설정
```java
package com.yourcompany.trpg.config;

import io.netty.channel.ChannelOption;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.reactive.ReactorClientHttpConnector;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.netty.http.client.HttpClient;

import java.time.Duration;

@Configuration
public class WebClientConfig {
    
    @Value("${dungeontalk.ai.base-url}")
    private String aiBaseUrl;
    
    @Bean
    public WebClient aiWebClient() {
        HttpClient httpClient = HttpClient.create()
                .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, 10000) // 연결 타임아웃 10초
                .responseTimeout(Duration.ofSeconds(60)); // 응답 타임아웃 60초
                
        return WebClient.builder()
                .baseUrl(aiBaseUrl)
                .clientConnector(new ReactorClientHttpConnector(httpClient))
                .build();
    }
}
```

### 4.2 AI 서비스 구현
```java
package com.yourcompany.trpg.service;

import com.yourcompany.trpg.dto.ChatRequest;
import com.yourcompany.trpg.dto.ChatResponse;
import com.yourcompany.trpg.dto.SessionInfo;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import reactor.core.publisher.Mono;
import reactor.util.retry.Retry;

import java.time.Duration;
import java.util.List;

@Service
@Slf4j
@RequiredArgsConstructor
public class DungeonTalkAIService {
    
    private final WebClient aiWebClient;
    
    /**
     * AI와 채팅 - 멀티유저 세션 지원
     */
    public Mono<ChatResponse> chat(String sessionId, String userName, String message) {
        ChatRequest request = new ChatRequest(sessionId, userName, message);
        
        log.info("AI 채팅 요청 - 세션: {}, 사용자: {}, 메시지: '{}'", 
                sessionId, userName, message);
        
        return aiWebClient.post()
                .uri("/chat")
                .bodyValue(request)
                .retrieve()
                .bodyToMono(ChatResponse.class)
                .timeout(Duration.ofSeconds(60))
                .retryWhen(Retry.backoff(2, Duration.ofSeconds(1))) // 재시도 2회
                .doOnSuccess(response -> 
                    log.info("AI 응답 성공 - 세션: {}, 응답 길이: {}자", 
                            sessionId, response.getResponse().length()))
                .doOnError(error -> 
                    log.error("AI 요청 실패 - 세션: {}, 오류: {}", sessionId, error.getMessage()));
    }
    
    /**
     * 서버 상태 체크
     */
    public Mono<Boolean> checkHealth() {
        return aiWebClient.get()
                .uri("/health")
                .retrieve()
                .bodyToMono(String.class)
                .map(response -> response.contains("healthy"))
                .timeout(Duration.ofSeconds(5))
                .onErrorReturn(false);
    }
    
    /**
     * 활성 세션 목록 조회
     */
    public Mono<SessionInfo> getActiveSessions() {
        return aiWebClient.get()
                .uri("/sessions")
                .retrieve()
                .bodyToMono(SessionInfo.class)
                .timeout(Duration.ofSeconds(10));
    }
    
    /**
     * 특정 세션의 대화 기록 조회
     */
    public Mono<String> getSessionHistory(String sessionId) {
        return aiWebClient.get()
                .uri("/sessions/{sessionId}/history", sessionId)
                .retrieve()
                .bodyToMono(String.class)
                .timeout(Duration.ofSeconds(10));
    }
}
```

---

## 🎮 5단계: 세션 관리 서비스

### 5.1 세션 서비스
```java
package com.yourcompany.trpg.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import javax.servlet.http.HttpSession;
import java.util.UUID;

@Service
@Slf4j
public class SessionService {
    
    private static final String GAME_SESSION_ID = "game_session_id";
    private static final String USER_NAME = "user_name";
    
    /**
     * 게임 세션 ID 조회 또는 생성
     */
    public String getOrCreateSessionId(HttpSession httpSession) {
        String sessionId = (String) httpSession.getAttribute(GAME_SESSION_ID);
        if (sessionId == null) {
            sessionId = createNewGameSession();
            httpSession.setAttribute(GAME_SESSION_ID, sessionId);
            log.info("새 게임 세션 생성: {}", sessionId);
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
     * 기존 세션에 참가
     */
    public void joinSession(HttpSession httpSession, String sessionId, String userName) {
        httpSession.setAttribute(GAME_SESSION_ID, sessionId);
        httpSession.setAttribute(USER_NAME, userName);
        log.info("세션 참가 - 세션: {}, 사용자: {}", sessionId, userName);
    }
    
    /**
     * 사용자명 조회 또는 생성
     */
    public String getOrCreateUserName(HttpSession httpSession) {
        String userName = (String) httpSession.getAttribute(USER_NAME);
        if (userName == null) {
            userName = "플레이어" + UUID.randomUUID().toString().substring(0, 4);
            httpSession.setAttribute(USER_NAME, userName);
            log.info("새 사용자명 생성: {}", userName);
        }
        return userName;
    }
    
    /**
     * 사용자명 설정
     */
    public void setUserName(HttpSession httpSession, String userName) {
        httpSession.setAttribute(USER_NAME, userName);
        log.info("사용자명 설정: {}", userName);
    }
    
    /**
     * 세션 정보 삭제 (로그아웃시)
     */
    public void clearSession(HttpSession httpSession) {
        httpSession.removeAttribute(GAME_SESSION_ID);
        httpSession.removeAttribute(USER_NAME);
        log.info("세션 정보 삭제");
    }
}
```

---

## 🎯 6단계: 컨트롤러 구현

### 6.1 TRPG 채팅 컨트롤러
```java
package com.yourcompany.trpg.controller;

import com.yourcompany.trpg.dto.ChatResponse;
import com.yourcompany.trpg.service.DungeonTalkAIService;
import com.yourcompany.trpg.service.SessionService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

import javax.servlet.http.HttpSession;
import java.util.Map;

@RestController 
@RequestMapping("/api/trpg")
@Slf4j
@RequiredArgsConstructor
@CrossOrigin(origins = "*") // 프론트엔드 도메인으로 제한 권장
public class TRPGController {
    
    private final DungeonTalkAIService aiService;
    private final SessionService sessionService;
    
    /**
     * TRPG 채팅 - 메인 엔드포인트
     */
    @PostMapping("/chat")
    public Mono<ResponseEntity<ChatResponse>> chat(
            @RequestBody Map<String, String> request,
            HttpSession httpSession) {
        
        // 세션 정보 추출
        String sessionId = sessionService.getOrCreateSessionId(httpSession);
        String userName = sessionService.getOrCreateUserName(httpSession);
        String message = request.get("message");
        
        // 입력 검증
        if (message == null || message.trim().isEmpty()) {
            return Mono.just(ResponseEntity.badRequest().build());
        }
        
        log.info("TRPG 채팅 요청 - 세션: {}, 사용자: {}, 메시지: '{}'", 
                sessionId, userName, message);
        
        return aiService.chat(sessionId, userName, message)
                .map(ResponseEntity::ok)
                .onErrorResume(error -> {
                    log.error("AI 서비스 오류", error);
                    ChatResponse errorResponse = new ChatResponse();
                    errorResponse.setResponse("죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.");
                    errorResponse.setSessionId(sessionId);
                    return Mono.just(ResponseEntity.ok(errorResponse));
                });
    }
    
    /**
     * 새 게임 세션 시작
     */
    @PostMapping("/sessions/new")
    public ResponseEntity<Map<String, String>> createNewSession(HttpSession httpSession) {
        String sessionId = sessionService.createNewGameSession();
        String userName = sessionService.getOrCreateUserName(httpSession);
        
        // 세션 정보 저장
        sessionService.joinSession(httpSession, sessionId, userName);
        
        return ResponseEntity.ok(Map.of(
            "sessionId", sessionId,
            "userName", userName,
            "message", "새로운 게임 세션이 생성되었습니다."
        ));
    }
    
    /**
     * 기존 세션에 참가
     */
    @PostMapping("/sessions/{sessionId}/join")
    public ResponseEntity<Map<String, Object>> joinSession(
            @PathVariable String sessionId,
            @RequestBody Map<String, String> request,
            HttpSession httpSession) {
        
        String userName = request.get("userName");
        if (userName == null || userName.trim().isEmpty()) {
            return ResponseEntity.badRequest()
                    .body(Map.of("error", "사용자명이 필요합니다."));
        }
        
        // 세션 ID 유효성 검사 (간단한 형식 체크)
        if (!sessionId.startsWith("room_") || sessionId.length() < 10) {
            return ResponseEntity.badRequest()
                    .body(Map.of("error", "유효하지 않은 세션 ID입니다."));
        }
        
        // 사용자를 해당 세션에 참가
        sessionService.joinSession(httpSession, sessionId, userName);
        
        return ResponseEntity.ok(Map.of(
            "sessionId", sessionId,
            "userName", userName,
            "message", userName + "님이 게임에 참가했습니다."
        ));
    }
    
    /**
     * 현재 세션 정보 조회
     */
    @GetMapping("/sessions/current")
    public ResponseEntity<Map<String, String>> getCurrentSession(HttpSession httpSession) {
        String sessionId = (String) httpSession.getAttribute("game_session_id");
        String userName = (String) httpSession.getAttribute("user_name");
        
        if (sessionId == null) {
            return ResponseEntity.ok(Map.of("message", "활성 세션이 없습니다."));
        }
        
        return ResponseEntity.ok(Map.of(
            "sessionId", sessionId,
            "userName", userName != null ? userName : "알 수 없음"
        ));
    }
    
    /**
     * 사용자명 변경
     */
    @PutMapping("/user/name")
    public ResponseEntity<Map<String, String>> updateUserName(
            @RequestBody Map<String, String> request,
            HttpSession httpSession) {
        
        String newUserName = request.get("userName");
        if (newUserName == null || newUserName.trim().isEmpty()) {
            return ResponseEntity.badRequest()
                    .body(Map.of("error", "사용자명이 필요합니다."));
        }
        
        sessionService.setUserName(httpSession, newUserName);
        
        return ResponseEntity.ok(Map.of(
            "userName", newUserName,
            "message", "사용자명이 변경되었습니다."
        ));
    }
}
```

### 6.2 관리자용 컨트롤러
```java
package com.yourcompany.trpg.controller;

import com.yourcompany.trpg.dto.SessionInfo;
import com.yourcompany.trpg.service.DungeonTalkAIService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/api/admin")
@Slf4j
@RequiredArgsConstructor
public class AdminController {
    
    private final DungeonTalkAIService aiService;
    
    /**
     * AI 서버 상태 확인
     */
    @GetMapping("/health")
    public Mono<ResponseEntity<String>> checkAIHealth() {
        return aiService.checkHealth()
                .map(isHealthy -> ResponseEntity.ok(
                    isHealthy ? "AI 서버 정상" : "AI 서버 오류"))
                .onErrorReturn(ResponseEntity.ok("AI 서버 연결 불가"));
    }
    
    /**
     * 활성 세션 목록 조회
     */
    @GetMapping("/sessions")
    public Mono<ResponseEntity<SessionInfo>> getActiveSessions() {
        return aiService.getActiveSessions()
                .map(ResponseEntity::ok)
                .onErrorReturn(ResponseEntity.internalServerError().build());
    }
    
    /**
     * 특정 세션 기록 조회
     */
    @GetMapping("/sessions/{sessionId}/history")
    public Mono<ResponseEntity<String>> getSessionHistory(@PathVariable String sessionId) {
        return aiService.getSessionHistory(sessionId)
                .map(ResponseEntity::ok)
                .onErrorReturn(ResponseEntity.notFound().build());
    }
}
```

---

## 🌐 7단계: 프론트엔드 연동

### 7.1 JavaScript (Vanilla)
```javascript
class TRPGClient {
    constructor(baseUrl = '/api/trpg') {
        this.baseUrl = baseUrl;
    }
    
    // TRPG 채팅
    async sendMessage(message) {
        try {
            const response = await fetch(`${this.baseUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin', // 세션 쿠키 포함
                body: JSON.stringify({ message: message })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('채팅 전송 실패:', error);
            throw error;
        }
    }
    
    // 새 게임 시작
    async startNewGame() {
        const response = await fetch(`${this.baseUrl}/sessions/new`, {
            method: 'POST',
            credentials: 'same-origin'
        });
        
        return await response.json();
    }
    
    // 기존 게임 참가
    async joinGame(sessionId, userName) {
        const response = await fetch(`${this.baseUrl}/sessions/${sessionId}/join`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin',
            body: JSON.stringify({ userName: userName })
        });
        
        return await response.json();
    }
    
    // 현재 세션 정보
    async getCurrentSession() {
        const response = await fetch(`${this.baseUrl}/sessions/current`, {
            credentials: 'same-origin'
        });
        
        return await response.json();
    }
}

// 사용 예시
const trpgClient = new TRPGClient();

// 채팅 전송
document.getElementById('sendButton').addEventListener('click', async () => {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    
    if (!message) return;
    
    try {
        // 사용자 메시지 표시
        displayMessage('user', message);
        messageInput.value = '';
        
        // AI 응답 요청
        const response = await trpgClient.sendMessage(message);
        
        // AI 응답 표시
        displayMessage('assistant', response.response);
        
        // 참고 문서 표시 (선택사항)
        if (response.sources && response.sources.length > 0) {
            displaySources(response.sources);
        }
        
    } catch (error) {
        displayMessage('system', '오류가 발생했습니다: ' + error.message);
    }
});

function displayMessage(role, content) {
    const chatContainer = document.getElementById('chatContainer');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.innerHTML = `
        <div class="message-content">
            ${content.replace(/\\n/g, '<br>')}
        </div>
        <div class="message-time">
            ${new Date().toLocaleTimeString()}
        </div>
    `;
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}
```

### 7.2 React Hook 예시
```javascript
import { useState, useCallback } from 'react';

export const useTRPG = () => {
    const [isLoading, setIsLoading] = useState(false);
    const [currentSession, setCurrentSession] = useState(null);
    
    const sendMessage = useCallback(async (message) => {
        setIsLoading(true);
        try {
            const response = await fetch('/api/trpg/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin',
                body: JSON.stringify({ message })
            });
            
            const data = await response.json();
            return data;
        } finally {
            setIsLoading(false);
        }
    }, []);
    
    const startNewGame = useCallback(async () => {
        const response = await fetch('/api/trpg/sessions/new', {
            method: 'POST',
            credentials: 'same-origin'
        });
        
        const data = await response.json();
        setCurrentSession(data);
        return data;
    }, []);
    
    return {
        sendMessage,
        startNewGame,
        isLoading,
        currentSession
    };
};
```

---

## 🧪 8단계: 테스트

### 8.1 단위 테스트
```java
package com.yourcompany.trpg.service;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.context.ActiveProfiles;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

@SpringBootTest
@ActiveProfiles("test")
class DungeonTalkAIServiceTest {
    
    @MockBean
    private DungeonTalkAIService aiService;
    
    @Test
    void testChatSuccess() {
        // Given
        String sessionId = "test_room";
        String userName = "테스터";
        String message = "안녕하세요";
        
        ChatResponse mockResponse = new ChatResponse();
        mockResponse.setResponse("안녕하세요! 던전마스터입니다.");
        mockResponse.setSessionId(sessionId);
        
        when(aiService.chat(sessionId, userName, message))
                .thenReturn(Mono.just(mockResponse));
        
        // When & Then
        StepVerifier.create(aiService.chat(sessionId, userName, message))
                .expectNext(mockResponse)
                .verifyComplete();
    }
}
```

### 8.2 통합 테스트
```java
package com.yourcompany.trpg.controller;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.test.context.ActiveProfiles;

import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
class TRPGControllerIntegrationTest {
    
    @Autowired
    private TestRestTemplate restTemplate;
    
    @Test
    void testCreateNewSession() {
        // When
        ResponseEntity<Map> response = restTemplate.postForEntity(
                "/api/trpg/sessions/new", null, Map.class);
        
        // Then
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getBody()).containsKey("sessionId");
        assertThat(response.getBody().get("sessionId").toString()).startsWith("room_");
    }
}
```

---

## 🚨 9단계: 운영 고려사항

### 9.1 에러 처리 및 로깅
```java
package com.yourcompany.trpg.exception;

import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.reactive.function.client.WebClientResponseException;

import java.util.Map;

@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler {
    
    @ExceptionHandler(WebClientResponseException.class)
    public ResponseEntity<Map<String, String>> handleWebClientException(WebClientResponseException e) {
        log.error("AI 서비스 통신 오류: {}", e.getMessage());
        
        return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE)
                .body(Map.of(
                    "error", "AI 서비스에 일시적인 문제가 발생했습니다.",
                    "message", "잠시 후 다시 시도해주세요."
                ));
    }
    
    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, String>> handleGenericException(Exception e) {
        log.error("예상치 못한 오류", e);
        
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of(
                    "error", "서버 내부 오류가 발생했습니다.",
                    "message", "관리자에게 문의해주세요."
                ));
    }
}
```

### 9.2 헬스체크
```java
package com.yourcompany.trpg.health;

import com.yourcompany.trpg.service.DungeonTalkAIService;
import lombok.RequiredArgsConstructor;
import org.springframework.boot.actuator.health.Health;
import org.springframework.boot.actuator.health.HealthIndicator;
import org.springframework.stereotype.Component;

import java.time.Duration;

@Component
@RequiredArgsConstructor
public class AIServiceHealthIndicator implements HealthIndicator {
    
    private final DungeonTalkAIService aiService;
    
    @Override
    public Health health() {
        try {
            boolean isHealthy = aiService.checkHealth()
                    .block(Duration.ofSeconds(5));
            
            if (isHealthy) {
                return Health.up()
                        .withDetail("ai-server", "정상")
                        .build();
            } else {
                return Health.down()
                        .withDetail("ai-server", "응답 없음")
                        .build();
            }
        } catch (Exception e) {
            return Health.down()
                    .withDetail("ai-server", "연결 실패")
                    .withException(e)
                    .build();
        }
    }
}
```

### 9.3 보안 설정
```java
package com.yourcompany.trpg.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

import java.util.Arrays;

@Configuration
public class SecurityConfig {
    
    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration configuration = new CorsConfiguration();
        
        // 프로덕션에서는 실제 도메인으로 제한
        configuration.setAllowedOriginPatterns(Arrays.asList("http://localhost:*", "https://yourdomain.com"));
        configuration.setAllowedMethods(Arrays.asList("GET", "POST", "PUT", "DELETE", "OPTIONS"));
        configuration.setAllowedHeaders(Arrays.asList("*"));
        configuration.setAllowCredentials(true);
        configuration.setMaxAge(3600L);
        
        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/api/**", configuration);
        
        return source;
    }
}
```

---

## 🎯 10단계: 실전 사용 시나리오

### 10.1 시나리오 1: 혼자 플레이
```javascript
// 1. 새 게임 시작
const session = await trpgClient.startNewGame();
console.log('세션 ID:', session.sessionId);

// 2. 게임 시작
await trpgClient.sendMessage("황혼의 새벽 세계관으로 새로운 모험을 시작하고 싶어");

// 3. 계속 플레이
await trpgClient.sendMessage("주변을 둘러보겠어");
await trpgClient.sendMessage("오크가 나타나면 공격할게");
```

### 10.2 시나리오 2: 친구들과 함께 플레이
```javascript
// 플레이어 1 (방장)
const session = await trpgClient.startNewGame();
const roomId = session.sessionId;
console.log('친구들에게 알려줄 방 ID:', roomId);

// 플레이어 2, 3 (참가자들)
await trpgClient.joinGame(roomId, "김철수");
await trpgClient.joinGame(roomId, "이영희");

// 모든 플레이어가 같은 방에서 대화
await trpgClient.sendMessage("안녕하세요! 김철수입니다.");
await trpgClient.sendMessage("저는 이영희예요. 잘 부탁드려요!");
await trpgClient.sendMessage("그럼 모험을 시작해볼까요?");
```

---

## 📚 11단계: 문제 해결

### 11.1 자주 발생하는 문제들

**Q: "AI 서비스에 연결할 수 없습니다" 오류**
```java
// A: 타임아웃 설정 증가
.responseTimeout(Duration.ofSeconds(120)) // 60초 → 120초
```

**Q: 한글 깨짐 현상**
```yaml
# A: application.yml에 인코딩 설정
server:
  servlet:
    encoding:
      charset: UTF-8
      force: true
```

**Q: 세션이 유지되지 않음**
```yaml
# A: 세션 타임아웃 증가
server:
  servlet:
    session:
      timeout: 60m # 30분 → 60분
```

### 11.2 성능 최적화
```java
// WebClient 커넥션 풀 설정
HttpClient httpClient = HttpClient.create()
    .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, 10000)
    .responseTimeout(Duration.ofSeconds(60))
    .option(ChannelOption.SO_KEEPALIVE, true)
    .option(EpollChannelOption.TCP_KEEPIDLE, 300)
    .option(EpollChannelOption.TCP_KEEPINTVL, 60)
    .option(EpollChannelOption.TCP_KEEPCNT, 8);
```

---

## 🎉 완료!

이 가이드를 따라하면 Spring Boot와 Python AI 서버가 완벽하게 연동되어 멀티플레이어 TRPG 게임을 즐길 수 있습니다.

**핵심 포인트:**
- ✅ 세션별 독립된 게임 공간
- ✅ 실시간 멀티플레이어 지원  
- ✅ 안정적인 에러 처리
- ✅ 확장 가능한 구조

**추가 개발시 참고:**
- 실시간 업데이트: WebSocket 도입
- 사용자 인증: Spring Security 적용
- 데이터 영속성: 대화 기록 DB 저장
- 모니터링: Actuator + Micrometer 활용
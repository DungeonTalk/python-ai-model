# 🌱 Spring Boot에서 Python RAG 연동 가이드

> Spring Boot 백엔드에서 Python RAG AI 서비스를 호출하는 완전한 가이드

## 📋 사전 준비

### 1. Python RAG 서버 실행 중이어야 함
```bash
# Python RAG 서버 실행
cd dungeontalk-mvp
python main.py
# ✅ http://localhost:8005 에서 실행 중 확인
```

### 2. Spring Boot 프로젝트 생성
- **Spring Initializr**: https://start.spring.io/
- **의존성**: Spring Web, Spring Session (선택)
- **Java**: 11 이상

## 🚀 구현 방법

### 방법 1: 기본 RestTemplate (추천)

#### 1. 의존성 추가 (pom.xml)
```xml
<dependencies>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
    <dependency>
        <groupId>org.apache.httpcomponents</groupId>
        <artifactId>httpclient</artifactId>
    </dependency>
</dependencies>
```

#### 2. RAG 서비스 클래스
```java
package com.example.service;

import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.ResponseEntity;
import java.util.Map;
import java.util.HashMap;

@Service
public class RagService {
    
    private final RestTemplate restTemplate;
    private final String RAG_BASE_URL = "http://localhost:8005";
    
    public RagService() {
        this.restTemplate = new RestTemplate();
    }
    
    /**
     * Python RAG에 채팅 요청
     */
    public String chat(String message) {
        String url = RAG_BASE_URL + "/chat";
        
        // 요청 객체 생성
        Map<String, String> request = new HashMap<>();
        request.put("message", message);
        
        try {
            // POST 요청 전송
            ResponseEntity<Map> response = restTemplate.postForEntity(
                url, request, Map.class);
            
            // 응답에서 답변 추출
            Map<String, Object> responseBody = response.getBody();
            return (String) responseBody.get("response");
            
        } catch (Exception e) {
            return "AI 서비스에 연결할 수 없습니다: " + e.getMessage();
        }
    }
    
    /**
     * Python RAG 서버 상태 확인
     */
    public boolean isHealthy() {
        try {
            String url = RAG_BASE_URL + "/health";
            ResponseEntity<String> response = restTemplate.getForEntity(url, String.class);
            return response.getStatusCode().is2xxSuccessful();
        } catch (Exception e) {
            return false;
        }
    }
    
    /**
     * 문서 재스캔 요청
     */
    public String rescanDocuments() {
        try {
            String url = RAG_BASE_URL + "/rescan";
            ResponseEntity<Map> response = restTemplate.postForEntity(url, null, Map.class);
            Map<String, Object> responseBody = response.getBody();
            return (String) responseBody.get("message");
        } catch (Exception e) {
            return "문서 재스캔 실패: " + e.getMessage();
        }
    }
}
```

#### 3. 컨트롤러 생성
```java
package com.example.controller;

import com.example.service.RagService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;
import java.util.HashMap;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*") // 프론트엔드 연동시
public class ChatController {
    
    @Autowired
    private RagService ragService;
    
    /**
     * 기본 채팅 API
     */
    @PostMapping("/chat")
    public ResponseEntity<Map<String, Object>> chat(@RequestBody Map<String, String> request) {
        String userMessage = request.get("message");
        
        if (userMessage == null || userMessage.trim().isEmpty()) {
            return ResponseEntity.badRequest()
                .body(Map.of("error", "메시지가 비어있습니다."));
        }
        
        // Python RAG 호출
        String aiResponse = ragService.chat(userMessage);
        
        Map<String, Object> response = new HashMap<>();
        response.put("response", aiResponse);
        response.put("timestamp", System.currentTimeMillis());
        
        return ResponseEntity.ok(response);
    }
    
    /**
     * 시스템 상태 확인
     */
    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        Map<String, Object> status = new HashMap<>();
        status.put("spring", "healthy");
        status.put("rag_service", ragService.isHealthy());
        status.put("timestamp", System.currentTimeMillis());
        
        return ResponseEntity.ok(status);
    }
    
    /**
     * 문서 재스캔
     */
    @PostMapping("/rescan")
    public ResponseEntity<Map<String, Object>> rescanDocuments() {
        String result = ragService.rescanDocuments();
        
        return ResponseEntity.ok(Map.of(
            "message", result,
            "timestamp", System.currentTimeMillis()
        ));
    }
}
```

### 방법 2: 세션 관리 포함 (고급)

#### 1. 세션 채팅 컨트롤러
```java
package com.example.controller;

import com.example.service.RagService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import javax.servlet.http.HttpSession;
import java.util.*;

@RestController
@RequestMapping("/api")
public class SessionChatController {
    
    @Autowired
    private RagService ragService;
    
    /**
     * 세션 기반 채팅 (대화 기록 유지)
     */
    @PostMapping("/chat/session")
    public ResponseEntity<Map<String, Object>> chatWithSession(
            HttpSession session,
            @RequestBody Map<String, String> request) {
        
        String userMessage = request.get("message");
        
        // 1. 세션에서 대화 기록 가져오기
        List<String> history = getConversationHistory(session);
        
        // 2. 컨텍스트 구성
        String contextMessage = buildContextWithHistory(history, userMessage);
        
        // 3. Python RAG 호출
        String aiResponse = ragService.chat(contextMessage);
        
        // 4. 세션에 저장
        saveToSession(session, userMessage, aiResponse);
        
        // 5. 응답 구성
        Map<String, Object> response = new HashMap<>();
        response.put("response", aiResponse);
        response.put("session_id", session.getId());
        response.put("turn_count", history.size() / 2 + 1);
        
        return ResponseEntity.ok(response);
    }
    
    /**
     * 세션 초기화
     */
    @PostMapping("/chat/session/reset")
    public ResponseEntity<Map<String, Object>> resetSession(HttpSession session) {
        session.removeAttribute("conversation");
        
        return ResponseEntity.ok(Map.of(
            "message", "대화 기록이 초기화되었습니다.",
            "session_id", session.getId()
        ));
    }
    
    /**
     * 세션에서 대화 기록 가져오기
     */
    @SuppressWarnings("unchecked")
    private List<String> getConversationHistory(HttpSession session) {
        List<String> history = (List<String>) session.getAttribute("conversation");
        return history != null ? history : new ArrayList<>();
    }
    
    /**
     * 대화 기록과 함께 컨텍스트 구성
     */
    private String buildContextWithHistory(List<String> history, String newMessage) {
        if (history.isEmpty()) {
            return newMessage;
        }
        
        StringBuilder context = new StringBuilder();
        context.append("이전 대화:\n");
        
        // 최근 5턴만 포함 (토큰 절약)
        int start = Math.max(0, history.size() - 10);
        for (int i = start; i < history.size(); i += 2) {
            if (i + 1 < history.size()) {
                context.append("사용자: ").append(history.get(i)).append("\n");
                context.append("AI: ").append(history.get(i + 1)).append("\n");
            }
        }
        
        context.append("\n새 질문: ").append(newMessage);
        return context.toString();
    }
    
    /**
     * 세션에 대화 저장
     */
    private void saveToSession(HttpSession session, String userMessage, String aiResponse) {
        List<String> history = getConversationHistory(session);
        history.add(userMessage);
        history.add(aiResponse);
        
        // 최대 20턴 유지 (40개 메시지)
        if (history.size() > 40) {
            history = new ArrayList<>(history.subList(history.size() - 40, history.size()));
        }
        
        session.setAttribute("conversation", history);
    }
}
```

#### 2. application.yml 설정
```yaml
# application.yml
server:
  port: 8080

# 세션 설정
spring:
  session:
    timeout: 30m
    store-type: memory

# RAG 서비스 설정
rag:
  service:
    url: http://localhost:8005
    timeout: 30s

# 로깅
logging:
  level:
    com.example: DEBUG
    org.springframework.web: INFO
```

### 방법 3: WebClient (비동기, 고급)

#### 1. WebClient 설정
```java
package com.example.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;

@Configuration
public class RagConfig {
    
    @Bean
    public WebClient ragWebClient() {
        return WebClient.builder()
            .baseUrl("http://localhost:8005")
            .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
            .build();
    }
}
```

#### 2. 비동기 RAG 서비스
```java
package com.example.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;
import java.util.Map;

@Service
public class AsyncRagService {
    
    @Autowired
    private WebClient ragWebClient;
    
    /**
     * 비동기 채팅 요청
     */
    public Mono<String> chatAsync(String message) {
        Map<String, String> request = Map.of("message", message);
        
        return ragWebClient.post()
            .uri("/chat")
            .bodyValue(request)
            .retrieve()
            .bodyToMono(Map.class)
            .map(response -> (String) response.get("response"))
            .onErrorReturn("AI 서비스 오류가 발생했습니다.");
    }
}
```

## 🧪 테스트 방법

### 1. 서버 실행
```bash
# 1. Python RAG 서버 실행
cd dungeontalk-mvp
python main.py

# 2. Spring Boot 서버 실행
./mvnw spring-boot:run
```

### 2. API 테스트

#### 기본 채팅 테스트
```bash
curl -X POST "http://localhost:8080/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "근접무기 중에 좋은 게 뭐 있어?"}'
```

#### 세션 채팅 테스트
```bash
# 첫 번째 메시지
curl -X POST "http://localhost:8080/api/chat/session" \
  -H "Content-Type: application/json" \
  -H "Cookie: JSESSIONID=YOUR_SESSION_ID" \
  -d '{"message": "안녕하세요"}'

# 두 번째 메시지 (같은 세션)
curl -X POST "http://localhost:8080/api/chat/session" \
  -H "Content-Type: application/json" \
  -H "Cookie: JSESSIONID=YOUR_SESSION_ID" \
  -d '{"message": "아까 말한 그 무기는?"}'
```

#### 헬스체크 테스트
```bash
curl -X GET "http://localhost:8080/api/health"
```

### 3. 응답 예시
```json
{
  "response": "안녕하세요, 던전마스터입니다. 근접무기에 대해 설명해드리겠습니다...",
  "timestamp": 1691234567890
}
```

## 🔧 문제 해결

### ❌ "Connection refused" 오류
```bash
# Python RAG 서버가 실행 중인지 확인
curl -X GET "http://localhost:8005/health"

# 포트 충돌 확인
netstat -ano | findstr :8005
```

### ❌ CORS 오류 (프론트엔드 연동시)
```java
@CrossOrigin(origins = "http://localhost:3000") // React 개발 서버
@RestController
public class ChatController {
    // ...
}
```

### ❌ 세션 문제
```java
// 세션 디버깅
@GetMapping("/session/debug")
public Map<String, Object> debugSession(HttpSession session) {
    return Map.of(
        "session_id", session.getId(),
        "creation_time", session.getCreationTime(),
        "conversation_size", getConversationHistory(session).size()
    );
}
```

## 🚀 프로덕션 고려사항

### 1. 커넥션 풀 설정
```java
@Configuration
public class HttpClientConfig {
    
    @Bean
    public RestTemplate restTemplate() {
        HttpComponentsClientHttpRequestFactory factory = 
            new HttpComponentsClientHttpRequestFactory();
        factory.setConnectTimeout(5000);
        factory.setReadTimeout(30000);
        
        RestTemplate restTemplate = new RestTemplate(factory);
        return restTemplate;
    }
}
```

### 2. 에러 핸들링
```java
@ControllerAdvice
public class GlobalExceptionHandler {
    
    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, Object>> handleException(Exception e) {
        return ResponseEntity.status(500).body(Map.of(
            "error", "서버 오류가 발생했습니다.",
            "message", e.getMessage(),
            "timestamp", System.currentTimeMillis()
        ));
    }
}
```

### 3. Redis 세션 (다중 서버)
```yaml
spring:
  redis:
    host: localhost
    port: 6379
  session:
    store-type: redis
```

## 🎯 다음 단계

1. **프론트엔드 연동**: React/Vue.js에서 Spring API 호출
2. **인증/권한**: Spring Security 추가
3. **모니터링**: Actuator + Prometheus
4. **배포**: Docker + Kubernetes

**이제 Spring Boot에서 Python RAG를 완전히 제어할 수 있습니다!** 🎮
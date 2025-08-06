# 🎲 DungeonTalk MVP - Architecture Analysis

## Project Overview

DungeonTalk MVP is a TRPG (Table-top Role Playing Game) RAG (Retrieval Augmented Generation) system that serves as an AI-powered Dungeon Master assistant. The system combines a FastAPI backend with a Streamlit frontend to provide intelligent, context-aware responses based on uploaded TRPG documents.

## 1. Overall Project Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    DungeonTalk MVP System                       │
│                                                                 │
│  ┌─────────────────┐    HTTP/REST     ┌──────────────────────┐  │
│  │   Streamlit     │◄─── API ────────►│    FastAPI Server    │  │
│  │   Frontend      │    (Port 8501)   │    (Port 8005)       │  │
│  │                 │                  │                      │  │
│  │ • Chat Interface│                  │ • RAG Engine         │  │
│  │ • File Upload   │                  │ • Document Processing│  │
│  │ • Status Monitor│                  │ • Vector Operations  │  │
│  └─────────────────┘                  └──────────────────────┘  │
│                                                ▲                │
│                                                │                │
│  ┌─────────────────┐                  ┌───────▼──────────────┐  │
│  │   Documents     │                  │   ChromaDB Vector    │  │
│  │   Repository    │◄─────────────────┤   Database           │  │
│  │                 │   File Scanning  │                      │  │
│  │ • Game Rules    │   & Embedding    │ • Document Vectors   │  │
│  │ • NPCs          │                  │ • Similarity Search  │  │
│  │ • World Setting │                  │ • Metadata Storage   │  │
│  │ • Scenarios     │                  │ • Hash Tracking      │  │
│  └─────────────────┘                  └──────────────────────┘  │
│                                                ▲                │
│                                                │                │
│  ┌─────────────────┐                  ┌───────▼──────────────┐  │
│  │  External APIs  │                  │   LLM Integration    │  │
│  │                 │◄─────────────────┤                      │  │
│  │ • Claude API    │   Query & Response│ • Claude 3.5 Sonnet │  │
│  │ • Ollama (Local)│                  │ • Ollama (Local LLM) │  │
│  │ • HuggingFace   │                  │ • Text Generation    │  │
│  └─────────────────┘                  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Component Relationships

The system follows a **microservices-like architecture** with clear separation of concerns:

1. **Presentation Layer**: Streamlit web interface
2. **API Layer**: FastAPI REST endpoints
3. **Business Logic**: RAG Engine for document processing and retrieval
4. **Data Layer**: ChromaDB vector database and file system
5. **External Services**: LLM providers (Claude/Ollama) and embedding models

## 2. MVC Pattern Implementation

While not strictly following traditional MVC, the system implements a **similar separation of concerns**:

### Model Layer (Data & Business Logic)
- **`RAGEngine` class** (main.py): Core business logic
- **ChromaDB**: Vector database for document storage
- **Document files**: Raw data in `/documents` folder
- **Pydantic models**: `ChatRequest`, `ChatResponse` for data validation

### View Layer (Presentation)
- **Streamlit interface** (streamlit_app.py): User interface
- **Chat interface**: Message display and input
- **File upload interface**: Document management
- **Status dashboard**: System monitoring

### Controller Layer (API & Routing)
- **FastAPI endpoints**: HTTP request handling
- **Route handlers**: `/chat`, `/upload`, `/health`, `/rescan`
- **CORS middleware**: Cross-origin request handling
- **Error handling**: HTTP exceptions and responses

## 3. Key Components and Relationships

### 3.1 RAGEngine Class (Core Component)

```python
class RAGEngine:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(...)      # Text embedding model
        self.vectorstore = Chroma(...)                     # Vector database
        self.llm = ChatAnthropic(...) or OllamaLLM(...)    # Language model
        self.qa_chain = RetrievalQA.from_chain_type(...)   # RAG pipeline
```

**Key Responsibilities:**
- Document processing and chunking
- Vector embedding generation
- Similarity search and retrieval
- LLM query processing
- File hash tracking for incremental updates

### 3.2 Component Interaction Flow

```
User Input → Streamlit → FastAPI → RAGEngine → ChromaDB
                                      ↓
LLM Provider ← RAGEngine ← Retrieved Documents
     ↓
Generated Response → FastAPI → Streamlit → User Display
```

### 3.3 Document Processing Pipeline

```
Text Files (.txt, .md, .csv)
    ↓
TextLoader (UTF-8 encoding)
    ↓
RecursiveCharacterTextSplitter
    ↓ (chunks: 1000 chars, overlap: 200)
HuggingFace Multilingual E5 Embeddings
    ↓
ChromaDB Vector Storage
    ↓
MD5 Hash Tracking (file_hashes.json)
```

## 4. Technology Stack

### Backend Technologies
- **FastAPI**: Modern, high-performance web framework
- **LangChain**: RAG framework and LLM orchestration
- **ChromaDB**: Open-source vector database
- **HuggingFace Transformers**: Multilingual embedding models
- **Pydantic**: Data validation and serialization

### Frontend Technologies
- **Streamlit**: Rapid web app development framework
- **Requests**: HTTP client for API communication

### AI/ML Technologies
- **Claude 3.5 Sonnet**: Advanced language model via Anthropic API
- **Ollama**: Local LLM serving (fallback option)
- **intfloat/multilingual-e5-large**: Embedding model for Korean/English text

### Infrastructure
- **Uvicorn**: ASGI server for FastAPI
- **Python-dotenv**: Environment variable management
- **Hashlib**: File integrity tracking
- **Python-multipart**: File upload handling

## 5. Data Flow Architecture

### 5.1 Document Ingestion Flow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   File Upload   │    │  Auto Scanner   │    │  Manual Add     │
│  (Streamlit UI) │    │  (Startup/API)  │    │ (Direct Copy)   │
└─────┬───────────┘    └─────┬───────────┘    └─────┬───────────┘
      │                      │                      │
      ▼                      ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Document Processing                         │
│                                                                 │
│  1. File Hash Check (MD5) → Skip if unchanged                  │
│  2. TextLoader → Load with UTF-8 encoding                      │
│  3. RecursiveCharacterTextSplitter → Chunk text               │
│  4. HuggingFace Embeddings → Generate vectors                  │
│  5. ChromaDB → Store vectors with metadata                     │
│  6. Hash Update → Update file_hashes.json                      │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Query Processing Flow

```
User Query (Korean/English)
    ↓
Streamlit Frontend
    ↓ (HTTP POST /chat)
FastAPI Endpoint
    ↓
RAGEngine.query()
    ↓
TRPG Context Prompt Template:
┌─────────────────────────────────────────────────────────────────┐
│ "당신은 TRPG GM입니다. 게임을 진행해주세요."                        │
│ "# 답변 형식 규칙:"                                              │
│ "1. 상황과 문맥에 맞는 대답을 해줘"                               │
│ "2. 게임 목표로 갈 수 있게 유도를 해줘"                           │
│ "3. 상황을 생생하게 묘사하고..."                                  │
│ "..."                                                           │
│ "{user_question}"                                               │
└─────────────────────────────────────────────────────────────────┘
    ↓
Vector Similarity Search (k=3)
    ↓
Retrieved Context Documents
    ↓
LLM Query (Claude/Ollama)
    ↓
Generated Response + Source Documents
    ↓
JSON Response → Streamlit → User Display
```

### 5.3 State Management

```
Session State (Streamlit):
├── messages[]          # Chat history
├── current_model       # LLM provider selection
└── api_base           # API server address

Persistent Storage:
├── vectorstore_new/    # ChromaDB database files
├── file_hashes.json   # Document change tracking
├── .env               # Configuration (API keys)
└── documents/         # Source documents
```

## 6. File Organization

### 6.1 Project Structure

```
dungeontalk-mvp/
├── main.py                    # FastAPI server + RAG engine
├── streamlit_app.py          # Web UI frontend
├── requirements.txt          # Python dependencies
├── setup.bat                # Windows installation script
├── README.md                # User documentation
├── SPRING_INTEGRATION.md     # Integration guide
│
├── documents/               # TRPG content repository
│   ├── NPC_*.txt           # Non-player characters
│   ├── 아이템_*.txt         # Items and equipment
│   ├── 세계관_*.txt         # World settings
│   ├── 시나리오_*.txt       # Game scenarios
│   ├── 규칙_*.txt          # Game rules
│   ├── 장소_*.txt          # Locations
│   └── 퀘스트_*.txt        # Quests
│
├── vectorstore_new/         # ChromaDB storage
│   ├── chroma.sqlite3      # SQLite database
│   ├── file_hashes.json    # Change tracking
│   └── [uuid]/             # Vector data files
│
└── vectorstore/            # Legacy vector storage
    └── ...
```

### 6.2 Configuration Management

```
Environment Variables (.env):
├── ANTHROPIC_API_KEY       # Claude API authentication
├── LLM_PROVIDER           # "claude" or "ollama"
├── CLAUDE_MODEL           # Model version selection
└── (Optional local settings)

Runtime Configuration:
├── Embedding Model: intfloat/multilingual-e5-large
├── Chunk Size: 1000 characters
├── Chunk Overlap: 200 characters
├── Retrieval K: 3 documents
├── Temperature: 0.7
└── Max Tokens: 2000
```

## 7. RAG System Deep Dive

### 7.1 Document Processing Strategy

**Supported Formats**: `.txt`, `.md`, `.csv`
**Encoding**: UTF-8
**Language Support**: Korean (primary), English
**Chunking Strategy**: Recursive character splitting

```python
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,        # Optimal for Korean text
    chunk_overlap=200       # Preserve context between chunks
)
```

### 7.2 Embedding Model Selection

**Model**: `intfloat/multilingual-e5-large`
**Rationale**: 
- Excellent Korean language support
- Cross-lingual capabilities
- High-quality semantic representations
- 1024-dimensional vectors

### 7.3 Vector Storage Architecture

**Database**: ChromaDB
**Features**:
- Local-first approach
- SQLite backend for metadata
- HNSW indexing for fast similarity search
- Persistent storage

### 7.4 Retrieval Strategy

```python
retriever = vectorstore.as_retriever(
    search_kwargs={"k": 3}  # Return top 3 most relevant chunks
)
```

**Search Process**:
1. Query embedding generation
2. Cosine similarity calculation
3. Top-k selection
4. Context assembly for LLM

### 7.5 Prompt Engineering

The system uses a sophisticated prompt template specifically designed for TRPG game mastering:

```
당신은 TRPG GM입니다. 게임을 진행해주세요.

# 답변 형식 규칙:
1. 상황과 문맥에 맞는 대답을 해줘
2. 게임 목표로 갈 수 있게 유도를 해줘
3. 상황을 생생하게 묘사하고, 플레이어의 행동과 선택한 세계관에 따라 스토리를 전개시킵니다
4. 각 세계관의 분위기에 맞는 몰입감 있는 롤플레잉을 제공합니다
5. 현재 상황을 기억하고 일관성 있게 반응합니다
[... additional rules ...]
```

## 8. API Structure

### 8.1 Endpoint Documentation

| Endpoint | Method | Purpose | Request/Response |
|----------|--------|---------|------------------|
| `/chat` | POST | Main chat interface | `ChatRequest` → `ChatResponse` |
| `/upload` | POST | Document upload | `FormData` → Success message |
| `/health` | GET | Health check | Status response |
| `/rescan` | POST | Re-scan documents | Success message |

### 8.2 Request/Response Models

```python
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    sources: list = []
```

### 8.3 Error Handling

- **HTTP 500**: Internal server errors with detailed messages
- **Connection timeouts**: Graceful fallback in UI
- **File processing errors**: Logged with specific file paths
- **API rate limits**: Handled by external providers

## 9. Performance Considerations

### 9.1 Optimization Strategies

**Document Processing**:
- Incremental updates via MD5 hash tracking
- Batch processing on startup
- Skip unchanged files

**Vector Operations**:
- Efficient similarity search with ChromaDB
- Normalized embeddings for better performance
- Local storage to minimize API calls

**Caching**:
- Persistent vector storage
- Session state management in Streamlit
- File hash-based change detection

### 9.2 Scalability Considerations

**Current Limitations**:
- Single-user design
- Local file storage
- Memory-bound vector operations

**Potential Improvements**:
- Multi-user support with user sessions
- Cloud storage integration
- Distributed vector database
- API rate limiting and queuing

## 10. Security and Configuration

### 10.1 Security Measures

- Environment variable management for API keys
- CORS middleware configuration
- Input validation with Pydantic models
- UTF-8 encoding enforcement

### 10.2 Configuration Flexibility

- Multiple LLM provider support (Claude/Ollama)
- Configurable embedding models
- Adjustable chunk sizes and retrieval parameters
- Environment-based model switching

## 11. Integration Points

### 11.1 External Dependencies

- **Anthropic Claude API**: Primary LLM provider
- **Ollama**: Local LLM fallback
- **HuggingFace**: Embedding model serving
- **ChromaDB**: Vector storage backend

### 11.2 Extension Opportunities

- **Database Integration**: PostgreSQL with pgvector
- **Cloud Deployment**: Docker containerization
- **Multi-modal Support**: Image and audio processing
- **Advanced RAG**: Query routing and ensemble methods
- **Real-time Collaboration**: WebSocket integration

## Conclusion

DungeonTalk MVP represents a well-architected RAG system specifically tailored for TRPG applications. The system demonstrates strong separation of concerns, efficient document processing, and user-friendly interfaces. The modular design allows for easy extension and customization while maintaining robust performance for its target use case.

The choice of technologies (FastAPI, Streamlit, LangChain, ChromaDB) creates a modern, maintainable system that can serve as a solid foundation for more advanced TRPG AI assistant applications.
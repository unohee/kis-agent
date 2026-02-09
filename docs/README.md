# PyKIS 문서화

PyKIS 한국투자증권 OpenAPI Python SDK 문서화 디렉토리입니다.

## 📁 문서 구조

```
docs/
├── README.md                           # 이 파일
├── architecture/                       # 아키텍처 문서
│   └── websocket-architecture.md      # 웹소켓 아키텍처 설계
├── api/                               # API 문서
│   └── websocket-api.md              # 웹소켓 API 레퍼런스
└── guides/                           # 사용 가이드
    ├── getting-started.md            # 시작 가이드
    └── examples/                     # 예제 코드
```

##  문서 목록

### 🏗️ 아키텍처 문서
- **[웹소켓 아키텍처](architecture/websocket-architecture.md)**: 다중 구독 웹소켓 시스템의 전체 아키텍처 설계

###  API 레퍼런스
- **[웹소켓 API](api/websocket-api.md)**: WSAgent 및 EnhancedWebSocketClient API 완전 참조

###  사용 가이드
- **[시작하기](guides/getting-started.md)**: PyKIS 설치 및 기본 사용법
- **[예제 코드](../examples/)**: 실전 사용 예제 모음

##  문서 업데이트

모든 문서는 코드 변경 시 자동으로 업데이트됩니다:

1. **API 문서**: docstring에서 자동 생성
2. **아키텍처 문서**: 주요 설계 변경 시 수동 업데이트  
3. **예제 코드**: 기능 추가/변경 시 업데이트

##  문서 작성 규칙

- **언어**: 한국어 우선, 기술 용어는 영어 병기
- **형식**: Markdown 표준 준수
- **구조**: 일관된 헤더 구조 사용
- **예제**: 실행 가능한 코드 예제 포함

##  외부 링크

- [한국투자증권 OpenAPI 공식 문서](https://apiportal.koreainvestment.com/)
- [PyKIS GitHub 저장소](https://github.com/your-repo/pykis)
- [이슈 트래커](https://github.com/your-repo/pykis/issues)
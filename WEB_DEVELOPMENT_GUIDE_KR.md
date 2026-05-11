# 웹 개발 가이드

## 1. 목적

이 문서는 현재 구현된 멀티 에이전트 기반 논문형 보고서 자동생성 시스템을 웹 서비스 형태로 확장하기 위한 개발 가이드이다.

현재 시스템은 다음 흐름을 기준으로 동작한다.

- Search Agent: 논문 검색 및 메타데이터 수집
- Reader Agent: 논문 요약
- Relevance Agent: 관련성 점수 계산 및 선별
- Writer Agent: 한국어 논문형 보고서 초안 생성

웹 버전의 목표는 위 파이프라인을 사용자가 브라우저에서 쉽게 실행하고 결과를 확인할 수 있도록 만드는 것이다.

---

## 2. 웹 버전 목표

웹에서 제공해야 할 핵심 기능은 아래와 같다.

- 사용자가 연구 주제를 입력할 수 있어야 한다.
- Search -> Reader -> Relevance -> Writer 파이프라인을 웹에서 실행할 수 있어야 한다.
- 각 단계의 진행 상태를 화면에서 확인할 수 있어야 한다.
- 검색된 논문 목록, 요약 결과, 관련성 점수, 최종 보고서 초안을 웹에서 볼 수 있어야 한다.
- 생성된 보고서를 다운로드하거나 저장된 결과를 다시 확인할 수 있어야 한다.

추후 확장 기능은 아래와 같다.

- Visualization Agent 결과 표시
- Review Agent 검토 결과 표시
- DOCX 다운로드
- 이전 실행 이력 조회

---

## 3. 권장 아키텍처

현재 Python 기반 에이전트 구조를 유지하는 것이 가장 효율적이다.

권장 구조:

- Frontend: React
- Backend API: FastAPI
- Agent 실행: 기존 Python 모듈 재사용
- 저장소: 로컬 JSON / 파일 시스템

이 구성이 좋은 이유:

- 현재 에이전트가 Python으로 구현되어 있어 재사용이 쉽다.
- FastAPI는 비동기 처리와 API 문서화가 편하다.
- React는 단계별 진행 화면, 결과 테이블, 보고서 뷰어를 만들기 좋다.

---

## 4. 권장 폴더 구조

```text
TeamProject2026/
├─ agents/
├─ services/
├─ data/
├─ outputs/
├─ web/
│  ├─ frontend/
│  └─ backend/
├─ run_pipeline.py
└─ WEB_DEVELOPMENT_GUIDE_KR.md
```

### backend 권장 구조

```text
web/backend/
├─ main.py
├─ routers/
│  ├─ pipeline.py
│  ├─ reports.py
│  └─ papers.py
├─ schemas/
│  ├─ request.py
│  └─ response.py
└─ services/
   └─ pipeline_service.py
```

### frontend 권장 구조

```text
web/frontend/
├─ src/
│  ├─ pages/
│  ├─ components/
│  ├─ api/
│  ├─ hooks/
│  └─ styles/
└─ package.json
```

---

## 5. 화면 설계

최소 MVP 기준으로 아래 4개 화면이면 충분하다.

### 5.1 메인 실행 화면

역할:

- 주제 입력
- 파이프라인 실행 버튼
- 현재 단계 표시

구성 예시:

- 입력창: 연구 주제
- 버튼: 보고서 생성
- 진행 상태:
  - Search 진행 중
  - Reader 진행 중
  - Relevance 진행 중
  - Writer 진행 중

### 5.2 논문 결과 화면

역할:

- Search 결과 및 Relevance 결과 확인

구성 예시:

- 논문 제목
- 저자
- 연도
- 출처
- 관련성 점수
- 선정 여부

### 5.3 보고서 초안 화면

역할:

- Writer Agent가 생성한 한국어 보고서 초안 표시

구성 예시:

- Markdown 렌더링
- 섹션별 스크롤 이동
- 저장 파일 경로 또는 다운로드 버튼

### 5.4 실행 이력 화면

역할:

- 이전에 생성한 보고서 목록 조회

구성 예시:

- 주제
- 생성 시각
- 저장 파일명
- 다시 보기 버튼

---

## 6. 백엔드 API 설계

### 6.1 파이프라인 실행 API

`POST /api/pipeline/run`

요청 예시:

```json
{
  "topic": "AI code review"
}
```

응답 예시:

```json
{
  "message": "Pipeline started",
  "topic": "AI code review"
}
```

### 6.2 파이프라인 결과 조회 API

`GET /api/pipeline/result`

응답 예시:

```json
{
  "topic": "AI code review",
  "search_count": 20,
  "summary_count": 20,
  "relevance_count": 8,
  "report_path": "outputs/reports/ai_code_review_20260511_130108.md"
}
```

### 6.3 검색 논문 목록 조회 API

`GET /api/papers/search-results`

### 6.4 관련성 결과 조회 API

`GET /api/papers/relevance-results`

### 6.5 보고서 초안 조회 API

`GET /api/reports/latest`

응답 예시:

```json
{
  "title": "AI 코드 리뷰에 관한 연구 동향 분석",
  "content": "보고서 본문...",
  "path": "outputs/reports/ai_code_review_20260511_130108.md"
}
```

---

## 7. 백엔드 구현 원칙

### 7.1 기존 로직 재사용

웹 백엔드는 새로 Agent를 다시 만들지 말고, 기존 함수를 불러서 사용해야 한다.

예:

- `run_search(topic)`
- `run_reader()`
- `run_relevance(topic)`
- `run_writer_draft_generation(topic=topic)`

### 7.2 비즈니스 로직 분리

라우터에서 직접 Agent를 호출하지 말고 서비스 계층을 둔다.

예:

- `routers/pipeline.py`: 요청/응답만 담당
- `services/pipeline_service.py`: 실제 실행 담당

### 7.3 파일 기반 결과 재사용

현재 구조는 JSON과 Markdown 파일을 저장하므로, 웹에서도 이를 그대로 읽어 결과를 내려주는 방식이 가장 빠르다.

---

## 8. 프론트엔드 구현 원칙

### 8.1 단계별 흐름이 보여야 함

이 프로젝트의 핵심은 멀티 에이전트 파이프라인이므로, 사용자는 단순히 최종 결과만 보는 것이 아니라 중간 단계도 확인할 수 있어야 한다.

보여줄 것:

- 현재 실행 단계
- 검색 결과 수
- 요약 완료 수
- 선별 논문 수
- 초안 생성 여부

### 8.2 결과를 한 화면에 몰아넣지 않기

추천 흐름:

- 상단: 주제 입력 + 실행 버튼
- 중간: 파이프라인 상태
- 하단 탭:
  - 검색 결과
  - 관련성 결과
  - 보고서 초안

### 8.3 보고서 화면은 읽기 쉽게 구성

추천:

- Markdown 렌더링 사용
- 본문 폭 제한
- 섹션 앵커 메뉴
- 저장 경로 또는 다운로드 버튼 제공

---

## 9. MVP 개발 순서

웹은 처음부터 모든 기능을 넣기보다 최소 동작 버전부터 만드는 것이 좋다.

### 1단계

- FastAPI 서버 생성
- React 프로젝트 생성
- 주제 입력 화면 생성

### 2단계

- `POST /api/pipeline/run` 구현
- 프론트에서 버튼 클릭 시 파이프라인 실행

### 3단계

- 검색 결과 / 관련성 결과 / 보고서 초안 조회 API 구현
- 프론트에서 결과 표시

### 4단계

- 진행 상태 UI 추가
- 에러 메시지 처리

### 5단계

- 보고서 다운로드
- 실행 이력 화면

---

## 10. 추천 UI 흐름

### 메인 문구 예시

`영문 논문을 분석해 한국어 논문형 보고서를 자동 생성합니다.`

### 입력 예시

- 주제 입력: `AI code review`

### 실행 후 표시 예시

- Search 완료: 20편 수집
- Reader 완료: 20편 요약
- Relevance 완료: 8편 선별
- Writer 완료: 보고서 초안 생성

---

## 11. 주의할 점

### 11.1 API 호출 시간

Search, Reader, Writer는 외부 API와 LLM 호출이 포함되어 있어 시간이 걸릴 수 있다.

따라서 웹에서는 아래 중 하나가 필요하다.

- 로딩 상태 표시
- 단계별 진행 메시지
- 비동기 작업 처리

### 11.2 실패 시 중단 처리

이미 `run_pipeline.py`에는 결과가 없을 때 다음 단계로 넘어가지 않는 로직이 들어가 있다.

웹에서도 이를 그대로 사용자에게 보여줘야 한다.

예:

- 검색 결과 없음
- Reader 요약 실패
- Writer 초안 생성 실패

### 11.3 인코딩

한글 결과를 다루므로 UTF-8 고정을 유지해야 한다.

### 11.4 긴 보고서 처리

초안 길이가 길어질 수 있으므로 프론트에서는 스크롤 가능한 보고서 뷰어가 필요하다.

---

## 12. 현재 구현과 웹 연결 포인트

현재 바로 연결 가능한 핵심 함수:

- `services.search_service.run_search(topic)`
- `agents.reader_agent.run_reader()`
- `agents.relevance_agent.run_relevance(topic)`
- `agents.write_agent.run_writer_draft_generation(topic=topic)`
- `agents.write_agent.run_writer_output_test(draft, topic=topic)`

즉 웹 백엔드는 위 함수들을 조합해 API로 감싸면 된다.

---

## 13. 권장 1차 목표

웹 1차 버전에서는 아래까지만 구현해도 충분하다.

- 주제 입력
- 파이프라인 실행
- 검색 결과 표 출력
- 관련성 결과 표 출력
- 보고서 초안 출력
- Markdown 파일 저장 결과 표시

이후 2차 확장:

- Visualization Agent 연결
- Review Agent 연결
- DOCX 다운로드
- 실행 이력 관리

---

## 14. 결론

현재 프로젝트는 Search, Reader, Relevance, Writer까지 핵심 파이프라인이 이미 갖춰져 있으므로, 웹 개발은 기존 Python 로직을 API로 감싸고 React 화면을 붙이는 방식으로 진행하는 것이 가장 효율적이다.

즉 웹 개발의 핵심은 새로운 AI 로직을 만드는 것이 아니라, 이미 구현된 멀티 에이전트 흐름을 사용자가 쉽게 실행하고 확인할 수 있도록 인터페이스를 제공하는 것이다.

# Google Gemini 3.8 / 3.7 Flash 웹 챗봇 서비스 (GCP Compute Engine 연동 가능)

Google Gemini 공식 웹([gemini.google.com/app](https://gemini.google.com/app?hl=ko))의 깔끔하고 미려한 디자인("언제든지 시작하세요", 부드러운 스카이블루 그라디언트, 플로팅 캡슐 프롬프트 바)을 그대로 재현한 로컬 웹 기반 AI 챗봇 서비스입니다.

최신 **Gemini 3.8 Flash**(기본값) 및 **Gemini 3.7 Flash** 모델을 자유롭게 선택하여 대화할 수 있으며, Server-Sent Events(SSE) 기반의 고속 실시간 토큰 스트리밍을 지원합니다.

---

## 주요 기능 및 특징

1. **공식 Gemini 스타일 UI/UX 정밀 구현**:
   - 몽환적이고 부드러운 스카이블루 파스텔 배경 및 미니멀한 타이포그래피.
   - 대기 상태의 중앙 환영 문구 **"언제든지 시작하세요"**.
   - 마이크, 모델 변경, 액션 메뉴가 통합된 화이트 캡슐형 플로팅 프롬프트 바.
   - 대화 시작 시 부드러운 화면 전환 및 하단 고정 프롬프트 바.
2. **Google 실시간 웹 검색(Search Grounding) 지원**:
   - Google 공식 실시간 웹 검색 연동(`tools: [{"googleSearch": {}}]`).
   - 최신 뉴스, 실시간 날씨, 주가, 최근 이벤트 등 모델 학습 시점 이후의 최신 정보를 정확하게 검색하여 답변.
   - 프롬프트 바 우측 **웹 검색 토글 버튼(`travel_explore`)**으로 검색 기능을 언제든 켜고 끌 수 있음.
   - 답변 생성 시 검색에 활용된 **검색 쿼리 배지** 및 클릭 가능한 **참고 출처(URL) 카드** 제공.
3. **AI 모델 다중 선택 지원**:
   - **Gemini 3.8 Flash (기본값)**: 한층 더 빠르고 강력한 최신 추론 성능.
   - **Gemini 3.7 Flash**: 검증된 고성능 및 안정적인 멀티턴 응답.
   - 입력창 우측 모델 알약(Pill) 또는 상단 헤더에서 원클릭으로 손쉽게 전환.
4. **실시간 SSE 스트리밍**:
   - Google Generative Language API의 `streamGenerateContent` 엔드포인트를 FastAPI를 통해 SSE로 중계하여 타자 치듯 빠른 실시간 답변 출력.
5. **리치 콘텐츠 렌더링**:
   - 마크다운(표, 리스트, 볼드, 링크) 완벽 지원.
   - 프로그래밍 코드 문법 강조(Syntax Highlighting) 및 원클릭 코드 복사 버튼.
6. **음성 입력(STT) 지원**:
   - Web Speech API 기반 마이크 버튼을 통해 한국어/영어 음성으로 간편하게 질문 입력 가능.
7. **대화 관리**:
   - 브라우저 로컬 저장소(localStorage) 기반 대화 세션 자동 저장 및 사이드바에서 이전 대화 열람/삭제.

---

## 프로젝트 구조

```
gcp-compute-engine-chatbot/
├── app/
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css       # Gemini 테마 및 반응형 디자인 시스템
│   │   ├── js/
│   │   │   └── app.js         # 스트리밍, 모델 전환, 음성인식, 마크다운 처리
│   │   └── index.html         # 메인 웹 페이지
│   ├── __init__.py
│   ├── config.py              # 환경변수(GEMINI_API_KEY) 로드 및 모델 정의
│   └── gemini_client.py       # 비동기 Gemini API 스트리밍 클라이언트
├── main.py                    # FastAPI 웹 서버 및 REST/SSE 엔드포인트
├── requirements.txt           # 의존성 패키지 목록
├── run.bat                    # 윈도우 원클릭 실행 스크립트
├── .env.example               # 환경변수 템플릿
└── README.md                  # 프로젝트 설명서
```

---

## 로컬 환경 실행 방법

### 1. 사전 요구 사항
- **Python 3.10 이상** (Windows / macOS / Linux)
- **Gemini API Key**: 환경변수 `GEMINI_API_KEY`에 등록되어 있어야 합니다.

### 2. 환경변수 확인 및 설정
현재 로컬 PC의 환경변수에 이미 등록되어 있다면 별도 설정이 필요 없으며, 필요 시 프로젝트 루트에 `.env` 파일을 생성하여 지정할 수 있습니다:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
PORT=8000
```

### 3. 원클릭 실행 (Windows)
프로젝트 폴더의 `run.bat` 파일을 더블클릭하면 의존성을 확인하고 자동으로 브라우저(`http://localhost:8000`)를 엽니다.

### 4. 수동 터미널 실행
```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 서버 실행
python main.py
```
실행 후 웹 브라우저에서 `http://localhost:8000` 으로 접속합니다.

---

## 구글 클라우드 (GCP) Compute Engine 배포 가이드

본 서비스는 가볍고 독립적인 구조로 되어 있어 GCP Compute Engine VM 인스턴스에 손쉽게 배포할 수 있습니다.

### 1. Compute Engine VM 생성
- 머신 유형: `e2-micro` 또는 `e2-small` (충분함)
- OS: Ubuntu 22.04 LTS / 24.04 LTS
- 방화벽: **HTTP 트래픽 허용(80)** 및 **HTTPS 트래픽 허용(443)** 체크

### 2. VM 인스턴스 설정 및 코드 배포
SSH를 통해 VM에 접속한 후 다음을 실행합니다:

```bash
# 패키지 업데이트 및 Python 설치
sudo apt update && sudo apt install -y python3-pip python3-venv git

# 저장소 복제 (또는 코드 업로드)
git clone <저장소_URL>
cd gcp-compute-engine-chatbot

# 가상환경 생성 및 패키지 설치
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 환경변수 설정 (.env 파일 생성)
echo "GEMINI_API_KEY=your_actual_api_key" > .env
echo "PORT=80" >> .env
```

### 3. systemd를 통한 백그라운드 상시 서비스 등록
VM이 재부팅되더라도 자동으로 서버가 실행되도록 등록합니다:

```bash
sudo bash -c 'cat <<EOF > /etc/systemd/system/gemini-chatbot.service
[Unit]
Description=Gemini Web Chatbot Service
After=network.target

[Service]
User=root
WorkingDirectory=/home/ubuntu/gcp-compute-engine-chatbot
EnvironmentFile=/home/ubuntu/gcp-compute-engine-chatbot/.env
ExecStart=/home/ubuntu/gcp-compute-engine-chatbot/venv/bin/uvicorn main:app --host 0.0.0.0 --port 80
Restart=always

[Install]
WantedBy=multi-user.target
EOF'

# 서비스 시작 및 자동 등록
sudo systemctl daemon-reload
sudo systemctl enable --now gemini-chatbot.service
sudo systemctl status gemini-chatbot.service
```

서비스가 시작되면 브라우저에서 Compute Engine VM의 **외부 IP(External IP)**로 접속하여 챗봇을 즉시 사용할 수 있습니다.

# Google Cloud Run 챗봇 (ADC 인증 모드)

Google Cloud의 공식 권장 인증 방식인 **애플리케이션 기본 사용자 인증 정보(ADC, Application Default Credentials)**를 적용한 Gemini 웹 챗봇 서비스 패키지입니다.

---

## 🛡️ 왜 API Key 대신 ADC(애플리케이션 기본 사용자 인증 정보)인가요?

[`capture.png`](../capture.png)의 Google Agent Platform 공식 가이드에 명시된 바와 같이, 엔터프라이즈 및 클라우드 환경에서는 API 키를 수동으로 생성하여 관리하는 대신 **ADC 방식을 적극 권장**합니다.

| 비교 항목 | 기존 `cloud_run` (API Key 방식) | 신규 `cloud_run2` (ADC 방식) |
| :--- | :--- | :--- |
| **인증 수단** | 정적 문자열 API 키 (`AIzaSy...`) | **IAM 서비스 계정 OAuth2 Bearer 토큰** |
| **비밀 키 관리** | Secret Manager에 키를 등록/매핑 필요 | **Secret 키 발급/보관 자체가 불필요 (No Secret)** |
| **키 유출 위험** | 소스코드/깃허브에 키 노출 시 심각한 보안 사고 | **외부 유출될 비밀 키 자체가 존재하지 않음** |
| **토큰 수명** | 영구적 (키 폐기 전까지 유효) | **1시간 주기 자동 만료 및 실시간 자동 갱신** |
| **호출 대상 API** | Google AI Studio Developer API | **Google Cloud Model API (Vertex AI)** |
| **권한 통제** | 키 보유자 누구나 호출 가능 | **GCP IAM 역할(`roles/aiplatform.user`)로 정밀 통제** |

---

## 📁 디렉토리 구성

```
cloud_run2/
├── app/
│   ├── static/                  # 반응형 웹 챗봇 UI (HTML, CSS, JS, SVG)
│   ├── __init__.py
│   ├── config.py                # ADC 토큰 획득 및 자동 갱신 (google.auth.default)
│   └── gemini_client.py         # Google Cloud Model API (Vertex AI) SSE 스트리밍
├── main.py                      # FastAPI 웹 서버 (포트 8080 & ADC 상태 헬스체크)
├── requirements.txt             # 경량 서버리스 의존성 패키지 (Secret Manager 불필요)
├── Dockerfile                   # Cloud Run 컨테이너 빌드 정의 (python:3.11-slim)
├── .dockerignore                # 빌드 제외 파일
├── deploy.sh                    # Secret 옵션이 필요 없는 순수 IAM 배포 스크립트
├── run.bat                      # 로컬 PC ADC 테스트 실행 스크립트 (포트 8080)
└── README.md                    # 본 안내서
```

---

## 🚀 배포 방법

### 방법 1. gcloud CLI 원클릭 배포 (가장 권장)

Secret Manager 매핑 옵션(`--set-secrets`) 없이 순수 IAM 권한으로 배포됩니다:

```bash
cd cloud_run2
chmod +x deploy.sh
./deploy.sh
```

또는 직접 명령어로 배포:
```bash
gcloud run deploy gemini-chatbot-adc \
    --source . \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --min-instances 0 \
    --max-instances 3
```

---

### 방법 2. 사전 IAM 권한 설정 (최초 1회)

Cloud Run의 컴퓨트 서비스 계정에 Vertex AI 사용 권한을 부여합니다:

```bash
# 서비스 계정 형식: [PROJECT_NUMBER]-compute@developer.gserviceaccount.com
gcloud projects add-iam-policy-binding <YOUR_PROJECT_ID> \
    --member="serviceAccount:<YOUR_PROJECT_NUMBER>-compute@developer.gserviceaccount.com" \
    --role="roles/aiplatform.user"
```

---

## 💻 로컬 PC 테스트 실행

로컬 환경에서도 `gcloud` ADC 로그인을 통해 동일한 방식으로 테스트할 수 있습니다:

```bash
# 1. 로컬 개발자 머신에 ADC 자격증명 등록 (최초 1회)
gcloud auth application-default login

# 2. 로컬 서버 실행
cd cloud_run2
run.bat
```
브라우저에서 `http://localhost:8080`으로 접속하면 API 키 없이 로컬 머신의 Google 계정 권한으로 Gemini 모델과 대화할 수 있습니다.

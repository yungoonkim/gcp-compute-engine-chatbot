# GCP 콘솔(브라우저)에서 Cloud Run으로 챗봇 배포하기 가이드

이 문서는 별도의 복잡한 CLI나 터미널 명령어 없이, **웹 브라우저로 Google Cloud Console(GCP 웹사이트)에 접속하여 클릭 몇 번으로 챗봇을 Cloud Run에 배포하고 Secret Manager를 연동하는 전체 과정**을 단계별로 설명합니다.

---

## 💡 왜 Compute Engine(VM) 대신 Cloud Run인가요?

| 구분 | Compute Engine (기존 VM) | Cloud Run (서버리스) |
| :--- | :--- | :--- |
| **비용 구조** | 사용 여부와 무관하게 24시간 내내 과금 (월 약 $25~) | **사용자가 접속할 때만 초 단위 과금 (트래픽 없으면 $0)** |
| **무료 할당량** | 상시 무료 VM 스펙 제한적 | **매월 200만 건 호출 무료, 36만 GB-초 무료** |
| **SSL/HTTPS** | Let's Encrypt 및 Nginx 직접 설정 필요 | **구글 관리형 HTTPS 인증서 및 도메인 자동 제공** |
| **Secret 연동** | 스크립트 작성 및 IAM 권한 수동 부여 필요 | **콘솔 화면에서 드롭다운 클릭으로 바로 환경변수 매핑** |
| **서버 관리** | OS 패치, 보안 업데이트, 재부팅 관리 필요 | **완전 관리형(Serverless)으로 인프라 관리 불필요** |

---

## [1단계] GCP 콘솔 접속 및 프로젝트 선택

1. 웹 브라우저를 열고 **[Google Cloud Console](https://console.cloud.google.com/)**에 로그인합니다.
2. 화면 최상단 바에서 **프로젝트 선택 드롭다운**을 클릭합니다.
3. 현재 사용 중인 프로젝트인 **`iceu-songpa11`** (프로젝트 번호: `976675812314`)을 선택합니다.

---

## [2단계] Secret Manager(보안 비밀) 확인 및 권한 점검

Secret Manager에 저장된 `GEMINI_API_KEY`를 Cloud Run이 읽을 수 있도록 브라우저에서 확인합니다.

1. 콘솔 상단 검색창에 **`Secret Manager`**를 검색하여 클릭하거나, 좌측 메뉴(`☰`)에서 **[보안] > [Secret Manager]**로 이동합니다.
2. 목록에 **`GEMINI_API_KEY`**가 있는지 확인하고 클릭합니다.
3. **[권한(Permissions)]** 탭을 클릭합니다.
4. 상단의 **[+액세스 권한 부여(Grant Access)]** 버튼을 누릅니다:
   - **새 주 구성원(New principals)**:
     - Cloud Run이 기본으로 사용하는 컴퓨팅 서비스 계정을 입력합니다:
       `976675812314-compute@developer.gserviceaccount.com`
   - **역할(Role)**:
     - `Secret Manager 보안 비밀 접근자` (영문: `Secret Manager Secret Accessor`) 선택
   - **[저장(Save)]** 버튼을 클릭합니다.
   *(※ 이미 이전 작업에서 권한이 등록되어 있다면 건너뛰셔도 됩니다.)*

---

## [3단계] Cloud Run 서비스 생성 시작

1. 콘솔 상단 검색창에 **`Cloud Run`**을 검색하여 클릭하거나, 좌측 메뉴(`☰`)에서 **[Serverless] > [Cloud Run]**으로 이동합니다.
2. 상단의 **[+ 서비스 만들기 (Create Service)]** 버튼을 클릭합니다.

---

## [4단계] 배포 소스 설정 (GitHub 저장소 연동)

Cloud Run은 GitHub 저장소를 직접 연결하여 소스 코드가 업데이트될 때마다 자동으로 빌드/배포할 수 있습니다.

1. **배포 방식 선택**:
   - **`소스 리포지토리에서 지속적으로 새 버전 배포 (Continuously deploy from a repository)`** 라디오 버튼을 선택합니다.
2. **[CLOUD BUILD 설정 (SET UP CLOUD BUILD)]** 버튼을 클릭합니다:
   - **저장소 제공업체(Repository Provider)**: `GitHub` 선택
   - GitHub 계정 연동 팝업이 뜨면 로그인 및 권한 승인 진행
   - **저장소(Repository)**: `yungoonkim/gcp-compute-engine-chatbot` 선택
   - **[다음(Next)]** 클릭
3. **빌드 구성(Build Configuration)**:
   - **분기(Branch)**: `^main$` (기본값)
   - **빌드 유형(Build Type)**:
     - **Google Cloud Buildpack** 선택 (Dockerfile 없이도 파이썬 앱을 구글이 자동으로 컨테이너화)
     - 진입점(Entrypoint): 비워두거나 필요 시 `uvicorn main:app --host 0.0.0.0 --port 8080` 지정
   - **[저장(Save)]** 클릭

> 💡 **대안 (가장 빠른 단 한 줄 배포 방법 - Cloud Shell 이용 시)**:
> 복잡한 GitHub 연동 승인 창을 거치지 않고 싶다면, 콘솔 우측 상단의 **Cloud Shell(터미널 아이콘 `>_`)**을 열고 아래 명령어만 복사해서 붙여넣으면 즉시 배포됩니다:
> ```bash
> cd ~/gcp-compute-engine-chatbot
> gcloud run deploy chatbot-service --source . --region us-central1 --allow-unauthenticated --set-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest
> ```

---

## [5단계] Cloud Run 서비스 기본 설정

1. **서비스 이름 (Service name)**:
   - 예: `gemini-chatbot` (원하는 이름 입력)
2. **리전 (Region)**:
   - 한국 사용자와의 빠른 응답 속도를 원할 경우: `asia-northeast3 (Seoul)`
   - 비용 최저가를 유지하고 싶을 경우: `us-central1 (Iowa)`
3. **CPU 할당 및 가격 책정 (CPU allocation and pricing)**:
   - **`요청이 처리되는 동안에만 CPU 할당 (CPU is only allocated during request processing)`** 선택 *(비용 절감을 위한 핵심 옵션!)*
4. **인스턴스 자동 확장 (Autoscaling)**:
   - **최소 인스턴스 수 (Min instances)**: `0` *(사용자가 없을 때 0대로 줄어들어 요금이 전혀 청구되지 않음)*
   - **최대 인스턴스 수 (Max instances)**: `3` 또는 `5` (실습용으로 적당)
5. **수신 (Ingress) 제어**:
   - **`모두(All)`** 선택 (외부 인터넷에서 브라우저로 접속 허용)
6. **인증 (Authentication)**:
   - **`미인증 호출 허용 (Allow unauthenticated invocations)`** 체크 *(일반 사용자가 웹 브라우저로 챗봇에 접속해야 하므로 필수)*

---

## [6단계] Secret Manager 키를 환경변수로 연결 (핵심!)

이 단계가 Cloud Run 콘솔 UI의 가장 강력한 기능입니다. 코드나 스크립트 작성 없이 브라우저에서 Secret Manager 키를 바로 챗봇에 전달할 수 있습니다.

1. 화면 하단의 **[컨테이너, 볼륨, 네트워킹, 보안 (Containers, Volumes, Networking, Security)]** 드롭다운 메뉴를 클릭하여 펼칩니다.
2. **[변수 및 보안 비밀 (Variables & Secrets)]** 탭을 클릭합니다.
3. **[+ 보안 비밀 참조 추가 (Reference a secret)]** 버튼을 클릭합니다:
   - **이름 (Name)**: `GEMINI_API_KEY` (애플리케이션이 읽을 환경변수 이름)
   - **보안 비밀 (Secret)**: 드롭다운에서 `GEMINI_API_KEY` 선택
   - **참조 버전 (Reference version)**: `최신(latest)` 선택
4. (선택 사항) 서비스 실행 포트 지정:
   - Cloud Run의 기본 포트는 `8080`입니다.
   - [컨테이너(Container)] 탭에서 **컨테이너 포트(Container port)**가 `8080` 또는 `8000`으로 일치하는지 확인합니다. (FastAPI 앱의 `PORT` 환경변수를 읽도록 구현되어 있으므로 Cloud Run의 8080에 자동 맞춰집니다.)

---

## [7단계] 배포 실행 및 접속 확인

1. 페이지 맨 아래에 있는 파란색 **[만들기 (Create)]** 버튼을 클릭합니다.
2. 약 1~2분 정도 Cloud Build가 컨테이너를 빌드하고 Cloud Run에 배포하는 과정이 진행됩니다.
3. 배포가 완료되면 화면 상단에 초록색 체크(`✔`) 표시와 함께 **서비스 URL**이 생성됩니다:
   - 예시 URL: `https://gemini-chatbot-xxxxxxxxxx-an.a.run.app`
4. 생성된 **URL을 클릭**하면 구글이 자동으로 발급한 **보안 HTTPS 연결**을 통해 챗봇 UI가 브라우저에 바로 나타납니다!

---

## [8단계] 동작 검증

1. **상태 배지 확인**:
   - 화면 좌측 상단 또는 헬스체크 배지에 **"Gemini 3.8 Flash 준비 완료 / 온라인"** 상태가 뜨는지 확인합니다.
2. **대화 테스트**:
   - 입력창에 `"안녕하세요! Cloud Run에서 잘 동작하나요?"`를 입력하고 전송합니다.
   - Secret Manager의 `GEMINI_API_KEY`를 통해 실시간 AI 답변이 타이핑 스트리밍되는지 확인합니다.

---

## [9단계] 기존 Compute Engine VM 정리 (중복 과금 방지)

Cloud Run 배포가 완료되었다면, 계속 켜두면 매월 약 $25씩 청구되는 기존 Compute Engine VM 인스턴스를 삭제하여 불필요한 비용을 막을 수 있습니다.

1. 콘솔 좌측 메뉴(`☰`) > **[Compute Engine] > [VM 인스턴스]**로 이동합니다.
2. 이전에 만든 `chatbot-instance` 체크박스를 선택합니다.
3. 상단의 **[삭제(Delete)]** 아이콘(휴지통 모양)을 클릭하여 인스턴스를 정리합니다.
4. Cloud Run은 사용하지 않을 때는 인스턴스 수가 0으로 유지되므로, 유지 비용 부담 없이 영구적으로 챗봇 URL을 보관하실 수 있습니다!

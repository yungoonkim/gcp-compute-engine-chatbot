# GCP Compute Engine 챗봇 배포 작업 로그 (Deployment Log)

- **생성 일시**: 2026-09-15 15:05:30 (KST)
- **대상 프로젝트**: `iceu-songpa11` (Project Number: `976675812314`)
- **인스턴스 명**: `chatbot-instance`
- **리전 / 영역**: `us-central1` / `us-central1-a` (글로벌 최저가 리전)
- **외부 IP**: `34.63.148.160`
- **서비스 접속 URL**: 
  - `http://34.63.148.160` (기본 80 포트)
  - `http://34.63.148.160:8000` (FastAPI 앱 포트)

---

## 1. 배포 작업 요약

| 작업 항목 | 상태 | 주요 내용 |
| :--- | :---: | :--- |
| **Secret Manager IAM 권한 부여** | ✅ 완료 | Compute 기본 서비스 계정에 `roles/secretmanager.secretAccessor` 부여 |
| **방화벽 규칙 생성** | ✅ 완료 | `default-allow-chatbot` (TCP 80, 8000 포트 인바운드 허용) |
| **애플리케이션 코드 수정 및 푸시** | ✅ 완료 | Secret Manager 조회 로직 추가 및 `origin main` 동기화 |
| **Compute Engine VM 인스턴스 생성** | ✅ 완료 | `e2-medium`, 10GB `pd-balanced`, Debian 13, `cloud-platform` scope |
| **디스크 스냅샷 스케줄 정책 연결** | ✅ 완료 | `default-schedule-1` (일일 스냅샷 보관 14일) 연결 |
| **VM 내부 초기화 및 서비스 가동** | ✅ 완료 | startup-script로 venv 생성, Secret 키 취득, systemd 서비스 등록 |
| **API 및 웹 서비스 검증** | ✅ 완료 | `/api/health` 및 `/api/chat` SSE 스트리밍 정상 응답 확인 |

---

## 2. 세부 작업 실행 로그 (Chronological Log)

### [Step 1] 사전 리소스 및 Secret Manager 상태 점검
- **실행 명령**:
  ```bash
  gcloud config list
  gcloud compute instances list
  gcloud secrets describe GEMINI_API_KEY --project=iceu-songpa11
  gcloud secrets versions access latest --secret=GEMINI_API_KEY --project=iceu-songpa11
  ```
- **점검 결과**:
  - 기존 실행 중인 Compute Engine 인스턴스: 0개 (미생성 상태 확인)
  - Secret Manager: `projects/976675812314/secrets/GEMINI_API_KEY`에 유효한 Gemini API 키 등록 확인

---

### [Step 2] IAM 권한 부여 (Secret Manager Accessor)
VM 내 Compute 엔진 기본 서비스 계정(`976675812314-compute@developer.gserviceaccount.com`)이 Secret Manager의 키를 직접 조회할 수 있도록 IAM 바인딩을 추가했습니다.
- **실행 명령**:
  ```bash
  gcloud secrets add-iam-policy-binding GEMINI_API_KEY \
      --project=iceu-songpa11 \
      --member="serviceAccount:976675812314-compute@developer.gserviceaccount.com" \
      --role="roles/secretmanager.secretAccessor"
  ```
- **실행 결과**:
  ```text
  Updated IAM policy for secret [GEMINI_API_KEY].
  bindings:
  - members:
    - serviceAccount:976675812314-compute@developer.gserviceaccount.com
    role: roles/secretmanager.secretAccessor
  ```

---

### [Step 3] 인바운드 방화벽 규칙 생성 (`default-allow-chatbot`)
외부 사용자가 웹 브라우저로 챗봇에 접근할 수 있도록 포트 80 및 8000 인바운드를 허용하는 방화벽 규칙을 생성했습니다.
- **실행 명령**:
  ```bash
  gcloud compute firewall-rules create default-allow-chatbot \
      --project=iceu-songpa11 \
      --direction=INGRESS \
      --priority=1000 \
      --network=default \
      --action=ALLOW \
      --rules=tcp:80,tcp:8000 \
      --source-ranges=0.0.0.0/0 \
      --target-tags=chatbot \
      --description="Allow HTTP and Chatbot port 8000"
  ```
- **실행 결과**:
  ```text
  Created [https://www.googleapis.com/compute/v1/projects/iceu-songpa11/global/firewalls/default-allow-chatbot].
  NAME                   NETWORK  DIRECTION  PRIORITY  ALLOW            DENY  DISABLED
  default-allow-chatbot  default  INGRESS    1000      tcp:80,tcp:8000        False
  ```

---

### [Step 4] 소스코드 Secret Manager 연동 기능 구현 및 Git 동기화
1. `requirements.txt`: `google-cloud-secret-manager>=2.16.0` 추가
2. `app/config.py`:
   - 기존 OS 환경변수 및 `.env` 우선 조회
   - 미설정 시 `projects/976675812314/secrets/GEMINI_API_KEY`에서 자동으로 시크릿을 조회하여 설정하는 `_fetch_from_secret_manager()` 및 `get_gemini_api_key()` 구현
3. `main.py` 및 `app/gemini_client.py`: 동적 키 획득 함수 연동
4. Git 커밋 및 원격 저장소(`https://github.com/yungoonkim/gcp-compute-engine-chatbot.git`) 푸시 완료

---

### [Step 5] Compute Engine VM 인스턴스 생성
주피터 노트북(`compute_engine_example.ipynb`) 사양을 기반으로 최저가 리전 `us-central1-a`에 VM을 프로비저닝했습니다.
- **실행 명령**:
  ```bash
  gcloud compute instances create chatbot-instance \
      --project=iceu-songpa11 \
      --zone=us-central1-a \
      --machine-type=e2-medium \
      --network-interface=network-tier=PREMIUM,stack-type=IPV4_ONLY,subnet=default \
      --metadata=enable-osconfig=TRUE \
      --metadata-from-file=startup-script=startup-script.sh \
      --tags=chatbot,http-server \
      --maintenance-policy=MIGRATE \
      --provisioning-model=STANDARD \
      --service-account=976675812314-compute@developer.gserviceaccount.com \
      --scopes=https://www.googleapis.com/auth/cloud-platform \
      --create-disk=auto-delete=yes,boot=yes,device-name=chatbot-instance,image=projects/debian-cloud/global/images/debian-13-trixie-v20260908,mode=rw,size=10,type=pd-balanced \
      --no-shielded-secure-boot \
      --shielded-vtpm \
      --shielded-integrity-monitoring \
      --labels=goog-ops-agent-policy=v2-template-1-7-0,goog-ec-src=vm_add-gcloud \
      --reservation-affinity=any
  ```
- **실행 결과**:
  ```text
  NAME              ZONE           MACHINE_TYPE  PREEMPTIBLE  INTERNAL_IP  EXTERNAL_IP    STATUS
  chatbot-instance  us-central1-a  e2-medium                  10.128.0.6   34.63.148.160  RUNNING
  ```

---

### [Step 6] 디스크 스냅샷 스케줄 정책 생성 및 연결
노트북 4~5단계에 명시된 백업 자동화 정책을 생성하고 부팅 디스크에 연결했습니다.
- **스케줄 정책 생성**:
  ```bash
  gcloud compute resource-policies create snapshot-schedule default-schedule-1 \
      --project=iceu-songpa11 \
      --region=us-central1 \
      --max-retention-days=14 \
      --on-source-disk-delete=keep-auto-snapshots \
      --daily-schedule \
      --start-time=23:00
  ```
- **부팅 디스크 연결**:
  ```bash
  gcloud compute disks add-resource-policies chatbot-instance \
      --project=iceu-songpa11 \
      --zone=us-central1-a \
      --resource-policies=projects/iceu-songpa11/regions/us-central1/resourcePolicies/default-schedule-1
  ```

---

### [Step 7] VM 내부 자동화 실행 내역 (Serial Port Log 발췌)
인스턴스 부팅 직후 startup-script가 자동으로 실행되어 서비스 배포를 완료했습니다.
```text
[Chatbot Startup] Starting deployment at Tue Sep 15 06:04:15 UTC 2026
[1/6] Updating system packages... (apt-get update, python3, pip, venv, git)
[2/6] Setting up project directory... Cloning https://github.com/yungoonkim/gcp-compute-engine-chatbot.git into /opt/chatbot
[3/6] Setting up Python virtual environment... Installing pip & requirements.txt
[4/6] Retrieving GEMINI_API_KEY from Secret Manager...
      Successfully retrieved GEMINI_API_KEY from Secret Manager!
      Wrote .env file with Secret Key and PORT=8000
[5/6] Creating systemd service unit... /etc/systemd/system/chatbot.service
      Started chatbot.service - Gemini Web Chatbot Service.
[6/6] Configuring port forwarding (80 -> 8000)...
[Chatbot Startup] Deployment completed successfully at Tue Sep 15 06:04:53 UTC 2026
```

---

## 3. 엔드포인트 검증 결과 (Verification Results)

### 1) 헬스체크 검증 (`GET /api/health`)
- **호출 URL**: `http://34.63.148.160/api/health` 및 `http://34.63.148.160:8000/api/health`
- **응답 HTTP 상태**: `200 OK`
- **응답 본문**:
  ```json
  {
    "status": "ok",
    "api_key_configured": true,
    "default_model": "gemini-3.8-flash"
  }
  ```
  *(Secret Manager로부터 취득된 키가 정상 로드되었음을 `api_key_configured: true`로 확인)*

### 2) 스트리밍 대화 API 검증 (`POST /api/chat`)
- **요청 메시지**: `"안녕! 너는 누구야? 짧게 한 줄로 대답해줘."`
- **응답 스트림 (SSE)**:
  ```text
  data: {"text": "안녕하세요! 저는 Google에서 개발한 대화형 "}
  data: {"text": "AI 어시스턴트 Gemini입니다."}
  data: [DONE]
  ```

### 3) 웹 인터페이스 정적 파일 제공 검증 (`GET /`)
- **응답 HTTP 상태**: `200 OK` (`text/html; charset=utf-8`, 8,874 bytes 정상 수신)

---

## 4. 인스턴스 관리 및 과금 방지 가이드

### 인스턴스 SSH 접속
```bash
gcloud compute ssh chatbot-instance --zone=us-central1-a --project=iceu-songpa11
```

### 서비스 상태 및 로그 확인 (인스턴스 내부)
```bash
sudo systemctl status chatbot.service
sudo journalctl -u chatbot.service -f
cat /var/log/chatbot-startup.log
```

### 테스트 완료 후 리소스 정리 (과금 방지)
```bash
# 1) VM 인스턴스 삭제 (부팅 디스크 함께 삭제)
gcloud compute instances delete chatbot-instance --zone=us-central1-a --project=iceu-songpa11 --quiet

# 2) 스냅샷 스케줄 정책 삭제
gcloud compute resource-policies delete default-schedule-1 --region=us-central1 --project=iceu-songpa11 --quiet

# 3) 방화벽 규칙 삭제
gcloud compute firewall-rules delete default-allow-chatbot --project=iceu-songpa11 --quiet
```

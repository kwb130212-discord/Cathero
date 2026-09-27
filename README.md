# Cathero Automation

PySide6 기반의 로컬 화면 분석/자동화 대시보드입니다.

## Architecture

```
MSS Capture
    │
    ├── OpenCV Template Matching ──> Detection
    │                                  │
    └── Local VLM (optional) ───────> State/Event
                                       │
                                  VisionWorker
                                       │
                         ┌─────────────┴─────────────┐
                         │                           │
                    Dashboard                  Action Rules
                         │                           │
                    Metrics/Log                 pyautogui
                                                     │
                                              Discord/Telegram
```

## Directory

```
Cathero/
├─ main.py
├─ requirements.txt
├─ .env.example
├─ config/
│  ├─ settings.py
│  ├─ actions.py
│  └─ actions.json
├─ core/
│  └─ engine.py
├─ vision/
│  ├─ capture.py
│  └─ analyzer.py
├─ notifications/
│  └─ webhook.py
├─ ui/
│  └─ main_window.py
└─ assets/templates/
```

## Install

Python 3.10+ 권장.

```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env
python main.py
```

Linux/macOS의 마지막 복사 명령은 `cp .env.example .env`를 사용하세요.

## Vision

### OpenCV

`assets/templates/`에 버튼 PNG를 넣으면 파일명이 detection 이름이 됩니다.

예:

```
assets/templates/upgrade.png
assets/templates/reward.png
assets/templates/close.png
```

### Local VLM

vLLM 등 OpenAI-compatible API를 사용할 수 있습니다.

```
VLM_ENABLED=true
VLM_ENDPOINT=http://127.0.0.1:8000/v1/chat/completions
VLM_MODEL=local-vlm
VLM_INTERVAL_MS=1000
```

VLM은 매 프레임마다 호출하지 않고 별도 주기로 샘플링합니다. 화면 분석의 기본 경로는 OpenCV입니다.

## Automation Rules

`config/actions.json`:

```json
{
  "rules": [
    {"template": "upgrade", "enabled": true, "click": false},
    {"template": "reward", "enabled": true, "click": false},
    {"template": "close", "enabled": true, "click": false}
  ]
}
```

실제 클릭이 필요한 규칙만 `click: true`로 바꾸고 Dashboard의 Automation을 켜야 합니다.

기본값은 감지 전용이며 클릭 자동화가 꺼져 있습니다.

## Webhooks

Discord:

```
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

Telegram:

```
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

비밀값은 `.env`에만 저장하고 Git에 커밋하지 마세요.

## UI

현재 Dashboard에는 다음이 포함됩니다.

- 실시간 화면 미리보기
- Stage/Detection 상태
- 분석 FPS
- 자동 클릭 횟수
- 실행 시간
- OpenCV / Local VLM 선택
- Template confidence 조정
- Start/Stop
- Automation ON/OFF
- 실시간 로그

다음 단계에서는 ROI 편집기, 다중 모니터/앱플레이어 선택, 액션 우선순위 편집, 이벤트별 webhook 정책을 추가할 수 있습니다.

## Scope

이 프로젝트는 로컬 화면 캡처와 일반적인 UI 자동화를 대상으로 합니다. 프로세스 변조, 인증 우회, 안티치트 회피 기능은 포함하지 않습니다.

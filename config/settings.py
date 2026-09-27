from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv
load_dotenv()
def env_bool(name: str, default: bool=False)->bool:
    value=os.getenv(name)
    return default if value is None else value.strip().lower() in {'1','true','yes','on'}
@dataclass(frozen=True)
class Settings:
    app_name:str=os.getenv('APP_NAME','Cathero Automation')
    capture_fps:int=int(os.getenv('CAPTURE_FPS','12'))
    analysis_interval_ms:int=int(os.getenv('ANALYSIS_INTERVAL_MS','150'))
    action_interval_ms:int=int(os.getenv('ACTION_INTERVAL_MS','500'))
    match_threshold:float=float(os.getenv('MATCH_THRESHOLD','0.86'))
    vlm_enabled:bool=env_bool('VLM_ENABLED')
    vlm_endpoint:str=os.getenv('VLM_ENDPOINT','http://127.0.0.1:8000/v1/chat/completions')
    vlm_model:str=os.getenv('VLM_MODEL','local-vlm')
    vlm_interval_ms:int=int(os.getenv('VLM_INTERVAL_MS','1000'))
    vlm_timeout:float=float(os.getenv('VLM_TIMEOUT','8'))
    discord_webhook_url:str=os.getenv('DISCORD_WEBHOOK_URL','')
    telegram_bot_token:str=os.getenv('TELEGRAM_BOT_TOKEN','')
    telegram_chat_id:str=os.getenv('TELEGRAM_CHAT_ID','')
    automation_enabled:bool=env_bool('AUTOMATION_ENABLED')
settings=Settings()

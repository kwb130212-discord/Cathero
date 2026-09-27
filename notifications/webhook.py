from __future__ import annotations
import requests
class WebhookNotifier:
    def __init__(self,discord_url='',telegram_token='',telegram_chat_id=''):self.discord_url=discord_url;self.telegram_token=telegram_token;self.telegram_chat_id=telegram_chat_id
    def send_sync(self,message):
        if self.discord_url:requests.post(self.discord_url,json={'content':message[:1900]},timeout=5).raise_for_status()
        if self.telegram_token and self.telegram_chat_id:
            requests.post(f'https://api.telegram.org/bot{self.telegram_token}/sendMessage',json={'chat_id':self.telegram_chat_id,'text':message[:4000]},timeout=5).raise_for_status()

import time
from dataclasses import dataclass, field
from typing import Dict, Tuple
from telegram import Bot

@dataclass
class Cooldown:
    last_sent: Dict[str, float] = field(default_factory=dict)
    cooldown: int = 900  # seconds

    def allow(self, key: str) -> bool:
        now = time.time()
        if key not in self.last_sent or now - self.last_sent[key] > self.cooldown:
            self.last_sent[key] = now
            return True
        return False

class AlertRouter:
    def __init__(self, bot_token: str, chat_id: str, cooldown_seconds: int = 900):
        self.bot = Bot(token=bot_token) if bot_token else None
        self.chat_id = chat_id
        self.cooldown = Cooldown(cooldown=cooldown_seconds)

    async def send(self, title: str, body: str, key: str):
        if not self.bot or not self.chat_id:
            print(f"[DRY] {title}: {body}")
            return
        if self.cooldown.allow(key):
            text = f"\u2728 <b>{title}</b>\n{body}"
            await self.bot.send_message(chat_id=self.chat_id, text=text, parse_mode="HTML")
        else:
            print(f"[SKIP] cooldown active for {key}")

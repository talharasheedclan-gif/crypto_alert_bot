from pydantic import BaseModel
import os

class Settings(BaseModel):
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")
    newsapi_key: str = os.getenv("NEWSAPI_KEY", "")
    cryptonewsapi_key: str = os.getenv("CRYPTONEWSAPI_KEY", "")
    etherscan_key: str = os.getenv("ETHERSCAN_API_KEY", "")

    binance_key: str = os.getenv("BINANCE_API_KEY", "")
    binance_secret: str = os.getenv("BINANCE_API_SECRET", "")
    use_binance_ws: bool = os.getenv("USE_BINANCE_WS", "true").lower() == "true"

    coins: list[str] = os.getenv("COINS", "BTC,ETH").split(",")
    base: str = os.getenv("BASE_CURRENCY", "USDT")
    timezone: str = os.getenv("TIMEZONE", "Asia/Dubai")

    duplicate_cooldown_seconds: int = int(os.getenv("DUPLICATE_COOLDOWN_SECONDS", "900"))

    # Rules
    price_alerts: list[str] = os.getenv("PRICE_ALERTS", "").split(",") if os.getenv("PRICE_ALERTS") else []
    vol_lookback_min: int = int(os.getenv("VOLUME_SPIKE_LOOKBACK_MIN", "60"))
    vol_multiplier: float = float(os.getenv("VOLUME_SPIKE_MULTIPLIER", "3.0"))
    rsi_period: int = int(os.getenv("RSI_PERIOD", "14"))
    rsi_oversold: float = float(os.getenv("RSI_OVERSOLD", "30"))
    rsi_overbought: float = float(os.getenv("RSI_OVERBOUGHT", "70"))

    enable_session_filter: bool = os.getenv("ENABLE_SESSION_FILTER", "true").lower() == "true"
    london_start: str = os.getenv("SESSION_LONDON_START", "11:00")
    london_end: str = os.getenv("SESSION_LONDON_END", "14:00")
    ny_start: str = os.getenv("SESSION_NEWYORK_START", "16:30")
    ny_end: str = os.getenv("SESSION_NEWYORK_END", "19:30")

    # Auto-trade
    enable_autotrade: bool = os.getenv("ENABLE_AUTOTRADE", "false").lower() == "true"
    autotrade_webhook_url: str = os.getenv("AUTOTRADE_WEBHOOK_URL", "")
    max_order_notional: float = float(os.getenv("MAX_ORDER_NOTIONAL", "50"))
    daily_max_orders: int = int(os.getenv("DAILY_MAX_ORDERS", "5"))
    circuit_breaker_pct_drop: float = float(os.getenv("CIRCUIT_BREAKER_PCT_DROP", "5"))

settings = Settings()


    # MEXC
    enable_mexc: bool = os.getenv("ENABLE_MEXC", "false").lower() == "true"
    mexc_symbols: list[str] = [s.strip() for s in os.getenv("MEXC_SYMBOLS", "BTC/USDT,ETH/USDT").split(",")]
    mexc_poll_interval_sec: int = int(os.getenv("MEXC_POLL_INTERVAL_SEC", "30"))

    # VWAP / Sweeps
    vwap_reset: str = os.getenv("VWAP_RESET", "DAILY")
    sweep_lookback: int = int(os.getenv("SWEEP_LOOKBACK", "20"))

    scheduler_news_seconds: int = int(os.getenv("SCHEDULER_NEWS_SECONDS", "900"))

    # Heartbeat
    heartbeat_seconds: int = int(os.getenv("HEARTBEAT_SECONDS", "7200"))

    # VWAP bands
    enable_vwap_band_alerts: bool = os.getenv("ENABLE_VWAP_BAND_ALERTS", "true").lower() == "true"
    vwap_band_window: int = int(os.getenv("VWAP_BAND_WINDOW", "50"))

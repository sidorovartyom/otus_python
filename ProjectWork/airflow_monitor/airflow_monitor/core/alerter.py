"""Alerting system - sends notifications."""

from typing import List

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from airflow_monitor.core.models import AnomalyResult
from airflow_monitor.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


class Alerter:
    """Sends alerts about detected anomalies."""

    def __init__(
        self,
        telegram_enabled: bool = False,
        bot_token: str = TELEGRAM_BOT_TOKEN,
        chat_id: str = TELEGRAM_CHAT_ID
    ):
        """
        Initialize alerter.

        Args:
            telegram_enabled: Whether to enable Telegram notifications
            bot_token: Telegram bot token
            chat_id: Telegram chat ID
        """
        self.telegram_enabled = telegram_enabled and bot_token and chat_id
        self.bot_token = bot_token
        self.chat_id = chat_id

    def send_anomaly_alert(self, anomalies: List[AnomalyResult]) -> bool:
        """
        Send alert about detected anomalies.

        Args:
            anomalies: List of detected anomalies

        Returns:
            True if alert sent successfully
        """
        if not anomalies:
            return False

        message = self._format_anomaly_message(anomalies)

        if self.telegram_enabled:
            return self._send_telegram(message)
        else:
            # Just print to console
            print(f"ALERT: {message}")
            return True

    def _format_anomaly_message(self, anomalies: List[AnomalyResult]) -> str:
        """Format anomalies into alert message."""
        dag_ids = list(set(a.dag_id for a in anomalies))

        message = f"⚠️ Anomaly Alert\n\n"
        message += f"Detected {len(anomalies)} anomalies in {len(dag_ids)} DAG(s):\n\n"

        for anomaly in anomalies:
            message += f"🔴 DAG: {anomaly.dag_id}\n"
            message += f"   Metric: {anomaly.metric_name}\n"
            message += f"   Expected: {anomaly.expected_value:.1f}\n"
            message += f"   Actual: {anomaly.actual_value:.1f}\n"
            message += f"   Score: {anomaly.anomaly_score:.2f}\n\n"

        return message

    def _send_telegram(self, message: str) -> bool:
        """
        Send message via Telegram.

        Args:
            message: Message text

        Returns:
            True if sent successfully
        """
        if not REQUESTS_AVAILABLE:
            print("requests library not available, cannot send Telegram alert")
            return False

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML"
            }

            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()

            print(f"Telegram alert sent successfully")
            return True

        except Exception as e:
            print(f"Failed to send Telegram alert: {e}")
            return False

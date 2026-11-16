import uuid
import random
from datetime import datetime, timezone
from faker import Faker

fake = Faker()


class TestDataFactory:
    """一键测试数据构造工厂：消除测试数据依赖，支持边界场景快速生成"""

    @staticmethod
    def build_payment_payload(
        amount: float = None,
        currency: str = "EUR",
        target_currency: str = "CNY",
        user_timezone: str = "Europe/Paris",
        custom_utc_iso: str = None,
    ) -> tuple[dict, dict]:
        """返回 (headers, payload)，自动生成唯一订单号与幂等性 Key"""
        order_id = f"ORD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        idempotency_key = f"IDEMP-{uuid.uuid4()}"

        if amount is None:
            amount = round(random.uniform(10.0, 500.0), 2)

        if custom_utc_iso is None:
            custom_utc_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        headers = {
            "X-Idempotency-Key": idempotency_key,
            "Accept-Language": "fr-FR" if user_timezone == "Europe/Paris" else "en-US",
        }

        payload = {
            "order_id": order_id,
            "amount": amount,
            "currency": currency,
            "target_currency": target_currency,
            "user_timezone": user_timezone,
            "timestamp_utc": custom_utc_iso,
        }
        return headers, payload
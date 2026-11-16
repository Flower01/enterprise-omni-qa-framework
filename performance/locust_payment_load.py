from locust import HttpUser, task, between
from utils.data_factory import TestDataFactory


class GlobalPaymentLoadUser(HttpUser):
    """模拟高并发跨境支付请求压测（用于验证 TPS 与 P99 响应时间）"""
    wait_time = between(0.2, 1.0)

    @task(3)
    def checkout_eur_payment(self):
        headers, payload = TestDataFactory.build_payment_payload(currency="EUR", target_currency="CNY")
        with self.client.post(
            "/api/v1/payment/checkout",
            json=payload,
            headers=headers,
            name="/api/v1/payment/checkout [EUR]",
            catch_response=True,
        ) as response:
            if response.status_code == 200 and response.json().get("code") == 200:
                response.success()
            else:
                response.failure(f"Checkout failed: {response.status_code}")

    @task(1)
    def generate_ai_photo(self):
        payload = {"image_id": "IMG-LOAD-001", "style": "anime_3d", "simulate_weak_network": False}
        self.client.post("/api/v1/ai/style-transfer", json=payload, name="/api/v1/ai/style-transfer")
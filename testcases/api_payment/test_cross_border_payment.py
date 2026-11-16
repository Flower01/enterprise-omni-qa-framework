import pytest
import allure
from utils.data_factory import TestDataFactory
from core.timezone_helper import TimezoneValidator


@allure.epic("Global Payment & Settlement")
@allure.feature("Cross-Border Checkout & Daily Cutoff")
class TestCrossBorderPayment:

    @pytest.mark.smoke
    @pytest.mark.payment
    @allure.story("Multi-currency FX calculation and settlement")
    @pytest.mark.parametrize(
        "currency,target_currency,amount,expected_settled",
        [
            ("EUR", "CNY", 100.00, 785.00),
            ("USD", "CNY", 50.50, 363.60),
            ("EUR", "USD", 200.00, 218.00),
        ],
    )
    def test_fx_settlement_precision(self, api_client, currency, target_currency, amount, expected_settled):
        """验证多币种实时汇率换算与清结算金额精度"""
        headers, payload = TestDataFactory.build_payment_payload(
            amount=amount, currency=currency, target_currency=target_currency
        )
        resp = api_client.post("/api/v1/payment/checkout", json_data=payload, headers=headers)

        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["settled_amount"] == expected_settled
        assert body["data"]["status"] == "SETTLED"

    @pytest.mark.smoke
    @pytest.mark.payment
    @allure.story("Idempotency protection against duplicate network retries")
    def test_payment_idempotency_protection(self, api_client):
        """验证弱网环境下客户端重复提交相同幂等 Key 时，服务端精准拦截防重复扣款"""
        headers, payload = TestDataFactory.build_payment_payload(amount=88.00, currency="EUR")

        # 第一次请求：正常扣款结算
        first_resp = api_client.post("/api/v1/payment/checkout", json_data=payload, headers=headers)
        assert first_resp.status_code == 200

        # 模拟弱网重试：使用完全相同的 X-Idempotency-Key 再次提交
        second_resp = api_client.post("/api/v1/payment/checkout", json_data=payload, headers=headers)
        assert second_resp.status_code == 409
        assert "Duplicate transaction" in second_resp.json()["detail"]

    @pytest.mark.i18n
    @pytest.mark.payment
    @allure.story("Cross-timezone daily cutoff boundary (Paris UTC+1 vs Shanghai UTC+8)")
    def test_cross_timezone_billing_cutoff(self, api_client):
        """
        核心边界场景：
        UTC 时间 2026-05-10T18:30:00Z
        - 巴黎时间 (UTC+2 夏令时) 为 2026-05-10 20:30 -> 账单日应归属 2026-05-10
        - 北京时间 (UTC+8) 为 2026-05-11 02:30 -> 总部清结算日切应归属 2026-05-11
        """
        boundary_utc = "2026-05-10T18:30:00Z"
        headers, payload = TestDataFactory.build_payment_payload(
            amount=120.00,
            currency="EUR",
            user_timezone="Europe/Paris",
            custom_utc_iso=boundary_utc,
        )

        resp = api_client.post("/api/v1/payment/checkout", json_data=payload, headers=headers)
        assert resp.status_code == 200

        data = resp.json()["data"]
        expected_dates = TimezoneValidator.calculate_expected_billing_dates(boundary_utc)

        assert data["local_billing_date"] == expected_dates["expected_local_date"] == "2026-05-10"
        assert data["hq_billing_date"] == expected_dates["expected_hq_date"] == "2026-05-11"

    @pytest.mark.i18n
    @pytest.mark.parametrize(
        "lang_code",
        ["fr-FR", "en-US", "zh-CN"],
    )
    def test_localization_response_messages(self, api_client, test_data, lang_code):
        """验证海外多语言环境下支付结果提示文案的本地化准确性"""
        headers, payload = TestDataFactory.build_payment_payload()
        headers["Accept-Language"] = lang_code

        resp = api_client.post("/api/v1/payment/checkout", json_data=payload, headers=headers)
        assert resp.status_code == 200
        expected_msg = test_data["i18n_messages"][lang_code]["payment_success"]
        assert resp.json()["message"] == expected_msg
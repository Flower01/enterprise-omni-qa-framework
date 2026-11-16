from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
import pytz
import uuid
import time
import random

app = FastAPI(title="Global Payment & AI Service Mock SUT", version="1.0.0")

# 模拟内存数据库与幂等性缓存
ORDERS_DB = {}
IDEMPOTENCY_KEYS = set()

RATES = {
    ("EUR", "CNY"): 7.85,
    ("USD", "CNY"): 7.20,
    ("EUR", "USD"): 1.09,
    ("EUR", "EUR"): 1.00,
    ("USD", "USD"): 1.00,
}

I18N_DICT = {
    "fr-FR": {"success": "Paiement effectué avec succès"},
    "en-US": {"success": "Payment completed successfully"},
    "zh-CN": {"success": "支付成功"},
}


class PaymentRequest(BaseModel):
    order_id: str
    amount: float = Field(..., gt=0, description="Transaction amount")
    currency: str = Field(..., pattern="^(EUR|USD|CNY)$")
    target_currency: str = Field(default="CNY")
    user_timezone: str = Field(default="Europe/Paris")
    timestamp_utc: str  # ISO 8601 UTC timestamp


class AIGenerateRequest(BaseModel):
    image_id: str
    style: str
    simulate_weak_network: bool = False


@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/api/v1/payment/checkout")
def process_payment(
    req: PaymentRequest,
    idempotency_key: str = Header(..., alias="X-Idempotency-Key"),
    accept_language: str = Header(default="en-US", alias="Accept-Language"),
):
    # 1. 幂等性校验（防止弱网重试导致重复扣款）
    if idempotency_key in IDEMPOTENCY_KEYS:
        raise HTTPException(status_code=409, detail="Duplicate transaction detected")

    # 2. 汇率换算与清结算金额计算（保留2位小数，四舍五入）
    rate = RATES.get((req.currency, req.target_currency))
    if not rate:
        raise HTTPException(status_code=400, detail="Unsupported currency pair")
    settled_amount = round(req.amount * rate, 2)

    # 3. 跨时区账单日切归属计算（解决巴黎 UTC+1 与 总部 UTC+8 账单日差异）
    utc_dt = datetime.fromisoformat(req.timestamp_utc.replace("Z", "+00:00"))
    local_tz = pytz.timezone(req.user_timezone)
    hq_tz = pytz.timezone("Asia/Shanghai")

    local_billing_date = utc_dt.astimezone(local_tz).strftime("%Y-%m-%d")
    hq_billing_date = utc_dt.astimezone(hq_tz).strftime("%Y-%m-%d")

    # 4. 落库并记录幂等 Key
    tx_id = f"TX-{uuid.uuid4().hex[:10].upper()}"
    IDEMPOTENCY_KEYS.add(idempotency_key)
    record = {
        "tx_id": tx_id,
        "order_id": req.order_id,
        "original_amount": req.amount,
        "currency": req.currency,
        "settled_amount": settled_amount,
        "target_currency": req.target_currency,
        "exchange_rate": rate,
        "local_billing_date": local_billing_date,
        "hq_billing_date": hq_billing_date,
        "status": "SETTLED",
    }
    ORDERS_DB[req.order_id] = record

    msg = I18N_DICT.get(accept_language, I18N_DICT["en-US"])["success"]
    return {"code": 200, "message": msg, "data": record}


@app.post("/api/v1/ai/style-transfer")
def generate_ai_image(req: AIGenerateRequest):
    start_time = time.time()

    # 模拟弱网抖动或云端排队延迟
    if req.simulate_weak_network:
        time.sleep(random.uniform(1.5, 2.5))
    else:
        time.sleep(random.uniform(0.1, 0.3))

    latency_ms = round((time.time() - start_time) * 1000, 2)
    return {
        "code": 200,
        "data": {
            "task_id": f"AI-{uuid.uuid4().hex[:8]}",
            "image_id": req.image_id,
            "style": req.style,
            "output_url": f"https://example.com{req.image_id}_{req.style}.jpg",
            "quality_score": round(random.uniform(0.88, 0.99), 3),
            "latency_ms": latency_ms,
        },
    }
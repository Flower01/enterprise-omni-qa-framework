import uuid
import pytest
import allure
from core.ai_evaluator import AIQualityEvaluator


@allure.epic("AI Image Generation")
@allure.feature("Style Transfer & Weak Network Resilience")
class TestAIGeneration:

    @pytest.mark.smoke
    @pytest.mark.ai
    @pytest.mark.parametrize("style", ["cyberpunk", "oil_painting", "anime_3d"])
    def test_ai_style_generation_sla_and_quality(self, api_client, style):
        """验证正常网络下多风格 AI 图像生成的延迟 SLA (<1000ms) 与质量分数阈值"""
        payload = {
            "image_id": f"IMG-{uuid.uuid4().hex[:8]}",
            "style": style,
            "simulate_weak_network": False,
        }
        resp = api_client.post("/api/v1/ai/style-transfer", json_data=payload)
        assert resp.status_code == 200

        eval_result = AIQualityEvaluator.evaluate_generation_response(
            resp.json(), max_latency_ms=1000.0, min_quality_score=0.85
        )
        assert eval_result["passed"], f"AI Evaluation failed: {eval_result}"

    @pytest.mark.ai
    def test_ai_generation_under_weak_network(self, api_client):
        """验证弱网高延迟场景下接口的优雅降级与输出完整性（允许放宽延迟阈值至 3000ms）"""
        payload = {
            "image_id": f"IMG-{uuid.uuid4().hex[:8]}",
            "style": "cyberpunk",
            "simulate_weak_network": True,
        }
        resp = api_client.post("/api/v1/ai/style-transfer", json_data=payload)
        assert resp.status_code == 200

        eval_result = AIQualityEvaluator.evaluate_generation_response(
            resp.json(), max_latency_ms=3000.0, min_quality_score=0.85
        )
        assert eval_result["passed"]
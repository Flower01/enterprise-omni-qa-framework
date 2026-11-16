class AIQualityEvaluator:
    """AI 生成类功能的质量、SLA 延迟与降级鲁棒性评估器"""

    @staticmethod
    def evaluate_generation_response(
        response_data: dict,
        max_latency_ms: float = 1000.0,
        min_quality_score: float = 0.85,
    ) -> dict:
        data = response_data.get("data", {})
        latency = data.get("latency_ms", float("inf"))
        quality_score = data.get("quality_score", 0.0)
        output_url = data.get("output_url", "")

        checks = {
            "has_valid_url": output_url.startswith("https://") and output_url.endswith(".jpg"),
            "meets_latency_sla": latency <= max_latency_ms,
            "meets_quality_threshold": quality_score >= min_quality_score,
        }

        return {
            "passed": all(checks.values()),
            "details": checks,
            "actual_latency_ms": latency,
            "actual_quality_score": quality_score,
        }
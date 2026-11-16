import pytest
import yaml
from core.api_client import RobustAPIClient


@pytest.fixture(scope="session")
def api_client():
    """全局复用的带连接池与重试机制的 API 客户端"""
    return RobustAPIClient()


@pytest.fixture(scope="session")
def test_data():
    """加载多语言与业务测试数据字典"""
    with open("config/test_data.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
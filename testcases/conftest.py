import subprocess
import sys
import time
import urllib.request
import pytest
import yaml
from core.api_client import RobustAPIClient


@pytest.fixture(scope="session", autouse=True)
def start_mock_sut_server():
    """在测试会话开始前自动拉起 FastAPI 模拟后端，测试结束后自动清理进程"""
    # 先探测外部是否已经手动启动了服务（兼容 Docker Compose 或本地手动启动）
    try:
        urllib.request.urlopen("http://127.0.0", timeout=1)
        yield
        return
    except Exception:
        pass

    # 自动在子进程启动 Uvicorn 服务
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "mock_server.app:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # 轮询等待服务就绪（最长 30 秒）
    for _ in range(30):
        try:
            urllib.request.urlopen("http://127.0.0", timeout=1)
            break
        except Exception:
            time.sleep(1)
    else:
        proc.terminate()
        raise RuntimeError("Mock SUT server failed to start within 30 seconds.")

    yield

    # 测试全部结束后优雅关闭服务
    proc.terminate()
    proc.wait(timeout=5)


@pytest.fixture(scope="session")
def api_client():
    """全局复用的带连接池与重试机制的 API 客户端"""
    return RobustAPIClient()


@pytest.fixture(scope="session")
def test_data():
    """加载多语言与业务测试数据字典"""
    with open("config/test_data.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

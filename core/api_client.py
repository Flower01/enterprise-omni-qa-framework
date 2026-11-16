import os
import yaml
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from utils.logger import get_logger

logger = get_logger("APIClient")


class RobustAPIClient:
    """支持自动重试与环境动态切换的企业级 HTTP 客户端"""

    def __init__(self, env: str = None):
        env = env or os.getenv("TEST_ENV", "local")
        with open("config/env_config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        env_cfg = config["environments"].get(env, config["default"])
        self.base_url = os.getenv("BASE_URL", env_cfg["base_url"])
        self.timeout = config["default"]["timeout"]
        self.session = self._init_session(retries=config["default"]["max_retries"])

    def _init_session(self, retries: int) -> requests.Session:
        session = requests.Session()
        # 针对网关超时或服务端瞬时抖动（502/503/504）启用指数退避重试
        retry_strategy = Retry(
            total=retries,
            backoff_factor=0.5,
            status_forcelist=[502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def post(self, endpoint: str, json_data: dict = None, headers: dict = None) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        logger.info(f"POST {url} | Headers: {headers} | Payload: {json_data}")
        response = self.session.post(url, json=json_data, headers=headers, timeout=self.timeout)
        logger.info(f"Response [{response.status_code}]: {response.text}")
        return response

    def get(self, endpoint: str, params: dict = None, headers: dict = None) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        logger.info(f"GET {url} | Params: {params}")
        response = self.session.get(url, params=params, headers=headers, timeout=self.timeout)
        logger.info(f"Response [{response.status_code}]: {response.text}")
        return response
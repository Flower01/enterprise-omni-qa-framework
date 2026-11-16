from datetime import datetime
import pytz


class TimezoneValidator:
    """跨时区日切（Daily Cutoff）与清结算时间校验引擎"""

    @staticmethod
    def calculate_expected_billing_dates(
        utc_iso_str: str,
        local_tz_name: str = "Europe/Paris",
        hq_tz_name: str = "Asia/Shanghai",
    ) -> dict:
        """
        根据 UTC 时间戳，精确计算海外本地账单日与国内总部清结算账单日。
        解决跨时区（如 UTC+1 与 UTC+8 存在7小时时差）导致的对账日切偏差问题。
        """
        utc_dt = datetime.fromisoformat(utc_iso_str.replace("Z", "+00:00"))
        local_tz = pytz.timezone(local_tz_name)
        hq_tz = pytz.timezone(hq_tz_name)

        return {
            "expected_local_date": utc_dt.astimezone(local_tz).strftime("%Y-%m-%d"),
            "expected_hq_date": utc_dt.astimezone(hq_tz).strftime("%Y-%m-%d"),
        }
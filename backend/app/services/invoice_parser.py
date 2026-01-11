from datetime import date, datetime, timedelta
from typing import Optional, Tuple

from ..config import CONFIDENCE_THRESHOLD, AMOUNT_ANOMALY_THRESHOLD, DATE_ANOMALY_DAYS

# 费用科目自动映射规则
CATEGORY_RULES = {
    "交通费": ["滴滴", "出租", "地铁", "公交", "高铁", "火车", "机票", "航空", "铁路", "出行"],
    "差旅费-住宿": ["酒店", "宾馆", "民宿", "住宿", "旅馆", "客房"],
    "业务招待费": ["餐饮", "餐厅", "饭店", "酒楼", "餐馆", "食堂", "全聚德", "海底捞"],
    "办公费": ["文具", "打印", "复印", "办公用品", "纸张", "墨盒", "笔记本", "文件夹"],
    "通讯费": ["电信", "移动", "联通", "话费", "通讯", "宽带"],
    "固定资产": ["固定资产", "设备", "电脑", "服务器", "打印机", "空调", "家具"],
    "低值易耗品": ["低值易耗", "工具", "耗材"],
}

# 科目编码映射
ACCOUNT_CODE_MAP = {
    "交通费": {"code": "660206", "name": "管理费用-交通费"},
    "差旅费-住宿": {"code": "660207", "name": "管理费用-差旅费"},
    "业务招待费": {"code": "660208", "name": "管理费用-业务招待费"},
    "办公费": {"code": "660201", "name": "管理费用-办公费"},
    "通讯费": {"code": "660203", "name": "管理费用-通讯费"},
    "固定资产": {"code": "1601", "name": "固定资产"},
    "低值易耗品": {"code": "140301", "name": "周转材料-低值易耗品"},
    "其他": {"code": "660299", "name": "管理费用-其他"},
}


def classify_expense(seller_name: str, items: list) -> str:
    """根据销方名称和商品名称自动分类费用科目"""
    text = (seller_name or "") + " ".join(items or [])
    text = text.lower()

    for category, keywords in CATEGORY_RULES.items():
        for keyword in keywords:
            if keyword.lower() in text:
                return category

    return "其他"


def detect_anomalies(
    amount: float,
    invoice_date: Optional[date],
    confidence: float,
    invoice_no: Optional[str] = None,
) -> Tuple[str, str]:
    """
    检测发票异常
    返回: (异常标记, 异常原因)
    """
    anomalies = []

    # 1. 金额异常
    if amount and amount > AMOUNT_ANOMALY_THRESHOLD:
        anomalies.append(f"金额>{AMOUNT_ANOMALY_THRESHOLD}元需审批")

    # 2. 置信度低
    if confidence < CONFIDENCE_THRESHOLD:
        anomalies.append(f"识别置信度低({confidence:.0%})")

    # 3. 日期异常
    if invoice_date:
        days_ago = (date.today() - invoice_date).days
        if days_ago > DATE_ANOMALY_DAYS:
            anomalies.append(f"发票已超过{DATE_ANOMALY_DAYS}天")
        elif days_ago < 0:
            anomalies.append("发票日期在未来")

    if anomalies:
        flag = "warning" if len(anomalies) == 1 else "error"
        return flag, "; ".join(anomalies)

    return "normal", ""


def get_account_code(category: str) -> dict:
    """获取科目编码"""
    return ACCOUNT_CODE_MAP.get(category, ACCOUNT_CODE_MAP["其他"])


def parse_date(date_str: str) -> Optional[date]:
    """解析日期字符串"""
    if not date_str:
        return None

    formats = ["%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日", "%Y.%m.%d"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None

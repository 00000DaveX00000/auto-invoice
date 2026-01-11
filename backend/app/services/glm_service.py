import base64
import json
import logging
import os
import re
import time
from datetime import datetime
from typing import Optional
from zhipuai import ZhipuAI

from ..config import GLM_API_KEY

# 配置日志
LOG_DIR = "./logs"
os.makedirs(LOG_DIR, exist_ok=True)

# 创建 GLM 专用 logger
glm_logger = logging.getLogger("glm_service")
glm_logger.setLevel(logging.DEBUG)

# 文件处理器 - 记录所有调用
file_handler = logging.FileHandler(
    os.path.join(LOG_DIR, "glm_calls.log"),
    encoding="utf-8"
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
))

# 控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(
    "%(asctime)s | GLM | %(message)s",
    datefmt="%H:%M:%S"
))

glm_logger.addHandler(file_handler)
glm_logger.addHandler(console_handler)

INVOICE_PROMPT = """请识别这张单据图片（可能是发票或费用报销单），提取以下信息并以 JSON 格式返回：
{
  "doc_type": "发票/费用报销单/收据/其他",
  "invoice_no": "发票号码或单据编号",
  "invoice_date": "日期 (YYYY-MM-DD格式)",
  "invoice_type": "增值税专票/增值税普票/电子普票/费用报销单/其他",
  "seller_name": "销方名称或供应商",
  "seller_tax_no": "销方税号",
  "amount": 金额(数字，不含税金额，如果没有税额则等于总金额),
  "tax_amount": 税额(数字，如果没有则为0),
  "total_amount": 价税合计或报销金额(数字),
  "items": ["商品/服务名称或摘要内容"],
  "payee": "领款人姓名(领款人签章处)",
  "handler": "经手人姓名(经手处)",
  "approver": "审批人姓名(审批人处)",
  "reviewer": "审核人姓名(审核处)",
  "department": "部门名称",
  "expense_category": "费用类别(必须从下方分类标准中选择)",
  "attachments_count": 附单据张数(数字),
  "confidence": 置信度(0-1之间的小数，表示识别准确度)
}

【费用科目分类标准】请根据单据内容判断，expense_category 必须是以下值之一：
- "交通费": 滴滴、出租车、地铁、公交、高铁、火车票、机票、航空、铁路、出行相关
- "差旅费-住宿": 酒店、宾馆、民宿、住宿、旅馆、客房
- "业务招待费": 餐饮、餐厅、饭店、酒楼、餐馆、食堂、请客吃饭
- "办公费": 文具、打印、复印、办公用品、纸张、墨盒、笔记本(文具类)、文件夹
- "通讯费": 电信、移动、联通、话费、通讯、宽带、网络费
- "固定资产": 固定资产、设备、电脑、服务器、打印机、空调、家具、大型办公设备
- "低值易耗品": 低值易耗品、工具、耗材
- "其他": 无法归入以上类别的费用

注意事项：
1. 如果某个字段无法识别，请设为 null
2. 金额字段必须是纯数字，不要带单位符号（如 ¥29659.07 应返回 29659.07）
3. 日期格式必须是 YYYY-MM-DD
4. 只返回 JSON 对象，不要包含其他说明文字
5. 费用报销单通常包含：日期、摘要、金额、附单据张数、领款人签章、经手人等
6. 如果是费用报销单，seller_name 可以填写供应商或留空
7. 注意识别手写内容，仔细辨认
8. expense_category 必须严格从上述分类标准中选择一个
"""


class GLMService:
    def __init__(self):
        self.client = ZhipuAI(api_key=GLM_API_KEY) if GLM_API_KEY else None
        self.call_count = 0
        self.total_tokens = 0

        if self.client:
            glm_logger.info(f"GLM Service 初始化成功, API Key: {GLM_API_KEY[:8]}...{GLM_API_KEY[-4:]}")
        else:
            glm_logger.warning("GLM Service 初始化: 无 API Key, 使用模拟模式")

    def recognize_invoice(self, image_path: str) -> Optional[dict]:
        """识别发票图片，返回解析结果"""
        self.call_count += 1
        call_id = f"GLM-{self.call_count:04d}"
        start_time = time.time()

        glm_logger.info(f"[{call_id}] 开始识别 | 图片: {image_path}")

        if not self.client:
            glm_logger.warning(f"[{call_id}] 使用模拟模式 (无 API Key)")
            return self._mock_response()

        try:
            # 获取图片大小
            file_size = os.path.getsize(image_path)
            glm_logger.debug(f"[{call_id}] 图片大小: {file_size / 1024:.1f} KB")

            # Read and encode image
            with open(image_path, "rb") as img_file:
                img_base64 = base64.b64encode(img_file.read()).decode("utf-8")

            # Determine image type
            if image_path.lower().endswith(".png"):
                img_url = f"data:image/png;base64,{img_base64}"
            elif image_path.lower().endswith((".jpg", ".jpeg")):
                img_url = f"data:image/jpeg;base64,{img_base64}"
            else:
                img_url = f"data:image/png;base64,{img_base64}"

            glm_logger.debug(f"[{call_id}] 调用 GLM API | Model: glm-4.6v")

            response = self.client.chat.completions.create(
                model="glm-4.6v",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": img_url}},
                            {"type": "text", "text": INVOICE_PROMPT},
                        ],
                    }
                ],
            )

            elapsed = time.time() - start_time
            content = response.choices[0].message.content

            # 记录 token 使用量
            usage = getattr(response, 'usage', None)
            if usage:
                prompt_tokens = getattr(usage, 'prompt_tokens', 0)
                completion_tokens = getattr(usage, 'completion_tokens', 0)
                total_tokens = getattr(usage, 'total_tokens', 0)
                self.total_tokens += total_tokens
                glm_logger.info(f"[{call_id}] Token 使用: prompt={prompt_tokens}, completion={completion_tokens}, total={total_tokens}")

            # 解析结果
            result = self._parse_response(content)

            if result:
                glm_logger.info(f"[{call_id}] 识别成功 | 耗时: {elapsed:.2f}s | 发票号: {result.get('invoice_no', 'N/A')} | 金额: {result.get('total_amount', 0)}")
                glm_logger.debug(f"[{call_id}] 完整结果: {json.dumps(result, ensure_ascii=False)}")
            else:
                glm_logger.warning(f"[{call_id}] 解析失败 | 耗时: {elapsed:.2f}s | 原始响应: {content[:200]}...")

            # 记录原始响应到日志文件
            self._log_raw_response(call_id, image_path, content, result, elapsed)

            return result

        except Exception as e:
            elapsed = time.time() - start_time
            glm_logger.error(f"[{call_id}] API 调用失败 | 耗时: {elapsed:.2f}s | 错误: {str(e)}")
            self._log_error(call_id, image_path, str(e), elapsed)
            return None

    def _parse_response(self, content: str) -> Optional[dict]:
        """解析 GLM 返回的内容"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r"\{[\s\S]*\}", content)
            if json_match:
                return json.loads(json_match.group())
            return None
        except json.JSONDecodeError as e:
            glm_logger.error(f"JSON 解析错误: {e}")
            return None

    def _log_raw_response(self, call_id: str, image_path: str, raw_content: str, parsed_result: dict, elapsed: float):
        """记录原始响应到详细日志文件"""
        log_file = os.path.join(LOG_DIR, "glm_details.jsonl")
        log_entry = {
            "call_id": call_id,
            "timestamp": datetime.now().isoformat(),
            "image_path": image_path,
            "elapsed_seconds": round(elapsed, 3),
            "success": parsed_result is not None,
            "raw_response": raw_content,
            "parsed_result": parsed_result
        }
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    def _log_error(self, call_id: str, image_path: str, error: str, elapsed: float):
        """记录错误到详细日志文件"""
        log_file = os.path.join(LOG_DIR, "glm_details.jsonl")
        log_entry = {
            "call_id": call_id,
            "timestamp": datetime.now().isoformat(),
            "image_path": image_path,
            "elapsed_seconds": round(elapsed, 3),
            "success": False,
            "error": error
        }
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    def _mock_response(self) -> dict:
        """当没有 API Key 时返回模拟数据"""
        return {
            "invoice_no": "12345678901234567890",
            "invoice_date": "2025-01-10",
            "invoice_type": "增值税普票",
            "seller_name": "测试公司",
            "seller_tax_no": "91110000MA12345678",
            "amount": 100.00,
            "tax_amount": 6.00,
            "total_amount": 106.00,
            "items": ["测试服务"],
            "confidence": 0.95,
        }

    def get_stats(self) -> dict:
        """获取调用统计"""
        return {
            "total_calls": self.call_count,
            "total_tokens": self.total_tokens,
            "api_key_configured": self.client is not None
        }


glm_service = GLMService()

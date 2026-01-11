import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Date, DateTime, Text, JSON
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON

from ..database import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_no = Column(String(50), nullable=True)
    invoice_date = Column(Date, nullable=True)
    invoice_type = Column(String(50), nullable=True)  # 增值税专票/普票/电子普票
    seller_name = Column(String(200), nullable=True)
    seller_tax_no = Column(String(50), nullable=True)
    amount = Column(Float, default=0)  # 金额（不含税）
    tax_amount = Column(Float, default=0)  # 税额
    total_amount = Column(Float, default=0)  # 价税合计
    expense_category = Column(String(50), nullable=True)  # 费用科目
    reimbursement_person = Column(String(50), nullable=True)  # 报销人
    confidence = Column(Float, default=0)  # 识别置信度 (0-1)
    anomaly_flag = Column(String(20), nullable=True)  # 异常标记: normal, warning, error
    anomaly_reason = Column(String(200), nullable=True)  # 异常原因
    image_path = Column(String(500), nullable=True)  # 原图路径
    raw_response = Column(JSON, nullable=True)  # GLM 原始返回
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

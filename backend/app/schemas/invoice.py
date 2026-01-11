from datetime import date, datetime
from typing import Optional, List, Any
from pydantic import BaseModel


class InvoiceBase(BaseModel):
    invoice_no: Optional[str] = None
    invoice_date: Optional[date] = None
    invoice_type: Optional[str] = None
    seller_name: Optional[str] = None
    seller_tax_no: Optional[str] = None
    amount: float = 0
    tax_amount: float = 0
    total_amount: float = 0
    expense_category: Optional[str] = None
    reimbursement_person: Optional[str] = None
    confidence: float = 0
    anomaly_flag: Optional[str] = None
    anomaly_reason: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    image_path: Optional[str] = None
    raw_response: Optional[dict] = None


class InvoiceUpdate(BaseModel):
    expense_category: Optional[str] = None
    reimbursement_person: Optional[str] = None
    anomaly_flag: Optional[str] = None
    anomaly_reason: Optional[str] = None


class InvoiceResponse(InvoiceBase):
    id: str
    image_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InvoiceListResponse(BaseModel):
    items: List[InvoiceResponse]
    total: int
    page: int
    size: int


class CategorySummary(BaseModel):
    category: str
    count: int
    amount: float
    tax_amount: float


class SummaryResponse(BaseModel):
    by_category: List[CategorySummary]
    total_count: int
    total_amount: float
    total_tax: float
    anomaly_count: int


class UploadResponse(BaseModel):
    task_id: str
    total_count: int
    processed: int
    message: str


class VoucherEntry(BaseModel):
    编制日期: str
    凭证类型: str
    凭证序号: int
    凭证号: str
    制单人: str
    附件张数: int
    会计年度: str
    科目编码: str
    科目名称: str
    凭证摘要: str
    借贷方向: str
    金额: float
    币种: str = "人民币"
    汇率: float = 1
    原币金额: float = 0
    数量: Optional[float] = None
    单价: Optional[float] = None
    结算方式名称: Optional[str] = None
    结算日期: Optional[str] = None
    结算票号: Optional[str] = None
    业务日期: Optional[str] = None
    员工编号: Optional[str] = None
    员工姓名: Optional[str] = None
    往来单位编号: Optional[str] = None
    往来单位名称: Optional[str] = None
    货品编号: Optional[str] = None
    货品名称: Optional[str] = None
    部门名称: Optional[str] = None
    项目名称: Optional[str] = None


class VoucherGenerateRequest(BaseModel):
    invoice_ids: List[str]
    voucher_date: str
    voucher_type: str = "转"
    maker: str = "系统"
    department: str = ""


class VoucherGenerateResponse(BaseModel):
    vouchers: List[VoucherEntry]
    total_debit: float
    total_credit: float

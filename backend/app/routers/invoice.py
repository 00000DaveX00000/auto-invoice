import os
import uuid
from datetime import date, datetime
from typing import List, Optional
from collections import defaultdict

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models.invoice import Invoice
from ..schemas.invoice import (
    InvoiceResponse,
    InvoiceUpdate,
    InvoiceListResponse,
    SummaryResponse,
    CategorySummary,
    UploadResponse,
    VoucherGenerateRequest,
    VoucherGenerateResponse,
)
from ..services.glm_service import glm_service
from ..services.invoice_parser import classify_expense, detect_anomalies, parse_date
from ..services.voucher_service import generate_vouchers
from ..services.excel_export import create_invoice_excel
from ..config import UPLOAD_DIR, MAX_FILES_PER_BATCH

router = APIRouter(prefix="/api/invoices", tags=["invoices"])

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=UploadResponse)
async def upload_invoices(
    files: List[UploadFile] = File(...),
    reimbursement_person: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """批量上传发票图片"""
    if len(files) > MAX_FILES_PER_BATCH:
        raise HTTPException(
            status_code=400, detail=f"最多支持 {MAX_FILES_PER_BATCH} 张发票同时上传"
        )

    task_id = str(uuid.uuid4())
    processed = 0

    for file in files:
        if not file.filename:
            continue

        # Validate file type
        ext = file.filename.lower().split(".")[-1]
        if ext not in ["jpg", "jpeg", "png", "pdf"]:
            continue

        # Save file
        file_id = str(uuid.uuid4())
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}.{ext}")
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        # Recognize invoice
        result = glm_service.recognize_invoice(file_path)

        if result:
            # Parse date
            invoice_date = parse_date(result.get("invoice_date"))

            # Get expense category from GLM or auto-classify
            expense_category = result.get("expense_category")
            if not expense_category:
                expense_category = classify_expense(
                    result.get("seller_name", ""), result.get("items", [])
                )

            # Get reimbursement person from GLM (优先级: 经手人 > 领款人 > 传入参数)
            handler = result.get("handler")  # 经手人
            payee = result.get("payee")  # 领款人
            person = handler or payee or result.get("reimbursement_person") or reimbursement_person

            # Get amounts
            amount = float(result.get("amount") or 0)
            tax_amount = float(result.get("tax_amount") or 0)
            total_amount = float(result.get("total_amount") or amount + tax_amount)
            confidence = float(result.get("confidence") or 0.5)

            # Detect anomalies
            anomaly_flag, anomaly_reason = detect_anomalies(
                total_amount, invoice_date, confidence, result.get("invoice_no")
            )

            # Create invoice record
            invoice = Invoice(
                invoice_no=result.get("invoice_no"),
                invoice_date=invoice_date,
                invoice_type=result.get("invoice_type") or result.get("doc_type"),
                seller_name=result.get("seller_name"),
                seller_tax_no=result.get("seller_tax_no"),
                amount=amount,
                tax_amount=tax_amount,
                total_amount=total_amount,
                expense_category=expense_category,
                reimbursement_person=person,
                confidence=confidence,
                anomaly_flag=anomaly_flag,
                anomaly_reason=anomaly_reason,
                image_path=file_path,
                raw_response=result,
            )
            db.add(invoice)
            processed += 1
        else:
            # Create record with error
            invoice = Invoice(
                image_path=file_path,
                reimbursement_person=reimbursement_person,
                anomaly_flag="error",
                anomaly_reason="识别失败",
                confidence=0,
            )
            db.add(invoice)

    db.commit()

    return UploadResponse(
        task_id=task_id,
        total_count=len(files),
        processed=processed,
        message=f"成功处理 {processed}/{len(files)} 张发票",
    )


@router.get("", response_model=InvoiceListResponse)
def list_invoices(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    anomaly_only: bool = False,
    db: Session = Depends(get_db),
):
    """查询发票列表"""
    query = db.query(Invoice)

    if category:
        query = query.filter(Invoice.expense_category == category)

    if anomaly_only:
        query = query.filter(Invoice.anomaly_flag != "normal")

    total = query.count()
    items = (
        query.order_by(Invoice.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    return InvoiceListResponse(
        items=[InvoiceResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        size=size,
    )


@router.get("/summary", response_model=SummaryResponse)
def get_summary(db: Session = Depends(get_db)):
    """获取汇总统计"""
    # By category
    category_stats = (
        db.query(
            Invoice.expense_category,
            func.count(Invoice.id).label("count"),
            func.sum(Invoice.amount).label("amount"),
            func.sum(Invoice.tax_amount).label("tax"),
        )
        .group_by(Invoice.expense_category)
        .all()
    )

    by_category = [
        CategorySummary(
            category=stat[0] or "其他",
            count=stat[1],
            amount=round(stat[2] or 0, 2),
            tax_amount=round(stat[3] or 0, 2),
        )
        for stat in category_stats
    ]

    # Totals
    totals = db.query(
        func.count(Invoice.id),
        func.sum(Invoice.amount),
        func.sum(Invoice.tax_amount),
    ).first()

    anomaly_count = db.query(Invoice).filter(Invoice.anomaly_flag != "normal").count()

    return SummaryResponse(
        by_category=by_category,
        total_count=totals[0] or 0,
        total_amount=round(totals[1] or 0, 2),
        total_tax=round(totals[2] or 0, 2),
        anomaly_count=anomaly_count,
    )


@router.get("/export")
def export_excel(db: Session = Depends(get_db)):
    """导出 Excel 文件"""
    # Get all invoices
    invoices = db.query(Invoice).order_by(Invoice.created_at.desc()).all()
    invoice_responses = [InvoiceResponse.model_validate(i) for i in invoices]

    # Get summary
    category_stats = (
        db.query(
            Invoice.expense_category,
            func.count(Invoice.id).label("count"),
            func.sum(Invoice.amount).label("amount"),
            func.sum(Invoice.tax_amount).label("tax"),
        )
        .group_by(Invoice.expense_category)
        .all()
    )
    summary = [
        CategorySummary(
            category=stat[0] or "其他",
            count=stat[1],
            amount=round(stat[2] or 0, 2),
            tax_amount=round(stat[3] or 0, 2),
        )
        for stat in category_stats
    ]

    # Get anomalies
    anomalies = [i for i in invoice_responses if i.anomaly_flag != "normal"]

    # Generate vouchers
    today = date.today().isoformat()
    vouchers = generate_vouchers(invoice_responses, today)

    # Create Excel
    output = create_invoice_excel(invoice_responses, summary, anomalies, vouchers)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=invoices_{today}.xlsx"},
    )


@router.patch("/{invoice_id}", response_model=InvoiceResponse)
def update_invoice(
    invoice_id: str, update: InvoiceUpdate, db: Session = Depends(get_db)
):
    """更新发票信息（人工修正）"""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    for key, value in update.model_dump(exclude_unset=True).items():
        setattr(invoice, key, value)

    invoice.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(invoice)

    return InvoiceResponse.model_validate(invoice)


@router.post("/vouchers/generate", response_model=VoucherGenerateResponse)
def generate_voucher_entries(request: VoucherGenerateRequest, db: Session = Depends(get_db)):
    """生成凭证分录"""
    invoices = (
        db.query(Invoice).filter(Invoice.id.in_(request.invoice_ids)).all()
    )

    if not invoices:
        raise HTTPException(status_code=404, detail="未找到指定发票")

    invoice_responses = [InvoiceResponse.model_validate(i) for i in invoices]
    vouchers = generate_vouchers(
        invoice_responses, request.voucher_date, request.voucher_type, request.maker, request.department
    )

    total_debit = sum(v.金额 for v in vouchers if v.借贷方向 == "借")
    total_credit = sum(v.金额 for v in vouchers if v.借贷方向 == "贷")

    return VoucherGenerateResponse(
        vouchers=vouchers, total_debit=total_debit, total_credit=total_credit
    )


@router.delete("/{invoice_id}")
def delete_invoice(invoice_id: str, db: Session = Depends(get_db)):
    """删除发票"""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    # Delete file if exists
    if invoice.image_path and os.path.exists(invoice.image_path):
        os.remove(invoice.image_path)

    db.delete(invoice)
    db.commit()

    return {"message": "删除成功"}

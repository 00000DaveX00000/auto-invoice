from datetime import datetime
from typing import List
from collections import defaultdict

from ..schemas.invoice import VoucherEntry, InvoiceResponse
from .invoice_parser import get_account_code


def generate_vouchers(
    invoices: List[InvoiceResponse],
    voucher_date: str,
    voucher_type: str = "转",
    maker: str = "系统",
    department: str = "",
) -> List[VoucherEntry]:
    """
    根据发票列表生成凭证分录
    按费用科目分组，生成借贷分录
    """
    if not invoices:
        return []

    # 按费用科目分组
    category_totals = defaultdict(lambda: {
        "amount": 0,
        "tax": 0,
        "count": 0,
        "invoices": [],
        "sellers": set(),  # 收集销方名称
    })

    for inv in invoices:
        category = inv.expense_category or "其他"
        category_totals[category]["amount"] += inv.amount
        category_totals[category]["tax"] += inv.tax_amount
        category_totals[category]["count"] += 1
        category_totals[category]["invoices"].append(inv)
        if inv.seller_name:
            category_totals[category]["sellers"].add(inv.seller_name)

    vouchers = []
    voucher_no = 1
    year_month = voucher_date[:7].replace("-", "")

    # 生成借方分录（费用科目）
    for category, data in category_totals.items():
        account = get_account_code(category)
        total = data["amount"] + data["tax"]

        # 获取报销人信息
        reimbursement_person = ""
        employee_no = ""
        if data["invoices"]:
            reimbursement_person = data["invoices"][0].reimbursement_person or ""

        # 获取往来单位（销方）
        sellers_list = list(data["sellers"])
        vendor_name = sellers_list[0] if len(sellers_list) == 1 else f"{sellers_list[0]}等{len(sellers_list)}家" if sellers_list else ""

        voucher = VoucherEntry(
            编制日期=voucher_date,
            凭证类型=voucher_type,
            凭证序号=voucher_no,
            凭证号=str(voucher_no),
            制单人=maker,
            附件张数=data["count"],
            会计年度=year_month,
            科目编码=account["code"],
            科目名称=account["name"],
            凭证摘要=f"报销{voucher_date[:7]}{category}费用",
            借贷方向="借",
            金额=round(total, 2),
            币种="人民币",
            汇率=1.0,
            原币金额=round(total, 2),
            数量=None,
            单价=None,
            结算方式名称="",
            结算日期="",
            结算票号="",
            业务日期=voucher_date,
            员工编号=employee_no,
            员工姓名=reimbursement_person,
            往来单位编号="",
            往来单位名称=vendor_name,
            货品编号="",
            货品名称="",
            部门名称=department,
            项目名称="",
        )
        vouchers.append(voucher)

    # 生成贷方分录（其他应付款）
    total_amount = sum(d["amount"] + d["tax"] for d in category_totals.values())
    total_count = sum(d["count"] for d in category_totals.values())

    # 获取所有报销人
    all_persons = set()
    for data in category_totals.values():
        for inv in data["invoices"]:
            if inv.reimbursement_person:
                all_persons.add(inv.reimbursement_person)
    person_name = list(all_persons)[0] if len(all_persons) == 1 else f"{list(all_persons)[0]}等{len(all_persons)}人" if all_persons else ""

    credit_voucher = VoucherEntry(
        编制日期=voucher_date,
        凭证类型=voucher_type,
        凭证序号=voucher_no,
        凭证号=str(voucher_no),
        制单人=maker,
        附件张数=total_count,
        会计年度=year_month,
        科目编码="2241",
        科目名称="其他应付款-员工",
        凭证摘要=f"报销{voucher_date[:7]}费用",
        借贷方向="贷",
        金额=round(total_amount, 2),
        币种="人民币",
        汇率=1.0,
        原币金额=round(total_amount, 2),
        数量=None,
        单价=None,
        结算方式名称="",
        结算日期="",
        结算票号="",
        业务日期=voucher_date,
        员工编号="",
        员工姓名=person_name,
        往来单位编号="",
        往来单位名称="",
        货品编号="",
        货品名称="",
        部门名称=department,
        项目名称="",
    )
    vouchers.append(credit_voucher)

    return vouchers

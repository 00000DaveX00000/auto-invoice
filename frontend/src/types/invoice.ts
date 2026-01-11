export interface Invoice {
  id: string
  invoice_no: string | null
  invoice_date: string | null
  invoice_type: string | null
  seller_name: string | null
  seller_tax_no: string | null
  amount: number
  tax_amount: number
  total_amount: number
  expense_category: string | null
  reimbursement_person: string | null
  confidence: number
  anomaly_flag: string | null
  anomaly_reason: string | null
  image_path: string | null
  created_at: string
  updated_at: string
}

export interface InvoiceListResponse {
  items: Invoice[]
  total: number
  page: number
  size: number
}

export interface CategorySummary {
  category: string
  count: number
  amount: number
  tax_amount: number
}

export interface SummaryResponse {
  by_category: CategorySummary[]
  total_count: number
  total_amount: number
  total_tax: number
  anomaly_count: number
}

export interface UploadResponse {
  task_id: string
  total_count: number
  processed: number
  message: string
}

export interface VoucherEntry {
  编制日期: string
  凭证类型: string
  凭证序号: number
  凭证号: string
  制单人: string
  附件张数: number
  会计年度: string
  科目编码: string
  科目名称: string
  凭证摘要: string
  借贷方向: string
  金额: number
  币种: string
  汇率: number
  原币金额: number
  数量?: number | null
  单价?: number | null
  结算方式名称?: string | null
  结算日期?: string | null
  结算票号?: string | null
  业务日期?: string | null
  员工编号?: string | null
  员工姓名?: string | null
  往来单位编号?: string | null
  往来单位名称?: string | null
  货品编号?: string | null
  货品名称?: string | null
  部门名称?: string | null
  项目名称?: string | null
}

export interface VoucherGenerateResponse {
  vouchers: VoucherEntry[]
  total_debit: number
  total_credit: number
}

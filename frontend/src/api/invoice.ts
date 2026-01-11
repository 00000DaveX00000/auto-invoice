import axios from 'axios'
import type {
  Invoice,
  InvoiceListResponse,
  SummaryResponse,
  UploadResponse,
  VoucherGenerateResponse
} from '../types/invoice'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

export const invoiceApi = {
  // 上传发票
  async upload(files: File[], reimbursementPerson?: string): Promise<UploadResponse> {
    const formData = new FormData()
    files.forEach(file => {
      formData.append('files', file)
    })
    if (reimbursementPerson) {
      formData.append('reimbursement_person', reimbursementPerson)
    }
    const { data } = await api.post<UploadResponse>('/invoices/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return data
  },

  // 获取发票列表
  async list(params: {
    page?: number
    size?: number
    category?: string
    anomaly_only?: boolean
  } = {}): Promise<InvoiceListResponse> {
    const { data } = await api.get<InvoiceListResponse>('/invoices', { params })
    return data
  },

  // 获取汇总统计
  async getSummary(): Promise<SummaryResponse> {
    const { data } = await api.get<SummaryResponse>('/invoices/summary')
    return data
  },

  // 导出 Excel
  async exportExcel(): Promise<Blob> {
    const { data } = await api.get('/invoices/export', {
      responseType: 'blob'
    })
    return data
  },

  // 更新发票
  async update(id: string, updates: Partial<Invoice>): Promise<Invoice> {
    const { data } = await api.patch<Invoice>(`/invoices/${id}`, updates)
    return data
  },

  // 删除发票
  async delete(id: string): Promise<void> {
    await api.delete(`/invoices/${id}`)
  },

  // 生成凭证
  async generateVouchers(params: {
    invoice_ids: string[]
    voucher_date: string
    voucher_type?: string
    maker?: string
  }): Promise<VoucherGenerateResponse> {
    const { data } = await api.post<VoucherGenerateResponse>('/invoices/vouchers/generate', params)
    return data
  }
}

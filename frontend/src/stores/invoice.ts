import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Invoice, SummaryResponse, CategorySummary } from '../types/invoice'
import { invoiceApi } from '../api/invoice'

export const useInvoiceStore = defineStore('invoice', () => {
  const invoices = ref<Invoice[]>([])
  const total = ref(0)
  const page = ref(1)
  const size = ref(20)
  const loading = ref(false)
  const summary = ref<SummaryResponse | null>(null)
  const selectedIds = ref<string[]>([])
  const currentCategory = ref<string | null>(null)
  const anomalyOnly = ref(false)

  // Computed
  const selectedInvoices = computed(() =>
    invoices.value.filter(inv => selectedIds.value.includes(inv.id))
  )

  const selectedTotal = computed(() =>
    selectedInvoices.value.reduce((sum, inv) => sum + inv.total_amount, 0)
  )

  const selectedTax = computed(() =>
    selectedInvoices.value.reduce((sum, inv) => sum + inv.tax_amount, 0)
  )

  // Actions
  async function fetchInvoices() {
    loading.value = true
    try {
      const response = await invoiceApi.list({
        page: page.value,
        size: size.value,
        category: currentCategory.value || undefined,
        anomaly_only: anomalyOnly.value
      })
      invoices.value = response.items
      total.value = response.total
    } finally {
      loading.value = false
    }
  }

  async function fetchSummary() {
    summary.value = await invoiceApi.getSummary()
  }

  async function uploadFiles(files: File[], reimbursementPerson?: string) {
    loading.value = true
    try {
      const result = await invoiceApi.upload(files, reimbursementPerson)
      await fetchInvoices()
      await fetchSummary()
      return result
    } finally {
      loading.value = false
    }
  }

  async function exportExcel() {
    const blob = await invoiceApi.exportExcel()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `invoices_${new Date().toISOString().slice(0, 10)}.xlsx`
    a.click()
    URL.revokeObjectURL(url)
  }

  async function deleteInvoice(id: string) {
    await invoiceApi.delete(id)
    await fetchInvoices()
    await fetchSummary()
  }

  function setCategory(category: string | null) {
    currentCategory.value = category
    page.value = 1
    fetchInvoices()
  }

  function setAnomalyOnly(value: boolean) {
    anomalyOnly.value = value
    page.value = 1
    fetchInvoices()
  }

  function toggleSelect(id: string) {
    const index = selectedIds.value.indexOf(id)
    if (index === -1) {
      selectedIds.value.push(id)
    } else {
      selectedIds.value.splice(index, 1)
    }
  }

  function selectAll() {
    selectedIds.value = invoices.value.map(inv => inv.id)
  }

  function clearSelection() {
    selectedIds.value = []
  }

  return {
    invoices,
    total,
    page,
    size,
    loading,
    summary,
    selectedIds,
    selectedInvoices,
    selectedTotal,
    selectedTax,
    currentCategory,
    anomalyOnly,
    fetchInvoices,
    fetchSummary,
    uploadFiles,
    exportExcel,
    deleteInvoice,
    setCategory,
    setAnomalyOnly,
    toggleSelect,
    selectAll,
    clearSelection
  }
})

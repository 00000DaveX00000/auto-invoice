<template>
  <a-modal
    v-model:open="visible"
    title="生成凭证预览"
    width="900px"
    :footer="null"
  >
    <a-form layout="inline" style="margin-bottom: 16px">
      <a-form-item label="编制日期">
        <a-date-picker v-model:value="voucherDate" />
      </a-form-item>
      <a-form-item label="凭证类型">
        <a-select v-model:value="voucherType" style="width: 120px">
          <a-select-option value="转">转账凭证</a-select-option>
          <a-select-option value="收">收款凭证</a-select-option>
          <a-select-option value="付">付款凭证</a-select-option>
        </a-select>
      </a-form-item>
      <a-form-item label="制单人">
        <a-input v-model:value="maker" style="width: 100px" />
      </a-form-item>
      <a-form-item>
        <a-button type="primary" :loading="loading" @click="handleGenerate">
          生成凭证
        </a-button>
      </a-form-item>
    </a-form>

    <a-table
      v-if="vouchers.length > 0"
      :data-source="vouchers"
      :columns="columns"
      :pagination="false"
      size="small"
      bordered
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'amount'">
          {{ record.金额.toFixed(2) }}
        </template>
      </template>
      <template #summary>
        <a-table-summary :fixed="true">
          <a-table-summary-row>
            <a-table-summary-cell :col-span="4">合计</a-table-summary-cell>
            <a-table-summary-cell />
            <a-table-summary-cell :col-span="2">
              借方: ¥{{ totalDebit.toFixed(2) }}
            </a-table-summary-cell>
            <a-table-summary-cell :col-span="2">
              贷方: ¥{{ totalCredit.toFixed(2) }}
            </a-table-summary-cell>
          </a-table-summary-row>
        </a-table-summary>
      </template>
    </a-table>

    <div v-if="vouchers.length > 0" style="margin-top: 16px; text-align: right">
      <a-button type="primary" @click="handleExport">导出Excel (含凭证)</a-button>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { message } from 'ant-design-vue'
import dayjs, { Dayjs } from 'dayjs'
import type { TableColumnsType } from 'ant-design-vue'
import { invoiceApi } from '../api/invoice'
import { useInvoiceStore } from '../stores/invoice'
import type { VoucherEntry } from '../types/invoice'

const store = useInvoiceStore()
const visible = ref(false)
const loading = ref(false)
const vouchers = ref<VoucherEntry[]>([])
const totalDebit = ref(0)
const totalCredit = ref(0)
const voucherDate = ref<Dayjs>(dayjs())
const voucherType = ref('转')
const maker = ref('系统')

const columns: TableColumnsType = [
  { title: '科目编码', dataIndex: '科目编码', key: 'code', width: 100 },
  { title: '科目名称', dataIndex: '科目名称', key: 'name', width: 150 },
  { title: '凭证摘要', dataIndex: '凭证摘要', key: 'summary', width: 200 },
  { title: '借贷方向', dataIndex: '借贷方向', key: 'direction', width: 80 },
  { title: '金额', dataIndex: '金额', key: 'amount', width: 120, align: 'right' },
]

const open = () => {
  visible.value = true
  vouchers.value = []
}

const handleGenerate = async () => {
  if (store.selectedIds.length === 0) {
    message.warning('请先选择要生成凭证的发票')
    return
  }

  loading.value = true
  try {
    const result = await invoiceApi.generateVouchers({
      invoice_ids: store.selectedIds,
      voucher_date: voucherDate.value.format('YYYY-MM-DD'),
      voucher_type: voucherType.value,
      maker: maker.value,
    })
    vouchers.value = result.vouchers
    totalDebit.value = result.total_debit
    totalCredit.value = result.total_credit
    message.success('凭证生成成功')
  } catch (error: any) {
    message.error(error.response?.data?.detail || '生成失败')
  } finally {
    loading.value = false
  }
}

const handleExport = () => {
  store.exportExcel()
}

defineExpose({ open })
</script>

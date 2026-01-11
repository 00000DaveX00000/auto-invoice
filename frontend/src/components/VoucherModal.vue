<template>
  <a-modal
    v-model:open="visible"
    title="生成凭证预览"
    width="100%"
    :style="{ top: '20px', maxWidth: '1400px' }"
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
      <a-form-item label="部门">
        <a-input v-model:value="department" style="width: 120px" placeholder="可选" />
      </a-form-item>
      <a-form-item>
        <a-button type="primary" :loading="loading" @click="handleGenerate">
          生成凭证
        </a-button>
      </a-form-item>
    </a-form>

    <div v-if="vouchers.length > 0" style="overflow-x: auto;">
      <a-table
        :data-source="vouchers"
        :columns="columns"
        :pagination="false"
        size="small"
        bordered
        :scroll="{ x: 2800 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === '金额' || column.key === '原币金额'">
            {{ record[column.dataIndex]?.toFixed(2) || '' }}
          </template>
          <template v-else-if="column.key === '汇率'">
            {{ record[column.dataIndex] || 1 }}
          </template>
        </template>
        <template #summary>
          <a-table-summary :fixed="true">
            <a-table-summary-row>
              <a-table-summary-cell :col-span="11">合计</a-table-summary-cell>
              <a-table-summary-cell>
                借方: ¥{{ totalDebit.toFixed(2) }}
              </a-table-summary-cell>
              <a-table-summary-cell :col-span="17">
                贷方: ¥{{ totalCredit.toFixed(2) }}
              </a-table-summary-cell>
            </a-table-summary-row>
          </a-table-summary>
        </template>
      </a-table>
    </div>

    <div v-if="vouchers.length > 0" style="margin-top: 16px; text-align: right">
      <a-button type="primary" @click="handleExport">导出Excel (含凭证)</a-button>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { ref } from 'vue'
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
const department = ref('')

// 完整的29个字段列定义
const columns: TableColumnsType = [
  { title: '编制日期', dataIndex: '编制日期', key: '编制日期', width: 100, fixed: 'left' },
  { title: '凭证类型', dataIndex: '凭证类型', key: '凭证类型', width: 80 },
  { title: '凭证序号', dataIndex: '凭证序号', key: '凭证序号', width: 80 },
  { title: '凭证号', dataIndex: '凭证号', key: '凭证号', width: 80 },
  { title: '制单人', dataIndex: '制单人', key: '制单人', width: 80 },
  { title: '附件张数', dataIndex: '附件张数', key: '附件张数', width: 80 },
  { title: '会计年度', dataIndex: '会计年度', key: '会计年度', width: 80 },
  { title: '科目编码', dataIndex: '科目编码', key: '科目编码', width: 100 },
  { title: '科目名称', dataIndex: '科目名称', key: '科目名称', width: 150 },
  { title: '凭证摘要', dataIndex: '凭证摘要', key: '凭证摘要', width: 180 },
  { title: '借贷方向', dataIndex: '借贷方向', key: '借贷方向', width: 80 },
  { title: '金额', dataIndex: '金额', key: '金额', width: 100, align: 'right' },
  { title: '币种', dataIndex: '币种', key: '币种', width: 80 },
  { title: '汇率', dataIndex: '汇率', key: '汇率', width: 60 },
  { title: '原币金额', dataIndex: '原币金额', key: '原币金额', width: 100, align: 'right' },
  { title: '数量', dataIndex: '数量', key: '数量', width: 80 },
  { title: '单价', dataIndex: '单价', key: '单价', width: 80 },
  { title: '结算方式', dataIndex: '结算方式名称', key: '结算方式名称', width: 100 },
  { title: '结算日期', dataIndex: '结算日期', key: '结算日期', width: 100 },
  { title: '结算票号', dataIndex: '结算票号', key: '结算票号', width: 100 },
  { title: '业务日期', dataIndex: '业务日期', key: '业务日期', width: 100 },
  { title: '员工编号', dataIndex: '员工编号', key: '员工编号', width: 100 },
  { title: '员工姓名', dataIndex: '员工姓名', key: '员工姓名', width: 100 },
  { title: '往来单位编号', dataIndex: '往来单位编号', key: '往来单位编号', width: 120 },
  { title: '往来单位名称', dataIndex: '往来单位名称', key: '往来单位名称', width: 150 },
  { title: '货品编号', dataIndex: '货品编号', key: '货品编号', width: 100 },
  { title: '货品名称', dataIndex: '货品名称', key: '货品名称', width: 100 },
  { title: '部门名称', dataIndex: '部门名称', key: '部门名称', width: 100 },
  { title: '项目名称', dataIndex: '项目名称', key: '项目名称', width: 100 },
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
      department: department.value,
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

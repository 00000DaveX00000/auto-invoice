<template>
  <a-table
    :data-source="store.invoices"
    :columns="columns"
    :loading="store.loading"
    :pagination="pagination"
    :row-selection="rowSelection"
    row-key="id"
    @change="handleTableChange"
    size="middle"
  >
    <template #bodyCell="{ column, record }">
      <template v-if="column.key === 'invoice_date'">
        {{ record.invoice_date || '-' }}
      </template>
      <template v-else-if="column.key === 'amount'">
        ¥{{ record.amount.toFixed(2) }}
      </template>
      <template v-else-if="column.key === 'tax_amount'">
        ¥{{ record.tax_amount.toFixed(2) }}
      </template>
      <template v-else-if="column.key === 'total_amount'">
        ¥{{ record.total_amount.toFixed(2) }}
      </template>
      <template v-else-if="column.key === 'confidence'">
        <a-progress
          :percent="Math.round(record.confidence * 100)"
          :stroke-color="record.confidence >= 0.9 ? '#52c41a' : '#faad14'"
          size="small"
          :show-info="true"
        />
      </template>
      <template v-else-if="column.key === 'status'">
        <a-tag :color="getStatusColor(record.anomaly_flag)">
          {{ getStatusText(record.anomaly_flag) }}
        </a-tag>
      </template>
      <template v-else-if="column.key === 'action'">
        <a-space>
          <a-popconfirm
            title="确定删除这张发票吗？"
            @confirm="handleDelete(record.id)"
          >
            <a-button type="link" danger size="small">删除</a-button>
          </a-popconfirm>
        </a-space>
      </template>
    </template>
  </a-table>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { TableColumnsType, TableProps } from 'ant-design-vue'
import { useInvoiceStore } from '../stores/invoice'
import type { Invoice } from '../types/invoice'

const store = useInvoiceStore()

const columns: TableColumnsType = [
  { title: '发票号', dataIndex: 'invoice_no', key: 'invoice_no', width: 180, ellipsis: true },
  { title: '日期', dataIndex: 'invoice_date', key: 'invoice_date', width: 110 },
  { title: '类型', dataIndex: 'invoice_type', key: 'invoice_type', width: 100 },
  { title: '销方名称', dataIndex: 'seller_name', key: 'seller_name', width: 150, ellipsis: true },
  { title: '金额', dataIndex: 'amount', key: 'amount', width: 100, align: 'right' },
  { title: '税额', dataIndex: 'tax_amount', key: 'tax_amount', width: 80, align: 'right' },
  { title: '价税合计', dataIndex: 'total_amount', key: 'total_amount', width: 100, align: 'right' },
  { title: '费用科目', dataIndex: 'expense_category', key: 'expense_category', width: 100 },
  { title: '报销人', dataIndex: 'reimbursement_person', key: 'reimbursement_person', width: 80 },
  { title: '置信度', dataIndex: 'confidence', key: 'confidence', width: 120 },
  { title: '状态', dataIndex: 'anomaly_flag', key: 'status', width: 80 },
  { title: '异常原因', dataIndex: 'anomaly_reason', key: 'anomaly_reason', width: 150, ellipsis: true },
  { title: '操作', key: 'action', width: 80, fixed: 'right' },
]

const pagination = computed(() => ({
  current: store.page,
  pageSize: store.size,
  total: store.total,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number) => `共 ${total} 条`,
}))

const rowSelection = computed(() => ({
  selectedRowKeys: store.selectedIds,
  onChange: (keys: string[]) => {
    store.selectedIds = keys
  },
}))

const handleTableChange: TableProps['onChange'] = (pag) => {
  store.page = pag.current || 1
  store.size = pag.pageSize || 20
  store.fetchInvoices()
}

const handleDelete = async (id: string) => {
  await store.deleteInvoice(id)
}

const getStatusColor = (flag: string | null) => {
  if (flag === 'normal') return 'success'
  if (flag === 'warning') return 'warning'
  return 'error'
}

const getStatusText = (flag: string | null) => {
  if (flag === 'normal') return '正常'
  if (flag === 'warning') return '警告'
  return '异常'
}
</script>

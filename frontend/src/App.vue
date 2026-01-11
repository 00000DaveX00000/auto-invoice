<template>
  <a-layout class="layout">
    <a-layout-header class="header">
      <div class="logo">出纳发票识别系统</div>
      <a-space>
        <a-button type="primary" @click="openVoucherModal" :disabled="store.selectedIds.length === 0">
          生成凭证
        </a-button>
        <a-button @click="handleExport">导出Excel</a-button>
      </a-space>
    </a-layout-header>

    <a-layout-content class="content">
      <a-card title="上传发票" style="margin-bottom: 16px">
        <InvoiceUpload />
      </a-card>

      <a-card title="发票列表">
        <SummaryPanel />
        <InvoiceTable />
      </a-card>
    </a-layout-content>

    <VoucherModal ref="voucherModalRef" />
  </a-layout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import InvoiceUpload from './components/InvoiceUpload.vue'
import InvoiceTable from './components/InvoiceTable.vue'
import SummaryPanel from './components/SummaryPanel.vue'
import VoucherModal from './components/VoucherModal.vue'
import { useInvoiceStore } from './stores/invoice'

const store = useInvoiceStore()
const voucherModalRef = ref<InstanceType<typeof VoucherModal>>()

onMounted(() => {
  store.fetchInvoices()
  store.fetchSummary()
})

const openVoucherModal = () => {
  voucherModalRef.value?.open()
}

const handleExport = () => {
  store.exportExcel()
}
</script>

<style>
.layout {
  min-height: 100vh;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #001529;
  padding: 0 24px;
}

.logo {
  color: white;
  font-size: 18px;
  font-weight: bold;
}

.content {
  padding: 24px;
  background: #f0f2f5;
}
</style>

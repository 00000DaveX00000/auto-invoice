<template>
  <div class="summary-panel">
    <a-row :gutter="16">
      <a-col :span="6">
        <a-statistic title="发票总数" :value="store.summary?.total_count || 0">
          <template #suffix>张</template>
        </a-statistic>
      </a-col>
      <a-col :span="6">
        <a-statistic
          title="合计金额"
          :value="store.summary?.total_amount || 0"
          :precision="2"
          prefix="¥"
        />
      </a-col>
      <a-col :span="6">
        <a-statistic
          title="合计税额"
          :value="store.summary?.total_tax || 0"
          :precision="2"
          prefix="¥"
        />
      </a-col>
      <a-col :span="6">
        <a-statistic
          title="异常发票"
          :value="store.summary?.anomaly_count || 0"
          :value-style="{ color: (store.summary?.anomaly_count || 0) > 0 ? '#cf1322' : '#3f8600' }"
        >
          <template #suffix>张</template>
        </a-statistic>
      </a-col>
    </a-row>

    <a-divider />

    <div class="category-tabs">
      <a-space wrap>
        <a-tag
          :color="!store.currentCategory && !store.anomalyOnly ? 'blue' : 'default'"
          style="cursor: pointer"
          @click="handleCategoryClick(null)"
        >
          全部 ({{ store.summary?.total_count || 0 }})
        </a-tag>
        <a-tag
          v-for="item in store.summary?.by_category"
          :key="item.category"
          :color="store.currentCategory === item.category ? 'blue' : 'default'"
          style="cursor: pointer"
          @click="handleCategoryClick(item.category)"
        >
          {{ item.category }} ({{ item.count }})
        </a-tag>
        <a-tag
          :color="store.anomalyOnly ? 'red' : 'default'"
          style="cursor: pointer"
          @click="handleAnomalyClick"
        >
          异常 ({{ store.summary?.anomaly_count || 0 }})
        </a-tag>
      </a-space>
    </div>

    <a-divider v-if="store.selectedIds.length > 0" />

    <div v-if="store.selectedIds.length > 0" class="selection-info">
      <a-alert type="info" show-icon>
        <template #message>
          已选 {{ store.selectedIds.length }} 张 |
          合计 ¥{{ store.selectedTotal.toFixed(2) }} |
          税额 ¥{{ store.selectedTax.toFixed(2) }}
        </template>
      </a-alert>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useInvoiceStore } from '../stores/invoice'

const store = useInvoiceStore()

const handleCategoryClick = (category: string | null) => {
  store.setAnomalyOnly(false)
  store.setCategory(category)
}

const handleAnomalyClick = () => {
  store.setCategory(null)
  store.setAnomalyOnly(!store.anomalyOnly)
}
</script>

<style scoped>
.summary-panel {
  padding: 16px 0;
}

.category-tabs {
  margin-top: 8px;
}

.selection-info {
  margin-top: 8px;
}
</style>

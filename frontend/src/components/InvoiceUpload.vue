<template>
  <a-upload-dragger
    v-model:file-list="fileList"
    name="files"
    :multiple="true"
    :before-upload="beforeUpload"
    :show-upload-list="true"
    accept=".jpg,.jpeg,.png,.pdf"
    @remove="handleRemove"
  >
    <p class="ant-upload-drag-icon">
      <inbox-outlined />
    </p>
    <p class="ant-upload-text">拖拽上传发票图片 或 点击选择文件</p>
    <p class="ant-upload-hint">
      支持 JPG/PNG/PDF，最多 200 张
    </p>
  </a-upload-dragger>

  <div v-if="fileList.length > 0" style="margin-top: 16px">
    <a-space>
      <a-input
        v-model:value="reimbursementPerson"
        placeholder="报销人姓名"
        style="width: 150px"
      />
      <a-button type="primary" :loading="uploading" @click="handleUpload">
        开始识别 ({{ fileList.length }} 张)
      </a-button>
      <a-button @click="clearFiles">清空</a-button>
    </a-space>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { InboxOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import type { UploadFile } from 'ant-design-vue'
import { useInvoiceStore } from '../stores/invoice'

const store = useInvoiceStore()
const fileList = ref<UploadFile[]>([])
const uploading = ref(false)
const reimbursementPerson = ref('')

const beforeUpload = (file: File) => {
  const isValidType = ['image/jpeg', 'image/png', 'application/pdf'].includes(file.type)
  if (!isValidType) {
    message.error('只支持 JPG/PNG/PDF 格式')
    return false
  }
  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isLt10M) {
    message.error('文件大小不能超过 10MB')
    return false
  }
  return false // Prevent auto upload
}

const handleRemove = (file: UploadFile) => {
  const index = fileList.value.indexOf(file)
  if (index > -1) {
    fileList.value.splice(index, 1)
  }
}

const handleUpload = async () => {
  if (fileList.value.length === 0) {
    message.warning('请先选择发票图片')
    return
  }

  uploading.value = true
  try {
    const files = fileList.value.map(f => f.originFileObj as File)
    const result = await store.uploadFiles(files, reimbursementPerson.value || undefined)
    message.success(result.message)
    fileList.value = []
    reimbursementPerson.value = ''
  } catch (error: any) {
    message.error(error.response?.data?.detail || '上传失败')
  } finally {
    uploading.value = false
  }
}

const clearFiles = () => {
  fileList.value = []
}
</script>

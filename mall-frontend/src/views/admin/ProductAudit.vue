<template>
  <div class="page-container">
    <!-- 页面标题 -->
    <h2 class="page-title">商品审核</h2>

    <!-- 待审核 / 已审核 标签页 -->
    <div class="page-card">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="待审核" name="pending" />
        <el-tab-pane label="已审核" name="reviewed" />
      </el-tabs>

      <!-- 商品表格 -->
      <el-table :data="productList" v-loading="loading" stripe border style="width: 100%">
        <el-table-column prop="id" label="ID" width="70" align="center" />
        <el-table-column prop="name" label="商品名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="price" label="价格" width="100" align="center">
          <template #default="{ row }">
            <span class="price">¥{{ row.price }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="merchant_name" label="商家" min-width="140" />
        <el-table-column prop="submitted_at" label="提交时间" min-width="170" />
        <!-- 已审核状态下显示审核结果列 -->
        <el-table-column
          v-if="activeTab === 'reviewed'"
          prop="audit_status"
          label="审核结果"
          width="100"
          align="center"
        >
          <template #default="{ row }">
            <el-tag :type="row.audit_status === 'approved' ? 'success' : 'danger'">
              {{ row.audit_status === 'approved' ? '通过' : '拒绝' }}
            </el-tag>
          </template>
        </el-table-column>
        <!-- 已审核状态下显示审核原因列 -->
        <el-table-column
          v-if="activeTab === 'reviewed'"
          prop="reject_reason"
          label="拒绝原因"
          min-width="180"
          show-overflow-tooltip
        />
        <!-- 操作列：仅待审核状态下显示审核按钮 -->
        <el-table-column
          v-if="activeTab === 'pending'"
          label="操作"
          width="200"
          align="center"
          fixed="right"
        >
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button type="success" size="small" @click="handleApprove(row)">
                审核通过
              </el-button>
              <el-button type="danger" size="small" @click="handleReject(row)">
                审核拒绝
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchProductList"
          @current-change="fetchProductList"
        />
      </div>
    </div>

    <!-- 拒绝原因弹窗 -->
    <el-dialog v-model="rejectDialogVisible" title="审核拒绝" width="500px">
      <el-form label-width="80px">
        <el-form-item label="商品名称">
          <el-input :model-value="currentProduct.name" disabled />
        </el-form-item>
        <el-form-item label="拒绝原因">
          <el-input
            v-model="rejectForm.reason"
            type="textarea"
            :rows="4"
            placeholder="请输入拒绝原因"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rejectDialogVisible = false">取消</el-button>
        <el-button type="danger" :loading="rejectLoading" @click="submitReject">确认拒绝</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/api/request'

// ========== 当前标签页 ==========
const activeTab = ref('pending')

// ========== 分页 ==========
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

// ========== 表格数据 ==========
const productList = ref([])
const loading = ref(false)

// ========== 获取商品列表 ==========
const fetchProductList = async () => {
  loading.value = true
  try {
    const { data } = await request.get('/admin/products/audit/', {
      params: {
        page: pagination.page,
        page_size: pagination.pageSize,
        status: activeTab.value
      }
    })
    productList.value = data.results || data
    pagination.total = data.count || 0
  } catch {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}

// ========== 切换标签页 ==========
const handleTabChange = () => {
  pagination.page = 1
  fetchProductList()
}

// ========== 审核通过 ==========
const handleApprove = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确认通过商品「${row.name}」的审核？`,
      '审核通过',
      { type: 'success' }
    )
    await request.post(`/admin/products/${row.id}/audit/`, {
      action: 'approve'
    })
    ElMessage.success('审核通过')
    fetchProductList()
  } catch {
    // 用户取消或请求失败
  }
}

// ========== 审核拒绝 ==========
const rejectDialogVisible = ref(false)
const rejectLoading = ref(false)
const currentProduct = ref({})
const rejectForm = reactive({ reason: '' })

const handleReject = (row) => {
  currentProduct.value = row
  rejectForm.reason = ''
  rejectDialogVisible.value = true
}

const submitReject = async () => {
  if (!rejectForm.reason.trim()) {
    ElMessage.warning('请输入拒绝原因')
    return
  }
  rejectLoading.value = true
  try {
    await request.post(`/admin/products/${currentProduct.value.id}/audit/`, {
      action: 'reject',
      reason: rejectForm.reason
    })
    ElMessage.success('已拒绝')
    rejectDialogVisible.value = false
    fetchProductList()
  } catch {
    // 错误已在拦截器中处理
  } finally {
    rejectLoading.value = false
  }
}

// ========== 初始化 ==========
onMounted(() => {
  fetchProductList()
})
</script>

<style scoped>
.page-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 20px;
}
</style>

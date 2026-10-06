<template>
  <div class="page-container">
    <!-- 页面标题 -->
    <h2 class="page-title">订单管理</h2>

    <!-- 状态标签页 -->
    <div class="page-card">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="全部" name="all" />
        <el-tab-pane label="待支付" name="unpaid" />
        <el-tab-pane label="已支付" name="paid" />
        <el-tab-pane label="待发货" name="pending_ship" />
        <el-tab-pane label="已发货" name="shipped" />
        <el-tab-pane label="已完成" name="completed" />
      </el-tabs>

      <!-- 订单表格 -->
      <el-table :data="orderList" v-loading="loading" stripe border style="width: 100%">
        <el-table-column prop="order_no" label="订单号" min-width="180" />
        <el-table-column prop="username" label="下单用户" min-width="120" />
        <!-- 商品信息列：展示商品名和数量 -->
        <el-table-column label="商品信息" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">
            <div v-for="item in row.items" :key="item.id" class="order-item-info">
              <span>{{ item.product_name }}</span>
              <span class="order-item-qty">x{{ item.quantity }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="total_amount" label="总金额" width="110" align="center">
          <template #default="{ row }">
            <span class="price">¥{{ row.total_amount }}</span>
          </template>
        </el-table-column>
        <!-- 状态列 -->
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="下单时间" min-width="170" />
        <!-- 操作列：仅待发货状态显示发货按钮 -->
        <el-table-column label="操作" width="100" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'paid'"
              type="primary"
              size="small"
              @click="handleShip(row)"
            >
              发货
            </el-button>
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
          @size-change="fetchOrderList"
          @current-change="fetchOrderList"
        />
      </div>
    </div>

    <!-- 发货弹窗 -->
    <el-dialog v-model="shipDialogVisible" title="订单发货" width="480px">
      <el-form
        ref="shipFormRef"
        :model="shipForm"
        :rules="shipRules"
        label-width="100px"
      >
        <el-form-item label="订单号">
          <el-input :model-value="currentOrder.order_no" disabled />
        </el-form-item>
        <el-form-item label="物流公司" prop="shipping_company">
          <el-input v-model="shipForm.shipping_company" placeholder="请输入物流公司名称" />
        </el-form-item>
        <el-form-item label="物流单号" prop="tracking_number">
          <el-input v-model="shipForm.tracking_number" placeholder="请输入物流单号" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="shipDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="shipLoading" @click="submitShip">确认发货</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'

// ========== 当前标签页 ==========
const activeTab = ref('all')

// ========== 分页 ==========
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

// ========== 表格数据 ==========
const orderList = ref([])
const loading = ref(false)

// ========== 获取订单列表（商家视角） ==========
const fetchOrderList = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize
    }
    // 非"全部"标签时传状态筛选
    if (activeTab.value !== 'all') {
      params.status = activeTab.value
    }
    const { data } = await request.get('/merchant/orders/', { params })
    orderList.value = data.results || data
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
  fetchOrderList()
}

// ========== 状态映射 ==========
const statusTagType = (status) => {
  const map = {
    unpaid: 'info',
    paid: 'warning',
    pending_ship: 'warning',
    shipped: '',
    completed: 'success',
    cancelled: 'danger'
  }
  return map[status] || 'info'
}

const statusLabel = (status) => {
  const map = {
    unpaid: '待支付',
    paid: '已支付',
    pending_ship: '待发货',
    shipped: '已发货',
    completed: '已完成',
    cancelled: '已取消'
  }
  return map[status] || status
}

// ========== 发货相关 ==========
const shipDialogVisible = ref(false)
const shipLoading = ref(false)
const currentOrder = ref({})
const shipFormRef = ref(null)

const shipForm = reactive({
  shipping_company: '',
  tracking_number: ''
})

const shipRules = {
  shipping_company: [{ required: true, message: '请输入物流公司', trigger: 'blur' }],
  tracking_number: [{ required: true, message: '请输入物流单号', trigger: 'blur' }]
}

// 打开发货弹窗
const handleShip = (row) => {
  currentOrder.value = row
  shipForm.shipping_company = ''
  shipForm.tracking_number = ''
  shipDialogVisible.value = true
}

// 提交发货
const submitShip = async () => {
  if (!shipFormRef.value) return
  await shipFormRef.value.validate()
  shipLoading.value = true
  try {
    await request.post(`/merchant/orders/${currentOrder.value.id}/ship/`, {
      shipping_company: shipForm.shipping_company,
      tracking_number: shipForm.tracking_number
    })
    ElMessage.success('发货成功')
    shipDialogVisible.value = false
    fetchOrderList()
  } catch {
    // 错误已在拦截器中处理
  } finally {
    shipLoading.value = false
  }
}

// ========== 初始化 ==========
onMounted(() => {
  fetchOrderList()
})
</script>

<style scoped>
.page-title {
  font-size: 22px;
  font-weight: 700;
  color: #1f2329;
  margin-bottom: 20px;
}

/* 订单商品信息 */
.order-item-info {
  line-height: 1.6;
}

.order-item-qty {
  color: #909399;
  margin-left: 8px;
}

:deep(.el-tabs__active-bar) {
  background-color: #e5482f;
}

:deep(.el-tabs__item.is-active),
:deep(.el-tabs__item:hover) {
  color: #1f2329;
}
</style>

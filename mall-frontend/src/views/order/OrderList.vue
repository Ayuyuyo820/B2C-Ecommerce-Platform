<template>
  <!-- 我的订单页面 -->
  <div class="page-container">
    <div class="page-card">
      <!-- 状态标签页 -->
      <el-tabs v-model="activeStatus" @tab-change="handleTabChange">
        <el-tab-pane label="全部" name="" />
        <el-tab-pane label="待支付" name="pending" />
        <el-tab-pane label="已支付" name="paid" />
        <el-tab-pane label="已发货" name="shipped" />
        <el-tab-pane label="已完成" name="completed" />
        <el-tab-pane label="已取消" name="cancelled" />
      </el-tabs>

      <!-- 加载状态 -->
      <el-skeleton :loading="loading" animated :rows="6" v-if="loading" />

      <!-- 订单列表为空 -->
      <el-empty v-else-if="orderList.length === 0" description="暂无订单" />

      <!-- 订单卡片列表 -->
      <div v-else class="order-list">
        <div
          v-for="order in orderList"
          :key="order.id"
          class="order-card"
          @click="goDetail(order.id)"
        >
          <!-- 订单头部：订单号 + 状态 + 时间 -->
          <div class="order-header">
            <div class="order-header-left">
              <span class="order-no">订单号：{{ order.order_no }}</span>
              <span class="merchant-name">
                <el-icon><Shop /></el-icon>
                {{ order.merchant?.username }}
              </span>
            </div>
            <div class="order-header-right">
              <el-tag :type="statusTagType(order.status)" size="small">
                {{ order.status_display }}
              </el-tag>
              <span class="create-time">{{ formatTime(order.create_time) }}</span>
            </div>
          </div>

          <!-- 订单商品列表 -->
          <div class="order-items">
            <div
              v-for="(item, idx) in order.items"
              :key="idx"
              class="order-item"
            >
              <el-image
                :src="item.product_image"
                fit="cover"
                class="item-image"
              >
                <template #error>
                  <div class="image-placeholder">
                    <el-icon><Picture /></el-icon>
                  </div>
                </template>
              </el-image>
              <div class="item-info">
                <div class="item-name">{{ item.product_name }}</div>
                <div class="item-price-qty">
                  <span class="price">¥{{ item.price }}</span>
                  <span class="qty">x{{ item.quantity }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 订单底部：总金额 + 操作按钮 -->
          <div class="order-footer" @click.stop>
            <div class="total-amount">
              共 {{ totalQty(order.items) }} 件，合计：
              <span class="price">¥{{ order.total_amount }}</span>
            </div>
            <div class="action-buttons">
              <!-- 待支付：去支付 + 取消订单 -->
              <template v-if="order.status === 'pending'">
                <el-button type="primary" size="small" @click.stop="handlePay(order)">
                  去支付
                </el-button>
                <el-button size="small" @click.stop="handleCancel(order)">
                  取消订单
                </el-button>
              </template>
              <!-- 已发货：确认收货 -->
              <el-button
                v-if="order.status === 'shipped'"
                type="success"
                size="small"
                @click.stop="handleConfirm(order)"
              >
                确认收货
              </el-button>
              <!-- 已完成：去评价（如果未评价） -->
              <el-button
                v-if="order.status === 'completed' && !order.is_reviewed"
                type="warning"
                size="small"
                @click.stop="goReview(order.id)"
              >
                去评价
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div class="pagination-wrapper" v-if="total > 0">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[5, 10, 20]"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="fetchOrders"
          @size-change="handleSizeChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Shop, Picture } from '@element-plus/icons-vue'
import { getOrderList, payOrder, cancelOrder, confirmOrder } from '@/api/order'

const router = useRouter()

// 当前筛选状态
const activeStatus = ref('')
// 订单列表
const orderList = ref([])
// 加载状态
const loading = ref(false)
// 分页
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

// 状态标签颜色映射
const statusTagType = (status) => {
  const map = {
    pending: 'warning',
    paid: 'primary',
    shipped: 'info',
    completed: 'success',
    cancelled: 'info'
  }
  return map[status] || 'info'
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return ''
  return time.replace('T', ' ').slice(0, 16)
}

// 计算订单商品总数量
const totalQty = (items) => {
  return (items || []).reduce((sum, item) => sum + item.quantity, 0)
}

// 获取订单列表
const fetchOrders = async () => {
  loading.value = true
  try {
    const { data } = await getOrderList({
      page: page.value,
      page_size: pageSize.value,
      status: activeStatus.value || undefined
    })
    orderList.value = data.results
    total.value = data.count
  } catch (e) {
    // 拦截器已处理错误提示
  } finally {
    loading.value = false
  }
}

// 切换状态标签
const handleTabChange = () => {
  page.value = 1
  fetchOrders()
}

// 每页条数变化
const handleSizeChange = () => {
  page.value = 1
  fetchOrders()
}

// 跳转订单详情
const goDetail = (id) => {
  router.push(`/order/${id}`)
}

// 跳转评价页
const goReview = (orderId) => {
  router.push(`/review/${orderId}`)
}

// 去支付
const handlePay = async (order) => {
  try {
    await ElMessageBox.confirm('确定要支付该订单吗？', '确认支付', { type: 'info' })
    await payOrder(order.id)
    ElMessage.success('支付成功')
    fetchOrders()
  } catch {
    // 用户取消或请求失败
  }
}

// 取消订单
const handleCancel = async (order) => {
  try {
    await ElMessageBox.confirm('确定要取消该订单吗？取消后不可恢复。', '取消订单', {
      type: 'warning'
    })
    await cancelOrder(order.id)
    ElMessage.success('订单已取消')
    fetchOrders()
  } catch {
    // 用户取消或请求失败
  }
}

// 确认收货
const handleConfirm = async (order) => {
  try {
    await ElMessageBox.confirm('确认已收到商品？', '确认收货', { type: 'info' })
    await confirmOrder(order.id)
    ElMessage.success('已确认收货')
    fetchOrders()
  } catch {
    // 用户取消或请求失败
  }
}

onMounted(() => {
  fetchOrders()
})
</script>

<style scoped>
.order-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.order-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 16px 20px;
  cursor: pointer;
  transition: box-shadow 0.2s;
}

.order-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* 订单头部 */
.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
  flex-wrap: wrap;
  gap: 8px;
}

.order-header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.order-no {
  font-size: 14px;
  color: #606266;
}

.merchant-name {
  font-size: 13px;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 4px;
}

.order-header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.create-time {
  font-size: 13px;
  color: #909399;
}

/* 订单商品 */
.order-items {
  padding: 12px 0;
}

.order-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
}

.item-image {
  width: 60px;
  height: 60px;
  border-radius: 4px;
  flex-shrink: 0;
}

.image-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  color: #c0c4cc;
  font-size: 20px;
}

.item-info {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.item-name {
  font-size: 14px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 400px;
}

.item-price-qty {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.qty {
  font-size: 13px;
  color: #909399;
}

/* 订单底部 */
.order-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
  flex-wrap: wrap;
  gap: 8px;
}

.total-amount {
  font-size: 14px;
  color: #606266;
}

.total-amount .price {
  font-size: 16px;
}

/* 分页 */
.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>

<template>
  <!-- 订单详情页面 -->
  <div class="page-container">
    <!-- 面包屑导航 -->
    <el-breadcrumb separator="/">
      <el-breadcrumb-item :to="{ path: '/orders' }">我的订单</el-breadcrumb-item>
      <el-breadcrumb-item>订单详情</el-breadcrumb-item>
    </el-breadcrumb>

    <!-- 加载状态 -->
    <el-skeleton :loading="loading" animated :rows="10" v-if="loading" />

    <template v-else-if="order">
      <!-- 订单信息卡片 -->
      <div class="page-card">
        <div class="section-title">订单信息</div>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="订单号">{{ order.order_no }}</el-descriptions-item>
          <el-descriptions-item label="订单状态">
            <el-tag :type="statusTagType(order.status)">
              {{ order.status_display }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="下单时间">{{ formatTime(order.create_time) }}</el-descriptions-item>
          <el-descriptions-item label="支付时间">{{ formatTime(order.pay_time) || '—' }}</el-descriptions-item>
          <el-descriptions-item label="发货时间">{{ formatTime(order.ship_time) || '—' }}</el-descriptions-item>
          <el-descriptions-item label="完成时间">{{ formatTime(order.complete_time) || '—' }}</el-descriptions-item>
          <el-descriptions-item label="商家">{{ order.merchant?.username }}</el-descriptions-item>
          <el-descriptions-item label="备注">{{ order.remark || '无' }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 收货地址卡片 -->
      <div class="page-card" v-if="order.address">
        <div class="section-title">收货地址</div>
        <div class="address-info">
          <div class="address-line">
            <span class="address-label">收货人：</span>
            <span>{{ order.address.receiver }}</span>
            <span class="address-phone">{{ order.address.phone }}</span>
          </div>
          <div class="address-line">
            <span class="address-label">详细地址：</span>
            <span>{{ order.address.full_address }}</span>
          </div>
        </div>
      </div>

      <!-- 商品清单卡片 -->
      <div class="page-card">
        <div class="section-title">商品清单</div>
        <el-table :data="order.items" border style="width: 100%">
          <el-table-column label="商品" min-width="300">
            <template #default="{ row }">
              <div class="product-cell">
                <el-image
                  :src="row.product?.image"
                  fit="cover"
                  class="product-image"
                >
                  <template #error>
                    <div class="image-placeholder">
                      <el-icon><Picture /></el-icon>
                    </div>
                  </template>
                </el-image>
                <span class="product-name">{{ row.product?.name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="单价" width="120" align="center">
            <template #default="{ row }">
              <span class="price">¥{{ row.price }}</span>
            </template>
          </el-table-column>
          <el-table-column label="数量" width="100" align="center" prop="quantity" />
          <el-table-column label="小计" width="120" align="center">
            <template #default="{ row }">
              <span class="price">¥{{ row.subtotal }}</span>
            </template>
          </el-table-column>
        </el-table>

        <!-- 合计金额 -->
        <div class="total-section">
          <span class="total-label">订单总额：</span>
          <span class="total-price">¥{{ order.total_amount }}</span>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="page-card action-bar" @click.stop>
        <el-button @click="goBack">返回订单列表</el-button>
        <!-- 待支付：去支付 + 取消订单 -->
        <template v-if="order.status === 'pending'">
          <el-button type="primary" @click="handlePay">去支付</el-button>
          <el-button @click="handleCancel">取消订单</el-button>
        </template>
        <!-- 已发货：确认收货 -->
        <el-button v-if="order.status === 'shipped'" type="success" @click="handleConfirm">
          确认收货
        </el-button>
        <!-- 已完成：去评价 -->
        <el-button
          v-if="order.status === 'completed' && !order.is_reviewed"
          type="warning"
          @click="goReview"
        >
          去评价
        </el-button>
      </div>
    </template>

    <!-- 订单不存在 -->
    <el-empty v-else description="订单不存在" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Picture } from '@element-plus/icons-vue'
import { getOrderDetail, payOrder, cancelOrder, confirmOrder } from '@/api/order'

const route = useRoute()
const router = useRouter()

// 订单详情数据
const order = ref(null)
const loading = ref(false)

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
  return time.replace('T', ' ').slice(0, 19)
}

// 获取订单详情
const fetchOrder = async () => {
  loading.value = true
  try {
    const id = route.params.id
    const { data } = await getOrderDetail(id)
    order.value = data
  } catch (e) {
    // 拦截器已处理错误提示
  } finally {
    loading.value = false
  }
}

// 返回订单列表
const goBack = () => {
  router.push('/orders')
}

// 跳转评价页
const goReview = () => {
  router.push(`/order/${order.value.id}/review`)
}

// 去支付
const handlePay = async () => {
  try {
    await ElMessageBox.confirm('确定要支付该订单吗？', '确认支付', { type: 'info' })
    await payOrder(order.value.id)
    ElMessage.success('支付成功')
    fetchOrder()
  } catch {
    // 用户取消或请求失败
  }
}

// 取消订单
const handleCancel = async () => {
  try {
    await ElMessageBox.confirm('确定要取消该订单吗？取消后不可恢复。', '取消订单', {
      type: 'warning'
    })
    await cancelOrder(order.value.id)
    ElMessage.success('订单已取消')
    fetchOrder()
  } catch {
    // 用户取消或请求失败
  }
}

// 确认收货
const handleConfirm = async () => {
  try {
    await ElMessageBox.confirm('确认已收到商品？', '确认收货', { type: 'info' })
    await confirmOrder(order.value.id)
    ElMessage.success('已确认收货')
    fetchOrder()
  } catch {
    // 用户取消或请求失败
  }
}

onMounted(() => {
  fetchOrder()
})
</script>

<style scoped>
/* 面包屑 */
.el-breadcrumb {
  margin-bottom: 20px;
}

/* 章节标题 */
.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #ebeef5;
}

/* 收货地址 */
.address-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.address-line {
  font-size: 14px;
  color: #606266;
}

.address-label {
  color: #909399;
  margin-right: 4px;
}

.address-phone {
  margin-left: 16px;
  color: #909399;
}

/* 商品表格中的商品单元格 */
.product-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.product-image {
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

.product-name {
  font-size: 14px;
  color: #303133;
}

/* 合计金额 */
.total-section {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}

.total-label {
  font-size: 14px;
  color: #606266;
}

.total-price {
  font-size: 20px;
  font-weight: bold;
  color: #f56c6c;
  margin-left: 8px;
}

/* 操作栏 */
.action-bar {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}
</style>

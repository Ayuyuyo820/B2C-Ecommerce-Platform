<template>
  <div class="page-container">
    <!-- 页面标题 -->
    <h2 class="page-title">数据统计</h2>

    <!-- 统计卡片区域 -->
    <div class="stats-row">
      <el-card
        v-for="item in statCards"
        :key="item.label"
        class="stat-card"
        shadow="hover"
      >
        <div class="stat-card-inner">
          <div class="stat-icon" :style="{ backgroundColor: item.color }">
            <el-icon :size="28"><component :is="item.icon" /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ item.value }}</div>
            <div class="stat-label">{{ item.label }}</div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 销售趋势区域 -->
    <div class="page-card">
      <div class="section-header">
        <h3 class="section-title">销售趋势</h3>
        <el-radio-group v-model="period" @change="fetchSalesData">
          <el-radio-button value="7d">近7天</el-radio-button>
          <el-radio-button value="30d">近30天</el-radio-button>
          <el-radio-button value="90d">近90天</el-radio-button>
          <el-radio-button value="1y">近一年</el-radio-button>
        </el-radio-group>
      </div>

      <!-- 销售数据表格 -->
      <el-table :data="salesList" v-loading="salesLoading" stripe border style="width: 100%">
        <el-table-column prop="date" label="日期" min-width="140" align="center" />
        <el-table-column prop="orders" label="订单数" min-width="100" align="center" />
        <el-table-column prop="amount" label="销售额" min-width="140" align="center">
          <template #default="{ row }">
            <span class="price">¥{{ row.amount }}</span>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ShoppingCart, Money, User, Goods, Document, Comment } from '@element-plus/icons-vue'
import request from '@/api/request'

// ========== 总览统计数据 ==========
const stats = reactive({
  today_orders: 0,
  today_amount: 0,
  total_users: 0,
  total_products: 0,
  pending_orders: 0,
  pending_reviews: 0
})

// 统计卡片配置
const statCards = computed(() => [
  { label: '今日订单数', value: stats.today_orders, icon: ShoppingCart, color: '#1f2329' },
  { label: '今日销售额', value: `¥${stats.today_amount}`, icon: Money, color: '#e5482f' },
  { label: '总用户数', value: stats.total_users, icon: User, color: '#4e5969' },
  { label: '总商品数', value: stats.total_products, icon: Goods, color: '#f26d21' },
  { label: '待处理订单', value: stats.pending_orders, icon: Document, color: '#6b7280' },
  { label: '待处理评价', value: stats.pending_reviews, icon: Comment, color: '#7c3aed' }
])

// ========== 获取总览统计 ==========
const fetchStats = async () => {
  try {
    const { data } = await request.get('/admin/statistics/')
    Object.assign(stats, data)
  } catch {
    // 错误已在拦截器中处理
  }
}

// ========== 销售趋势 ==========
const period = ref('7d')
const salesList = ref([])
const salesLoading = ref(false)

const fetchSalesData = async () => {
  salesLoading.value = true
  try {
    const { data } = await request.get('/admin/statistics/sales/', {
      params: { period: period.value }
    })
    salesList.value = data.data
  } catch {
    // 错误已在拦截器中处理
  } finally {
    salesLoading.value = false
  }
}

// ========== 初始化 ==========
onMounted(() => {
  fetchStats()
  fetchSalesData()
})
</script>

<style scoped>
.page-title {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 20px;
}

/* 统计卡片行 */
.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 8px;
  border: 1px solid #ebeef2;
}

.stat-card :deep(.el-card__body) {
  padding: 22px;
}

.stat-card-inner {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #1f2329;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

/* 区域标题 */
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
}

/* 响应式：小屏幕2列 */
@media (max-width: 900px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>

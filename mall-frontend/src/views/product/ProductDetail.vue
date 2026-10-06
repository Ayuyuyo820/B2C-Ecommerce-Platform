<template>
  <div class="page-container">
    <!-- 404 提示 -->
    <div v-if="notFound" class="page-card" style="text-align: center; padding: 80px 0">
      <el-empty description="商品不存在或已下架">
        <el-button type="primary" @click="router.push('/products')">返回商品列表</el-button>
      </el-empty>
    </div>

    <!-- 加载中 -->
    <div v-else-if="loading" class="page-card" v-loading="loading" style="min-height: 400px" />

    <!-- 商品主体 -->
    <template v-else-if="product">
      <!-- 上半部分：图片 + 基本信息 -->
      <div class="page-card detail-main">
        <!-- 左侧：商品图片 -->
        <div class="detail-images">
          <el-image
            :src="currentImage"
            fit="contain"
            class="main-image"
          >
            <template #error>
              <div class="image-error">
                <el-icon size="60"><Picture /></el-icon>
              </div>
            </template>
          </el-image>
          <!-- 缩略图列表 -->
          <div class="thumb-list" v-if="product.images && product.images.length > 1">
            <div
              v-for="(img, index) in product.images"
              :key="index"
              :class="['thumb-item', { active: currentImage === img }]"
              @click="currentImage = img"
            >
              <el-image :src="img" fit="cover" class="thumb-img" />
            </div>
          </div>
        </div>

        <!-- 右侧：商品信息 -->
        <div class="detail-info">
          <h1 class="detail-title">{{ product.name }}</h1>

          <div class="detail-price-row">
            <span class="price-label">价格</span>
            <span class="price">¥{{ product.price }}</span>
            <span class="price-original" v-if="product.original_price">
              ¥{{ product.original_price }}
            </span>
          </div>

          <div class="detail-meta">
            <span>销量：{{ product.sales }} 件</span>
            <span>库存：{{ product.stock }} 件</span>
          </div>

          <div class="detail-meta">
            <span>分类：{{ product.category?.name || '-' }}</span>
          </div>

          <!-- 商家信息 -->
          <div class="merchant-info" v-if="product.merchant">
            <el-avatar :src="product.merchant.avatar" :size="32" />
            <span class="merchant-name">{{ product.merchant.username }}</span>
          </div>

          <!-- 数量选择 -->
          <div class="quantity-row">
            <span class="quantity-label">数量</span>
            <el-input-number
              v-model="quantity"
              :min="1"
              :max="product.stock > 0 ? product.stock : 1"
              :disabled="product.stock <= 0"
            />
            <span class="stock-tip" v-if="product.stock <= 0">该商品已售罄</span>
          </div>

          <!-- 操作按钮 -->
          <div class="action-row">
            <el-button
              type="warning"
              size="large"
              :disabled="product.stock <= 0"
              @click="handleAddCart"
            >
              <el-icon><ShoppingCart /></el-icon>加入购物车
            </el-button>
            <el-button
              type="danger"
              size="large"
              :disabled="product.stock <= 0"
              @click="handleBuyNow"
            >
              立即购买
            </el-button>
          </div>
        </div>
      </div>

      <!-- 下半部分：Tab 切换 -->
      <div class="page-card">
        <el-tabs v-model="activeTab">
          <!-- 商品详情 -->
          <el-tab-pane label="商品详情" name="detail">
            <div class="description-content" v-if="product.description">
              {{ product.description }}
            </div>
            <el-empty v-else description="暂无详情" :image-size="80" />
          </el-tab-pane>

          <!-- 商品评价 -->
          <el-tab-pane label="商品评价" name="reviews">
            <!-- 评价统计 -->
            <div class="review-stats" v-if="reviewStats">
              <span class="stats-score">{{ reviewStats.average_rating }}</span>
              <span class="stats-label">综合评分</span>
              <span class="stats-rate">好评率 {{ reviewStats.good_rate }}%</span>
            </div>

            <!-- 评价列表 -->
            <div v-loading="reviewLoading">
              <div v-if="reviewList.length">
                <div class="review-item" v-for="review in reviewList" :key="review.id">
                  <div class="review-header">
                    <el-avatar :src="review.user?.avatar" :size="36" />
                    <div class="review-user">
                      <span class="review-username">{{ review.user?.username }}</span>
                      <el-rate
                        :model-value="review.rating"
                        disabled
                        size="small"
                        style="margin-top: 2px"
                      />
                    </div>
                    <span class="review-time">{{ formatTime(review.create_time) }}</span>
                  </div>
                  <div class="review-content">{{ review.content }}</div>
                  <!-- 评价图片 -->
                  <div class="review-images" v-if="review.images && review.images.length">
                    <el-image
                      v-for="(img, idx) in review.images"
                      :key="idx"
                      :src="img"
                      fit="cover"
                      class="review-img"
                      :preview-src-list="review.images"
                      :initial-index="idx"
                    />
                  </div>
                  <!-- 商家回复 -->
                  <div class="review-reply" v-if="review.reply">
                    <span class="reply-label">商家回复：</span>{{ review.reply }}
                  </div>
                </div>

                <!-- 评价分页 -->
                <div class="pagination-wrapper">
                  <el-pagination
                    v-model:current-page="reviewPagination.page"
                    :page-size="reviewPagination.page_size"
                    :total="reviewTotal"
                    layout="prev, pager, next"
                    @current-change="fetchReviews"
                  />
                </div>
              </div>
              <el-empty v-else-if="!reviewLoading" description="暂无评价" />
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </template>

    <!-- 立即购买：选择收货地址弹窗 -->
    <el-dialog v-model="addressDialogVisible" title="选择收货地址" width="500px">
      <div v-if="addressList.length">
        <div
          v-for="addr in addressList"
          :key="addr.id"
          :class="['address-item', { active: selectedAddressId === addr.id }]"
          @click="selectedAddressId = addr.id"
        >
          <div class="address-info">
            <span class="address-receiver">{{ addr.receiver }} {{ addr.phone }}</span>
            <span class="address-detail">
              {{ addr.province }}{{ addr.city }}{{ addr.district }}{{ addr.detail }}
            </span>
          </div>
          <el-tag v-if="addr.is_default" size="small" type="success">默认</el-tag>
        </div>
      </div>
      <el-empty v-else description="暂无收货地址，请先去个人中心添加" />
      <template #footer>
        <el-button @click="addressDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :disabled="!selectedAddressId"
          @click="confirmBuyNow"
        >
          确认下单
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Picture, ShoppingCart } from '@element-plus/icons-vue'
import request from '@/api/request'

const route = useRoute()
const router = useRouter()

// ========== 商品数据 ==========
const loading = ref(false)
const notFound = ref(false)
const product = ref(null)
const currentImage = ref('')
const quantity = ref(1)

// ========== Tab ==========
const activeTab = ref('detail')

// ========== 评价数据 ==========
const reviewLoading = ref(false)
const reviewList = ref([])
const reviewTotal = ref(0)
const reviewStats = ref(null)
const reviewPagination = reactive({ page: 1, page_size: 10 })

// ========== 立即购买弹窗 ==========
const addressDialogVisible = ref(false)
const addressList = ref([])
const selectedAddressId = ref(null)

// ========== 获取商品详情 ==========
const fetchProduct = async () => {
  loading.value = true
  notFound.value = false
  try {
    const { data } = await request.get(`/products/${route.params.id}/`)
    product.value = data
    // 默认显示第一张图片
    currentImage.value = data.images?.[0] || data.image || ''
  } catch (error) {
    if (error.response?.status === 404) {
      notFound.value = true
    }
  } finally {
    loading.value = false
  }
}

// ========== 获取评价列表 ==========
const fetchReviews = async () => {
  reviewLoading.value = true
  try {
    const { data } = await request.get(`/products/${route.params.id}/reviews/`, {
      params: {
        page: reviewPagination.page,
        page_size: reviewPagination.page_size
      }
    })
    reviewList.value = data.results
    reviewTotal.value = data.count
    reviewStats.value = data.stats || null
  } catch {
    // 错误已在拦截器中处理
  } finally {
    reviewLoading.value = false
  }
}

// ========== 加入购物车 ==========
const handleAddCart = async () => {
  try {
    await request.post('/cart/', {
      product_id: product.value.id,
      quantity: quantity.value
    })
    ElMessage.success('已添加到购物车')
  } catch {
    // 错误已在拦截器中处理
  }
}

// ========== 立即购买 ==========
const handleBuyNow = async () => {
  // 先获取收货地址列表
  try {
    const { data } = await request.get('/addresses/')
    addressList.value = Array.isArray(data) ? data : (data.results || [])
    // 默认选中默认地址
    const defaultAddr = addressList.value.find((a) => a.is_default)
    selectedAddressId.value = defaultAddr?.id || addressList.value[0]?.id || null
    addressDialogVisible.value = true
  } catch {
    // 错误已在拦截器中处理
  }
}

// ========== 确认下单（立即购买） ==========
const confirmBuyNow = async () => {
  if (!selectedAddressId.value) {
    ElMessage.warning('请选择收货地址')
    return
  }
  try {
    await ElMessageBox.confirm('确认创建订单？', '提示', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'info'
    })
    // 立即购买：先加入购物车，再用购物车ID下单
    const { data: cartData } = await request.post('/cart/', {
      product_id: product.value.id,
      quantity: quantity.value
    })
    const { data: orderData } = await request.post('/orders/', {
      cart_ids: [cartData.id],
      address_id: selectedAddressId.value
    })
    ElMessage.success('订单创建成功')
    addressDialogVisible.value = false
    router.push(`/order/${orderData.id}`)
  } catch {
    // 用户取消或请求失败
  }
}

// ========== 格式化时间 ==========
const formatTime = (timeStr) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

// ========== 监听Tab切换，懒加载评价 ==========
watch(activeTab, (val) => {
  if (val === 'reviews' && reviewList.value.length === 0) {
    fetchReviews()
  }
})

// ========== 初始化 ==========
onMounted(() => {
  fetchProduct()
})
</script>

<style scoped>
/* 主体布局：左图右信息 */
.detail-main {
  display: flex;
  gap: 36px;
}

/* 左侧图片区 */
.detail-images {
  width: 400px;
  flex-shrink: 0;
}

.main-image {
  width: 400px;
  height: 400px;
  border-radius: 8px;
  background: #f6f7f9;
  border: 1px solid #ebeef2;
}

.image-error {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  color: #c0c4cc;
}

/* 缩略图列表 */
.thumb-list {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.thumb-item {
  width: 60px;
  height: 60px;
  border-radius: 4px;
  overflow: hidden;
  cursor: pointer;
  border: 2px solid transparent;
  transition: border-color 0.2s;
}

.thumb-item.active,
.thumb-item:hover {
  border-color: #e5482f;
}

.thumb-img {
  width: 100%;
  height: 100%;
}

/* 右侧信息区 */
.detail-info {
  flex: 1;
}

.detail-title {
  font-size: 24px;
  font-weight: bold;
  color: #1f2329;
  line-height: 1.5;
  margin-bottom: 16px;
}

.detail-price-row {
  background: #fff7f4;
  padding: 18px 20px;
  border-radius: 8px;
  border: 1px solid rgba(229, 72, 47, 0.14);
  margin-bottom: 16px;
}

.price-label {
  font-size: 14px;
  color: #999;
  margin-right: 12px;
}

.detail-price-row .price {
  font-size: 32px;
  color: #e5482f;
  font-weight: bold;
}

.detail-price-row .price-original {
  font-size: 14px;
  color: #999;
  text-decoration: line-through;
  margin-left: 10px;
}

.detail-meta {
  display: flex;
  gap: 30px;
  font-size: 14px;
  color: #4e5969;
  margin-bottom: 12px;
}

/* 商家信息 */
.merchant-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding: 10px 12px;
  background: #f7f8fa;
  border-radius: 8px;
  border: 1px solid #ebeef2;
}

.merchant-name {
  font-size: 14px;
  color: #1f2329;
}

/* 数量选择 */
.quantity-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.quantity-label {
  font-size: 14px;
  color: #666;
}

.stock-tip {
  font-size: 13px;
  color: #e5482f;
}

/* 操作按钮 */
.action-row {
  display: flex;
  gap: 16px;
}

/* 商品详情描述 */
.description-content {
  font-size: 14px;
  line-height: 1.8;
  color: #4e5969;
  white-space: pre-wrap;
  padding: 10px 0;
}

/* 评价统计 */
.review-stats {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 0;
  border-bottom: 1px solid #eee;
  margin-bottom: 16px;
}

.stats-score {
  font-size: 36px;
  font-weight: bold;
  color: #e5482f;
}

.stats-label {
  font-size: 14px;
  color: #666;
}

.stats-rate {
  font-size: 14px;
  color: #67c23a;
  margin-left: 16px;
}

/* 评价项 */
.review-item {
  padding: 16px 0;
  border-bottom: 1px solid #f0f0f0;
}

.review-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.review-user {
  flex: 1;
}

.review-username {
  font-size: 14px;
  color: #1f2329;
  display: block;
}

.review-time {
  font-size: 12px;
  color: #999;
}

.review-content {
  font-size: 14px;
  color: #333;
  line-height: 1.6;
  margin-bottom: 8px;
}

/* 评价图片 */
.review-images {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.review-img {
  width: 80px;
  height: 80px;
  border-radius: 4px;
  cursor: pointer;
}

/* 商家回复 */
.review-reply {
  background: #f7f8fa;
  padding: 10px 12px;
  border-radius: 6px;
  font-size: 13px;
  color: #4e5969;
}

.reply-label {
  color: #e5482f;
  font-weight: bold;
}

/* 收货地址选择 */
.address-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border: 1px solid #ebeef2;
  border-radius: 6px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.address-item:hover {
  border-color: #e5482f;
}

.address-item.active {
  border-color: #e5482f;
  background: #fff7f4;
}

.address-receiver {
  font-size: 14px;
  font-weight: bold;
  color: #1f2329;
  display: block;
  margin-bottom: 4px;
}

.address-detail {
  font-size: 13px;
  color: #666;
}

@media (max-width: 900px) {
  .detail-main {
    flex-direction: column;
  }

  .detail-images,
  .main-image {
    width: 100%;
  }
}
</style>

<template>
  <!-- 评价页面 -->
  <div class="page-container">
    <!-- 面包屑导航 -->
    <el-breadcrumb separator="/">
      <el-breadcrumb-item :to="{ path: '/orders' }">我的订单</el-breadcrumb-item>
      <el-breadcrumb-item>评价订单</el-breadcrumb-item>
    </el-breadcrumb>

    <!-- 加载状态 -->
    <el-skeleton :loading="loading" animated :rows="8" v-if="loading" />

    <template v-else-if="order">
      <!-- 订单信息 -->
      <div class="page-card">
        <div class="section-title">订单信息</div>
        <div class="order-info">
          <span>订单号：{{ order.order_no }}</span>
          <span class="divider">|</span>
          <span>下单时间：{{ formatTime(order.create_time) }}</span>
        </div>
      </div>

      <!-- 逐个商品评价 -->
      <div class="page-card">
        <div class="section-title">商品评价</div>

        <div
          v-for="(item, index) in reviewItems"
          :key="index"
          class="review-item"
        >
          <!-- 商品信息 -->
          <div class="item-header">
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
            <div class="item-detail">
              <div class="item-name">{{ item.product_name }}</div>
              <div class="item-price">
                <span class="price">¥{{ item.price }}</span>
                <span class="qty">x{{ item.quantity }}</span>
              </div>
            </div>
          </div>

          <!-- 评分 -->
          <div class="review-field">
            <span class="field-label">评分：</span>
            <el-rate v-model="item.rating" show-text :texts="['很差', '较差', '一般', '较好', '非常好']" />
          </div>

          <!-- 评价内容 -->
          <div class="review-field">
            <span class="field-label">评价：</span>
            <el-input
              v-model="item.content"
              type="textarea"
              :rows="3"
              placeholder="请分享您的使用体验（至少5个字）"
              maxlength="500"
              show-word-limit
            />
          </div>

          <!-- 上传图片 -->
          <div class="review-field">
            <span class="field-label">图片：</span>
            <el-upload
              :file-list="item.fileList"
              :http-request="(options) => handleImageUpload(options, index)"
              :on-remove="(file) => handleImageRemove(file, index)"
              list-type="picture-card"
              accept="image/*"
              :limit="5"
            >
              <el-icon><Plus /></el-icon>
            </el-upload>
          </div>

          <!-- 分割线 -->
          <el-divider v-if="index < reviewItems.length - 1" />
        </div>
      </div>

      <!-- 提交按钮 -->
      <div class="page-card submit-bar">
        <el-button @click="goBack">返回订单列表</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          提交评价
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
import { ElMessage } from 'element-plus'
import { Picture, Plus } from '@element-plus/icons-vue'
import { getOrderDetail } from '@/api/order'
import { createReview } from '@/api/review'
import { uploadFile } from '@/api/upload'

const route = useRoute()
const router = useRouter()

// 订单数据
const order = ref(null)
const loading = ref(false)
const submitting = ref(false)

// 评价列表（每个商品一条）
const reviewItems = ref([])

// 格式化时间
const formatTime = (time) => {
  if (!time) return ''
  return time.replace('T', ' ').slice(0, 16)
}

// 初始化评价数据（从订单商品项生成）
const initReviewItems = (items) => {
  reviewItems.value = items.map((item) => ({
    product_id: item.product?.id,
    product_name: item.product?.name,
    product_image: item.product?.image,
    price: item.price,
    quantity: item.quantity,
    rating: 5,
    content: '',
    images: [],
    fileList: []
  }))
}

// 获取订单详情
const fetchOrder = async () => {
  loading.value = true
  try {
    const id = route.params.orderId
    const { data } = await getOrderDetail(id)
    order.value = data
    initReviewItems(data.items || [])
  } catch (e) {
    // 拦截器已处理错误提示
  } finally {
    loading.value = false
  }
}

// 上传图片
const handleImageUpload = async (options, index) => {
  const file = options.file
  try {
    const { data } = await uploadFile(file, 'review')
    reviewItems.value[index].images.push(data.url)
    ElMessage.success('图片上传成功')
  } catch (e) {
    // 拦截器已处理错误提示
  }
}

// 删除图片
const handleImageRemove = (file, index) => {
  const images = reviewItems.value[index].images
  const idx = images.indexOf(file.url)
  if (idx > -1) {
    images.splice(idx, 1)
  }
}

// 提交评价
const handleSubmit = async () => {
  // 校验所有商品的评价内容
  for (let i = 0; i < reviewItems.value.length; i++) {
    const item = reviewItems.value[i]
    if (!item.content || item.content.length < 5) {
      ElMessage.warning(`请为"${item.product_name}"填写至少5个字的评价`)
      return
    }
  }

  submitting.value = true
  try {
    const reviews = reviewItems.value.map((item) => ({
      product_id: item.product_id,
      rating: item.rating,
      content: item.content,
      images: item.images
    }))
    await createReview(route.params.orderId, { reviews })
    ElMessage.success('评价提交成功')
    router.push('/orders')
  } catch (e) {
    // 拦截器已处理错误提示
  } finally {
    submitting.value = false
  }
}

// 返回订单列表
const goBack = () => {
  router.push('/orders')
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

/* 订单信息 */
.order-info {
  font-size: 14px;
  color: #606266;
}

.divider {
  margin: 0 12px;
  color: #dcdfe6;
}

/* 评价商品项 */
.review-item {
  padding: 16px 0;
}

/* 商品头部信息 */
.item-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
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

.item-detail {
  flex: 1;
}

.item-name {
  font-size: 14px;
  color: #303133;
  margin-bottom: 4px;
}

.item-price {
  display: flex;
  align-items: center;
  gap: 8px;
}

.qty {
  font-size: 13px;
  color: #909399;
}

/* 评价字段 */
.review-field {
  display: flex;
  align-items: flex-start;
  margin-bottom: 12px;
}

.field-label {
  width: 60px;
  font-size: 14px;
  color: #606266;
  flex-shrink: 0;
  padding-top: 4px;
}

.review-field .el-input,
.review-field .el-textarea {
  flex: 1;
}

/* 提交栏 */
.submit-bar {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>

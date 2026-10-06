<template>
  <div class="home-wrapper page-container">
    <!-- ========== Hero 横幅区域 ========== -->
    <section class="hero-banner">
      <div class="hero-content">
        <h1 class="hero-title">Mall Store</h1>
        <p class="hero-subtitle">精选数码、家居与日用好物，简洁下单，快速管理</p>
        <el-button type="primary" size="large" @click="router.push('/product')">
          立即选购
        </el-button>
      </div>
    </section>

    <!-- ========== 分类快捷导航 ========== -->
    <section class="section-block">
      <h2 class="section-title">商品分类</h2>
      <!-- 加载骨架屏 -->
      <el-row v-if="categoryLoading" :gutter="16">
        <el-col v-for="i in 6" :key="i" :xs="8" :sm="6" :md="4">
          <el-skeleton :rows="1" animated style="height: 80px; margin-bottom: 16px" />
        </el-col>
      </el-row>
      <!-- 分类列表 -->
      <el-row v-else :gutter="16">
        <el-col
          v-for="category in categoryList"
          :key="category.id"
          :xs="8"
          :sm="6"
          :md="4"
        >
          <div
            class="category-card"
            @click="router.push(`/product?category=${category.id}`)"
          >
            <div class="category-icon">
              <el-icon :size="28">
                <component :is="category.icon || 'Grid'" />
              </el-icon>
            </div>
            <span class="category-name">{{ category.name }}</span>
          </div>
        </el-col>
      </el-row>
    </section>

    <!-- ========== 热门商品 ========== -->
    <section class="section-block">
      <h2 class="section-title">热门商品</h2>
      <!-- 加载骨架屏 -->
      <el-row v-if="productLoading" :gutter="20">
        <el-col v-for="i in 4" :key="i" :xs="12" :sm="8" :md="6">
          <el-skeleton :rows="3" animated style="margin-bottom: 20px" />
        </el-col>
      </el-row>
      <!-- 商品列表 -->
      <el-row v-else :gutter="20">
        <el-col
          v-for="product in productList"
          :key="product.id"
          :xs="12"
          :sm="8"
          :md="6"
        >
          <div class="product-card" @click="router.push(`/product/${product.id}`)">
            <div class="product-image">
              <el-image
                :src="product.image || product.main_image"
                fit="cover"
                style="width: 100%; height: 200px"
              >
                <template #error>
                  <div class="image-placeholder">
                    <el-icon :size="40"><Picture /></el-icon>
                  </div>
                </template>
              </el-image>
            </div>
            <div class="product-info">
              <h3 class="product-name">{{ product.name }}</h3>
              <div class="product-meta">
                <span class="price">¥{{ product.price }}</span>
                <span class="sales">已售 {{ product.sales || 0 }} 件</span>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getCategoryList } from '@/api/category'
import { getProductList } from '@/api/product'
import { Grid, Picture, Iphone, Monitor, Goods, ShoppingBag, Notebook, Star, Collection, Van, Bicycle, Watch } from '@element-plus/icons-vue'
const router = useRouter()

// ========== 分类数据 ==========
const categoryList = ref([])
const categoryLoading = ref(false)

// 获取分类列表
const fetchCategories = async () => {
  categoryLoading.value = true
  try {
    const { data } = await getCategoryList()
    categoryList.value = data.results || data || []
  } catch {
    // 错误已在拦截器中处理
  } finally {
    categoryLoading.value = false
  }
}

// ========== 热门商品数据 ==========
const productList = ref([])
const productLoading = ref(false)

// 获取热门商品列表（取前8个）
const fetchHotProducts = async () => {
  productLoading.value = true
  try {
    const { data } = await getProductList({ page_size: 8 })
    productList.value = data.results || data || []
  } catch {
    // 错误已在拦截器中处理
  } finally {
    productLoading.value = false
  }
}

// ========== 初始化加载 ==========
onMounted(() => {
  fetchCategories()
  fetchHotProducts()
})
</script>

<style scoped>
/* Hero 横幅 */
.hero-banner {
  position: relative;
  overflow: hidden;
  background:
    radial-gradient(circle at 84% 18%, rgba(229, 72, 47, 0.22), transparent 28%),
    linear-gradient(135deg, #151922 0%, #2a303a 100%);
  border-radius: 8px;
  padding: 72px 56px;
  margin-bottom: 24px;
  color: #fff;
}

.hero-banner::after {
  content: "";
  position: absolute;
  right: 58px;
  bottom: -34px;
  width: 300px;
  height: 210px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 28px;
  transform: rotate(-8deg);
}

.hero-content {
  position: relative;
  z-index: 1;
  max-width: 520px;
}

.hero-title {
  font-size: 42px;
  font-weight: 700;
  margin-bottom: 12px;
  letter-spacing: 0;
}

.hero-subtitle {
  font-size: 18px;
  opacity: 0.9;
  margin-bottom: 24px;
}

/* 区块通用 */
.section-block {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 24px;
  border: 1px solid #ebeef2;
}

.section-title {
  font-size: 20px;
  font-weight: 600;
  color: #1f2329;
  margin-bottom: 20px;
  padding-left: 12px;
  border-left: 4px solid #e5482f;
}

/* 分类卡片 */
.category-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px 8px;
  margin-bottom: 16px;
  border-radius: 8px;
  background: #f7f8fa;
  border: 1px solid #eef1f5;
  cursor: pointer;
  transition: all 0.3s ease;
}

.category-card:hover {
  background: #fff7f4;
  transform: translateY(-2px);
  border-color: rgba(229, 72, 47, 0.24);
  box-shadow: 0 8px 20px rgba(31, 35, 41, 0.08);
}

.category-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #1f2329;
  color: #fff;
  border-radius: 8px;
}

.category-name {
  font-size: 14px;
  color: #1f2329;
  font-weight: 500;
}

/* 商品卡片 */
.product-card {
  background: #fff;
  border: 1px solid #ebeef2;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.product-card:hover {
  transform: translateY(-4px);
  border-color: rgba(31, 35, 41, 0.18);
  box-shadow: 0 14px 30px rgba(31, 35, 41, 0.12);
}

.product-image {
  width: 100%;
  height: 200px;
  overflow: hidden;
  background: #f5f7fa;
}

.image-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #c0c4cc;
}

.product-info {
  padding: 12px;
}

.product-name {
  font-size: 14px;
  font-weight: 500;
  color: #1f2329;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.product-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.price {
  color: #e5482f;
  font-size: 18px;
  font-weight: 700;
}

.sales {
  font-size: 12px;
  color: #999;
}

@media (max-width: 768px) {
  .hero-banner {
    padding: 48px 24px;
  }

  .hero-title {
    font-size: 32px;
  }
}
</style>

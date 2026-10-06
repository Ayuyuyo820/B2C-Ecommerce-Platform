<template>
  <div class="page-container">
    <!-- 搜索栏 -->
    <div class="page-card search-bar">
      <el-input
        v-model="searchForm.keyword"
        placeholder="请输入商品关键词"
        clearable
        style="width: 200px"
        @keyup.enter="handleSearch"
      />
      <el-select
        v-model="searchForm.category"
        placeholder="选择分类"
        clearable
        style="width: 160px"
      >
        <!-- 扁平化分类列表（含子分类） -->
        <el-option
          v-for="item in flatCategories"
          :key="item.id"
          :label="item.name"
          :value="item.id"
        />
      </el-select>
      <el-input
        v-model="searchForm.min_price"
        placeholder="最低价格"
        clearable
        style="width: 120px"
        @keyup.enter="handleSearch"
      />
      <el-input
        v-model="searchForm.max_price"
        placeholder="最高价格"
        clearable
        style="width: 120px"
        @keyup.enter="handleSearch"
      />
      <el-button type="primary" @click="handleSearch">
        <el-icon><Search /></el-icon>搜索
      </el-button>
      <el-button @click="handleReset">重置</el-button>
    </div>

    <!-- 排序选项 -->
    <div class="sort-bar page-card">
      <span
        v-for="item in sortOptions"
        :key="item.value"
        :class="['sort-item', { active: currentSort === item.value }]"
        @click="handleSort(item.value)"
      >
        {{ item.label }}
      </span>
    </div>

    <!-- 商品列表 -->
    <div class="page-card" v-loading="loading">
      <el-row :gutter="20" v-if="productList.length">
        <el-col
          v-for="product in productList"
          :key="product.id"
          :xs="12"
          :sm="8"
          :md="6"
          :lg="4"
          class="product-col"
        >
          <div class="product-card" @click="goDetail(product.id)">
            <el-image
              :src="product.image"
              fit="cover"
              class="product-image"
              lazy
            >
              <template #error>
                <div class="image-error">
                  <el-icon size="40"><Picture /></el-icon>
                </div>
              </template>
            </el-image>
            <div class="product-info">
              <h3 class="product-name">{{ product.name }}</h3>
              <div class="product-price">
                <span class="price">¥{{ product.price }}</span>
                <span class="price-original" v-if="product.original_price">
                  ¥{{ product.original_price }}
                </span>
              </div>
              <div class="product-sales">已售 {{ product.sales }} 件</div>
            </div>
          </div>
        </el-col>
      </el-row>

      <!-- 空状态 -->
      <el-empty v-else-if="!loading" description="暂无商品" />
    </div>

    <!-- 分页 -->
    <div class="pagination-wrapper" v-if="total > 0">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="total"
        :page-sizes="[12, 24, 36]"
        layout="total, sizes, prev, pager, next, jumper"
        @current-change="fetchProducts"
        @size-change="handleSizeChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Picture } from '@element-plus/icons-vue'
import request from '@/api/request'

const router = useRouter()

// ========== 搜索表单 ==========
const searchForm = reactive({
  keyword: '',
  category: '',
  min_price: '',
  max_price: ''
})

// ========== 分页 ==========
const pagination = reactive({
  page: 1,
  page_size: 12
})
const total = ref(0)

// ========== 排序 ==========
const sortOptions = [
  { label: '综合', value: '-create_time' },
  { label: '价格升序', value: 'price' },
  { label: '价格降序', value: '-price' },
  { label: '销量排序', value: '-sales' }
]
const currentSort = ref('-create_time')

// ========== 数据 ==========
const loading = ref(false)
const productList = ref([])
const categoryList = ref([])

// 将树形分类扁平化，方便下拉选择
const flatCategories = computed(() => {
  const result = []
  const flatten = (list) => {
    list.forEach((item) => {
      result.push({ id: item.id, name: item.name })
      if (item.children && item.children.length) {
        flatten(item.children)
      }
    })
  }
  flatten(categoryList.value)
  return result
})

// ========== 获取分类列表 ==========
const fetchCategories = async () => {
  try {
    const { data } = await request.get('/categories/')
    categoryList.value = data
  } catch {
    // 错误已在拦截器中处理
  }
}

// ========== 获取商品列表 ==========
const fetchProducts = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size
    }
    // 仅传递非空搜索条件
    if (searchForm.keyword) params.keyword = searchForm.keyword
    if (searchForm.category) params.category = searchForm.category
    if (searchForm.min_price) params.min_price = searchForm.min_price
    if (searchForm.max_price) params.max_price = searchForm.max_price
    if (currentSort.value) params.ordering = currentSort.value

    const { data } = await request.get('/products/', { params })
    productList.value = data.results
    total.value = data.count
  } catch {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}

// ========== 搜索 / 重置 ==========
const handleSearch = () => {
  pagination.page = 1
  fetchProducts()
}

const handleReset = () => {
  searchForm.keyword = ''
  searchForm.category = ''
  searchForm.min_price = ''
  searchForm.max_price = ''
  currentSort.value = '-create_time'
  pagination.page = 1
  fetchProducts()
}

// ========== 排序切换 ==========
const handleSort = (value) => {
  currentSort.value = value
  pagination.page = 1
  fetchProducts()
}

// ========== 分页大小变化 ==========
const handleSizeChange = () => {
  pagination.page = 1
  fetchProducts()
}

// ========== 跳转商品详情 ==========
const goDetail = (id) => {
  router.push(`/product/${id}`)
}

// ========== 初始化 ==========
onMounted(() => {
  fetchCategories()
  fetchProducts()
})
</script>

<style scoped>
/* 排序栏 */
.sort-bar {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 10px;
}

.sort-item {
  padding: 6px 16px;
  cursor: pointer;
  border-radius: 6px;
  font-size: 14px;
  color: #4e5969;
  transition: all 0.2s;
}

.sort-item:hover {
  color: #1f2329;
  background: #f4f5f7;
}

.sort-item.active {
  color: #fff;
  background: #1f2329;
  font-weight: bold;
}

/* 商品网格 */
.product-col {
  margin-bottom: 20px;
}

.product-card {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s;
  border: 1px solid #ebeef2;
}

.product-card:hover {
  transform: translateY(-4px);
  border-color: rgba(31, 35, 41, 0.18);
  box-shadow: 0 14px 30px rgba(31, 35, 41, 0.12);
}

.product-image {
  width: 100%;
  height: 200px;
  display: block;
}

.image-error {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 200px;
  background: #f6f7f9;
  color: #c0c4cc;
}

.product-info {
  padding: 12px;
}

.product-name {
  font-size: 14px;
  font-weight: normal;
  color: #1f2329;
  line-height: 1.4;
  height: 40px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  margin-bottom: 8px;
}

.product-price {
  margin-bottom: 4px;
}

.product-price .price {
  font-size: 18px;
  color: #e5482f;
  font-weight: bold;
}

.product-price .price-original {
  font-size: 12px;
  color: #999;
  text-decoration: line-through;
  margin-left: 6px;
}

.product-sales {
  font-size: 12px;
  color: #999;
}
</style>

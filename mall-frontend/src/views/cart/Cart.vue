<template>
  <div class="page-container">
    <div class="page-card">
      <h2 class="cart-title">我的购物车</h2>

      <!-- 购物车为空 -->
      <el-empty v-if="!loading && cartList.length === 0" description="购物车是空的">
        <el-button type="primary" @click="router.push('/products')">去逛逛</el-button>
      </el-empty>

      <!-- 购物车列表 -->
      <template v-else>
        <el-table
          v-loading="loading"
          :data="cartList"
          style="width: 100%"
          @selection-change="handleSelectionChange"
          ref="tableRef"
        >
          <!-- 全选 / 勾选列 -->
          <el-table-column type="selection" width="55" />

          <!-- 商品图片 -->
          <el-table-column label="商品" min-width="300">
            <template #default="{ row }">
              <div class="cart-product">
                <el-image
                  :src="row.product.image"
                  fit="cover"
                  class="cart-product-img"
                  @click="router.push(`/product/${row.product.id}`)"
                />
                <span
                  class="cart-product-name"
                  @click="router.push(`/product/${row.product.id}`)"
                >
                  {{ row.product.name }}
                </span>
              </div>
            </template>
          </el-table-column>

          <!-- 单价 -->
          <el-table-column label="单价" width="120" align="center">
            <template #default="{ row }">
              <span class="price">¥{{ row.product.price }}</span>
            </template>
          </el-table-column>

          <!-- 数量 -->
          <el-table-column label="数量" width="180" align="center">
            <template #default="{ row }">
              <el-input-number
                :model-value="row.quantity"
                :min="1"
                :max="row.product.stock"
                size="small"
                @change="(val) => handleQuantityChange(row, val)"
              />
            </template>
          </el-table-column>

          <!-- 小计 -->
          <el-table-column label="小计" width="120" align="center">
            <template #default="{ row }">
              <span class="price">¥{{ (row.product.price * row.quantity).toFixed(2) }}</span>
            </template>
          </el-table-column>

          <!-- 操作 -->
          <el-table-column label="操作" width="100" align="center">
            <template #default="{ row }">
              <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 底部结算栏 -->
        <div class="cart-footer">
          <div class="cart-footer-left">
            <el-checkbox
              :model-value="isAllSelected"
              @change="handleSelectAll"
            >
              全选
            </el-checkbox>
            <span class="selected-info">
              已选 <strong>{{ selectedList.length }}</strong> 件商品
            </span>
          </div>
          <div class="cart-footer-right">
            <span class="total-price">
              合计：<strong>¥{{ totalAmount }}</strong>
            </span>
            <el-button type="primary" size="large" :disabled="selectedList.length === 0" @click="handleCheckout">
              去结算
            </el-button>
            <el-button type="danger" plain size="large" @click="handleClearCart">清空购物车</el-button>
          </div>
        </div>
      </template>
    </div>

    <!-- 结算：选择收货地址弹窗 -->
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
        <el-button type="primary" :disabled="!selectedAddressId" @click="confirmOrder">
          确认下单
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/api/request'

const router = useRouter()

// ========== 购物车数据 ==========
const loading = ref(false)
const cartList = ref([])
const selectedList = ref([])
const tableRef = ref(null)

// ========== 地址弹窗 ==========
const addressDialogVisible = ref(false)
const addressList = ref([])
const selectedAddressId = ref(null)

// ========== 计算属性：是否全选、总金额 ==========
const isAllSelected = computed(() => {
  return cartList.value.length > 0 && selectedList.value.length === cartList.value.length
})

const totalAmount = computed(() => {
  return selectedList.value
    .reduce((sum, item) => sum + item.product.price * item.quantity, 0)
    .toFixed(2)
})

// ========== 获取购物车列表 ==========
const fetchCart = async () => {
  loading.value = true
  try {
    const { data } = await request.get('/cart/')
    cartList.value = data.results || []
    // 设置默认勾选（后端返回 selected 字段）
    nextTick(() => {
      cartList.value.forEach((item) => {
        if (item.selected) {
          tableRef.value?.toggleRowSelection(item, true)
        }
      })
    })
  } catch {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}

// ========== 勾选变化 ==========
const handleSelectionChange = (val) => {
  selectedList.value = val
}

// ========== 全选 / 取消全选 ==========
const handleSelectAll = (val) => {
  if (val) {
    cartList.value.forEach((row) => {
      tableRef.value?.toggleRowSelection(row, true)
    })
  } else {
    tableRef.value?.clearSelection()
  }
}

// ========== 修改数量 ==========
const handleQuantityChange = async (row, val) => {
  try {
    await request.put(`/cart/${row.id}/`, { quantity: val })
    // 更新本地数据
    row.quantity = val
  } catch {
    // 错误已在拦截器中处理，回滚数量显示
    fetchCart()
  }
}

// ========== 删除单个商品 ==========
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确认删除该商品？', '提示', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await request.delete(`/cart/${row.id}/`)
    ElMessage.success('已删除')
    fetchCart()
  } catch {
    // 用户取消或请求失败
  }
}

// ========== 清空购物车 ==========
const handleClearCart = async () => {
  try {
    await ElMessageBox.confirm('确认清空购物车？', '提示', {
      confirmButtonText: '清空',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await request.delete('/cart/clear/')
    ElMessage.success('购物车已清空')
    fetchCart()
  } catch {
    // 用户取消或请求失败
  }
}

// ========== 去结算 ==========
const handleCheckout = async () => {
  if (selectedList.value.length === 0) {
    ElMessage.warning('请先选择商品')
    return
  }
  // 获取收货地址列表
  try {
    const { data } = await request.get('/addresses/')
    addressList.value = Array.isArray(data) ? data : (data.results || [])
    const defaultAddr = addressList.value.find((a) => a.is_default)
    selectedAddressId.value = defaultAddr?.id || addressList.value[0]?.id || null
    addressDialogVisible.value = true
  } catch {
    // 错误已在拦截器中处理
  }
}

// ========== 确认下单 ==========
const confirmOrder = async () => {
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
    const cartIds = selectedList.value.map((item) => item.id)
    const { data } = await request.post('/orders/', {
      cart_ids: cartIds,
      address_id: selectedAddressId.value
    })
    ElMessage.success('订单创建成功')
    addressDialogVisible.value = false
    // 跳转订单详情
    router.push(`/order/${data.id}`)
  } catch {
    // 用户取消或请求失败
  }
}

// ========== 初始化 ==========
onMounted(() => {
  fetchCart()
})
</script>

<style scoped>
.cart-title {
  font-size: 22px;
  font-weight: bold;
  color: #1f2329;
  margin-bottom: 20px;
}

/* 商品信息单元格 */
.cart-product {
  display: flex;
  align-items: center;
  gap: 12px;
}

.cart-product-img {
  width: 60px;
  height: 60px;
  border-radius: 6px;
  cursor: pointer;
  flex-shrink: 0;
  border: 1px solid #ebeef2;
}

.cart-product-name {
  font-size: 14px;
  color: #1f2329;
  cursor: pointer;
  transition: color 0.2s;
}

.cart-product-name:hover {
  color: #e5482f;
}

/* 底部结算栏 */
.cart-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 18px;
  margin-top: 16px;
  border: 1px solid #ebeef2;
  border-radius: 8px;
  background: #fafbfc;
}

.cart-footer-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.selected-info {
  font-size: 14px;
  color: #666;
}

.selected-info strong {
  color: #e5482f;
}

.cart-footer-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.total-price {
  font-size: 14px;
  color: #1f2329;
}

.total-price strong {
  font-size: 22px;
  color: #e5482f;
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

@media (max-width: 768px) {
  .cart-footer {
    align-items: flex-start;
    flex-direction: column;
  }

  .cart-footer-right {
    width: 100%;
    justify-content: flex-end;
    flex-wrap: wrap;
  }
}
</style>

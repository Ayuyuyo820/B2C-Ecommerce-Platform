<template>
  <div class="page-container">
    <!-- 页面标题 + 发布按钮 -->
    <div class="page-header">
      <h2 class="page-title">商品管理</h2>
      <el-button type="primary" :icon="Plus" @click="handleAdd">发布商品</el-button>
    </div>

    <!-- 商品表格 -->
    <div class="page-card">
      <el-table :data="productList" v-loading="loading" stripe border style="width: 100%">
        <el-table-column prop="id" label="ID" width="70" align="center" />
        <!-- 商品图片列 -->
        <el-table-column label="商品图片" width="100" align="center">
          <template #default="{ row }">
            <el-image
              :src="row.image"
              :preview-src-list="[row.image]"
              fit="cover"
              style="width: 60px; height: 60px; border-radius: 4px"
            >
              <template #error>
                <div style="width:60px;height:60px;display:flex;align-items:center;justify-content:center;color:#c0c4cc;font-size:12px">
                  暂无图片
                </div>
              </template>
            </el-image>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="商品名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="price" label="价格" width="100" align="center">
          <template #default="{ row }">
            <span class="price">¥{{ row.price }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="stock" label="库存" width="80" align="center" />
        <el-table-column prop="sales" label="销量" width="80" align="center" />
        <!-- 状态列（审核状态） -->
        <el-table-column prop="audit_status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.audit_status)">{{ statusLabel(row.audit_status) }}</el-tag>
          </template>
        </el-table-column>
        <!-- 操作列 -->
        <el-table-column label="操作" width="160" align="center" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
              <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
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

    <!-- 新增/编辑商品弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑商品' : '发布商品'"
      width="650px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="productForm"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="商品名称" prop="name">
          <el-input v-model="productForm.name" placeholder="请输入商品名称" />
        </el-form-item>
        <el-form-item label="商品描述" prop="description">
          <el-input
            v-model="productForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入商品描述"
          />
        </el-form-item>
        <el-form-item label="价格" prop="price">
          <el-input-number v-model="productForm.price" :min="0" :precision="2" :step="1" />
        </el-form-item>
        <el-form-item label="原价" prop="original_price">
          <el-input-number v-model="productForm.original_price" :min="0" :precision="2" :step="1" />
        </el-form-item>
        <el-form-item label="库存" prop="stock">
          <el-input-number v-model="productForm.stock" :min="0" :step="1" />
        </el-form-item>
        <el-form-item label="分类" prop="category">
          <el-select v-model="productForm.category" placeholder="请选择分类" style="width: 100%">
            <el-option
              v-for="cat in categoryList"
              :key="cat.id"
              :label="cat.name"
              :value="cat.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="商品图片">
          <el-upload
            :action="uploadUrl"
            :headers="uploadHeaders"
            :file-list="fileList"
            list-type="picture-card"
            :limit="5"
            :on-success="handleUploadSuccess"
            :on-remove="handleUploadRemove"
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitForm">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/api/request'

// ========== 分页 ==========
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

// ========== 表格数据 ==========
const productList = ref([])
const loading = ref(false)

// ========== 获取商品列表（商家视角） ==========
const fetchProductList = async () => {
  loading.value = true
  try {
    const { data } = await request.get('/merchant/products/', {
      params: {
        page: pagination.page,
        page_size: pagination.pageSize
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

// ========== 状态映射 ==========
const statusTagType = (status) => {
  const map = { approved: 'success', rejected: 'danger', pending: 'warning' }
  return map[status] || 'info'
}

const statusLabel = (status) => {
  const map = { approved: '已上架', rejected: '已拒绝', pending: '待审核' }
  return map[status] || status
}

// ========== 弹窗相关 ==========
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitLoading = ref(false)
const formRef = ref(null)

// 表单数据
const productForm = reactive({
  id: null,
  name: '',
  description: '',
  price: 0,
  original_price: 0,
  stock: 0,
  category: '',
  images: []
})

// 表单校验规则
const formRules = {
  name: [{ required: true, message: '请输入商品名称', trigger: 'blur' }],
  price: [{ required: true, message: '请输入价格', trigger: 'blur' }],
  stock: [{ required: true, message: '请输入库存', trigger: 'blur' }],
  category: [{ required: true, message: '请选择分类', trigger: 'change' }]
}

// 分类列表（从接口获取或本地定义）
const categoryList = ref([])

// 上传相关
const uploadUrl = '/api/v1/upload/'
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${localStorage.getItem('access_token')}`
}))
const fileList = ref([])

// 重置表单
const resetForm = () => {
  Object.assign(productForm, {
    id: null,
    name: '',
    description: '',
    price: 0,
    original_price: 0,
    stock: 0,
    category: '',
    images: []
  })
  fileList.value = []
}

// 新增商品
const handleAdd = () => {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

// 编辑商品
const handleEdit = (row) => {
  isEdit.value = true
  Object.assign(productForm, {
    id: row.id,
    name: row.name,
    description: row.description || '',
    price: Number(row.price),
    original_price: Number(row.original_price || 0),
    stock: row.stock,
    category: row.category?.id || '',
    images: row.images || []
  })
  fileList.value = (row.images || []).map((url, idx) => ({ name: `图片${idx + 1}`, url }))
  dialogVisible.value = true
}

// 上传成功回调
const handleUploadSuccess = (response, file) => {
  productForm.images.push(response.url || response.data?.url || '')
}

// 移除图片回调
const handleUploadRemove = (file) => {
  const idx = productForm.images.indexOf(file.url)
  if (idx > -1) productForm.images.splice(idx, 1)
}

// 提交表单
const submitForm = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  submitLoading.value = true
  try {
    // 后端字段是 category_id，前端表单字段是 category，提交时做映射
    const payload = { ...productForm, category_id: productForm.category }
    delete payload.category
    if (isEdit.value) {
      await request.put(`/merchant/products/${productForm.id}/`, payload)
      ElMessage.success('商品更新成功')
    } else {
      await request.post('/merchant/products/', payload)
      ElMessage.success('商品发布成功')
    }
    dialogVisible.value = false
    fetchProductList()
  } catch {
    // 错误已在拦截器中处理
  } finally {
    submitLoading.value = false
  }
}

// ========== 删除商品 ==========
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确认删除商品「${row.name}」？删除后不可恢复。`,
      '删除确认',
      { type: 'warning' }
    )
    await request.delete(`/merchant/products/${row.id}/`)
    ElMessage.success('删除成功')
    fetchProductList()
  } catch {
    // 用户取消或请求失败
  }
}

// ========== 获取分类列表 ==========
const fetchCategories = async () => {
  try {
    const { data } = await request.get('/categories/')
    categoryList.value = data.results || data
  } catch {
    // 忽略
  }
}

// ========== 初始化 ==========
onMounted(() => {
  fetchProductList()
  fetchCategories()
})
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.page-title {
  font-size: 22px;
  font-weight: 700;
  color: #1f2329;
}

.action-buttons {
  justify-content: center;
}
</style>

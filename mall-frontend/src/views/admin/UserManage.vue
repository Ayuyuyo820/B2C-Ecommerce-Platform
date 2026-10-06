<template>
  <div class="page-container">
    <!-- 页面标题 -->
    <h2 class="page-title">用户管理</h2>

    <!-- 搜索栏 -->
    <div class="page-card">
      <div class="search-bar">
        <el-input
          v-model="searchForm.keyword"
          placeholder="用户名/手机号/邮箱"
          clearable
          style="width: 220px"
          @keyup.enter="handleSearch"
        />
        <el-select v-model="searchForm.role" placeholder="角色" clearable style="width: 140px">
          <el-option label="全部" value="" />
          <el-option label="用户" value="user" />
          <el-option label="商家" value="merchant" />
          <el-option label="管理员" value="admin" />
          <el-option label="超级管理员" value="superadmin" />
        </el-select>
        <el-select v-model="searchForm.status" placeholder="状态" clearable style="width: 120px">
          <el-option label="全部" value="" />
          <el-option label="正常" value="true" />
          <el-option label="禁用" value="false" />
        </el-select>
        <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
        <el-button :icon="Refresh" @click="handleReset">重置</el-button>
      </div>
    </div>

    <!-- 用户表格 -->
    <div class="page-card">
      <el-table :data="userList" v-loading="loading" stripe border style="width: 100%">
        <el-table-column prop="id" label="ID" width="70" align="center" />
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="phone" label="手机号" min-width="130" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <!-- 角色列：使用 tag 区分 -->
        <el-table-column prop="role" label="角色" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="roleTagType(row.role)">{{ roleLabel(row.role) }}</el-tag>
          </template>
        </el-table-column>
        <!-- 状态列：正常绿色，禁用红色 -->
        <el-table-column prop="is_active" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="注册时间" min-width="170" />
        <el-table-column prop="last_login" label="最后登录" min-width="170" />
        <!-- 操作列 -->
        <el-table-column label="操作" width="200" align="center" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button
                :type="row.is_active ? 'danger' : 'success'"
                size="small"
                @click="handleToggleStatus(row)"
              >
                {{ row.is_active ? '禁用' : '启用' }}
              </el-button>
              <el-button
                type="warning"
                size="small"
                @click="handleAssignRole(row)"
              >
                分配角色
              </el-button>
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
          @size-change="fetchUserList"
          @current-change="fetchUserList"
        />
      </div>
    </div>

    <!-- 分配角色弹窗 -->
    <el-dialog v-model="roleDialogVisible" title="分配角色" width="400px">
      <el-form label-width="80px">
        <el-form-item label="用户">
          <el-input :model-value="currentUser.username" disabled />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="roleForm.role" placeholder="请选择角色" style="width: 100%">
            <el-option label="用户" value="user" />
            <el-option label="商家" value="merchant" />
            <el-option label="管理员" value="admin" />
            <el-option label="超级管理员" value="superadmin" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="roleDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="roleLoading" @click="submitRole">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Search, Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/api/request'

// ========== 搜索表单 ==========
const searchForm = reactive({
  keyword: '',
  role: '',
  status: ''
})

// ========== 分页 ==========
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

// ========== 表格数据 ==========
const userList = ref([])
const loading = ref(false)

// ========== 获取用户列表 ==========
const fetchUserList = async () => {
  loading.value = true
  try {
    const { data } = await request.get('/admin/users/', {
      params: {
        page: pagination.page,
        page_size: pagination.pageSize,
        keyword: searchForm.keyword || undefined,
        role: searchForm.role || undefined,
        is_active: searchForm.status || undefined
      }
    })
    userList.value = data.results || data
    pagination.total = data.count || 0
  } catch {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}

// ========== 搜索 / 重置 ==========
const handleSearch = () => {
  pagination.page = 1
  fetchUserList()
}

const handleReset = () => {
  searchForm.keyword = ''
  searchForm.role = ''
  searchForm.status = ''
  handleSearch()
}

// ========== 角色标签映射 ==========
const roleTagType = (role) => {
  const map = { user: '', merchant: 'warning', admin: 'danger', superadmin: 'danger' }
  return map[role] || 'info'
}

const roleLabel = (role) => {
  const map = { user: '用户', merchant: '商家', admin: '管理员', superadmin: '超级管理员' }
  return map[role] || role
}

// ========== 启用/禁用用户 ==========
const handleToggleStatus = async (row) => {
  const action = row.is_active ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(
      `确认${action}用户「${row.username}」？`,
      '提示',
      { type: 'warning' }
    )
    await request.patch(`/admin/users/${row.id}/status/`, { is_active: !row.is_active })
    ElMessage.success(`${action}成功`)
    fetchUserList()
  } catch {
    // 用户取消或请求失败
  }
}

// ========== 分配角色 ==========
const roleDialogVisible = ref(false)
const roleLoading = ref(false)
const currentUser = ref({})
const roleForm = reactive({ role: '' })

const handleAssignRole = (row) => {
  currentUser.value = row
  roleForm.role = row.role
  roleDialogVisible.value = true
}

const submitRole = async () => {
  roleLoading.value = true
  try {
    await request.put(`/admin/users/${currentUser.value.id}/role/`, { role: roleForm.role })
    ElMessage.success('角色分配成功')
    roleDialogVisible.value = false
    fetchUserList()
  } catch {
    // 错误已在拦截器中处理
  } finally {
    roleLoading.value = false
  }
}

// ========== 初始化 ==========
onMounted(() => {
  fetchUserList()
})
</script>

<style scoped>
.page-title {
  font-size: 22px;
  font-weight: 700;
  color: #1f2329;
  margin-bottom: 20px;
}

.action-buttons {
  justify-content: center;
}
</style>

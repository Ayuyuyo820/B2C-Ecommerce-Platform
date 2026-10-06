<template>
  <!-- 地址管理页面 -->
  <div class="page-container">
    <div class="page-card">
      <!-- 页面头部：标题 + 新增按钮 -->
      <div class="page-header">
        <div class="section-title">收货地址</div>
        <el-button type="primary" @click="openDialog()">
          <el-icon><Plus /></el-icon>
          新增地址
        </el-button>
      </div>

      <!-- 加载状态 -->
      <el-skeleton :loading="loading" animated :rows="4" v-if="loading" />

      <!-- 地址列表为空 -->
      <el-empty v-else-if="addressList.length === 0" description="暂无收货地址" />

      <!-- 地址卡片列表 -->
      <div v-else class="address-list">
        <div
          v-for="addr in addressList"
          :key="addr.id"
          class="address-card"
        >
          <!-- 默认标签 -->
          <el-tag v-if="addr.is_default" type="danger" size="small" class="default-tag">
            默认
          </el-tag>

          <!-- 收货人信息 -->
          <div class="address-main">
            <div class="receiver-info">
              <span class="receiver-name">{{ addr.receiver }}</span>
              <span class="receiver-phone">{{ addr.phone }}</span>
            </div>
            <div class="address-detail">
              {{ addr.province }}{{ addr.city }}{{ addr.district }}{{ addr.detail }}
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="address-actions">
            <el-button
              v-if="!addr.is_default"
              link
              type="primary"
              size="small"
              @click="handleSetDefault(addr)"
            >
              设为默认
            </el-button>
            <el-button link type="primary" size="small" @click="openDialog(addr)">
              编辑
            </el-button>
            <el-button link type="danger" size="small" @click="handleDelete(addr)">
              删除
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 新增/编辑地址弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑地址' : '新增地址'"
      width="500px"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="80px"
      >
        <el-form-item label="收货人" prop="receiver">
          <el-input v-model="form.receiver" placeholder="请输入收货人姓名" />
        </el-form-item>

        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入手机号" />
        </el-form-item>

        <el-form-item label="省份" prop="province">
          <el-input v-model="form.province" placeholder="请输入省份" />
        </el-form-item>

        <el-form-item label="城市" prop="city">
          <el-input v-model="form.city" placeholder="请输入城市" />
        </el-form-item>

        <el-form-item label="区/县" prop="district">
          <el-input v-model="form.district" placeholder="请输入区/县" />
        </el-form-item>

        <el-form-item label="详细地址" prop="detail">
          <el-input
            v-model="form.detail"
            type="textarea"
            :rows="2"
            placeholder="请输入详细地址"
          />
        </el-form-item>

        <el-form-item label="设为默认">
          <el-switch v-model="form.is_default" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { getAddressList, addAddress, updateAddress, deleteAddress } from '@/api/address'

// 地址列表
const addressList = ref([])
const loading = ref(false)

// 弹窗相关
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const submitting = ref(false)
const formRef = ref(null)

// 表单数据
const form = reactive({
  receiver: '',
  phone: '',
  province: '',
  city: '',
  district: '',
  detail: '',
  is_default: false
})

// 表单校验规则
const formRules = {
  receiver: [
    { required: true, message: '请输入收货人姓名', trigger: 'blur' }
  ],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ],
  province: [
    { required: true, message: '请输入省份', trigger: 'blur' }
  ],
  city: [
    { required: true, message: '请输入城市', trigger: 'blur' }
  ],
  district: [
    { required: true, message: '请输入区/县', trigger: 'blur' }
  ],
  detail: [
    { required: true, message: '请输入详细地址', trigger: 'blur' }
  ]
}

// 重置表单
const resetForm = () => {
  form.receiver = ''
  form.phone = ''
  form.province = ''
  form.city = ''
  form.district = ''
  form.detail = ''
  form.is_default = false
}

// 打开弹窗（新增/编辑）
const openDialog = (addr) => {
  if (addr) {
    // 编辑模式
    isEdit.value = true
    editId.value = addr.id
    form.receiver = addr.receiver
    form.phone = addr.phone
    form.province = addr.province
    form.city = addr.city
    form.district = addr.district
    form.detail = addr.detail
    form.is_default = addr.is_default
  } else {
    // 新增模式
    isEdit.value = false
    editId.value = null
    resetForm()
  }
  dialogVisible.value = true
}

// 获取地址列表
const fetchAddresses = async () => {
  loading.value = true
  try {
    const { data } = await getAddressList()
    addressList.value = Array.isArray(data) ? data : (data.results || [])
  } catch (e) {
    // 拦截器已处理错误提示
  } finally {
    loading.value = false
  }
}

// 提交表单（新增/编辑）
const handleSubmit = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const payload = { ...form }
    if (isEdit.value) {
      await updateAddress(editId.value, payload)
      ElMessage.success('地址修改成功')
    } else {
      await addAddress(payload)
      ElMessage.success('地址添加成功')
    }
    dialogVisible.value = false
    fetchAddresses()
  } catch (e) {
    // 拦截器已处理错误提示
  } finally {
    submitting.value = false
  }
}

// 删除地址
const handleDelete = async (addr) => {
  try {
    await ElMessageBox.confirm('确定要删除该地址吗？', '删除地址', { type: 'warning' })
    await deleteAddress(addr.id)
    ElMessage.success('地址已删除')
    fetchAddresses()
  } catch (e) {
    // 用户取消或请求失败
  }
}

// 设为默认地址
const handleSetDefault = async (addr) => {
  try {
    await updateAddress(addr.id, {
      receiver: addr.receiver,
      phone: addr.phone,
      province: addr.province,
      city: addr.city,
      district: addr.district,
      detail: addr.detail,
      is_default: true
    })
    ElMessage.success('已设为默认地址')
    fetchAddresses()
  } catch (e) {
    // 拦截器已处理错误提示
  }
}

onMounted(() => {
  fetchAddresses()
})
</script>

<style scoped>
/* 页面头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

/* 地址卡片列表 */
.address-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.address-card {
  position: relative;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: box-shadow 0.2s;
}

.address-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

/* 默认标签 */
.default-tag {
  position: absolute;
  top: -1px;
  left: -1px;
  border-radius: 8px 0 8px 0;
}

/* 收货人信息 */
.address-main {
  flex: 1;
}

.receiver-info {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 6px;
}

.receiver-name {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.receiver-phone {
  font-size: 14px;
  color: #606266;
}

.address-detail {
  font-size: 14px;
  color: #909399;
  line-height: 1.5;
}

/* 操作按钮 */
.address-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
  margin-left: 20px;
}
</style>

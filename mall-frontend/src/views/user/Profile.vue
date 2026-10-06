<template>
  <!-- 个人中心页面 -->
  <div class="page-container">
    <div class="profile-layout">
      <!-- 左侧菜单 -->
      <div class="profile-sidebar page-card">
        <div class="user-avatar-section">
          <el-avatar :size="64" :src="userInfo.avatar">
            {{ userInfo.username?.charAt(0)?.toUpperCase() }}
          </el-avatar>
          <div class="username">{{ userInfo.username }}</div>
        </div>
        <el-menu :default-active="activeMenu" @select="handleMenuSelect">
          <el-menu-item index="info">
            <el-icon><User /></el-icon>
            <span>个人信息</span>
          </el-menu-item>
          <el-menu-item index="password">
            <el-icon><Lock /></el-icon>
            <span>修改密码</span>
          </el-menu-item>
        </el-menu>
      </div>

      <!-- 右侧内容区 -->
      <div class="profile-content page-card">
        <!-- 个人信息 -->
        <template v-if="activeMenu === 'info'">
          <div class="section-title">个人信息</div>
          <el-form
            ref="infoFormRef"
            :model="infoForm"
            :rules="infoRules"
            label-width="100px"
            style="max-width: 500px"
          >
            <!-- 头像上传 -->
            <el-form-item label="头像">
              <el-upload
                class="avatar-uploader"
                :show-file-list="false"
                :http-request="handleAvatarUpload"
                accept="image/*"
              >
                <el-avatar :size="80" :src="infoForm.avatar">
                  {{ infoForm.username?.charAt(0)?.toUpperCase() }}
                </el-avatar>
                <div class="upload-tip">点击更换头像</div>
              </el-upload>
            </el-form-item>

            <!-- 用户名（只读） -->
            <el-form-item label="用户名">
              <el-input v-model="infoForm.username" disabled />
            </el-form-item>

            <!-- 手机号 -->
            <el-form-item label="手机号" prop="phone">
              <el-input v-model="infoForm.phone" placeholder="请输入手机号" />
            </el-form-item>

            <!-- 邮箱 -->
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="infoForm.email" placeholder="请输入邮箱" />
            </el-form-item>

            <!-- 保存按钮 -->
            <el-form-item>
              <el-button type="primary" :loading="infoSaving" @click="handleSaveInfo">
                保存修改
              </el-button>
            </el-form-item>
          </el-form>
        </template>

        <!-- 修改密码 -->
        <template v-if="activeMenu === 'password'">
          <div class="section-title">修改密码</div>
          <el-form
            ref="pwdFormRef"
            :model="pwdForm"
            :rules="pwdRules"
            label-width="120px"
            style="max-width: 500px"
          >
            <el-form-item label="原密码" prop="old_password">
              <el-input
                v-model="pwdForm.old_password"
                type="password"
                show-password
                placeholder="请输入原密码"
              />
            </el-form-item>

            <el-form-item label="新密码" prop="new_password">
              <el-input
                v-model="pwdForm.new_password"
                type="password"
                show-password
                placeholder="请输入新密码"
              />
            </el-form-item>

            <el-form-item label="确认新密码" prop="new_password_confirm">
              <el-input
                v-model="pwdForm.new_password_confirm"
                type="password"
                show-password
                placeholder="请再次输入新密码"
              />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" :loading="pwdSaving" @click="handleChangePassword">
                确认修改
              </el-button>
            </el-form-item>
          </el-form>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { getUserInfo, updateUserInfo, changePassword } from '@/api/user'
import { uploadFile } from '@/api/upload'

// 当前激活的菜单
const activeMenu = ref('info')

// 用户信息
const userInfo = reactive({
  username: '',
  phone: '',
  email: '',
  avatar: ''
})

// 个人信息表单
const infoFormRef = ref(null)
const infoForm = reactive({
  username: '',
  phone: '',
  email: '',
  avatar: ''
})
const infoSaving = ref(false)

// 个人信息校验规则
const infoRules = {
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ]
}

// 密码表单
const pwdFormRef = ref(null)
const pwdForm = reactive({
  old_password: '',
  new_password: '',
  new_password_confirm: ''
})
const pwdSaving = ref(false)

// 确认密码校验
const validateConfirm = (rule, value, callback) => {
  if (value !== pwdForm.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

// 密码校验规则
const pwdRules = {
  old_password: [
    { required: true, message: '请输入原密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  new_password_confirm: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' }
  ]
}

// 切换菜单
const handleMenuSelect = (index) => {
  activeMenu.value = index
}

// 获取用户信息
const fetchUserInfo = async () => {
  try {
    const { data } = await getUserInfo()
    Object.assign(userInfo, data)
    Object.assign(infoForm, {
      username: data.username,
      phone: data.phone,
      email: data.email,
      avatar: data.avatar
    })
  } catch (e) {
    // 拦截器已处理错误提示
  }
}

// 保存个人信息
const handleSaveInfo = async () => {
  const valid = await infoFormRef.value.validate().catch(() => false)
  if (!valid) return

  infoSaving.value = true
  try {
    await updateUserInfo({
      phone: infoForm.phone,
      email: infoForm.email,
      avatar: infoForm.avatar
    })
    Object.assign(userInfo, {
      phone: infoForm.phone,
      email: infoForm.email,
      avatar: infoForm.avatar
    })
    ElMessage.success('保存成功')
  } catch (e) {
    // 拦截器已处理错误提示
  } finally {
    infoSaving.value = false
  }
}

// 头像上传
const handleAvatarUpload = async (options) => {
  const file = options.file
  try {
    const { data } = await uploadFile(file, 'avatar')
    infoForm.avatar = data.url
    ElMessage.success('头像上传成功')
  } catch (e) {
    // 拦截器已处理错误提示
  }
}

// 修改密码
const handleChangePassword = async () => {
  const valid = await pwdFormRef.value.validate().catch(() => false)
  if (!valid) return

  pwdSaving.value = true
  try {
    await changePassword({
      old_password: pwdForm.old_password,
      new_password: pwdForm.new_password,
      new_password_confirm: pwdForm.new_password_confirm
    })
    ElMessage.success('密码修改成功')
    // 清空表单
    pwdFormRef.value.resetFields()
  } catch (e) {
    // 拦截器已处理错误提示
  } finally {
    pwdSaving.value = false
  }
}

onMounted(() => {
  fetchUserInfo()
})
</script>

<style scoped>
/* 布局 */
.profile-layout {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

/* 左侧边栏 */
.profile-sidebar {
  width: 220px;
  flex-shrink: 0;
}

.user-avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 0;
  border-bottom: 1px solid #ebeef5;
  margin-bottom: 8px;
}

.username {
  margin-top: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

/* 右侧内容 */
.profile-content {
  flex: 1;
  min-width: 0;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 24px;
  padding-bottom: 12px;
  border-bottom: 1px solid #ebeef5;
}

/* 头像上传 */
.avatar-uploader {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
}

.upload-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
}
</style>

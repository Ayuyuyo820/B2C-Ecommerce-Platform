<template>
  <div class="layout-wrapper">
    <!-- ========== 顶部导航栏 ========== -->
    <header class="header">
      <div class="header-inner">
        <!-- 左侧：Logo + 导航菜单 -->
        <div class="header-left">
          <div class="logo" @click="router.push('/')">
            <span class="logo-mark">M</span>
            <span class="logo-text">Mall Store</span>
          </div>
          <!-- 主导航菜单（路由模式） -->
          <el-menu
            :default-active="activeMenu"
            mode="horizontal"
            :ellipsis="false"
            router
            class="nav-menu"
          >
            <el-menu-item index="/">首页</el-menu-item>
            <el-menu-item index="/products">商品</el-menu-item>
            <el-menu-item index="/cart">购物车</el-menu-item>
            <el-menu-item index="/orders">我的订单</el-menu-item>

            <!-- 后台入口（商家/管理员在买家端只显示一个入口） -->
            <el-menu-item v-if="isAdmin" index="/admin/statistics">管理后台</el-menu-item>
            <el-menu-item v-else-if="isMerchant" index="/merchant/products">商家后台</el-menu-item>
          </el-menu>
        </div>

        <!-- 右侧：用户信息 -->
        <div class="header-right">
          <template v-if="userStore.isLoggedIn">
            <el-dropdown @command="handleCommand">
              <span class="user-info">
                <el-icon><User /></el-icon>
                <span class="username">{{ userStore.userInfo.username }}</span>
                <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                  <el-dropdown-item command="address">地址管理</el-dropdown-item>
                  <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
          <template v-else>
            <div class="auth-buttons">
              <el-button type="primary" link @click="router.push('/login')">登录</el-button>
              <el-button link @click="router.push('/register')">注册</el-button>
            </div>
          </template>
        </div>
      </div>
    </header>

    <!-- ========== 主内容区域 ========== -->
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/store/user'
import { User, ArrowDown } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// 当前激活的菜单项，跟随路由路径
const activeMenu = computed(() => route.path)

// 判断用户角色：管理员或超级管理员
const isAdmin = computed(() => {
  const role = userStore.userInfo?.role
  return role === 'admin' || role === 'superadmin'
})

// 判断用户角色：商家
const isMerchant = computed(() => {
  return userStore.userInfo?.role === 'merchant'
})

// 下拉菜单命令处理
const handleCommand = (command) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'address':
      router.push('/address')
      break
    case 'logout':
      userStore.logout()
      router.push('/login')
      break
  }
}
</script>

<style scoped>
.layout-wrapper {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f6f7f9;
}

/* 顶部导航栏 */
.header {
  background: rgba(255, 255, 255, 0.94);
  border-bottom: 1px solid rgba(31, 35, 41, 0.08);
  backdrop-filter: blur(14px);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-inner {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 60px;
}

.header-left {
  display: flex;
  align-items: center;
  min-width: 0;
}

/* Logo 样式 */
.logo {
  display: flex;
  align-items: center;
  gap: 9px;
  cursor: pointer;
  margin-right: 24px;
  flex-shrink: 0;
}

.logo-mark {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #1f2329;
  color: #fff;
  font-size: 15px;
  font-weight: 800;
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  color: #1f2329;
  letter-spacing: 0;
}

/* 导航菜单 */
.nav-menu {
  border-bottom: none;
  background: transparent;
  min-width: 0;
}

.nav-menu :deep(.el-menu-item) {
  color: #4e5969;
  font-weight: 500;
}

.nav-menu :deep(.el-menu-item.is-active) {
  color: #1f2329;
  border-bottom-color: #e5482f;
}

.nav-menu .el-menu-item {
  height: 60px;
  line-height: 60px;
}

/* 右侧用户信息 */
.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: #1f2329;
  font-size: 14px;
}

.username {
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.auth-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 主内容区域 */
.main-content {
  flex: 1;
  background:
    linear-gradient(180deg, #ffffff 0, #f6f7f9 170px),
    #f6f7f9;
  padding: 0;
}

@media (max-width: 768px) {
  .header-inner {
    padding: 0 14px;
  }

  .logo-text {
    display: none;
  }
}
</style>

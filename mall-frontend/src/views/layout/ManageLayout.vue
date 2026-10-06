<template>
  <div class="manage-layout">
    <!-- 左侧侧边栏 -->
    <aside class="sidebar">
      <div class="logo" @click="goHome">
        <span class="logo-mark">M</span>
        <span class="logo-text">运营后台</span>
      </div>

      <el-menu
        :default-active="activeMenu"
        class="sidebar-menu"
        router
        background-color="#151922"
        text-color="#aeb6c2"
        active-text-color="#ffffff"
      >
        <!-- 商家菜单 -->
        <template v-if="isMerchant">
          <el-menu-item index="/merchant/products">
            <el-icon><Goods /></el-icon>
            <span>商品管理</span>
          </el-menu-item>
          <el-menu-item index="/merchant/orders">
            <el-icon><List /></el-icon>
            <span>订单管理</span>
          </el-menu-item>
          <el-menu-item index="/merchant/reviews">
            <el-icon><ChatDotRound /></el-icon>
            <span>评价管理</span>
          </el-menu-item>
        </template>

        <!-- 管理员菜单 -->
        <template v-if="isAdmin">
          <el-menu-item index="/admin/users">
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </el-menu-item>
          <el-menu-item index="/admin/products">
            <el-icon><DocumentChecked /></el-icon>
            <span>商品审核</span>
          </el-menu-item>
          <el-menu-item index="/admin/statistics">
            <el-icon><DataAnalysis /></el-icon>
            <span>数据统计</span>
          </el-menu-item>
        </template>
      </el-menu>
    </aside>

    <!-- 右侧主区域 -->
    <div class="main-area">
      <header class="topbar">
        <span class="topbar-title">商城后台</span>
        <el-dropdown @command="handleCommand">
          <span class="user-info">
            <el-icon><User /></el-icon>
            <span class="username">{{ userStore.userInfo?.username }}</span>
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="home">返回商城</el-dropdown-item>
              <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </header>

      <main class="content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/store/user'
import { User, ArrowDown, Goods, List, ChatDotRound, DocumentChecked, DataAnalysis } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const activeMenu = computed(() => route.path)

const isMerchant = computed(() => userStore.userInfo?.role === 'merchant')
const isAdmin = computed(() => ['admin', 'superadmin'].includes(userStore.userInfo?.role))

const goHome = () => router.push('/')

const handleCommand = (command) => {
  if (command === 'home') {
    router.push('/')
  } else if (command === 'logout') {
    userStore.logout()
    router.push('/login')
  }
}
</script>

<style scoped>
.manage-layout { display: flex; height: 100vh; background: #f4f6f8; }

.sidebar {
  width: 216px; background: #151922;
  border-right: 1px solid #151922;
  display: flex; flex-direction: column; flex-shrink: 0;
}
.logo {
  height: 64px; display: flex; align-items: center; justify-content: center; gap: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08); cursor: pointer;
}
.logo-mark {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #e5482f;
  color: #fff;
  font-size: 15px;
  font-weight: 800;
}
.logo-text { font-size: 18px; font-weight: 700; color: #ffffff; }
.sidebar-menu { border-right: none; flex: 1; padding: 12px 10px; }
.sidebar-menu :deep(.el-menu-item) {
  height: 42px;
  line-height: 42px;
  border-radius: 7px;
  margin-bottom: 4px;
}
.sidebar-menu :deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.07);
}
.sidebar-menu :deep(.el-menu-item.is-active) {
  background: #e5482f;
}

.main-area { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.topbar {
  height: 64px; background: #ffffff; border-bottom: 1px solid #e7eaf0;
  display: flex; align-items: center; justify-content: space-between; padding: 0 24px;
}
.topbar-title { font-size: 15px; font-weight: 700; color: #1f2329; }
.user-info { display: flex; align-items: center; gap: 6px; cursor: pointer; color: #1f2329; font-size: 14px; }
.username { max-width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.content { flex: 1; overflow: auto; padding: 4px 4px 24px; }
</style>

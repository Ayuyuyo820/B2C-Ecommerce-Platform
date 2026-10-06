import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useUserStore = defineStore('user', () => {
  // 从localStorage恢复状态
  const token = ref(localStorage.getItem('access_token') || '')
  const refreshTokenVal = ref(localStorage.getItem('refresh_token') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('user_info') || 'null'))

  // 是否已登录
  const isLoggedIn = computed(() => !!token.value)

  // 用户角色
  const userRole = computed(() => userInfo.value?.role || '')

  // 是否管理员
  const isAdmin = computed(() => ['admin', 'superadmin'].includes(userRole.value))

  // 是否商家
  const isMerchant = computed(() => userRole.value === 'merchant')

  // 是否超级管理员
  const isSuperAdmin = computed(() => userRole.value === 'superadmin')

  // 设置登录信息
  function setLoginData(data) {
    token.value = data.access
    refreshTokenVal.value = data.refresh
    userInfo.value = data.user
    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
    localStorage.setItem('user_info', JSON.stringify(data.user))
  }

  // 更新token（刷新后）
  function setToken(newToken) {
    token.value = newToken
    localStorage.setItem('access_token', newToken)
  }

  // 更新用户信息
  function setUserInfo(info) {
    userInfo.value = info
    localStorage.setItem('user_info', JSON.stringify(info))
  }

  // 退出登录，清除所有状态
  function logout() {
    token.value = ''
    refreshTokenVal.value = ''
    userInfo.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_info')
  }

  return {
    token, refreshTokenVal, userInfo,
    isLoggedIn, userRole, isAdmin, isMerchant, isSuperAdmin,
    setLoginData, setToken, setUserInfo, logout
  }
})

import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 15000
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器
request.interceptors.response.use(
  (response) => response,
  (error) => {
    const { response } = error
    if (response) {
      switch (response.status) {
        case 401:
          localStorage.clear()
          ElMessage.error('登录已过期，请重新登录')
          router.push({ path: '/login', query: { redirect: router.currentRoute.value.fullPath } })
          break
        case 403:
          ElMessage.error('没有权限')
          break
        case 400: {
          const data = response.data
          const msg = (data && data.message) ? data.message : '请求错误'
          ElMessage.error(msg)
          break
        }
        case 500:
          ElMessage.error('服务器错误')
          break
        default:
          ElMessage.error(response.statusText || '请求失败')
      }
    } else {
      ElMessage.error('网络连接失败')
    }
    return Promise.reject(error)
  }
)

export default request

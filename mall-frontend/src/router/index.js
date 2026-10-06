import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage } from 'element-plus'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/Login.vue')
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/register/Register.vue')
  },
  {
    path: '/',
    component: () => import('@/views/layout/MainLayout.vue'),
    children: [
      {
        path: '',
        redirect: '/home'
      },
      {
        path: 'home',
        name: 'Home',
        component: () => import('@/views/home/Home.vue')
      },
      {
        path: 'products',
        name: 'ProductList',
        component: () => import('@/views/product/ProductList.vue')
      },
      {
        path: 'product/:id',
        name: 'ProductDetail',
        component: () => import('@/views/product/ProductDetail.vue')
      },
      {
        path: 'cart',
        name: 'Cart',
        component: () => import('@/views/cart/Cart.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'orders',
        name: 'OrderList',
        component: () => import('@/views/order/OrderList.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'order/:id',
        name: 'OrderDetail',
        component: () => import('@/views/order/OrderDetail.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/user/Profile.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'address',
        name: 'Address',
        component: () => import('@/views/user/Address.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'review/:orderId',
        name: 'Review',
        component: () => import('@/views/review/Review.vue'),
        meta: { requiresAuth: true }
      }
    ]
  },
  {
    path: '/admin',
    component: () => import('@/views/layout/ManageLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: 'users', name: 'UserManage', component: () => import('@/views/admin/UserManage.vue'), meta: { requiresAuth: true, role: 'admin' } },
      { path: 'products', name: 'ProductAudit', component: () => import('@/views/admin/ProductAudit.vue'), meta: { requiresAuth: true, role: 'admin' } },
      { path: 'statistics', name: 'Statistics', component: () => import('@/views/admin/Statistics.vue'), meta: { requiresAuth: true, role: 'admin' } }
    ]
  },
  {
    path: '/merchant',
    component: () => import('@/views/layout/ManageLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: 'products', name: 'ProductManage', component: () => import('@/views/merchant/ProductManage.vue'), meta: { requiresAuth: true, role: 'merchant' } },
      { path: 'orders', name: 'OrderManage', component: () => import('@/views/merchant/OrderManage.vue'), meta: { requiresAuth: true, role: 'merchant' } },
      { path: 'reviews', name: 'ReviewManage', component: () => import('@/views/merchant/ReviewManage.vue'), meta: { requiresAuth: true, role: 'merchant' } }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 导航守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')
  const userInfo = JSON.parse(localStorage.getItem('user_info') || 'null')
  const role = userInfo?.role || ''

  if (to.meta.requiresAuth) {
    if (!token) {
      ElMessage.error('请先登录')
      next({ path: '/login', query: { redirect: to.fullPath } })
      return
    }

    if (to.meta.role === 'admin') {
      if (!['admin', 'superadmin'].includes(role)) {
        ElMessage.error('没有权限访问该页面')
        next(from.path || '/')
        return
      }
    }

    if (to.meta.role === 'merchant') {
      if (!['merchant', 'admin', 'superadmin'].includes(role)) {
        ElMessage.error('没有权限访问该页面')
        next(from.path || '/')
        return
      }
    }
  }

  next()
})

export default router

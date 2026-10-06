import request from './request'

// 管理员-用户列表
export const getUserList = (params) => request.get('/admin/users/', { params })

// 管理员-修改用户状态
export const updateUserStatus = (id, data) => request.put(`/admin/users/${id}/status/`, data)

// 管理员-分配角色
export const assignRole = (id, data) => request.put(`/admin/users/${id}/role/`, data)

// 管理员-待审核商品列表
export const getPendingProducts = (params) => request.get('/admin/products/audit/', { params })

// 管理员-审核商品
export const auditProduct = (id, data) => request.post(`/admin/products/${id}/audit/`, data)

// 管理员-首页统计
export const getStatistics = () => request.get('/admin/statistics/')

// 管理员-销售统计
export const getSalesStatistics = (params) => request.get('/admin/statistics/sales/', { params })

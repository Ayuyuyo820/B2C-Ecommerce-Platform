import request from './request'

// 商品列表（公开，支持分页/搜索/筛选）
export const getProductList = (params) => request.get('/products/', { params })

// 商品详情（公开）
export const getProductDetail = (id) => request.get(`/products/${id}/`)

// ===== 商家接口 =====
// 商家发布商品
export const createProduct = (data) => request.post('/merchant/products/', data)

// 商家修改商品
export const updateProduct = (id, data) => request.put(`/merchant/products/${id}/`, data)

// 商家删除商品
export const deleteProduct = (id) => request.delete(`/merchant/products/${id}/`)

// 商家商品列表（仅自己的）
export const getMerchantProductList = (params) => request.get('/merchant/products/', { params })

import request from './request'

// 用户订单列表
export const getOrderList = (params) => request.get('/orders/', { params })

// 订单详情
export const getOrderDetail = (id) => request.get(`/orders/${id}/`)

// 创建订单
export const createOrder = (data) => request.post('/orders/', data)

// 确认支付
export const payOrder = (id) => request.post(`/orders/${id}/pay/`)

// 取消订单
export const cancelOrder = (id) => request.post(`/orders/${id}/cancel/`)

// 确认收货
export const confirmOrder = (id) => request.post(`/orders/${id}/confirm/`)

// 商家发货
export const shipOrder = (id, data) => request.post(`/merchant/orders/${id}/ship/`, data)

// 商家订单列表
export const getMerchantOrderList = (params) => request.get('/merchant/orders/', { params })

import request from './request'

// 商品评价列表
export const getReviewList = (productId, params) => request.get(`/products/${productId}/reviews/`, { params })

// 发表评价
export const createReview = (orderId, data) => request.post(`/orders/${orderId}/review/`, data)

// 商家回复评价
export const replyReview = (id, data) => request.post(`/merchant/reviews/${id}/reply/`, data)

// 商家评价列表
export const getMerchantReviewList = (params) => request.get('/merchant/reviews/', { params })

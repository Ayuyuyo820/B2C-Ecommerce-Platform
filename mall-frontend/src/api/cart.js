import request from './request'

// 购物车列表
export const getCartList = () => request.get('/cart/')

// 添加到购物车
export const addToCart = (data) => request.post('/cart/', data)

// 修改数量
export const updateCartItem = (id, data) => request.put(`/cart/${id}/`, data)

// 删除购物车商品
export const deleteCartItem = (id) => request.delete(`/cart/${id}/`)

// 清空购物车
export const clearCart = () => request.delete('/cart/clear/')

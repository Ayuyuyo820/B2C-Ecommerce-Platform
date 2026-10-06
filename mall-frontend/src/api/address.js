import request from './request'

// 地址列表
export const getAddressList = (params) => request.get('/addresses/', { params })

// 新增地址
export const addAddress = (data) => request.post('/addresses/', data)

// 修改地址
export const updateAddress = (id, data) => request.put(`/addresses/${id}/`, data)

// 删除地址
export const deleteAddress = (id) => request.delete(`/addresses/${id}/`)

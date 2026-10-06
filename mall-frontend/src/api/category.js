import request from './request'

// 分类列表（树形）
export const getCategoryList = () => request.get('/categories/')

// 分类详情
export const getCategoryDetail = (id) => request.get(`/categories/${id}/`)

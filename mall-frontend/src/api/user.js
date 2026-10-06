import request from './request'

// 用户注册
export const register = (data) => request.post('/users/register/', data)

// 用户登录（自定义，返回access+refresh+user）
export const login = (data) => request.post('/users/login/', data)

// 刷新token
export const refreshToken = (data) => request.post('/users/token/refresh/', data)

// 获取当前用户信息
export const getUserInfo = () => request.get('/users/me/')

// 修改个人信息
export const updateUserInfo = (data) => request.put('/users/me/', data)

// 修改密码
export const changePassword = (data) => request.put('/users/change_password/', data)

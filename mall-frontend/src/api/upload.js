import request from './request'

// 通用文件上传
export const uploadFile = (file, type = '') => {
  const formData = new FormData()
  formData.append('file', file)
  if (type) formData.append('type', type)
  return request.post('/upload/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

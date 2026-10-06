<template>
  <div class="page-container">
    <!-- 页面标题 -->
    <h2 class="page-title">评价管理</h2>

    <!-- 评价表格 -->
    <div class="page-card">
      <el-table :data="reviewList" v-loading="loading" stripe border style="width: 100%">
        <el-table-column prop="id" label="ID" width="70" align="center" />
        <el-table-column prop="product_name" label="商品名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="username" label="用户" min-width="100" />
        <!-- 评分列：使用 el-rate 展示 -->
        <el-table-column prop="rating" label="评分" width="180" align="center">
          <template #default="{ row }">
            <el-rate :model-value="row.rating" disabled text-color="#ff9900" />
          </template>
        </el-table-column>
        <el-table-column prop="content" label="评价内容" min-width="220" show-overflow-tooltip />
        <el-table-column prop="create_time" label="评价时间" min-width="170" />
        <!-- 商家回复列 -->
        <el-table-column prop="reply" label="商家回复" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.reply">{{ row.reply }}</span>
            <span v-else style="color: #c0c4cc">暂未回复</span>
          </template>
        </el-table-column>
        <!-- 操作列 -->
        <el-table-column label="操作" width="100" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="!row.reply"
              type="primary"
              size="small"
              @click="handleReply(row)"
            >
              回复
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchReviewList"
          @current-change="fetchReviewList"
        />
      </div>
    </div>

    <!-- 回复弹窗 -->
    <el-dialog v-model="replyDialogVisible" title="回复评价" width="500px">
      <el-form label-width="80px">
        <el-form-item label="评价内容">
          <el-input :model-value="currentReview.content" type="textarea" :rows="3" disabled />
        </el-form-item>
        <el-form-item label="回复内容">
          <el-input
            v-model="replyContent"
            type="textarea"
            :rows="4"
            placeholder="请输入回复内容"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="replyDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="replyLoading" @click="submitReply">确认回复</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'

// ========== 分页 ==========
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

// ========== 表格数据 ==========
const reviewList = ref([])
const loading = ref(false)

// ========== 获取评价列表（商家视角） ==========
const fetchReviewList = async () => {
  loading.value = true
  try {
    const { data } = await request.get('/merchant/reviews/', {
      params: {
        page: pagination.page,
        page_size: pagination.pageSize
      }
    })
    reviewList.value = data.results || data
    pagination.total = data.count || 0
  } catch {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}

// ========== 回复相关 ==========
const replyDialogVisible = ref(false)
const replyLoading = ref(false)
const currentReview = ref({})
const replyContent = ref('')

// 打开回复弹窗
const handleReply = (row) => {
  currentReview.value = row
  replyContent.value = ''
  replyDialogVisible.value = true
}

// 提交回复
const submitReply = async () => {
  if (!replyContent.value.trim()) {
    ElMessage.warning('请输入回复内容')
    return
  }
  replyLoading.value = true
  try {
    await request.post(`/merchant/reviews/${currentReview.value.id}/reply/`, {
      reply: replyContent.value
    })
    ElMessage.success('回复成功')
    replyDialogVisible.value = false
    fetchReviewList()
  } catch {
    // 错误已在拦截器中处理
  } finally {
    replyLoading.value = false
  }
}

// ========== 初始化 ==========
onMounted(() => {
  fetchReviewList()
})
</script>

<style scoped>
.page-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 20px;
}
</style>

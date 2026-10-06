from rest_framework.pagination import PageNumberPagination


'''统一分页类：让前端 ?page_size=20 生效，并限制最大页大小'''
class StandardPagination(PageNumberPagination):
    page_size = 10                       # 默认每页 10 条
    page_size_query_param = 'page_size'  # 前端可通过 ?page_size=xx 覆盖默认值
    max_page_size = 100                  # 上限，防止一次性拉取过多数据拖垮接口
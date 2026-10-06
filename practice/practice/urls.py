from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # 用户模块（注册/登录/CRUD）
    path("api/v1/", include("apps.users.urls")),
]

# 开发环境：让 /media/ 下的上传文件（商品图/头像）能被访问；生产环境交给 nginx
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

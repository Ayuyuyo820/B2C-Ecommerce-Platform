from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from rest_framework_simplejwt.views import TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static
router = DefaultRouter()
# 使用ModelViewSet的方式 CBV
# 用户端商品
router.register(r"products",views.ProductViewSet)
#  商家端商品
router.register(r"merchant/products",views.MerchantProductViewSet,basename="merchant-products")
# 购物车
router.register(r"cart",views.CartItemViewSet)
# 订单模块
router.register(r"orders",views.OrdersViewSet)
# 商家回复
router.register(r"merchant/reviews", views.MerchantReviewViewSet, basename="merchant-reviews")
# 商家订单列表 + 发货
router.register(r"merchant/orders", views.MerchantOrdersViewSet, basename="merchant-orders")

# 常规的FBV
urlpatterns = [
    # 刷新token
    path("users/token/refresh/",TokenRefreshView.as_view(),name="token_refresh"),
    # 注册
    path("users/register/", views.register, name="register"),
    # 登录
    path("users/login/", views.login, name="login"),
    # 用户信息
    path("users/me/", views.me, name="me"),
    # 修改密码
    path("users/change_password/", views.change_password, name="change_password"),
    # 新增和获取用户地址
    path("addresses/",views.addresses,name="addresses"),
    # 修改和删除用户地址
    path("addresses/<int:pk>/", views.address_detail, name="address_detail"),
    # 商品分类列表
    path("categories/",views.categories,name= "categories"),
    # 商品分类详情
    path("categories/<int:pk>/", views.detail_categories, name="detail_categories"),
    # 上传文件
    path("upload/", views.upload, name="upload"),
    # 用户CRUD（列表/详情/修改/删除）
    path("", include(router.urls)),

# 管理后台 - 用户管理
path("admin/users/", views.admin_user_list, name="admin-user-list"),
path("admin/users/<int:pk>/status/", views.admin_user_status, name="admin-user-status"),
path("admin/users/<int:pk>/role/", views.admin_user_role, name="admin-user-role"),
# 管理后台 - 商品审核
path("admin/products/audit/", views.admin_product_audit_list, name="admin-product-audit-list"),
path("admin/products/<int:pk>/audit/", views.admin_product_audit, name="admin-product-audit"),
# 管理后台 - 数据统计
path("admin/statistics/", views.admin_statistics, name="admin-statistics"),
path("admin/statistics/sales/", views.admin_sales, name="admin-statistics-sales"),
]

# 开发环境下让 Django 提供媒体文件
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
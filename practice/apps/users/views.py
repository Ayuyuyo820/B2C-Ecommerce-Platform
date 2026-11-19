import json
import os
from django.utils import timezone
from uuid import uuid4
from datetime import datetime, time, timedelta, timezone as datetime_timezone
from hashlib import sha256
from django.db import transaction
from rest_framework import mixins
from rest_framework.exceptions import ValidationError
from django.db.models import Sum, F, Count
from django.db.models.functions import TruncDate
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.viewsets import GenericViewSet, ModelViewSet, ReadOnlyModelViewSet  # ReadOnlyModelViewSet只能查看
from rest_framework.permissions import AllowAny, IsAuthenticated, BasePermission
from rest_framework.response import Response
from apps.common.pagination import StandardPagination  # 全局分页器（让 page_size 生效）
from django.contrib.auth.hashers import check_password, make_password
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.files.storage import default_storage
from django.utils.text import get_valid_filename
from django.core.cache import cache  # Django 缓存框架（指向 Redis）
from apps.users.models import (
    UserInfo,UserAddresses,ProductCategories,Products,CartItem,
Checkout,Orders,OrdersItem,Reviews
)
from apps.users.serializers import (
    OrderShipSerializer,
    UserMeSerializer, UserInfoSerializer,UserAddressesSerializer,
    ProductCategoriesSerializer,ProductsSerializer,CartItemSerializer,
    MerchantProductUpdateSerializer, ProductStockAdjustmentSerializer,
    CheckoutCreateSerializer, OrdersSerializer,ReviewsSerializer,MerchantOrderSerializer,
    AdminUserSerializer, AdminProductSerializer,MerchantReviewSerializer
)

'''商家端专用权限：只有 merchant / admin / superadmin 能访问'''
class IsMerchantOrAdmin(BasePermission):
    message = "无权限访问商家端接口"
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ["merchant", "admin", "superadmin"]


# 注册接口
@api_view(["POST"])
@permission_classes([AllowAny])  # 不需要登录就能访问
def register(request):
    serializer = UserInfoSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)


# 登录接口
@api_view(["POST"])
@permission_classes([AllowAny])  # 不需要登录就能访问
def login(request):
    username = request.data.get("username")
    password = request.data.get("password")

    # 查找用户
    try:
        user = UserInfo.objects.get(username=username)
    except UserInfo.DoesNotExist:
        return Response({"detail": "用户名不存在"}, status=400)

    # 验证密码（明文 vs 哈希）
    if not check_password(password, user.password):
        return Response({"detail": "密码错误"}, status=400)
    # 校验账号是否被禁用
    if not user.is_active:
        return Response({"detail": "账号已被禁用，请联系管理员"}, status=403)

    # 生成 token
    refresh = RefreshToken.for_user(user)

    # 返回 token 和用户信息
    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": {
            "id": user.id,
            "username": user.username,
            "role":user.role,
        }
    })

'''获取/修改用户信息'''
@api_view(["GET", "PUT"])
@permission_classes([IsAuthenticated])  # 需要登录就能访问
def me(request):
    # request.user 是 DRF 自动从 token 解析出来的当前用户
    user = request.user
    if request.method == "GET":
        serializer = UserMeSerializer(user)  # 序列化转为->json
        return Response(serializer.data)
    # PUT 修改个人信息
    serializer = UserMeSerializer(user,data=request.data,partial=True)  # partial=True 只更新传了的字段
    if serializer.is_valid(): #检查前端传来的数据格式对不对
        serializer.save()      # 验证通过传入数据库
        return Response(serializer.data) # 返回更新后的数据
    return Response(serializer.errors,status=400)


'''修改密码'''
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def change_password(request):
    # 从请求里取出三个字段
    old_password = request.data.get("old_password")
    new_password = request.data.get("new_password")
    new_password_confirm = request.data.get("new_password_confirm")

    # 1. 校验字段是否齐全
    if not old_password or not new_password or not new_password_confirm:
        return Response({"detail": "请填写完整的密码信息"}, status=400)

    # 2. 校验原密码是否正确（用 check_password 对比哈希）
    if not check_password(old_password, request.user.password):
        return Response({"detail": "原密码错误"}, status=400)

    # 3. 校验两次新密码是否一致
    if new_password != new_password_confirm:
        return Response({"detail": "两次新密码不一致"}, status=400)

    # 4. 新密码长度限制
    if len(new_password) < 6:
        return Response({"detail": "新密码长度不能少于6位"}, status=400)

    # 5. 加密并保存
    request.user.password = make_password(new_password)
    request.user.save()

    return Response({"message": "密码修改成功"})

'''获取/新增地址'''
@api_view(["GET","POST"])
@permission_classes([IsAuthenticated])
def addresses(request):
    # GET：获取当前用户的所有地址，默认地址排最前
    if request.method == "GET":
        address_list = UserAddresses.objects.filter(user=request.user).order_by("-is_default", "-id")
        serializer = UserAddressesSerializer(address_list, many=True)
        return Response(serializer.data)

    # POST：新增地址
    serializer = UserAddressesSerializer(data=request.data)
    if serializer.is_valid():
        # 如果用户勾选了"设为默认"，先把其他默认地址取消
        is_default = serializer.validated_data.get("is_default", False)
        if is_default:
            UserAddresses.objects.filter(user=request.user, is_default=True).update(is_default=False)
        # 保存新地址
        serializer.save(user=request.user)
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)
'''修改/删除地址'''
@api_view(['PUT','DELETE'])
@permission_classes([IsAuthenticated])
def address_detail(request, pk):
    # 用 filter().first() 代替 get()，找不到返回 None 而不是直接报错
    address = UserAddresses.objects.filter(pk=pk, user=request.user).first()
    if not address:
        return Response({"detail": "地址不存在"}, status=404)

    # DELETE：删除地址
    if request.method == "DELETE":
        address.delete()
        return Response(status=204)

    # PUT：修改地址
    serializer = UserAddressesSerializer(address, data=request.data, partial=True)
    if serializer.is_valid():
        # 如果用户把这条设为默认，先取消其他默认地址（排除当前这条）
        if serializer.validated_data.get("is_default"):
            UserAddresses.objects.filter(user=request.user, is_default=True).exclude(pk=address.pk).update(is_default=False)
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=400)

'''商品分类列表'''
@api_view(['GET'])
@permission_classes([AllowAny]) # 需要登录就能访问
def categories(request):
    cache_key = "category:tree"     # 缓存的 key（实际存成 mall:category:tree）
    cached = cache.get(cache_key)    # 先查 Redis
    if cached is not None:  # 命中则直接返回，不再查库
        return Response(cached)
    category_list  = ProductCategories.objects.filter(parent = None) # 只查一级分类
    serializer  = ProductCategoriesSerializer(category_list,many=True)#  many=True 序列化多条数据
    cache.set(cache_key, serializer.data, timeout=60 * 30)  # 未命中查库后 缓存 30 分钟
    return  Response(serializer.data)
'''商品分类详情'''
@api_view(['GET'])
@permission_classes([AllowAny])
def detail_categories(request,pk):
    # 缓存
    cache_key = f"category:detail:{pk}" # 每个分类一个缓存 key
    cached = cache.get(cache_key)
    if cached is not None:
        # 命中"空值标记"说明之前查过确实不存在，直接返回 404，不查库
        if cached == "__not_found__":
            return Response({"detail": "商品分类不存在"}, status=404)
        return Response(cached)
    try:
        category_list = ProductCategories.objects.get(pk=pk)
    except ProductCategories.DoesNotExist:
        # 查不到也缓存一个空标记（短 TTL），防恶意请求反复穿透数据库
        cache.set(cache_key, "__not_found__", timeout=60)
        return Response({"detail": "商品分类不存在"}, status=404)

    data = ProductCategoriesSerializer(category_list).data
    cache.set(cache_key, data, timeout=60 * 30)  # 命中后缓存 30 分钟
    return Response(data)

'''商品模块 - ModelViewSet 自动生成增删改查
GET    /products/       → 列表
POST   /products/       → 新增
GET    /products/{id}/  → 详情
PUT    /products/{id}/  → 全量更新
PATCH  /products/{id}/  → 局部更新
DELETE /products/{id}/  → 删除
'''

'''用户端商品'''

class ProductViewSet(ReadOnlyModelViewSet):
    queryset = Products.objects.all() # 获取数据
    # 序列化
    serializer_class  = ProductsSerializer
    permission_classes = [AllowAny]  # 公开商品
    def list(self, request, *args, **kwargs):
        # 分页链接和图片地址可能包含请求域名。
        url_hash = sha256(request.build_absolute_uri().encode()).hexdigest()
        cache_key = f"products:list:{url_hash}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=60 * 5)
        return response

    def get_queryset(self):
        # 1、只查上架商品                                #select_related 一次性把关联的数据都查出来
        qs = Products.objects.filter(is_active=True).select_related('category','merchant')  # is_active商品是否上架 category分类 merchant 商家
        # request.query_params 支持按分类筛选：/api/v1/products/?category=1  解析成字典 {"category": "1", "page_size": "8"}
        params = self.request.query_params  # query_params 就是 URL 里 ? 后面的参数。
        category_id  = params.get('category')
        # 2. 如果前端传了分类ID，过滤分类（非法值如 abc 时忽略，避免 int() 报 500）
        if category_id:
            try:
                qs = qs.filter(category_id = int(category_id))
            except (ValueError, TypeError):
                pass
        # 3. 如果前端传了关键词，模糊搜索商品名
        keyword  = params.get('keyword')
        if keyword:
            qs = qs.filter(name__icontains=keyword)
        # 4. 如果前端传了最低价，过滤价格（非法值忽略，避免报 500）
        min_price = params.get('min_price')
        if min_price:
            try:
                qs = qs.filter(price__gte=float(min_price))
            except (ValueError, TypeError):
                pass
        # 5. 如果前端传了最高价，过滤价格（非法值忽略，避免报 500）
        max_price = params.get('max_price')
        if max_price:
            try:
                qs = qs.filter(price__lte=float(max_price))
            except (ValueError, TypeError):
                pass
        # 6. 如果前端传了排序字段，排序
        ordering = params.get('ordering')
        # 白名单：只允许这些字段排序，防止传非法字段报 500
        allowed = ["price", "-price", "sales", "-sales", "create_time", "-create_time", "id", "-id"]
        if ordering in ("id", "-id"):
            return qs.order_by(ordering)
        if ordering in allowed:
            return qs.order_by(ordering, "id")
        return qs.order_by("id")
        # 查询商品评价列表
    @action(detail=True,methods=["GET"],permission_classes=[AllowAny])
    def reviews(self,request,pk=None):
        # ① 拿到 URL 里的 pk（就是 product_id）
        # ② 查这个商品的所有评价
        reviews = Reviews.objects.filter(product_id=pk)
        # ③ 支持按星级筛选：/products/1/reviews/?rating=5（非法值忽略，避免报 500）
        rating = request.query_params.get('rating')
        if rating:
            try:
                reviews = reviews.filter(rating=int(rating))
            except (ValueError, TypeError):
                pass
        # 序列化
        serializer = ReviewsSerializer(reviews,many=True)
        # ⑤ 计算 stats（平均分、好评率、各星级数量）
        all_ratings = [r.rating for r in Reviews.objects.filter(product_id=pk)]  #评分列表
        count = len(all_ratings) #总评分数量
        stats = {
            "average_rating": round(sum(all_ratings) / count, 1) if count else 0, # 计算平均分
            "good_rate": round(len([r for r in all_ratings if r >= 4]) / count * 100) if count else 0, #好评率
            "count": {str(i): all_ratings.count(i) for i in range(1, 6)} #1‑5 分每个分数的数量统计
        }

        return  Response({
            "count":count,
            "results":serializer.data,
            "stats":stats
        })
'''商家端商品管理 - ModelViewSet
POST   /merchant/products/       → 发布商品
GET    /merchant/products/       → 商品列表
GET    /merchant/products/{id}/  → 商品详情
PUT    /merchant/products/{id}/  → 修改商品
PATCH  /merchant/products/{id}/  → 局部修改商品资料
POST   /merchant/products/{id}/adjust-stock/  → 增减库存
DELETE /merchant/products/{id}/  → 删除商品
'''
class MerchantProductViewSet(ModelViewSet):
    # 获取数据
    queryset = Products.objects.all()
    # 序列化
    serializer_class = ProductsSerializer
    permission_classes = [IsAuthenticated, IsMerchantOrAdmin] # 发布/管理商品需登录

    # 只查看当前商家的商品
    def get_queryset(self):
        return Products.objects.filter(merchant=self.request.user)

    def get_serializer_class(self):
        if self.action in {"update", "partial_update"}:
            return MerchantProductUpdateSerializer
        return super().get_serializer_class()

    # 创建商品
    def perform_create(self, serializer):
        # 发布商品时自动绑定当前用户为商家
        serializer.save(merchant=self.request.user)

    @action(detail=True, methods=["post"], url_path="adjust-stock")
    @transaction.atomic
    def adjust_stock(self, request, pk=None):
        product = self.get_object()  # 商品必须属于当前商家
        serializer = ProductStockAdjustmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        delta = serializer.validated_data["delta"]
        products = self.get_queryset().filter(pk=product.pk)
        if delta < 0:
            products = products.filter(stock__gte=-delta)
        else:
            products = products.filter(stock__lte=serializer.MAX_STOCK - delta)

        # 按数据库当前库存增减，库存边界判断和写入由同一条 SQL 完成。
        updated = products.update(stock=F("stock") + delta, updated_at=timezone.now())
        if not updated:
            message = "库存不足，无法减少指定数量" if delta < 0 else "调整后的库存超出上限"
            raise ValidationError({"delta": message})

        product.refresh_from_db(fields=["stock"])
        return Response({"stock": product.stock})

'''购物车'''
class CartItemViewSet(ModelViewSet):
    # 获取数据
    queryset = CartItem.objects.all()
    # 序列化
    serializer_class = CartItemSerializer
    # 限制条件
    permission_classes = [IsAuthenticated]

    # 获取用户购物车记录
    def get_queryset(self):
        # 购物车列表一次性查出商品信息，减少查询次数
        queryset = CartItem.objects.filter(user=self.request.user).select_related("product")
        # DRF 在 perform_update 前查询购物车项，先锁行才能读到上次提交的数量。
        if self.action in {"update", "partial_update"}:
            queryset = queryset.select_for_update()
        return queryset

    @transaction.atomic
    def perform_create(self, serializer):
        product = serializer.validated_data["product"]
        quantity = serializer.validated_data.get("quantity", 1)

        # 联合唯一约束防止重复创建，行锁让已有记录上的并发累加依次执行。
        existing_item, created = CartItem.objects.select_for_update().get_or_create(
            user=self.request.user, product=product,
            defaults={"quantity": quantity, "total_price": product.price * quantity},
        )

        if not created:
            existing_item.quantity += quantity
            existing_item.total_price = product.price * existing_item.quantity
            existing_item.save(update_fields=["quantity", "total_price"])

        serializer.instance = existing_item

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        # 兼容只提交单个字段的 PUT 请求，省略的字段按局部更新处理。
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)

    def perform_update(self, serializer):
        item = serializer.instance
        changes = serializer.validated_data.copy()
        # 改数量时一次写入数量和小计，单独勾选时只写 is_selected。
        if "quantity" in changes:
            changes["total_price"] = item.product.price * changes["quantity"]
        for field, value in changes.items():
            setattr(item, field, value)
        if changes:
            item.save(update_fields=list(changes))

    def list(self,request,*args,**kwargs):
        # 第1步：获取当前用户的购物车数据
        queryset  = self.get_queryset()  # → CartItem.objects.filter(user=request.user)
        # 第2步：尝试分页（settings.py 里配置了 PAGE_SIZE = 10）
        page = self.paginate_queryset(queryset)
        # 第3步：如果有分页（数据量超过10条）
        if page is not None:
            # 序列化当前页的数据
            serializer  = self.get_serializer(page,many=True)
            # 生成分页响应（包含 count、next、previous、results）
            paginated = self.get_paginated_response(serializer.data)

            # 第4步：计算选中商品的总金额
            selected_items = queryset.filter(is_selected=True)  # 只算选中的
            total_amount = sum(item.total_price for item in selected_items)

            # 第5步：往分页响应里额外加两个字段
            paginated.data['total_amount'] = str(total_amount)  # 总金额
            paginated.data['selected_count'] = selected_items.count()  # 选中数量

            return paginated  # 返回带分页的响应

            # 第6步：如果数据量少，不需要分页
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    # 清空
    @action(detail=False, methods=['delete'])
    def clear(self, request):
        CartItem.objects.filter(user=request.user).delete()
        return Response(status=204)

'''订单模块'''
class OrdersViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
    GenericViewSet,
):
    queryset = Orders.objects.all()
    serializer_class = OrdersSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = (
            Orders.objects.filter(user=self.request.user)
            .select_related("merchant", "checkout")
            .prefetch_related("items__product")
            .order_by("-create_time", "-pk")
        )
        status = self.request.query_params.get("status")
        if status and self.action == "list":
            qs = qs.filter(status=status)
        return qs

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = CheckoutCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        address = UserAddresses.objects.filter(pk=data["address_id"], user=request.user).first()
        if address is None:
            raise ValidationError({"address_id": "收货地址不存在或不属于当前用户"})

        if "cart_ids" in data:
            cart_ids = data["cart_ids"]
            cart_items = list(
                CartItem.objects.filter(pk__in=cart_ids, user=request.user)
                .select_related("product")
                .order_by("product_id", "pk")
                .select_for_update()
            )
            if len(cart_items) != len(data["cart_ids"]):
                raise ValidationError({"cart_ids": "购物车商品无效或重复，请刷新后重新选择"})
            lines = [(item.product, item.quantity) for item in cart_items]
        else:
            product = Products.objects.select_for_update().filter(pk=data["product_id"]).first()
            if product is None:
                raise ValidationError({"product_id": "商品不存在"})
            lines = [(product, data["quantity"])]

        items_by_merchant = {}
        for product, quantity in lines:
            # 加购后可能发生下架或审核变化，两种结算入口都在此重新校验。
            # 在创建结算单、订单和扣库存之前拒绝无商家、不可售或数值异常的数据。
            # 此处库存非负仅检查数据合法性；购买数量是否足够，
            # 仍由下方 stock__gte=quantity 的条件更新和受影响行数判断。
            if (
                not product.merchant_id or not product.is_active
                or product.audit_status != "approved" or quantity < 1
                or product.price < 0 or product.stock < 0
            ):
                raise ValidationError({"detail": f"商品「{product.name}」无法结算，请检查购物车"})
            items_by_merchant.setdefault(product.merchant_id, []).append((product, quantity))

        checkout = Checkout.objects.create(
            user=request.user,
            total_amount=sum(product.price * quantity for product, quantity in lines),
            order_count=len(items_by_merchant),
            address_snapshot={
                "receiver": address.receiver,
                "phone": address.phone,
                "full_address": f"{address.province}{address.city}{address.district}{address.detail}",
            },
        )
        order_ids = []
        for merchant_id, items in items_by_merchant.items():
            order = Orders.objects.create(
                user=request.user,
                merchant_id=merchant_id,
                checkout=checkout,
                order_no=f"ORD{uuid4().hex[:29]}",
                total_amount=sum(product.price * quantity for product, quantity in items),
                remark=data["remark"],
            )
            order_ids.append(order.pk)
            for product, quantity in items:
                updated = Products.objects.filter(
                    pk=product.pk, stock__gte=quantity,
                ).update(stock=F("stock") - quantity)
                if not updated:
                    raise ValidationError({"detail": f"商品「{product.name}」库存不足"})
                OrdersItem.objects.create(
                    order=order, product=product, price=product.price, quantity=quantity,
                    # 两种结算入口都在这里保存下单时的名称和图片地址。
                    product_name=product.name, product_image=product.image,
                )

        if "cart_ids" in data:
            CartItem.objects.filter(pk__in=cart_ids, user=request.user).delete()
        orders = self.get_serializer(
            self.get_queryset().filter(pk__in=order_ids).order_by("pk"), many=True,
        ).data
        return Response({**orders[0], "orders": orders}, status=201)

    def _locked_checkout_orders(self, order):
        orders = Orders.objects.filter(user=self.request.user)
        if order.checkout_id:
            checkout = Checkout.objects.select_for_update().get(pk=order.checkout_id)
            return checkout, orders.filter(checkout=checkout)
        return None, orders.filter(pk=order.pk)

    @action(detail=True, methods=["POST"])
    @transaction.atomic
    def pay(self, request, pk=None):
        order = self.get_object()
        checkout, orders = self._locked_checkout_orders(order)
        if checkout and checkout.pay_time:
            return Response(self.get_serializer(self.get_object()).data)

        locked_orders = list(orders.select_for_update().order_by("pk"))
        if any(row.status != "pending" for row in locked_orders):
            return Response({"detail": "订单状态不允许支付"}, status=400)

        paid_at = timezone.now()
        orders.update(status="paid", pay_time=paid_at)
        if checkout:
            checkout.pay_time = paid_at
            checkout.save(update_fields=["pay_time"])
        return Response(self.get_serializer(self.get_object()).data)

    @action(detail=True, methods=["POST"])
    @transaction.atomic
    def cancel(self, request, pk=None):
        order = self.get_object()
        checkout, orders = self._locked_checkout_orders(order)
        if checkout and checkout.cancelled_at:
            return Response(self.get_serializer(self.get_object()).data)

        locked_orders = list(orders.select_for_update().order_by("pk"))
        if any(row.status != "pending" for row in locked_orders):
            return Response({"detail": "订单状态不允许取消"}, status=400)

        items = OrdersItem.objects.filter(
            order_id__in=[row.pk for row in locked_orders], product_id__isnull=False,
        ).order_by("product_id", "pk")
        for item in items:
            Products.objects.filter(pk=item.product_id).update(stock=F("stock") + item.quantity)
        orders.update(status="cancelled")
        if checkout:
            checkout.cancelled_at = timezone.now()
            checkout.save(update_fields=["cancelled_at"])
        return Response(self.get_serializer(self.get_object()).data)

    @action(detail=True, methods=["POST"])
    def confirm(self, request, pk=None):
        order = self.get_object()
        updated = Orders.objects.filter(pk=order.pk, user=request.user, status="shipped").update(
            status="completed", complete_time=timezone.now(),
        )
        if not updated:
            return Response({"detail": "订单状态不允许确认收货"}, status=400)
        return Response(self.get_serializer(self.get_object()).data)

    # 发表评价
    @action(detail=True, methods=["POST"])
    def review(self, request, pk=None):
        # 先查订单
        order = self.get_object()  # 要查的是 Orders 表，pk 正好是订单ID
        if order.status != 'completed':
            return Response({"detail": "只能评价已完成的订单"}, status=400)

        # 前端传的是数组：{reviews: [{product_id, rating, content, images}, ...]}
        reviews_data = request.data.get("reviews", [])
        if not reviews_data:
            return Response({"detail": "评价内容不能为空"}, status=400)

        # 把订单里的商品映射成 {商品ID: 订单项}，方便校验传入的 product_id 是否属于本订单
        order_items = {item.product_id: item for item in order.items.all()}

        created_count = 0
        for r in reviews_data:
            product_id = r.get("product_id")
            rating = r.get("rating", 5)
            content = r.get("content", "")
            images = r.get("images", [])
            # 校验0：评分必须是 1~5 的整数，非法值跳过本条
            try:
                rating = int(rating)
            except (ValueError, TypeError):
                continue
            if rating < 1 or rating > 5:
                continue
            # 校验0：images 必须是列表，否则按无图处理
            if not isinstance(images, list):
                images = []
            # 校验1：传的商品必须属于该订单，防止给别人的商品刷评价
            if product_id not in order_items:
                continue
            # 校验2：同一个订单里的同一个商品只能评一次，评过了就跳过
            if Reviews.objects.filter(user=request.user, product_id=product_id, order=order).exists():
                continue
            Reviews.objects.create(
                user=request.user,
                product_id=product_id,
                order=order,
                rating=rating,
                content=content,
                images=json.dumps(images),  # 数组转字符串存数据库
            )
            created_count += 1

        # 只有当订单里所有商品都评完了，才标记为"已评价"
        all_product_ids = set(order.items.filter(product_id__isnull=False).values_list("product_id", flat=True))
        reviewed_ids = set(Reviews.objects.filter(user=request.user, order=order).values_list("product_id", flat=True))
        if all_product_ids and all_product_ids.issubset(reviewed_ids):
            order.is_reviewed = True
            order.save()

        # 一条都没评成功，说明这些商品全都评过了
        if created_count == 0:
            return Response({"detail": "这些商品都已评价过"}, status=400)

        return Response({"order_id": order.id, "count": created_count, "message": "评价成功"}, status=201)

'''商家回复'''
class MerchantReviewViewSet(ReadOnlyModelViewSet):  # 只读：商家只能查看/回复，不能改或删评价
    queryset = Reviews.objects.all() # 获取数据
    serializer_class = MerchantReviewSerializer  # 序列化
    permission_classes = [IsAuthenticated, IsMerchantOrAdmin]

    # 只查询商家名下的商品的评价
    def get_queryset(self):
        # 商家 A 登录后，只能查到自己商品下面收到的评价      一次查询把关联的 product 和 user 两张表一起查出来并缓存
        return Reviews.objects.filter(product__merchant=self.request.user).select_related('product','user')

    @action(detail=True,methods=["POST"])
    def reply(self,request,pk=None):
        review = self.get_object()  # get_object 查的是当前 ViewSet 的 queryset 对应的表。
        review.reply = request.data.get('reply','')
        review.save()
        return Response({"id":review.id,"reply":review.reply,"message":"回复成功"})

'''文件上传'''
# 上传类型白名单：只允许这三类目录，防止路径穿越
ALLOWED_FILE_TYPES = {"avatars", "products", "reviews"}
# 上传后缀白名单：只允许图片
ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
# 上传大小上限：5MB
MAX_SIZE = 5 * 1024 * 1024

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload(request):
    # 从请求里拿到上传的文件
    file = request.FILES.get('file') #FILES接收上传文件的对象
    if not file:
        return  Response({"detail":"请上传文件"},status=400)
    # 后缀校验：只允许图片格式
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_EXTS:
        return Response({"detail": "只支持 jpg/jpeg/png/gif/webp 格式"}, status=400)
    # 大小校验
    if file.size > MAX_SIZE:
        return Response({"detail": "文件不能超过 5MB"}, status=400)
    # 获取文件类型（avatars/products/reviews），不在白名单内一律归入 uploads
    file_type = request.data.get("type") or "uploads"
    if file_type not in ALLOWED_FILE_TYPES:
        file_type = "uploads"
    # 把文件名里的特殊字符去掉，防止安全问题
    filename = get_valid_filename(file.name)
    # 生成唯一文件名：类型/随机字符串_原文件名
    path = default_storage.save(f"{file_type}/{uuid4().hex}_{filename}", file)

    # 返回完整 URL
    return Response({
        "url": request.build_absolute_uri(default_storage.url(path)),
        "filename": filename,
        "size": file.size,
    })

'''商家订单管理 - ModelViewSet
GET    /merchant/orders/            → 订单列表（仅当前商家的订单）
POST   /merchant/orders/{id}/ship/  → 发货
'''
class MerchantOrdersViewSet(ReadOnlyModelViewSet):
    serializer_class = MerchantOrderSerializer
    permission_classes = [IsAuthenticated, IsMerchantOrAdmin]

    def get_queryset(self):
        user = self.request.user
        # 角色校验：只有商家/管理员/超管能看到商家订单
        if user.role not in ["merchant", "admin", "superadmin"]:
            return Orders.objects.none()
        # 只查 merchant 指向自己的订单
        qs = Orders.objects.filter(merchant=user).select_related("user", "checkout").prefetch_related("items__product").order_by("-create_time", "-pk")

        # 状态筛选：前端传的值和后端模型不同，做映射
        # unpaid(待支付)→pending；pending_ship(待发货)→paid
        status_map = {"unpaid": "pending", "pending_ship": "paid"}
        status = self.request.query_params.get("status")
        if status and self.action == "list":
            status = status_map.get(status, status)
            qs = qs.filter(status=status)
        return qs

    # 发货：paid → shipped
    @action(detail=True, methods=["POST"])
    def ship(self, request, pk=None):
        order = self.get_object()  # 在 get_queryset 过滤后的范围内找，天然只能操作自己的订单
        serializer = OrderShipSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # 状态判断与物流信息保存使用同一条 SQL，避免重复发货覆盖单号。
        updated = Orders.objects.filter(pk=order.pk, merchant=request.user, status="paid").update(
            status="shipped", ship_time=timezone.now(), **serializer.validated_data,
        )
        if not updated:
            return Response({"detail": "订单状态不允许发货"}, status=400)
        return Response(self.get_serializer(self.get_object()).data)
'''校验是否为管理员，不是则返回 True 表示需要拦截'''
def is_not_admin(user):
    return user.role not in ['admin','superadmin']

''' 用户列表'''
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_user_list(request):
    if is_not_admin(request.user):
        return Response({'detail':'无权限'},status=403)
    # 普通管理员只查看用户和商家，后续筛选也在这个权限范围内执行。
    qs = UserInfo.objects.all()
    if request.user.role == "admin":
        qs = qs.filter(role__in=["user", "merchant"])
    # 角色筛选
    role = request.query_params.get("role")
    if role:
        qs = qs.filter(role=role)
    # 关键词搜索：用户名/手机/邮箱
    keyword = request.query_params.get('keyword')
    if keyword:
        qs = qs.filter(username__icontains=keyword) | qs.filter(phone__icontains=keyword) | qs.filter(email__icontains=keyword)
    # is_active 状态筛选
    is_active = request.query_params.get('is_active')
    if is_active is not None and is_active != '':
        qs = qs.filter(is_active=is_active.lower()=="true")

    # 分页
    paginator = StandardPagination()
    page = paginator.paginate_queryset(qs.order_by("id"),request)
    serializer = AdminUserSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)

def _lock_admin_target(pk):
    # 两个管理入口都先按 ID 顺序锁超管，再锁目标账号，调用方必须开启事务。
    # 并发禁用、降级会依次检查，避免各自认为还有其他超管可用。
    superadmins = list(
        UserInfo.objects.filter(role="superadmin").order_by("pk").select_for_update()
    )
    user = UserInfo.objects.select_for_update().filter(pk=pk).first()
    active_superadmin_count = sum(admin.is_active for admin in superadmins)
    return user, active_superadmin_count


'''修改用户状态'''
# 修改用户状态（启用/封禁）
@api_view(["PATCH"])                      # 只接受 PATCH 请求（改单字段语义）
@permission_classes([IsAuthenticated])    # 必须登录
@transaction.atomic
def admin_user_status(request, pk):
    # 权限校验：只有管理员/超管能操作
    if is_not_admin(request.user):
        return Response({"detail": "无权限"}, status=403)

    # 必须明确提交 JSON 布尔值，漏传、字符串或数字都返回错误。
    is_active = request.data.get("is_active")
    if type(is_active) is not bool:
        return Response({"detail": "is_active 必须为 true 或 false"}, status=400)

    user, active_superadmin_count = _lock_admin_target(pk)
    if user is None:
        return Response({"detail": "用户不存在"}, status=404)

    # 等待锁期间操作者可能已被降级或禁用，使用数据库当前权限再次判断。
    operator_role = (
        UserInfo.objects.filter(pk=request.user.pk, is_active=True)
        .values_list("role", flat=True).first()
    )
    if operator_role not in ["admin", "superadmin"]:
        return Response({"detail": "无权限"}, status=403)
    # 列表隐藏之外，接口也限制目标角色，防止手动指定管理员或超管 ID。
    if operator_role == "admin" and user.role not in ["user", "merchant"]:
        return Response({"detail": "只能管理普通用户和商家"}, status=403)
    if user.role == "superadmin" and user.is_active and not is_active and active_superadmin_count <= 1:
        return Response({"detail": "至少保留一个启用的超级管理员"}, status=400)

    user.is_active = is_active
    # 只更新状态，避免覆盖其他账号资料。
    user.save(update_fields=["is_active"])

    # is_active 为 false → 返回"已禁用"；为 true → "已启用"
    return Response({"message": "用户已禁用" if not is_active else "用户已启用"})

'''分配角色'''
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def admin_user_role(request,pk):
    # 只有超级管理员能改角色
    if request.user.role != 'superadmin':
        return Response({"detail":"无权限"},status=403)
    # 获取用户角色
    role = request.data.get('role')
    valid_roles = ['user','merchant','admin','superadmin']
    if role not in valid_roles:
        return Response({"detail":"非法角色"},status=400)

    user, active_superadmin_count = _lock_admin_target(pk)
    if user is None:
        return Response({"detail":"用户不存在"},status=404)
    # 与禁用入口共用锁定顺序，并复核等待期间可能发生的权限变化。
    if not UserInfo.objects.filter(pk=request.user.pk, role="superadmin", is_active=True).exists():
        return Response({"detail":"无权限"},status=403)
    if user.role == "superadmin" and user.is_active and role != "superadmin" and active_superadmin_count <= 1:
        return Response({"detail": "至少保留一个启用的超级管理员"}, status=400)
    user.role = role
    user.save(update_fields=["role"])
    return Response({"message": "角色分配成功", "user": {"id": user.id, "username": user.username, "role": user.role}})


'''待审核商品列表'''
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_product_audit_list(request):
    # 校验身份
    if is_not_admin(request.user):
        return Response({"detail":"无权限"},status=403)
    # 获取商家待上架商品
    # 新发布的商品在前，同一发布时间按唯一 ID 排序，保证分页顺序确定。
    qs = Products.objects.select_related('merchant').order_by('-create_time', '-id')
    status = request.query_params.get('status')
    # 判断商品状态
    if status == 'pending':         # 前端点了「待审核」标签
        qs = qs.filter(audit_status='pending')  # 只看 pending
    elif status == 'reviewed':      # 前端点了「已审核」标签
        qs = qs.filter(audit_status__in=["approved","rejected"]) # 看 approved + rejected 两种
    # 前端没传 status → 不过滤，查全部

    # 分页：商品可能很多，按页返回（前端传 page / page_size）
    paginator = StandardPagination()                        # ① 创建分页器对象
    page = paginator.paginate_queryset(qs, request)           # ② 按请求里的分页参数切分数据，得到"当前页"
    serializer = AdminProductSerializer(page, many=True)      # ③ 把当前页数据序列化成 JSON
    return paginator.get_paginated_response(serializer.data)  # ④ 返回带 count/next/previous 的分页结构

'''审核商品'''
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def admin_product_audit(request,pk): # 传入商品ID
    # 判断权限
    if is_not_admin(request.user):
        return Response({"detail":"无权限"},status=403)
    # 获取商品
    product = Products.objects.filter(pk=pk).first()
    if not product:
        return  Response({"detail":"商品不存在"},status=404)

    action = request.data.get("action")         # 前端告诉后端"这次审核是通过还是拒绝"
    reason = request.data.get("reason", "")     # 拒绝原因

    if action == 'approve':  # 管理员点了「通过」
        product.audit_status = 'approved'  # 审核状态 → 已通过
        product.is_active = True  # 上架（商品对外可见）
        product.reject_reason = ""  # 清空拒绝原因（通过不需要原因）

    elif action == 'reject':  # 管理员点了「拒绝」
        product.audit_status = 'rejected'  # 审核状态 → 已拒绝
        product.is_active = False  # 不上架（商品隐藏）
        product.reject_reason = reason  # 存下拒绝原因

    else:  # 前端传了别的值
        return Response({"detail": "action 参数错误"}, status=400)
    # 审核只写审核相关字段，避免把读取商品时的库存写回数据库。
    product.save(update_fields=["audit_status", "is_active", "reject_reason", "updated_at"])
    return Response({
        "message": "审核通过" if action == "approve" else "已拒绝",
        "product": {"id": product.id, "is_active": product.is_active}
    })

'''首页统计'''
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_statistics(request):
    # 权限校验：只有管理员/超管能看
    if is_not_admin(request.user):
        return Response({"detail": "无权限"}, status=403)
    today = timezone.localdate()
    # 新口径使用新版本缓存，并按日期隔离，避免跨午夜读到昨天的数据。
    cache_key = f'admin:statistics:daily:v2:{today}'
    cached = cache.get(cache_key)
    if cached is not None:
        return  Response(cached)
    start_at = timezone.make_aware(datetime.combine(today, time.min))
    end_at = timezone.make_aware(datetime.combine(today + timedelta(days=1), time.min))
    # 成交额按支付时间统计，仅包括已支付、已发货、已完成的订单。
    # 时间范围采用左闭右开，明天零点的数据留给明天。
    today_amount = Orders.objects.filter(
        status__in=["paid", "shipped", "completed"],
        pay_time__gte=start_at, pay_time__lt=end_at,
    ).aggregate(total=Sum("total_amount"))["total"] or 0

    data =  {
        # 今天创建了几个订单（数数）
        "today_orders": Orders.objects.filter(create_time__gte=start_at, create_time__lt=end_at).count(),
        # 今天成交多少钱（上面算好，转字符串给前端）
        "today_amount": str(today_amount),
        # 平台一共有多少用户（全表数数）
        "total_users": UserInfo.objects.count(),
        # 平台一共有多少商品（全表数数）
        "total_products": Products.objects.count(),
        # 还有多少"未支付"订单（按状态筛选再数数）
        "pending_orders": Orders.objects.filter(status="pending").count(),
        # 还有多少评价"商家没回复"（reply 为空字符串的就是未回复）
        "pending_reviews": Reviews.objects.filter(reply="").count(),
    }
    cache.set(cache_key, data, timeout=60 * 5)
    return Response(data)

'''销售统计'''
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_sales(request):
    # 权限校验：只有管理员/超管能看
    if is_not_admin(request.user):
        return Response({"detail": "无权限"}, status=403)

    # ① 取统计周期（默认 7d），用映射表把周期字符串转成天数
    #    显式列出支持的范围，非法值回落默认 7 天，避免悄悄按别的天数算
    PERIOD_MAP = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
    period = request.query_params.get("period", "7d")
    if period not in PERIOD_MAP:
        period = "7d"
    days = PERIOD_MAP[period]
    today = timezone.localdate()

    # ② 缓存：每个周期单独一个 key（7d/30d/1y 是不同的数据，不能共用），先查 Redis
    cache_key = f"admin:sales:v2:{today}:{period}"
    cached = cache.get(cache_key)
    if cached is not None:
        return Response(cached)

    # ③ 算出起始日期：今天是第 days 天，往前推 days-1 天就是第 1 天
    start = today - timedelta(days=days - 1)
    start_at = timezone.make_aware(datetime.combine(start, time.min))
    end_at = timezone.make_aware(datetime.combine(today + timedelta(days=1), time.min))
    # 项目使用 Asia/Shanghai，统计区间内固定为 +08:00。
    # 数据库按 UTC 存储，先加北京时间偏移再取日期，避免依赖 MySQL 命名时区表。
    # TruncDate 指定 UTC，防止 Django 对已经平移的时间再次转换。
    day_offset = start_at.utcoffset()

    # 下单数按创建时间统计，包含待支付和已取消订单。
    # values + annotate 让数据库一次返回整个区间的每日数量。
    order_rows = (
        Orders.objects.filter(create_time__gte=start_at, create_time__lt=end_at)
        .annotate(day=TruncDate(F("create_time") + day_offset, tzinfo=datetime_timezone.utc))
        .values("day").annotate(orders=Count("id")).order_by("day")
    )
    # 成交额按支付时间统计，与首页口径一致；金额由数据库 Sum 聚合。
    amount_rows = (
        Orders.objects.filter(
            status__in=["paid", "shipped", "completed"],
            pay_time__gte=start_at, pay_time__lt=end_at,
        )
        .annotate(day=TruncDate(F("pay_time") + day_offset, tzinfo=datetime_timezone.utc))
        .values("day").annotate(amount=Sum("total_amount")).order_by("day")
    )
    orders_by_day = {row["day"]: row["orders"] for row in order_rows}
    amounts_by_day = {row["day"]: row["amount"] for row in amount_rows}

    data = []
    # 两次查询已完成，下面只在内存中补齐无数据日期，不再逐日查询数据库。
    for i in range(days):
        d = start + timedelta(days=i)          # 当前是第 i 天的日期
        data.append({
            "date": d.strftime("%Y-%m-%d"),    # 日期格式化成 2026-08-27 这种字符串
            "orders": orders_by_day.get(d, 0),
            "amount": format(amounts_by_day.get(d, 0), ".2f"),
        })

    result = {"period": period, "data": data}
    cache.set(cache_key, result, timeout=60 * 5)  # 缓存 5 分钟
    return Response(result)

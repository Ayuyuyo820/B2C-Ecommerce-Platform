import json
import os
from django.utils import timezone
from uuid import uuid4
from datetime import timedelta
from django.db import transaction
from django.db.models import Sum, F
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet  # ReadOnlyModelViewSet只能查看
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
Orders,OrdersItem,Reviews
)
from apps.users.serializers import (
    UserMeSerializer, UserInfoSerializer,UserAddressesSerializer,
    ProductCategoriesSerializer,ProductsSerializer,CartItemSerializer,
    OrdersSerializer,ReviewsSerializer,MerchantOrderSerializer,
    AdminUserSerializer, AdminProductSerializer,MerchantReviewSerializer
)
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

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
    # 负责“接收请求、返回商品列表”
    # 加装饰器缓存整个响应
    @method_decorator(cache_page(60 * 5))
    def list(self,request,*args,**kwargs):
        return super().list(request,*args,**kwargs)

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
        if ordering in allowed:
            qs = qs.order_by(ordering)

        return qs
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

    # 创建商品
    def perform_create(self, serializer):
        # 发布商品时自动绑定当前用户为商家
        serializer.save(merchant=self.request.user)

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
        return CartItem.objects.filter(user=self.request.user).select_related('product')



    @transaction.atomic
    def perform_create(self,serializer):
        # 取出商品对象和购买数量（数量默认 1）
        product  = serializer.validated_data['product']
        quantity = serializer.validated_data.get('quantity',1)

        # get_or_create 原子处理：已有该商品则取出来累加，没有则新建。
        # 相比 filter().first() + save()，能避免并发加购时触发 unique_together 冲突
        existing_item, created = CartItem.objects.get_or_create(
            user=self.request.user, product=product,
            defaults={'quantity': quantity, 'total_price': product.price * quantity}
        )

        if not created:
            # 已存在 → 累加数量，重新计算总价
            existing_item.quantity += quantity
            existing_item.total_price = product.price * existing_item.quantity
            existing_item.save()

        # 把序列化器实例指向合并后的购物车记录，保证返回最新数量
        serializer.instance = existing_item

    def perform_update(self,serializer):
        # 1. 保存前端传的数据（quantity、is_selected 等）
        instance = serializer.save()  # 保存到数据库  更新所有字段
        # 2. 根据新数量重新计算总价
        instance.total_price = instance.product.price * instance.quantity
        # 3. 只更新总价、数量、勾选状态这三个字段
        instance.save(update_fields=["total_price", "quantity", "is_selected"]) # 只更新指定的字段

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
class OrdersViewSet(ModelViewSet):
    queryset = Orders.objects.all() # 获取数据
    serializer_class = OrdersSerializer # 序列化
    permission_classes = [IsAuthenticated] # 权限登录才能访问

    # 默认：Orders.objects.all()  → 能看到所有人的订单
    # 只能访问自己的
    def get_queryset(self):
        # select_related 一次性查出关联的商家和地址，prefetch_related  用于反向关系（一对多) 查出订单项里的商品分两次查询，然后在 Python 里拼接
        qs = Orders.objects.filter(user=self.request.user).select_related("merchant", "address").prefetch_related("items__product")
        # 支持按状态筛选：/api/v1/orders/?status=paid
        status = self.request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs

    # 默认：serializer.save() → 只保存前端传的数据
    # 问题：订单号谁生成？金额谁计算？购物车谁删？
    # 所以要重写：
    @transaction.atomic  # 事务：建订单+建订单项+扣库存+删购物车，任一失败整体回滚，避免脏数据
    def perform_create(self, serializer):
        #  生成订单号
        order_no = f"ORD{timezone.now().strftime('%Y%m%d%H%M%S')}{str(uuid4())[:8]}"
        # 校验收货地址属于当前用户，防止绑定别人的地址
        address = serializer.validated_data.get("address")
        if address and address.user != self.request.user:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"address_id": "收货地址不属于当前用户"})
        # ② 取购物车商品，select_related 一次性查出商品信息
        cart_ids = serializer.validated_data.pop("cart_ids") # validated_data 是序列化器校验通过后，整理好的干净数据。
        # 根据前端传的购物车 ID 列表，查出对应的购物车记录。
        # select_for_update 悲观锁：锁住购物车行，防止同一购物车被并发重复下单（下单成功后要删除购物车）
        cart_items = CartItem.objects.filter(id__in=cart_ids, user=self.request.user).select_for_update().select_related("product")

        # ③ 检查购物车是否为空
        if not cart_items.exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"cart_ids": "请至少选择一个购物车商品"})

        # ④ 取第一个商品的商家作为订单商家
        merchant = cart_items.first().product.merchant
        # ⑤ 算总金额 → 遍历每个购物车项，算 单价×数量
        total_amount = sum(item.product.price * item.quantity for item in cart_items)

        # ⑤-1 下单前校验库存是否充足（不足直接报错，不做任何扣减）
        for item in cart_items:
            if item.product.stock < item.quantity:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({"detail": f"商品「{item.product.name}」库存不足，仅剩 {item.product.stock} 件"})

        # ⑥ 保存订单 → 自动填入 user、merchant、order_no、total_amount
        order = serializer.save(
            user=self.request.user,
            merchant=merchant,
            order_no=order_no,
            total_amount=total_amount,
            status="pending",
        )
        # ⑦ 创建订单项 + 原子扣库存
        # 乐观锁（CAS）：不锁商品行，靠「stock >= 数量」这个条件做原子更新。
        # F("stock") 直接用数据库当前库存做减法，消除「读-改-写」竞态导致的丢失更新/超卖。
        # 影响 0 行（updated==0）说明库存已被，并发抢光，报「库存不足」。
        # stock__gte本质上就是乐观锁（CAS） 防止超卖
        for item in cart_items:
            updated = Products.objects.filter(
                pk=item.product.pk, stock__gte=item.quantity
            ).update(stock=F("stock") - item.quantity)
            if updated == 0:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({"detail": f"商品「{item.product.name}」库存不足"})
            OrdersItem.objects.create(
                order=order,
                product=item.product,
                price=item.product.price,  # 记录购买时的价格（防止后续改价）
                quantity=item.quantity
            )
        # ⑧ 删除购物车
        cart_items.delete()
    '''自定义接口'''
    # 支付订单
    @action(detail=True,methods=["POST"])
    def pay(self,request,pk=None):
        order = self.get_object()
        if order.status != "pending":
            return Response({"detail":"订单状态不允许支付"},status=400)
        order.status ='paid'
        order.pay_time = timezone.now()
        order.save()
        serializer = OrdersSerializer(order)
        return Response(serializer.data)

    # 取消订单
    @transaction.atomic
    @action(detail=True,methods=["POST"])
    def cancel(self,request,pk=None):
        order  = self.get_object()
        if order.status not in ["pending"]:
            return  Response({"detail":"订单状态不允许取消"},status=400)
        order.status = "cancelled"
        order.save()
        # 回补库存：取消订单时，原子加回库存（同样用 F() 乐观锁思路，避免并发下加错数量）
        for item in order.items.select_related("product"):
            Products.objects.filter(pk=item.product.pk).update(stock=F("stock") + item.quantity)
        serializer = OrdersSerializer(order)
        return  Response(serializer.data)

    # 确认收货
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        order = self.get_object()
        if order.status != 'shipped':
            return Response({"detail": "订单状态不允许确认收货"}, status=400)
        order.status = 'completed'
        order.complete_time = timezone.now()
        order.save()
        serializer = OrdersSerializer(order)
        return Response(serializer.data)

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
class MerchantOrdersViewSet(ModelViewSet):
    serializer_class = MerchantOrderSerializer
    permission_classes = [IsAuthenticated, IsMerchantOrAdmin]

    def get_queryset(self):
        user = self.request.user
        # 角色校验：只有商家/管理员/超管能看到商家订单
        if user.role not in ["merchant", "admin", "superadmin"]:
            return Orders.objects.none()
        # 只查 merchant 指向自己的订单
        qs = Orders.objects.filter(merchant=user).select_related("user").prefetch_related("items__product")

        # 状态筛选：前端传的值和后端模型不同，做映射
        # unpaid(待支付)→pending；pending_ship(待发货)→paid
        status_map = {"unpaid": "pending", "pending_ship": "paid"}
        status = self.request.query_params.get("status")
        if status:
            status = status_map.get(status, status)
            qs = qs.filter(status=status)
        return qs

    # 发货：paid → shipped
    @action(detail=True, methods=["POST"])
    def ship(self, request, pk=None):
        order = self.get_object()  # 在 get_queryset 过滤后的范围内找，天然只能操作自己的订单
        if order.status != "paid":
            return Response({"detail": "订单状态不允许发货"}, status=400)
        order.status = "shipped"
        order.ship_time = timezone.now()
        order.save()
        serializer = self.get_serializer(order)
        return Response(serializer.data)
'''校验是否为管理员，不是则返回 True 表示需要拦截'''
def is_not_admin(user):
    return user.role not in ['admin','superadmin']

''' 用户列表'''
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_user_list(request):
    if is_not_admin(request.user):
        return Response({'detail':'无权限'},status=403)
    # 获取全部用户数据
    qs = UserInfo.objects.all()
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
    page = paginator.paginate_queryset(qs,request)
    serializer = AdminUserSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)

'''修改用户状态'''
# 修改用户状态（启用/封禁）
@api_view(["PATCH"])                      # 只接受 PATCH 请求（改单字段语义）
@permission_classes([IsAuthenticated])    # 必须登录
def admin_user_status(request, pk):
    # 权限校验：只有管理员/超管能操作
    if is_not_admin(request.user):
        return Response({"detail": "无权限"}, status=403)

    # 查 URL 里指定 id 的目标用户；filter 返回一组，first 取第一个
    # 注意：这里的 pk 是"要操作的用户"，不是登录者自己
    user = UserInfo.objects.filter(pk=pk).first()
    if not user:                          # 查不到说明 id 不存在
        return Response({"detail": "用户不存在"}, status=404)

    # 从请求体取新的启用状态（前端传 true/false）
    raw = request.data.get("is_active")
    # 兼容前端可能传字符串 "false"：字符串按 true/false 解析，其他类型显式转布尔，避免 "false" 被当成真
    if isinstance(raw, str):
        is_active = raw.lower() in ("true", "1", "yes")
    else:
        is_active = bool(raw)
    user.is_active = is_active            # 更新字段
    user.save()                           # 保存到数据库

    # is_active 为 false → 返回"已禁用"；为 true → "已启用"
    return Response({"message": "用户已禁用" if not is_active else "用户已启用"})

'''分配角色'''
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def admin_user_role(request,pk):
    # 只有超级管理员能改角色
    if request.user.role != 'superadmin':
        return Response({"detail":"无权限"},status=403)
    # 获取当前用户信息
    user = UserInfo.objects.filter(pk=pk).first()
    if not user:
        return Response({"detail":"用户不存在"},status=404)
    # 获取用户角色
    role = request.data.get('role')
    valid_roles = ['user','merchant','admin','superadmin']
    if role not in valid_roles:
        return Response({"detail":"非法角色"},status=400)
    user.role = role
    user.save()
    return Response({"message": "角色分配成功", "user": {"id": user.id, "username": user.username, "role": user.role}})


'''待审核商品列表'''
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_product_audit_list(request):
    # 校验身份
    if is_not_admin(request.user):
        return Response({"detail":"无权限"},status=403)
    # 获取商家待上架商品
    qs = Products.objects.select_related('merchant') # 联表查询
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
    product.save() # 提交
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
    cache_key = 'admin:statistics:daily'
    cached = cache.get(cache_key)
    if cached is not None:
        return  Response(cached)
    # ① 拿到"今天"的纯日期（去掉时分秒），作为统计基准
    today = timezone.now().date()

    # ② 今日成交额：筛选"支付时间在今天"的订单，用 Sum 聚合它们的 total_amount 求和
    #    filter：筛出今天支付的订单
    #    pay_time__date：只要支付时间的日期部分（把时分秒丢掉再比较）
    #    Sum("total_amount")：把这些订单的金额全部加起来
    #    ["total"]：从聚合结果字典里取出求和的数字
    #    or 0：今天没有支付订单时，Sum 是 None，兜底成 0
    today_amount = Orders.objects.filter(pay_time__date=today).aggregate(total=Sum("total_amount"))["total"] or 0

    data =  {
        # 今天创建了几个订单（数数）
        "today_orders": Orders.objects.filter(create_time__date=today).count(),
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
    days = PERIOD_MAP.get(period, 7)  # get 第二参数=非法值时兜底 7 天

    # ② 缓存：每个周期单独一个 key（7d/30d/1y 是不同的数据，不能共用），先查 Redis
    cache_key = f"admin:sales:{period}"
    cached = cache.get(cache_key)
    if cached is not None:              # 命中就直接返回，不再跑下面 365 天的循环查询
        return Response(cached)

    # ③ 算出起始日期：今天是第 days 天，往前推 days-1 天就是第 1 天
    start = timezone.now().date() - timedelta(days=days - 1)

    data = []
    # ④ 从起始日开始，逐天循环，统计每天的数据
    for i in range(days):
        d = start + timedelta(days=i)          # 当前是第 i 天的日期
        day_orders = Orders.objects.filter(create_time__date=d)  # 查"这一天"创建的订单
        data.append({
            "date": d.strftime("%Y-%m-%d"),    # 日期格式化成 2026-08-27 这种字符串
            "orders": day_orders.count(),      # 这天下了几单
            "amount": str(sum(o.total_amount for o in day_orders)),  # 这天的订单金额合计
        })

    result = {"period": period, "data": data}
    cache.set(cache_key, result, timeout=60 * 5)  # 缓存 5 分钟
    return Response(result)
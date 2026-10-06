from rest_framework import serializers
from apps.users.models import (UserInfo,UserAddresses,ProductCategories,
                               Products,CartItem,Orders,OrdersItem,Reviews)
from django.contrib.auth.hashers import make_password

import  json

class JsonListField(serializers.Field):
    """列表字段：写入时 list→JSON字符串存库，读取时 JSON字符串→list"""
    def to_internal_value(self, data):
        return json.dumps(data)

    def to_representation(self, value):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return []


class UserInfoSerializer(serializers.ModelSerializer):
    # 只用于写入验证，不存数据库，不会出现在响应里
    password_confirm = serializers.CharField(write_only=True, max_length=64, label="确认密码")
    # 注册可选角色：只开放「用户 / 商家」，管理员不允许通过注册产生
    role = serializers.ChoiceField(
        choices=[("user", "普通用户"), ("merchant", "商家")],
        default="user", required=False, label="角色"
    )

    class Meta:
        model = UserInfo
        fields = ['id', 'username', 'password', 'password_confirm', 'phone', 'email','role']
        extra_kwargs = {
            'password': {'write_only': True},  # 密码只写不读，响应里不返回
        }

    # 验证：两次密码是否一致
    def validate(self, data):
        password = data.get("password")
        password_confirm = data.get("password_confirm")
        if password and password != password_confirm:
            raise serializers.ValidationError({"password_confirm": "两次密码不一致"})
        return data

    # 创建时加密密码
    def create(self, validated_data):
        validated_data.pop('password_confirm')  # 删掉，不存数据库
        validated_data['password'] = make_password(validated_data['password'])  # 哈希加密
        return super().create(validated_data)

    # 更新时也要加密（如果传了密码的话）
    def update(self, instance, validated_data):
        validated_data.pop('password_confirm', None)  # 可能没传，加 None 防报错
        if 'password' in validated_data:
            validated_data['password'] = make_password(validated_data['password'])
        return super().update(instance, validated_data)

class UserMeSerializer(serializers.ModelSerializer):
        '''获取/修改个人信息的序列化(不反悔密码)'''
        class Meta:
            model = UserInfo
            fields = ['id', 'username', 'phone', 'email', 'role', 'avatar', 'create_time']

'''用户地址模块'''
class UserAddressesSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddresses
        fields = "__all__"
        extra_kwargs = {
            'user': {'read_only': True},
        }
'''商品分类'''
class ProductCategoriesSerializer(serializers.ModelSerializer):
    # 二级分类
    children = serializers.SerializerMethodField()
    class Meta:
        model = ProductCategories
        fields = "__all__"
    def get_children(self,obj): #序列化的那一条分类记录
        children = ProductCategories.objects.filter(parent = obj)  # 筛出 parent 外键 == 当前这条分类，下面的子分类
        # 把筛出来的子分类，再用同一个序列化器递归序列化（所以子分类又能带上它自己的children，层层嵌套）。
        return  ProductCategoriesSerializer(children,many=True).data

class ProductCategoryBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategories
        fields = ['id','name']

class ProductMerchantSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserInfo
        fields = ["id", "username", "avatar"]

'''商品列表'''
class ProductsSerializer(serializers.ModelSerializer):
    category = ProductCategoryBriefSerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductCategories.objects.all(), # 把前端传的数字 ID（比如 2）自动转成 ProductCategories 表的对象。
        source='category',  # 存的时候，把这个对象写进模型的 category 外键字段
        write_only=True     # 只在请求时接收，响应里不重复返回
    )
    merchant = ProductMerchantSerializer(read_only=True)
    images  = JsonListField(required=False)
    audit_status_display = serializers.CharField(source="get_audit_status_display", read_only=True)  # 审核状态中文名

    class Meta:
        model = Products
        fields = [
            "id", "name", "price", "original_price", "image", "images",
            "description", "sales", "stock", "category","category_id","merchant",
            "is_active", "audit_status", "audit_status_display", "reject_reason",  # ← 加 3 个字段
            "create_time", "updated_at",
        ]
        # 审核/上架/销量字段只读：只能由管理员审核流程修改，商家端不能改
        extra_kwargs = {
            "is_active": {"read_only": True},
            "audit_status": {"read_only": True},
            "reject_reason": {"read_only": True},
            "sales": {"read_only": True},
        }

    '''商品的精简序列化器'''
class ProductBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Products
        fields = ['id', 'name', 'price', 'image', 'stock']


'''购物车'''
class CartItemSerializer(serializers.ModelSerializer):
    product = ProductBriefSerializer(read_only=True) # 只读
    product_id = serializers.PrimaryKeyRelatedField(  # PrimaryKeyRelatedField 把前端传的数字 ID，自动转换成数据库里的对象
        queryset = Products.objects.all(),  # 根据前端ID查询商品表
        source='product',       # 前端传 product_id，但存到模型的 product 字段里
        write_only=True         # 只管写（请求）
    )
    #  前端用 selected，映射到模型的 is_selected
    selected = serializers.BooleanField(source='is_selected', required=False)  # 前端用 selected，映射到模型的 is_selected

    class Meta:
        model = CartItem
        fields = ['id', 'user', 'product', 'product_id', 'quantity', 'total_price', 'selected']
        read_only_fields = ['id', 'total_price']
        extra_kwargs = {
            'user': {'read_only': True},
        }
'''订单项里嵌套的商品信息（比购物车的更精简）'''
class OrderProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Products
        fields = ["id","name","image"]

'''地址精简序列化器（嵌套在订单里，返回拼接好的完整地址）'''
class AddressBriefSerializer(serializers.ModelSerializer):
    full_address = serializers.SerializerMethodField()  # 自定义字段：拼接省市区+详细地址

    class Meta:
        model = UserAddresses
        fields = ["receiver", "phone", "full_address"]

    def get_full_address(self, obj):
        # 把省市区详细地址拼成一个字符串，前端直接渲染
        return f"{obj.province}{obj.city}{obj.district}{obj.detail}"

'''订单项（被嵌套在订单里，不单独使用）'''
class OrderItemSerializer(serializers.ModelSerializer):
    product = OrderProductSerializer(read_only=True)    # 嵌套商品信息，不只返回ID
    product_name = serializers.CharField(source="product.name", read_only=True)  # 商品名，方便前端直接取
    product_image = serializers.CharField(source="product.image", read_only=True)  # 商品图，方便前端直接取
    subtotal = serializers.SerializerMethodField()        # 自定义字段：小计金额

    class Meta:
        model = OrdersItem
        fields = ["id","product","product_name","product_image","price","quantity","subtotal"]

    def get_subtotal(self,obj):
        # obj 就是当前这条 OrdersItem 记录
        return str(obj.price * obj.quantity)  # 单价 * 数量

'''评价用户信息（嵌套在订单/评价里，只返回id和用户名）'''
class ReviewsUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserInfo
        fields = ["id","username","avatar"]

class OrdersSerializer(serializers.ModelSerializer):
    # 创建订单时前端传的字段（write_only 只在请求时接收，响应不返回）
    cart_ids = serializers.ListField(
        child=serializers.IntegerField(),  # 类型：整数列表 [1, 3]
        write_only=True
    )
    address_id = serializers.PrimaryKeyRelatedField(
        queryset=UserAddresses.objects.all(),  # 根据ID查地址表
        source='address',  # 前端传 address_id，存到模型的 address 字段
        write_only=True
    )
    items = OrderItemSerializer(many=True, read_only=True)   # 嵌套订单项列表
    status_display = serializers.CharField(source="get_status_display", read_only=True)  # 状态中文名（待支付/已支付等）
    address = AddressBriefSerializer(read_only=True)  # 嵌套地址信息（含拼接好的完整地址）
    merchant = ReviewsUserSerializer(read_only=True)  # 嵌套商家信息

    class Meta:
        model = Orders
        fields = [
            "id", "order_no", "status", "status_display", "total_amount", "items",
            "merchant", "address", "cart_ids", "address_id", "remark",
            "create_time", "pay_time", "ship_time", "complete_time", "is_reviewed",
        ]
        read_only_fields = ["id", "order_no", "status", "total_amount", "create_time", "pay_time"]


'''商家订单序列化器（字段对齐商家订单管理页）'''
class MerchantOrderSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)  # 下单用户名（字符串）
    items = OrderItemSerializer(many=True, read_only=True)  # 嵌套订单项
    status = serializers.SerializerMethodField()  # 自定义：把后端 pending 转成前端 unpaid

    class Meta:
        model = Orders
        fields = ["id", "order_no", "username", "items", "total_amount", "status", "create_time"]

    def get_status(self, obj):
        # 前端状态值约定是 unpaid，后端模型是 pending，做一次转换
        return "unpaid" if obj.status == "pending" else obj.status

'''商家评价列表序列化器(扁平返回，对齐商家评价管理页)'''
class MerchantReviewSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name',read_only=True)  # 商品名
    username = serializers.CharField(source='user.username',read_only=True)      # 评价用户
    images = serializers.SerializerMethodField()      # 图片字符串转数组

    class Meta:
        model = Reviews
        fields = ['id','product_name','username','rating','content','images','reply','create_time']
        read_only_fields = ['id', 'rating', 'content', 'reply', 'create_time']
    # 转字符串
    def get_images(self,obj):
        try:
            return json.loads(obj.images)  #反序列化成真正的 Python 列表
        except (json.JSONDecodeError,TypeError):
            return [] # 兜底

'''评价'''
class ReviewsSerializer(serializers.ModelSerializer):
    user = ReviewsUserSerializer(read_only=True)# 嵌套商品信息，不只返回ID
    # 把图片的字符串转为数组
    images = serializers.SerializerMethodField()  # 覆盖默认行为
    class Meta:
        model = Reviews
        fields = ["id", "user", "rating", "content", "images", "reply", "create_time"]
        read_only_fields = ["id", "user", "reply", "create_time"] #后端生成前端不传递

    def get_images(self,obj):
        # obj = Reviews(id=1, user=..., images='["url1","url2"]', ...)
        try:
            return json.loads(obj.images)  # 字符串 → Python列表 → 自动转JSON数组
        except (json.JSONDecodeError, TypeError):
            return []

'''管理员-用户列表序列化器'''
class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserInfo
        fields = ["id", "username", "phone", "email", "role", "is_active", "create_time", "last_login"]

'''管理员-待审核商品列表序列化器'''
class AdminProductSerializer(serializers.ModelSerializer):
    merchant_name  = serializers.CharField(source='merchant.username',read_only=True) # 商家名
    submitted_at = serializers.DateTimeField(source="create_time", read_only=True)  # 提交时间
    audit_status_display = serializers.CharField(source="get_audit_status_display", read_only=True)

    class Meta:
        model = Products
        fields = ["id", "name", "price", "merchant_name", "submitted_at", "audit_status", "audit_status_display",
                  "reject_reason"]

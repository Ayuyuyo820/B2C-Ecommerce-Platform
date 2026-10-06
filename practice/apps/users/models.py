
from django.db import models
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.utils import timezone

'''自定义用户管理器'''
class UserInfoManager(BaseUserManager):
    """自定义用户管理器：让 createsuperuser 等命令能正常工作"""
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("用户名不能为空")
        extra_fields.setdefault("role", "user")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault("role", "superadmin")
        return self.create_user(username, password, **extra_fields)

'''用户基本信息'''
class UserInfo(AbstractBaseUser):
    ROLE_CHOICES = [
        ("user", "普通用户"),
        ("merchant", "商家"),
        ("admin", "管理员"),
        ("superadmin", "超级管理员"),
    ]
    username = models.CharField(max_length=32, verbose_name="用户名",unique=True)
    phone = models.CharField(max_length=11, verbose_name="手机号")
    email = models.CharField(max_length=64, verbose_name="邮箱号")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="user", verbose_name="角色")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")  # True=正常，False=封禁
    create_time = models.DateTimeField(default=timezone.now, verbose_name="创建时间")  # 注册时间（创建时自动取当前时间）
    avatar = models.URLField(max_length=500,blank=True,default="",verbose_name="头像")
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ['phone', 'email']
    objects = UserInfoManager()
    def __str__(self):
        return self.username

'''用户地址模块'''
class UserAddresses(models.Model):
    user = models.ForeignKey(UserInfo, on_delete=models.CASCADE, verbose_name="用户")
    receiver = models.CharField(max_length=32,verbose_name="姓名")
    phone = models.CharField(max_length=11,verbose_name="手机号")
    province = models.CharField(max_length=10,verbose_name="省份")
    city = models.CharField(max_length=10,verbose_name="城市")
    district = models.CharField(max_length=10,verbose_name="区域")
    detail = models.CharField(max_length=255,verbose_name="详细地址")
    is_default = models.BooleanField(default=False,verbose_name="是否默认")
'''商品分类列表'''
class ProductCategories(models.Model):
    name = models.CharField(max_length=32,verbose_name="商品名")
    icon = models.CharField(max_length=32,verbose_name="分类图标",default="Grid")
    # null=True 数据库运行为空，blank=True表单允许不填，on_delete=models.CASCADE	父级删了，子级也删
    parent = models.ForeignKey('self',null=True,blank=True,on_delete=models.CASCADE,verbose_name="父级分类")

    def __str__(self):
        return self.name

'''商品列表'''
class Products(models.Model):
    AUDIT_STATUS_CHOICES = [
        ('pending', '待审核'),
        ('approved', '审核通过'),
        ('rejected', '审核拒绝'),
    ]
    name = models.CharField(max_length=128,verbose_name="商品名称")
    price = models.DecimalField(max_digits=10,decimal_places=2,verbose_name="价格")
    original_price = models.DecimalField(max_digits=10,decimal_places=2, null=True, blank=True,verbose_name="打折价格")
    image = models.URLField(max_length=500,verbose_name="商品图片",blank=True,default="")
    images = models.TextField(verbose_name="商品图片列表", blank=True, default="[]")
    merchant = models.ForeignKey(UserInfo, on_delete=models.SET_NULL, null=True, blank=True, related_name="products", verbose_name="商家")
    description = models.TextField(verbose_name="商品详情",blank=True,default="")
    sales = models.IntegerField(default=0,verbose_name="销量")
    stock = models.IntegerField(default=0,verbose_name="库存")
    category = models.ForeignKey(ProductCategories,on_delete=models.SET_NULL,null=True,verbose_name="所属分类") # SET_NULL 父删子留
    is_active = models.BooleanField(default=False,
                                    verbose_name="是否上架")  # ← default 从 True 改成 False（新商品默认不上架，等审核通过后才上架）
    audit_status = models.CharField(max_length=20, default='pending', choices=AUDIT_STATUS_CHOICES,
                                    verbose_name="审核状态")
    reject_reason = models.TextField(blank=True, default="", verbose_name="拒绝原因")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    def __str__(self):
        return self.name

'''购物车'''
class CartItem(models.Model):
    user = models.ForeignKey(UserInfo,on_delete=models.CASCADE,verbose_name="用户")
    product = models.ForeignKey(Products, on_delete=models.CASCADE, verbose_name="商品")
    quantity = models.IntegerField(default=1,verbose_name="数量")
    total_price = models.DecimalField(max_digits=10,decimal_places=2,default=0,verbose_name="总价")
    is_selected = models.BooleanField(default=True,verbose_name="是否选中")
    create_time = models.DateTimeField(auto_now_add=True,verbose_name="创建时间")

    # 联合唯一
    class Meta:
        unique_together = ["user","product"]

    # 结构化中文
    def __str__(self):
        return f"{self.user.username} - {self.product.name}"

'''订单模块'''
class Orders(models.Model):
    # 订单状态
    STATUS_CHOICES = [
        ('pending', '待支付'),
        ('paid', '已支付'),
        ('shipped', '已发货'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    user = models.ForeignKey(UserInfo,on_delete=models.CASCADE,verbose_name='用户')
    merchant = models.ForeignKey(UserInfo, on_delete=models.SET_NULL, null=True, blank=True, related_name='merchant_orders', verbose_name='商家')
    order_no = models.CharField(max_length=32,verbose_name="订单号",unique=True)
    status = models.CharField(max_length=20,default="pending",choices=STATUS_CHOICES,verbose_name="订单状态")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="订单总金额")
    address = models.ForeignKey(UserAddresses, on_delete=models.SET_NULL, null=True, verbose_name="收货地址")
    remark = models.TextField(blank=True, default="", verbose_name="订单备注")
    create_time = models.DateTimeField(auto_now_add=True,verbose_name="创建时间")
    pay_time = models.DateTimeField(null=True, blank=True, verbose_name="支付时间")  # blank=True 表单允许为空
    ship_time = models.DateTimeField(null=True, blank=True, verbose_name="发货时间")  # 新增：发货时间
    complete_time = models.DateTimeField(null=True, blank=True, verbose_name="完成时间")  # 新增：完成时间
    is_reviewed = models.BooleanField(default=False, verbose_name="是否已评价")  # 新增：是否已评价



    def __str__(self):
        return f"{self.order_no}"

'''订单项（一个订单包含多个商品）'''
class OrdersItem(models.Model):
    order = models.ForeignKey(Orders, on_delete=models.CASCADE, related_name='items', verbose_name="订单")
    product = models.ForeignKey(Products,on_delete=models.SET_NULL,null=True)
    price =   models.DecimalField(max_digits=10,decimal_places=2,verbose_name="购买时单价")
    quantity = models.IntegerField(default=1,verbose_name="数量")

    def __str__(self):
        return f"{self.order.order_no} - {self.product.name}"

'''评价模块'''
class Reviews(models.Model):
    user = models.ForeignKey(UserInfo,on_delete=models.CASCADE,verbose_name="评价用户")
    product = models.ForeignKey(Products,on_delete=models.CASCADE,verbose_name="评价商品")
    order = models.ForeignKey(Orders, on_delete=models.CASCADE, null=True, blank=True, verbose_name="关联订单")
    rating = models.IntegerField(default=5,verbose_name="(1-5)星")
    content = models.TextField(blank=True, default="",verbose_name="评论")
    images = models.TextField(blank=True,default="[]",verbose_name="评价图片")
    reply = models.TextField(blank=True,default="",verbose_name="商家回复")
    create_time = models.DateTimeField(auto_now_add=True,verbose_name="创建时间")

    def __str__(self):
        return f"{self.user.username} 评价 {self.product.name}"

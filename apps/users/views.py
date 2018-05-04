from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.views.generic import View
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer  # 信息加密
from itsdangerous import SignatureExpired  # token过期的异常
from django.core.mail import send_mail  # django内置的邮件发送
from celery_tasks.tasks import send_register_active_view  # celery任务函数

from django.contrib.auth import authenticate, login, logout

from django.conf import settings

import re
from apps.users.models import User, Address
from apps.goods.models import GoodsSKU
from utils.mixin import LoginrequiredMixin
from django_redis import get_redis_connection  # redisl连接

# Create your views here.


def register(request):
    """登陆"""
    return render(request, "register.html")


def register_handle(request):
    """127.0.0.1:8000/users/register_handle"""
    # 接收数据
    username = request.POST.get("user_name")
    pwd = request.POST.get("pwd")
    email = request.POST.get("email")
    allow = request.POST.get("allow")

    # 校验数据
    #  1.数据完整性
    if not all([username, pwd, email]):
        print("完整")
        return render(request, "register.html", {"errmsg": "信息不完整"})

    # 2.校验邮箱合法性
    res = re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email)
    if not res:
        print("邮箱")
        return render(request, "register.html", {"errmsg": "邮箱地址不正确"})

    # 4.协议是否同意
    if allow != "on":
        print("allow")
        return render(request, "register.html", {"errmsg": "请同意协议"})

    # 3.用户名重名--查询数据库
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = None
    if user:
        return render(request, "register.html", {"errmsg": "用户名重复"})

    # 进行业务处理
    # 新建用户，使用django内置的User对象的create_user()方法
    user = User.objects.create_user(username, email, pwd)
    # 创建用户后，默认激活，需要更改默认
    user.is_active = False
    user.save()

    # 返回应答 跳转到主页
    return redirect(reverse("goods:index"))


class RegisterView(View):
    def get(self, request):
        """登陆"""
        return render(request, "register.html")

    def post(self, request):
        # 接收数据
        username = request.POST.get("user_name")
        pwd = request.POST.get("pwd")
        email = request.POST.get("email")
        allow = request.POST.get("allow")

        # 校验数据
        #  1.数据完整性
        if not all([username, pwd, email]):
            print("完整")
            return render(request, "register.html", {"errmsg": "信息不完整"})

        # 2.校验邮箱合法性
        res = re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email)
        if not res:
            print("邮箱")
            return render(request, "register.html", {"errmsg": "邮箱地址不正确"})

        # 4.协议是否同意
        if allow != "on":
            print("allow")
            return render(request, "register.html", {"errmsg": "请同意协议"})

        # 3.用户名重名--查询数据库
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None
        if user:
            return render(request, "register.html", {"errmsg": "用户名重复"})

        # 进行业务处理
        # 新建用户，使用django内置的User对象的create_user()方法，此时已经保存在了数据库中
        user = User.objects.create_user(username, email, pwd)
        # 创建用户后，默认激活，需要更改默认
        user.is_active = 0
        user.save()  # 更改属性后，要重新保存

        # 给用户发送激活链接，其中应包含用户信息 127.0.0.1:8000/users/active/user_id
        # url中的信息需要加密
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {"confirm": user.id}
        token = serializer.dumps(info)  # 解密后是byte 需要解码为str 默认解码是utf8
        token = token.decode()

        # 给用户发送激活邮件
        send_register_active_view.delay(email, username, token)

        # 返回应答 跳转到主页
        return redirect(reverse("goods:index"))


# /users/active/?
class ActiveView(View):
    """激活"""
    def get(self, request, token):
        # 接收并还原token
        serializer = Serializer(settings.SECRET_KEY, 3600)
        # 解密可能过期，所以要用错误捕获
        try:
            info = serializer.loads(token)

            # 获取用户信息
            user_id = info["confirm"]
            user = User.objects.get(id=user_id)

            # 激活用户
            user.is_active = 1
            user.save()

            # 返回应答
            return redirect(reverse("users:login"))
        except SignatureExpired as e:
            return HttpResponse("激活链接已过期，请重新激活")


# /users/login
class LoginView(View):
    """登陆"""
    def get(self, request):
        # 查验是否记住用户名
        if "username" in request.COOKIES:
            username = request.COOKIES.get("username")
            checked = "checked"
        else:
            username = ""
            checked = ""

        return render(request, "login.html", {"username": username, "checked": checked})

    def post(self, request):
        """登陆校验"""
        # 接收数据
        username = request.POST.get("username")
        pwd = request.POST.get("pwd")
        remember = request.POST.get("remember")

        # 校验数据
        if not all([username, pwd]):
            return render(request, "login.html", {"errmsg": "信息不完整"})
        # 业务处理 验证用户名密码是否正确，使用Django自带的用户验证 authenticate
        user = authenticate(username=username, password=pwd)
        if user is not None:
            if user.is_active:
                # 记住用户的登陆状态
                login(request, user)

                # 未登录的话，跳转到商品index页 登陆了的话，直接跳转到next的路径
                next_url = request.GET.get("next", reverse("goods:index"))
                # Redirect to a success page.
                response = redirect(next_url)

                # 记住用户名
                if remember == "on":
                    response.set_cookie("username", username, max_age=3600)

                return response
            else:
                # Return a 'disabled account' error message
                return render(request, "login.html",  {"errmsg": "账户未激活"})
        else:
            # Return an 'invalid login' error message.
            return render(request, "login.html", {"errmsg": "用户名或密码不正确"})


# /users/logout
class LogoutView(View):
    def get(self, request):

        # 清除用户登陆session
        logout(request)

        # 退出后跳转到首页
        return redirect(reverse("goods:index"))


# /users
class UserInfoView(LoginrequiredMixin, View):
    def get(self, request):
        # html中的active标签 传入page="info"
        # 用户登陆后，django会给request设置一个user属性
        # 如果登陆了，request.user返回User类的实例对象 is_authenticate() True
        # 没有登陆，request.user返回AnonymoUser类的实例对象 is_authenticate() False
        # 除了视图函数传回的模版变量，django会默认传回request.user,可以直接在模版中使用user

        # 获取基本信息
        user = request.user

        username = user.username
        address = Address.objects.get_default_address(user)

        # 查找历史浏览记录并显示 保存在redis中
        # 获取链接对象
        con = get_redis_connection("default")
        # 设置key
        history_key = "history_%d" % user.id
        # 根据key查询出5条商品信息的id，从左边开始提取 lrange
        sku_ids = con.lrange(history_key, 0, 4)

        # 遍历sku_id，按顺序取出
        goods_li = []
        for a in sku_ids:
            good = GoodsSKU.objects.get(id=a)
            goods_li.append(good)

        # 准备模版上下文
        contxt = {"page": "info", "address": address, "goods_li": goods_li}

        return render(request, "user_center_info.html", contxt)


# /users/order
class UserOrderView(LoginrequiredMixin, View):
    def get(self, request):

        # 获取订单信息

        return render(request, "user_center_order.html", {"page": "order"})


# /users/address
class AddressView(LoginrequiredMixin, View):
    def get(self, request):

        # 查找默认收货地址并显示
        # 获取默认地址
        user = request.user
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist as e:
        #     # 不存在默认地址
        #     address = None
        address = Address.objects.get_default_address(user)

        return render(request, "user_center_site.html", {"page": "address", "address": address})

    def post(self, request):

        # 获取表单信息，添加新地址
        receiver = request.POST.get("receiver")
        addr = request.POST.get("addr")
        zip_code = request.POST.get("zip_code")
        phone = request.POST.get("phone")

        # 校验信息
        if not all([receiver, addr, phone]):
            return render(request, "user_center_site.html", {"errmsg": "信息不完整"})
        # 业务逻辑处理
        # 验证手机号
        if not re.match(r'^1[3|4|5|7|8][0-9]{9}$', phone):
            return render(request, "user_center_site.html", {"errmsg": "无效手机号"})

        # 如果用户没有默认地址，新添加的地址则是默认地址，如果已存在默认地址，则添加的不是默认地址
        user = request.user  # django会默认传回request.user

        # 获取默认地址
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist as e:
        #     # 不存在默认地址
        #     address = None
        address = Address.objects.get_default_address(user)

        if address:
            # 如果存在默认地址
            is_default = False
        else:
            is_default = True

        # 新建地址
        Address.objects.create(user=user,
                               receiver=receiver,
                               addr=addr,
                               zip_code=zip_code,
                               phone=phone,
                               is_default=is_default)

        return redirect(reverse("users:address"))  # 用get方式重新请求这个页面
        # return render(request, "user_center_site.html")  # 这种方式传回的只有模版，但是里面没有数据
        # return self.get(request)






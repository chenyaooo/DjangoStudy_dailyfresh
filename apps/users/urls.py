from django.conf.urls import url
from apps.users import views
from apps.users.views import RegisterView, ActiveView, LoginView, UserInfoView, UserOrderView, AddressView, LogoutView

from django.contrib.auth.decorators import login_required
urlpatterns = [
    # url(r'^register$', views.register, name="register"),
    # url(r'^register_handle$', views.register_handle, name="register_handle"),

    url(r'^register$', RegisterView.as_view(), name="register"),  # 注册
    url(r'^active/(?P<token>.*)$', ActiveView.as_view(), name="active"),  # 激活
    url(r'^login$', LoginView.as_view(), name="login"),  # 登陆

    # url(r'^$', login_required(UserInfoView.as_view()), name="user"),  # 用户信息页
    # url(r'^order$', login_required(UserOrderView.as_view()), name="order"),  # 订单
    # url(r'^address$', login_required(AddressView.as_view()), name="address"),  # 用户地址

    url(r'^$', UserInfoView.as_view(), name="user"),  # 用户信息页
    url(r'^order$', UserOrderView.as_view(), name="order"),  # 订单
    url(r'^address$', AddressView.as_view(), name="address"),  # 用户地址
    url(r'^logout$', LogoutView.as_view(), name="logout")   # 登出

]

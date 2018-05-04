from django.conf.urls import url
from apps.goods.views import IndexView, DetailView

urlpatterns = [
    # url(r'^$', IndexView.as_view(), name="index"),  # 商品主页
    url(r'^index/$', IndexView.as_view(), name="index"),  # 为区分静态主页和动态，改写动态主页url 商品主页
    url(r'^goods/(?P<goods_id>\d+)$', DetailView.as_view(), name="detail"),  # 商品详情页,获取商品id的关键字参数
]


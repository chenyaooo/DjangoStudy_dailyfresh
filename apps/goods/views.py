from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.views.generic import View
from apps.goods.models import GoodsType, GoodsSKU, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner
from apps.orders.models import OrderGoods

from django_redis import get_redis_connection
from django.core.cache import cache
# Create your views here.


# http://127.0.0.1:8000/index
class IndexView(View):

    def get(self, request):
        """商品主页
        使用url，链接访问，发起get请求，获得主页的数据
        """
        # 优化用户登陆后的主页，一样的内容从缓存中获取，减少数据库查询的次数
        contxt = cache.get("index_page_data")  # 从缓存中获取

        # 如果获取不到则从数据库中查询并存入
        if contxt is None:

            # 获取商品种类信息
            types = GoodsType.objects.all()
            # 获取轮播图
            goods_banners = IndexGoodsBanner.objects.all().order_by("index")

            # 获取促销商品信息
            promotion_banners = IndexPromotionBanner.objects.all().order_by("index")

            # 获取首页分类展示商品信息
            # type_goods = IndexTypeGoodsBanner.objects.all() # 这种方式会获取所有的分类商品
            for a in types:
                # 获取type种类首页分类商品的图片展示信息
                image_banners = IndexTypeGoodsBanner.objects.filter(type=a, display_type=1).order_by("index")

                # 获取type种类首页分类商品的文字展示信息
                title_banners = IndexTypeGoodsBanner.objects.filter(type=a, display_type=0).order_by("index")

                # 为了方便在模版中分别显示出图片商品和文字商品
                # 给遍历出来的一个type的商品增加图片显示属性和文字显示属性
                a.image_banners = image_banners
                a.title_banners = title_banners

            contxt = {"types": types,
                      "goods_banners": goods_banners,
                      "promotion_banners": promotion_banners}

            # 设置缓存 key value timeout
            cache.set("index_page_data", contxt, 3600)

        # 与用户信息相关的数据，查询数据库后使用

        user = request.user  # 获取请求的user对象，如果登陆了返回User对象，没有的话返回None
        cart_count = 0

        if user.is_authenticated():

            # 如果用户登陆了，创建redis链接
            conn = get_redis_connection("default")
            # 设置购物车redis数据的key
            cart_key = "cart_%d" % user.id
            # 根据key返回这个key中的数据个数
            cart_count = conn.hlen(cart_key)

        # 由于之前尝试获取的cache中没有cart_count，更新方法 update
        contxt.update(cart_count=cart_count)

        return render(request, "index.html", contxt)


# /goods/商品id
class DetailView(View):
    """商品详情页"""
    def get(self, request, goods_id):
        # 查询商品，没有则返回主页
        try:
            sku = GoodsSKU.objects.get(id=goods_id)
        except GoodsSKU.DoesNotExist:
            return redirect(reverse("goods:index"))

        # 如果查询到商品，则根据查询出来的sku查询出详情页需要的数据
        # 获取商品分类信息
        types = GoodsType.objects.all()

        # 获取新品数据 商品类型与详情页商品一致，更新时间是最新的2个商品
        new_goods = GoodsSKU.objects.filter(type=sku.type).order_by("-create_time")[:2]

        # 获取商品评论，评论在订单商品内，因此需要获取订单商品
        comment_goods = OrderGoods.objects.filter(sku=sku)

        # 准备上下文

        # 返回模版数据




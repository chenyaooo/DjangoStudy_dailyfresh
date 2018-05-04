from celery import Celery
from django.conf import settings
from django.core.mail import send_mail

from django.template import loader

# 在任务处理者一方进行django初始化（代码在任务处理者一方）
import os
# import django
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dailyfresh.settings")
# django.setup()

from apps.goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner
from django_redis import get_redis_connection

# 创建一个Celery对象 参数一：起名，通常是路径名 参数二：指定broker"redis的IP：port/数据库号"
celery = Celery("celery_tasks.tasks", broker="redis://172.16.173.138:6379/8")

# 定义任务函数


@celery.task
def send_register_active_view(email, username, token):
    """发送激活邮件"""
    # 主题
    subject = "天天生鲜激活"
    # 正文
    message = ""
    from_email = settings.EMAIL_FROM
    reciever = [email]
    html_message = '%s，欢迎您成为天天生鲜注册会员<a href="http://127.0.0.1:8000/users/active/%s">http://127.0.0.1:8000/users/active/%s</a>' % (username, token, token)
    send_mail(subject, message, from_email, reciever, html_message=html_message)


# 由celery生成未登录状态访问的index页面

@celery.task
def generate_static_index_html():
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

    # 获取购物车中商品数量
    # cart_count = 1

    # 准备模版上下文
    contxt = {"types": types,
              "goods_banners": goods_banners,
              "promotion_banners": promotion_banners}

    # 不需要返回一个httpresponse对象，只需要返回静态html，不需要使用render
    # 准备模板
    temp = loader.get_template("static_index.html")
    # 渲染模版
    static_index_html = temp.render(contxt)

    # 生成首页对应的静态页面
    save_path = os.path.join(settings.BASE_DIR, "static/index.html")
    with open(save_path, "w") as f:
        f.write(static_index_html)







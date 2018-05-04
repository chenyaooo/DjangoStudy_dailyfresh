from django.contrib import admin
from apps.goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner
# Register your models here.

from celery_tasks.tasks import generate_static_index_html
from django.core.cache import cache


class BaseModelAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        """更新或新增表中数据时使用"""
        # 继承父类的方法
        super().save_model(request, obj, form, change)

        # 启动celery，更改模型后重新生成静态页面
        generate_static_index_html.delay()

        # 当表中数据发生改变时，删除缓存中的主页数据
        cache.delete("index_page_data")

    def delete_model(self, request, obj):
        """删除表中数据时使用"""
        #  继承父类的方法
        super().delete_model(request, obj)

        # 启动celery，更改模型后重新生成静态页面
        # from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

        # 当表中数据发生改变时，删除缓存中的主页数据
        cache.delete("index_page_data")

# 注册时继承改写的ModelAdmin
admin.site.register(GoodsType, BaseModelAdmin)
admin.site.register(IndexGoodsBanner, BaseModelAdmin)
admin.site.register(IndexPromotionBanner, BaseModelAdmin)
admin.site.register(IndexTypeGoodsBanner, BaseModelAdmin)




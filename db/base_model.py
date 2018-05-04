from django.db import models


class BaseModel(models.Model):
    """定义模型抽象基类"""
    # 创建事件
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    # 更新事件
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    # 软删除
    isDelete = models.BooleanField(default=False, verbose_name="删除标记")

    class Meta:
        """抽象基类需要定义Meta类"""
        abstract = True




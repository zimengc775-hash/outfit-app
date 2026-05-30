from django.db import models
from django.conf import settings
# Create your models here.
CATEGORY_CHOICES=[
    ('top', '上衣'),
    ('bottom', '下装'),
    ('outerwear', '外套'),
    ('dress', '连衣裙'),
    ('shoes', '鞋子'),
    ('accessory', '配饰'),
]
THICKNESS_CHOICES = [
    ('thin', '薄'),
    ('medium', '中'),
    ('thick', '厚'),
]
class ClothingItem(models.Model):
    user=models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='用户名字',
    )
    img=models.ImageField( verbose_name='图片',upload_to='clothes/')
    clothes_name=models.CharField(verbose_name='衣服名称',max_length=100, blank=True, default='未命名')
    category=models.CharField(verbose_name='类别',choices=CATEGORY_CHOICES,max_length=20, blank=True, default='top')
    color=models.CharField(verbose_name='颜色',max_length=100, blank=True, default='未知')
    style_label=models.CharField(verbose_name='风格标签',max_length=100, blank=True, default='')
    thickness=models.CharField(verbose_name='厚度',max_length=100,choices=THICKNESS_CHOICES, blank=True, default='medium')
    temp_min=models.IntegerField(verbose_name='最低温度', blank=True, null=True)
    temp_max=models.IntegerField(verbose_name='最高温度', blank=True, null=True)
    weather=models.CharField(verbose_name='适合天气',max_length=100, blank=True, default='')
    time=models.DateTimeField(verbose_name='添加时间',auto_now_add=True)
    
    def __str__(self):
        return self.clothes_name
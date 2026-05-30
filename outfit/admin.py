from django.contrib import admin
from .models import ClothingItem
# Register your models here.
@admin.register(ClothingItem)
#@admin.register(ClothingItem) 是一个装饰器——它的作用是告诉 
# Django admin："把 ClothingItem 模型注册到后台管理系统"。
# 你不需要手动写 admin.site.register(...)，它帮你做了。
class ClothingItemAdmin(admin.ModelAdmin):
    pass
from django.urls import path
from .import views
urlpatterns = [
    path('', views.home, name='home'),  # 首页
    path('wardrobe/',views.wardrobe_list,name='wardrobe-list'),
    path('wardrobe/add/',views.wardrobe_add,name='wardrobe-add'),
    path('wardrobe/<int:id>/edit/',views.wardrobe_edit,name='wardrobe-edit'),
    path('wardrobe/<int:id>/delete/',views.wardrobe_delete,name='wardrobe-delete'),    
]

from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from.models import  ClothingItem
from django import forms
from outfit import models
from . import ai_service, weather_service
import json
# Create your views here.
#衣柜展示页面
@login_required
def wardrobe_list(request):
    clothes=ClothingItem.objects.filter(user=request.user)
    return render(request,'outfit/wardrobe_list.html',{'clothes':clothes})

# 完整表单：编辑页用
class ClothingItemForm(forms.ModelForm):
    class Meta:
        model = models.ClothingItem
        fields = ['img','clothes_name','category','color','style_label','thickness','temp_min','temp_max','weather']

# 上传表单：添加页只用图片
class UploadForm(forms.Form):
    img = forms.ImageField(label='选择衣服照片')
#添加衣服
@login_required
def wardrobe_add(request):
    if request.method == 'GET':
        form = UploadForm()
        return render(request, 'outfit/wardrobe_add.html', {'form': form})

    # POST：用户上传了图片
    form = UploadForm(data=request.POST, files=request.FILES)
    if form.is_valid():
        # 先创建 ClothingItem，只保存图片，其他字段暂时留空
        item = ClothingItem(user=request.user)
        item.img = form.cleaned_data['img']
        item.save()

        # AI 识别
        if item.img:
            result = ai_service.analyze_clothing_image(item.img.path)
            if result:
                item.clothes_name = result.get('name', '未命名')
                item.category = result.get('category', 'top')
                item.color = result.get('color', '未知')
                item.style_label = result.get('style_tags', '')
                item.thickness = result.get('thickness', 'medium')
                item.temp_min = result.get('temp_min', 20)
                item.temp_max = result.get('temp_max', 30)
                item.weather = result.get('weather_types', '')
                item.save()
                return redirect('wardrobe-edit', id=item.id)

        # AI 失败或没图片，也跳到编辑页让用户手动填
        return redirect('wardrobe-edit', id=item.id)

    return render(request, 'outfit/wardrobe_add.html', {'form': form})

#编辑衣服
@login_required
def wardrobe_edit(request,id):
    item = get_object_or_404(ClothingItem, id=id, user=request.user)
    if request.method=='GET':
        form = ClothingItemForm(instance=item)
        return render(request,'outfit/wardrobe_edit.html',{'form':form})
    form = ClothingItemForm(data=request.POST,files=request.FILES,instance=item)
    if form.is_valid():
        form.save()
        return redirect('wardrobe-list')
    return render(request,'outfit/wardrobe_edit.html',{'form':form})

#删除衣服
@login_required
def wardrobe_delete(request,id):
    item = get_object_or_404(ClothingItem, id=id, user=request.user)
    if request.method=='POST':
        item.delete()
        return redirect('wardrobe-list')
    # GET 请求 → 显示确认页面
    return render(request, 'outfit/wardrobe_delete.html', {'item': item})


# ===== 首页 =====

@login_required
def home(request):
    """首页：天气展示 + 心情选择 + AI 推荐"""

    if request.method == 'POST':
        # AJAX 请求，分两种 action
        data = json.loads(request.body)
        action = data.get('action')

        # 获取天气
        if action == 'weather':
            lat = data.get('lat')
            lng = data.get('lng')
            weather = weather_service.get_weather_by_location(lat, lng)
            if weather:
                return JsonResponse({'success': True, 'weather': weather})
            return JsonResponse({'success': False, 'error': '获取天气失败'})

        # AI 推荐穿搭
        if action == 'recommend':
            mood = data.get('mood', '')
            weather = data.get('weather', {})
            clothes = ClothingItem.objects.filter(user=request.user)
            if not clothes.exists():
                return JsonResponse({'success': False, 'error': '衣柜是空的，请先添加衣服'})

            result = ai_service.recommend_outfit(
                weather, mood, clothes,
                exclude_ids=data.get('exclude_ids', []),
            )
            if result:
                return JsonResponse({
                    'success': True,
                    'items': [
                        {
                            'id': item.id,
                            'name': item.clothes_name,
                            'category': item.get_category_display(),
                            'img_url': item.img.url if item.img else '',
                        }
                        for item in result['items']
                    ],
                    'explanation': result['explanation'],
                })
            return JsonResponse({'success': False, 'error': 'AI 推荐失败，请重试'})

    # GET：渲染首页
    return render(request, 'outfit/home.html')

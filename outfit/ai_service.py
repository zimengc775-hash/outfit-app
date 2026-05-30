"""
AI 服务模块
- 识图：通义千问 Qwen-VL（便宜、中文好、OpenAI 兼容）
- 推荐：DeepSeek（便宜、文本推理强）
"""

import base64
import json
import io
from PIL import Image
from openai import OpenAI
from django.conf import settings

# 通义千问（百炼平台）— 用于识图
qwen_client = OpenAI(
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=settings.QWEN_API_KEY,
)

# DeepSeek — 用于穿搭推荐（文本）
deepseek_client = OpenAI(
    base_url="https://api.deepseek.com",
    api_key=settings.DEEPSEEK_API_KEY,
)


def analyze_clothing_image(image_path):
    """分析衣服图片，返回 AI 识别结果。"""

    # 压缩图片：缩小到最长边 512px，JPEG 质量 70%，大幅减少 token 消耗
    img = Image.open(image_path)
    img = img.convert("RGB")  # 统一转 RGB（去掉 PNG 透明通道等）
    max_size = 512
    if max(img.size) > max_size:
        ratio = max_size / max(img.size)
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.LANCZOS)

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=70)
    image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    instruction = (
        "请仔细观察图片，判断这是衣服的哪个部位/种类，然后按以下 JSON 格式输出：\n"
        '{"name":"颜色+款式名称","category":"类别","color":"颜色",'
        '"style_tags":"风格标签","thickness":"厚度","temp_min":温度数字,"temp_max":温度数字,'
        '"weather_types":"天气"}\n\n'
        "=== 类别判断指南 ===\n"
        "- top: T恤、衬衫、卫衣、毛衣、背心等上半身穿的\n"
        "- bottom: 牛仔裤、短裤、长裤、半身裙等下半身穿的\n"
        "- outerwear: 外套、夹克、大衣、风衣等最外层穿的单品\n"
        "- dress: 连衣裙、连体裤等一件式\n"
        "- shoes: 运动鞋、帆布鞋、皮鞋、靴子、凉鞋、高跟鞋等脚上穿的！！！\n"
        "- accessory: 帽子、围巾、包包、腰带等配饰\n\n"
        "=== 各类别示例 ===\n"
        '鞋子→{"name":"白色帆布鞋","category":"shoes","color":"白色","style_tags":"休闲,简约","thickness":"medium","temp_min":10,"temp_max":35,"weather_types":"晴,阴"}\n'
        'T恤→{"name":"白色圆领短袖T恤","category":"top","color":"白色","style_tags":"休闲,简约,纯色","thickness":"thin","temp_min":20,"temp_max":35,"weather_types":"晴,阴"}\n'
        '牛仔裤→{"name":"蓝色直筒牛仔裤","category":"bottom","color":"牛仔蓝","style_tags":"休闲,简约","thickness":"medium","temp_min":10,"temp_max":30,"weather_types":"晴,阴"}\n'
        '连衣裙→{"name":"蓝色方领泡泡袖连衣裙","category":"dress","color":"深蓝色","style_tags":"甜美,修身","thickness":"thin","temp_min":22,"temp_max":35,"weather_types":"晴,阴"}\n\n'
        "注意：鞋子的类别是 shoes，不是 outerwear！外套的类别是 outerwear，不是 shoes！"
    )

    try:
        response = qwen_client.chat.completions.create(
            model="qwen-vl-plus",
            messages=[
                {"role": "system", "content": "你是服装识别专家。只输出 JSON，不要 markdown。"},
                {"role": "user", "content": [
                    {"type": "text", "text": instruction},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
                ]},
            ],
            max_tokens=500,
        )

        result_text = response.choices[0].message.content
        print(f"[AI 识别结果] {result_text}")

        result_text = result_text.strip()
        if result_text.startswith("```"):
            result_text = result_text.split("\n", 1)[1]
            if result_text.endswith("```"):
                result_text = result_text[:-3]

        result = json.loads(result_text)
        return result

    except Exception as e:
        print(f"AI 识别出错: {e}")
        return None


def recommend_outfit(weather, mood, wardrobe_items, exclude_ids=None):
    """根据天气、心情和衣柜推荐穿搭。exclude_ids 是上一套的 ID，用来避免重复。"""

    # 构建衣柜清单
    wardrobe_text = ""
    for i, item in enumerate(wardrobe_items, 1):
        already_used = "（上一套用过，尽量别选）" if exclude_ids and item.id in exclude_ids else ""
        wardrobe_text += (
            f"{i}. ID={item.id} | {item.clothes_name} | "
            f"类别:{item.get_category_display()} | 颜色:{item.color} | "
            f"风格:{item.style_label} | 厚度:{item.get_thickness_display()} | "
            f"适合{item.temp_min}~{item.temp_max}°C{already_used}\n"
        )

    weather_text = (
        f"{weather['text']}，{weather['temp']}°C，体感{weather['feels_like']}°C，"
        f"湿度{weather['humidity']}%，{weather['wind_dir']}{weather['wind_scale']}级"
    )

    system_prompt = (
        "你是一位资深的服装搭配师。请根据用户衣柜搭配一套完整的 outfit。\n\n"
        "=== 搭配铁律 ===\n"
        "1.【连衣裙规则】选了连衣裙(dress)→搭配就是连衣裙，不能再选上衣或下装\n"
        "2.【非连衣裙规则】没选连衣裙→必须选：1件上衣(top)+1件下装(bottom)\n"
        "3.【外套可选】天冷(<15°C)可加1件外套(outerwear)，但外套里面必须有上衣\n"
        "4.【温度定厚度】>28°C短袖短裤, 20-28°C短袖长裤, 10-20°C长袖长裤+可选外套, <10°C厚款必加外套\n"
        "5.【风格统一】JK风配百褶裙,运动风配运动裤,甜美风配短裙,休闲风配牛仔裤\n"
        "6.【颜色协调】上下装颜色不冲突，整身不超过3个主色\n"
        "7.【心情呼应】开心→亮色活泼, emo→柔和舒适, 自信→干练修身, 慵懒→宽松柔软\n"
        "8.【拒绝重复】如果用户说“再来一套”，必须换方案——至少换掉一件衣服，不能和上次一模一样\n"
        "9.【雨露均沾】在满足天气条件的前提下，优先挑还没出现在 explain 里的衣服，让每件都有机会被穿\n\n"
        "只输出 JSON，不要 markdown。"
    )

    user_message = (
        f"天气：{weather_text}\n"
        f"心情：{mood}\n\n"
        f"衣柜清单：\n{wardrobe_text}\n"
        f"请从衣柜里搭配一套完整 outfit。连衣裙→连衣裙；非连衣裙→上衣+下装(天冷加外套)。"
        f"输出格式：{{\"item_ids\":[ID列表],\"explanation\":\"搭配理由80字内\"}}"
    )

    try:
        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=600,
        )

        result_text = response.choices[0].message.content.strip()
        print(f"[AI 推荐结果] {result_text}")

        if result_text.startswith("```"):
            result_text = result_text.split("\n", 1)[1]
            if result_text.endswith("```"):
                result_text = result_text[:-3]

        data = json.loads(result_text)

        item_ids = data.get("item_ids", [])
        items = [item for item in wardrobe_items if item.id in item_ids]
        items.sort(key=lambda x: item_ids.index(x.id) if x.id in item_ids else 999)

        return {
            "items": items,
            "explanation": data.get("explanation", "根据天气和心情为你搭配~"),
        }

    except Exception as e:
        print(f"AI 推荐出错: {e}")
        return None

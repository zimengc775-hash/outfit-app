"""
天气服务模块
使用 Open-Meteo API（完全免费，无需注册）
"""

import requests

# 天气代码 → 中文描述
WEATHER_CODES = {
    0: "晴",
    1: "晴", 2: "多云", 3: "阴",
    45: "雾", 48: "雾凇",
    51: "小雨", 53: "中雨", 55: "大雨",
    61: "小雨", 63: "中雨", 65: "大雨",
    71: "小雪", 73: "中雪", 75: "大雪",
    80: "阵雨", 81: "阵雨", 82: "暴雨",
    95: "雷暴", 96: "雷暴冰雹", 99: "雷暴冰雹",
}


def get_weather_by_location(lat, lng):
    """
    根据经纬度获取实时天气（Open-Meteo 免费 API）。

    返回:
        dict: {city, temp, feels_like, text, humidity, wind_dir, wind_scale}
        失败返回 None
    """

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lng,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,wind_direction_10m",
        "timezone": "auto",
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        current = data["current"]
        code = current["weather_code"]

        # 风向角度 → 中文
        wind_deg = current["wind_direction_10m"]
        wind_dir = _deg_to_direction(wind_deg)

        # 风速 m/s → 风力等级
        wind_speed = current["wind_speed_10m"]
        wind_scale = _speed_to_scale(wind_speed)

        return {
            "city": f"{lat:.1f}°N, {lng:.1f}°E",
            "temp": round(current["temperature_2m"]),
            "feels_like": round(current["apparent_temperature"]),
            "text": WEATHER_CODES.get(code, "未知"),
            "humidity": current["relative_humidity_2m"],
            "wind_dir": wind_dir,
            "wind_scale": wind_scale,
        }

    except Exception as e:
        print(f"获取天气出错: {e}")
        return None


def _deg_to_direction(deg):
    """风向角度 → 中文方向"""
    directions = ["北", "东北", "东", "东南", "南", "西南", "西", "西北"]
    idx = round(deg / 45) % 8
    return directions[idx]


def _speed_to_scale(speed_ms):
    """风速 m/s → 风力等级"""
    if speed_ms < 0.3: return 0
    if speed_ms < 1.6: return 1
    if speed_ms < 3.4: return 2
    if speed_ms < 5.5: return 3
    if speed_ms < 8.0: return 4
    if speed_ms < 10.8: return 5
    if speed_ms < 13.9: return 6
    if speed_ms < 17.2: return 7
    return 8

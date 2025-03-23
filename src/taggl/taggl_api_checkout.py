import requests
from base64 import b64encode
import datetime
import pytz
from urllib.parse import quote
import re

from src.tokens import api_tokens

# 设置时区为 UTC
utc_timezone = pytz.utc

# 输入日期字符串 (YYYYMMDD 格式)
date_str = "20250322"  # 修改这里来改变日期

# 解析日期字符串
try:
    base_date = datetime.datetime.strptime(date_str, "%Y%m%d").date()
except ValueError:
    print("日期格式错误，请输入 YYYYMMDD 格式的日期。")
    exit()

previous_date = base_date - datetime.timedelta(days=1)

# 计算开始和结束时间
start_datetime = datetime.datetime(previous_date.year, previous_date.month, previous_date.day, 16, 0, 0, tzinfo=utc_timezone) #  YYYYMMDD - 1 16:00:00 UTC
end_datetime = datetime.datetime(base_date.year, base_date.month, base_date.day, 15, 59, 59, tzinfo=utc_timezone)  #  YYYYMMDD 15:59:59 UTC

# 转换为 ISO 8601 格式
start_date = start_datetime.isoformat().replace('+00:00', 'Z')
end_date = end_datetime.isoformat().replace('+00:00', 'Z')

url = f"https://api.track.toggl.com/api/v9/me/time_entries?start_date={quote(start_date)}&end_date={quote(end_date)}"

headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Basic %s' % b64encode(f"{api_tokens.taggl_token}:api_token".encode("ascii")).decode("ascii")
}

response = requests.get(url, headers=headers)

print(f"状态码: {response.status_code}")

if response.status_code == 200:
    json_data = response.json()

    # 提取 description
    descriptions = []
    for entry in json_data:
        description = entry.get('description', '')  # 获取描述，如果为 None 则使用空字符串
        if description:  # 只保留非空的描述
            descriptions.append(description)

    def custom_sort_key(description):
        """
        创建排序键，确保非数字开头的字符串排在前面，
        并且能正确处理数字和字母的混合情况。
        """
        if not description:
            return []  # 空字符串排在最后

        # 提取字符串中的时间
        time_match = re.search(r'(\d{1,2})点(半|\d{1,2})?', description)
        time_priority = 0

        if time_match:
            hours = int(time_match.group(1))
            minutes_str = time_match.group(2)
            if minutes_str == '半':
                minutes = 30
            elif minutes_str is not None and minutes_str != "":
                minutes = int(minutes_str)
            else:
                minutes = 0
            time_priority = hours * 60 + minutes

        return [time_priority, description]

    # 排序
    sorted_descriptions = sorted(descriptions, key=custom_sort_key)

    for i in range(len(sorted_descriptions)):
        sorted_descriptions[i] = "- " + sorted_descriptions[i]

    # 格式化输出字符串
    output_string = "\n".join(sorted_descriptions)  # 使用换行符连接所有描述
    output_string = date_str + "\n" + output_string

    print(output_string)
else:
    print(f"错误: {response.text}")

import requests
from base64 import b64encode
import datetime
import pytz
from urllib.parse import quote, urlencode
import re

from src.tokens import api_tokens

def get_config(date_str: str):
    base_date = datetime.datetime.strptime(date_str, "%Y%m%d").date()
    previous_date = base_date - datetime.timedelta(days=1)

    # UTC 时间范围
    utc = pytz.utc
    start_dt = datetime.datetime(previous_date.year, previous_date.month, previous_date.day, 16, 0, 0, tzinfo=utc)
    end_dt = datetime.datetime(base_date.year, base_date.month, base_date.day, 15, 59, 59, tzinfo=utc)

    return {
        "base_date": base_date,
        "start_iso": start_dt.isoformat().replace("+00:00", "Z"),
        "end_iso": end_dt.isoformat().replace("+00:00", "Z"),
        "date_str": date_str,
        "headers": {
            "Content-Type": "application/json",
            "Authorization": "Basic " + b64encode(f"{api_tokens.taggl_token}:api_token".encode("ascii")).decode("ascii")
        }
    }

def get_time_entries(start_iso, end_iso, headers) -> str:
    url = f"https://api.track.toggl.com/api/v9/me/time_entries?meta=true&start_date={quote(start_iso)}&end_date={quote(end_iso)}"

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        json_data = response.json()
        return json_data
    else:
        print("failed to get time_entries", response.status_code, response.text)
        return response.status_code + response.text

def get_content(time_entries, date_str):
        # 提取 description
    descriptions = []
    for entry in time_entries:
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


def get_workspace_id(headers) -> str:
    # Step 1: 获取 workspace
    workspaces_url = "https://api.track.toggl.com/api/v9/me/workspaces"
    response = requests.get(workspaces_url, headers=headers)

    if response.status_code != 200:
        print(f"获取工作空间失败: {response.text}")
        exit()

    workspaces = response.json()
    if not workspaces:
        print("没有找到工作空间")
        exit()

    # 使用第一个工作空间
    workspace_id = workspaces[0]['id']
    return workspace_id

def get_clients(workspace_id, headers) -> dict:
    # Step 2: 获取所有客户端
    clients_url = f"https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/clients"
    response = requests.get(clients_url, headers=headers)

    if response.status_code != 200:
        print(f"获取客户端失败: {response.text}")
        exit()

    clients = response.json()
    client_map = {client['id']: client['name'] for client in clients}
    if not client_map:
        print("没有找到客户端")
        exit()

    return client_map

# {66920502: '自我提升', 66920505: '娱乐', 66920525: '休息放松', 66920529: '日常', 66920538: '打发时间', 67047478: '半学习', 67710440: '睡眠'}
def print_important_clients_duration(time_entries):
    client_durations = {}
    for entry in time_entries:
        client_name = entry.get('client_name')
        duration = entry.get('duration', 0)
        if client_name and duration > 0:
            client_durations[client_name] = client_durations.get(client_name, 0) + duration

    # print(f"\n{date_str} 客户端时长：")
    # for client_name, total_seconds in sorted(client_durations.items()):
    #     hours = total_seconds / 3600
    #     print(f"{client_name}: {hours:.2f} hours")
    # if not client_durations:
    #     print("没有找到有效的时间条目")

    time1, time2 = 0, 0
    for client_name, total_seconds in sorted(client_durations.items()):
        if client_name == "睡眠":
            time1 = total_seconds / 3600
        elif client_name == "半学习":
            time2 += total_seconds / 3600 / 2
        elif client_name == "自我提升":
            time2 += total_seconds / 3600

    print(f"睡眠: {time1:.2f} hours")
    print(f"自我提升: {time2:.2f} hours")

def get_week_range_utc(date_str: str):
    base_date = datetime.datetime.strptime(date_str, "%Y%m%d").date()
    weekday = base_date.weekday()  # 周一 = 0，周日 = 6

    # 原本周一日期
    monday = base_date - datetime.timedelta(days=weekday)

    # 修正起点（前一天16:00）
    week_start_dt = datetime.datetime(monday.year, monday.month, monday.day, 16, 0, 0, tzinfo=pytz.utc) - datetime.timedelta(days=1)
    week_end_dt = week_start_dt + datetime.timedelta(days=7) - datetime.timedelta(seconds=1)

    return week_start_dt.isoformat().replace("+00:00", "Z"), week_end_dt.isoformat().replace("+00:00", "Z")

def main():
    config = get_config("20250721")

    time_entries = get_time_entries(config["start_iso"], config["end_iso"], config["headers"])
    get_content(time_entries, config["date_str"])
    print("\n=== 本日统计 ===")
    print_important_clients_duration(time_entries)

    week_st, week_ed = get_week_range_utc(config["date_str"])
    time_entries_week = get_time_entries(week_st, week_ed, config["headers"])
    print("\n=== 本周统计 ===")
    print_important_clients_duration(time_entries_week)


if __name__ == "__main__":
    main()
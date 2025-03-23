import requests
from datetime import datetime

from src.tokens.api_tokens import NOTION_API_KEY

# 1. 需要访问页面授权给 token, 在页面的设置的connections中添加token名
# 2. Database_ID, 可以通过在 DB 页面 share 中 copy link 获取
DATABASE_ID = "e3907c0bf3304fbd8633285d69ce56a3"
DATE_COLUMN = "Scheduled"
COLUMN_A = "笔记名"
COLUMN_B = "备注2"

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def update_rows(date_column, column_a, column_b):
    cursor = None
    cnt = 0
    while True:
        payload = {"start_cursor": cursor} if cursor else {}
        response = requests.post(
            f"https://api.notion.com/v1/databases/{DATABASE_ID}/query",
            headers=headers,
            json=payload
        ).json()

        for row in response.get("results", []):
            try:
                # 获取当前值
                col_a_value = row["properties"][column_a]["title"][0]["text"]["content"]
                col_b_value = row["properties"][column_b]["rich_text"][0]["text"]["content"] \
                    if row["properties"][column_b]["rich_text"] else ""

                # 正确地交换两个字段的内容
                updated_properties = {
                    column_a: {"title": [{"text": {"content": col_b_value}}]},
                    column_b: {"rich_text": [{"text": {"content": col_a_value}}]}
                }

                # 发起更新请求
                page_id = row["id"]
                update_response = requests.patch(
                    f"https://api.notion.com/v1/pages/{page_id}",
                    headers=headers,
                    json={"properties": updated_properties}
                ).json()
                cnt += 1
                print(f"已更新页面 {page_id}，交换{column_a}和{column_b}, cnt {cnt}")

            except (KeyError, ValueError) as e:
                print(f"Error processing row: {e}")

        if not response.get("has_more"):
            break

        cursor = response.get("next_cursor")

update_rows(DATE_COLUMN, COLUMN_A, COLUMN_B)
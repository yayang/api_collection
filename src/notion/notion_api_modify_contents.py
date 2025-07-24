import requests

from src.tokens.api_tokens import NOTION_API_KEY

# 替换中文逗号

# 1. 需要访问页面授权给 token, 在页面的设置的connections中添加token名
# 2. Database_ID, 可以通过在 DB 页面 share 中 copy link 获取
DATABASE_ID = "1ef15d9eb4a880629a58e322461b01c9"    # 游戏花费
COLUMN_NAME = "游戏名"

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def update_content(column_name):
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
                page_id = row["id"]
                rich_text_prop = row["properties"][column_name]["rich_text"]
                if not rich_text_prop:
                    continue
                col_value = rich_text_prop[0]["text"]["content"]
                if "，" in col_value:
                    new_value = col_value.replace("，", ", ")
                    print(f"Updating '{col_value}' -> '{new_value}'")

                    update_data = {
                        "properties": {
                            column_name: {
                                "rich_text": [
                                    {
                                        "type": "text",
                                        "text": {
                                            "content": new_value
                                        }
                                    }
                                ]
                            }
                        }
                    }

                    update_url = f"https://api.notion.com/v1/pages/{page_id}"
                    update_resp = requests.patch(update_url, headers=headers, json=update_data)
                    if update_resp.status_code == 200:
                        cnt += 1
                    else:
                        print(f"Failed to update page {page_id}: {update_resp.text}")

            except (KeyError, ValueError, IndexError) as e:
                print(f"Error processing row: {e}")

        if not response.get("has_more"):
            break

        cursor = response.get("next_cursor")
    print(f"✅ 共更新了 {cnt} 行")

update_content(COLUMN_NAME)
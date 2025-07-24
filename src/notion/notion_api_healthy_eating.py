import json
import re
import requests

from src.tokens.api_tokens import NOTION_API_KEY

# 1. 需要访问页面授权给 token, 在页面的设置的connections中添加token名
# 2. Database_ID, 可以通过在 DB 页面 share 中 copy link 获取
DATABASE_ID = "1fa15d9eb4a880bd91bdcebf51d6620f"    # 营养素
NAME = "具体食材"
AMOUNT = "分量"

food_name = "11 杂粮馒头 1个"
new_amount = 27

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}


def smart_limit_to_4_digits(x):
    if x == 0:
        return 0.0
    abs_x = abs(x)
    if abs_x >= 100:
        return round(x)
    elif abs_x >= 10:
        return round(x, 1)
    elif abs_x >= 1:
        return round(x, 2)
    else:
        return round(x, 3)

def extract_number_and_unit(text):
    match = re.match(r"(\d+(?:\.\d+)?)(\s*\S*)", text.strip())
    if not match:
        raise ValueError(f"无法从分量中解析出数值和单位: {text}")
    return float(match.group(1)), match.group(2)


def query_page(ingredient_name):
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    body = {
        "filter": {
            "property": NAME,
            "rich_text": {
                "equals": ingredient_name
            }
        }
    }
    res = requests.post(url, headers=headers, json=body)
    res.raise_for_status()
    results = res.json().get("results", [])
    if not results:
        raise Exception(f"❌ 未找到食材 '{ingredient_name}'")
    return results[0]


def extract_numeric_properties(properties):
    numeric = {}
    for key, val in properties.items():
        if val["type"] == "number" and val["number"] is not None:
            numeric[key] = val["number"]
    return numeric


def extract_amount_text(properties):
    rich = properties[AMOUNT]["rich_text"]
    if not rich:
        raise Exception("❌ 分量字段为空")
    return rich[0]["text"]["content"]


def adjust_ingredient(ingredient_name, new_amount):
    page = query_page(ingredient_name)
    page_id = page["id"]
    props = page["properties"]

    # 1. 获取原始分量
    amount_text = extract_amount_text(props)
    old_amount, unit = extract_number_and_unit(amount_text)
    ratio = new_amount / old_amount

    print(f"🔍 找到食材：{ingredient_name}")
    print(f"📦 原分量：{amount_text}，新分量：{new_amount}{unit}，比例：{round(ratio, 4)}")

    old_values = extract_numeric_properties(props)
    print("📊 更新前：")
    print(json.dumps(old_values, indent=2, ensure_ascii=False))

    # 2. 构建更新字段
    updated_props = {}

    for key, val in old_values.items():
        updated_props[key] = {
            "number": smart_limit_to_4_digits(val * ratio)
        }


    updated_props[AMOUNT] = {
        "rich_text": [{"text": {"content": f"{new_amount}{unit}"}}]
    }

    # 3. 更新页面
    update_url = f"https://api.notion.com/v1/pages/{page_id}"
    res = requests.patch(update_url, headers=headers, json={"properties": updated_props})
    res.raise_for_status()

    print("✅ 已更新页面")
    print("📊 更新后：")
    new_values = {k: smart_limit_to_4_digits(v * ratio) for k, v in old_values.items()}
    print(json.dumps(new_values, indent=2, ensure_ascii=False))


# ✅ 示例调用
if __name__ == "__main__":
    adjust_ingredient(food_name, new_amount)
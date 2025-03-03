import re

def custom_sort_key(s):
    # 使用正则表达式分解字符串为字母和数字部分
    parts = re.findall(r'[A-Za-z]+|\d+', s)

    # 将每个部分转换为元组，数字部分转为整数，字母部分保持原样
    key = []
    for part in parts:
        if part.isdigit():
            key.append((0, int(part)))  # 数字部分转为整数，并加一个标记（0）
        else:
            key.append((1, part))  # 字母部分保持原样，并加一个标记（1）

    return tuple(key)

# 测试字符串列表
strings = ["abc10", "abc2", "xyz100", "xyz20", "1ab", "10ab","02ab"]

# 使用自定义排序函数进行排序
sorted_strings = sorted(strings, key=custom_sort_key)

print(sorted_strings)

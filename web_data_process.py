import csv
import json
import pandas as pd
import requests
from tqdm import tqdm
import time
import os

'''
    格式化的非遗项目_web文件，将其中的申报地区、传承人信息以及文章详情格式化成字符串形式方便后续QA数据集的制作
    顺便在这里把数据清洗做了
'''

# 需要额外处理的表项
special_item = [
    "孟姜女传说", "格萨（斯）尔", "江格尔", "苏东坡传说", "蒙古包营造技艺", "瑶族服饰", "苗族鼓藏节", "蒙古族服饰",
    "藏族服饰",  "上海港码头号子", "古琴艺术", "大铜器", "蒙古族四胡音乐", "长江峡江号子", "土家族撒叶儿嗬", "苗族芦笙舞",
    "萨吾尔登", "二人台", "淮北梆子戏", "茂腔", "豫剧", "黄梅戏", "岳家拳", "蒙古族搏克",
    "螳螂拳", "蒙古族刺绣", "麦秆剪贴", "乐亭大鼓", "含岔曲", "山东落子", "西河大鼓", "鼓盆歌"
]

# -1去除开头，1去除结尾
flag = [
    1, 1, 1, 1, 1, 1, 1, 1,
    1, -1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1
]

# 配置 DeepSeek API
DEEPSEEK_API_KEY = os.getenv("DeepSeek_API_KEY")  # 替换为你的 DeepSeek API Key
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
MAX_LENGTH = 1096  # 判断是否需要压缩的阈值
MAX_TOKENS = 1024   # 压缩后的最大字符数

# 设置请求头
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
}

# 摘要提示词
REQUEST_BODY_TEMPLATE = {
    "model": "deepseek-reasoner",
    "messages": [
        {
            "role": "user",
            "content": ""
        }
    ],
    "temperature": 0.7,
    "top_p": 0.95,
    "max_tokens": MAX_TOKENS
}

SUMMARIZE_PROMPT = "请用中文对以下内容进行专业、准确的总结，保留关键信息，并确保总字数不超过1024个字符（注意，你只需要输出总结后的内容，不要输出任何无关文字）：\n\n"

def summarize_text(type: str, text: str, retries=3, delay=5) -> str:
    if not isinstance(text, str) or len(text.strip()) == 0:
        return text

    if type != "相关文章" and len(text) <= MAX_LENGTH:
        return text

    payload = REQUEST_BODY_TEMPLATE.copy()
    payload["messages"][0]["content"] = SUMMARIZE_PROMPT + text[:4096]  # 添加长度限制
    timeout = 0

    for attempt in range(retries):
        timeout += 180
        try:
            response = requests.post(DEEPSEEK_API_URL, headers=HEADERS, json=payload, timeout=timeout)
            
            # 检查HTTP状态码
            if response.status_code != 200:
                print(f"HTTP Error {response.status_code}: {response.text}")
                continue
                
            result = response.json()
            
            # 检查API响应结构
            if 'choices' not in result or len(result['choices']) == 0:
                print(f"Invalid API response: {result}")
                continue
                
            print(result['choices'][0]['message']['content'].strip())
            return result['choices'][0]['message']['content'].strip()
            
        except requests.exceptions.RequestException as e:
            print(f"Request failed on attempt {attempt + 1}: {e}")
            time.sleep(delay * (attempt + 1))  # 指数退避
        except KeyError as e:
            print(f"Key error in response: {e}")
            break
    print(text[:MAX_TOKENS])
    return text[:MAX_TOKENS]  # 失败时返回截断文本

def process_region(region_str):
    """处理申报地区或单位字段"""
    try:
        regions = json.loads(region_str.replace("'", '"'))
        if isinstance(regions, list):
            return '、'.join(regions), len(regions)
        return region_str, 1
    except (json.JSONDecodeError, TypeError):
        return region_str, 1

def process_description(project_name, desc_str):
    """处理官网描述字段，确保数组元素为字符串，过滤空字符串和单引号"""
    try:
        if project_name in special_item:
            if flag[special_item.index(project_name)] == -1:
                desc_str = desc_str.replace('nan, ', '') 
            else:
                desc_str = desc_str.replace(', nan', '')
        # 替换单引号为双引号并尝试解析JSON
        desc_data = json.loads(desc_str.replace("'", '"'))
        if isinstance(desc_data, list):
            filtered = [
                item for item in desc_data
                if isinstance(item, str)
            ]
            # API 总结
            filtered = [summarize_text("官网描述", item) for item in filtered]
            if len(filtered) == 1:
                return filtered[0]
            elif len(filtered) > 1:
                return filtered
            else:
                return ''
        elif isinstance(desc_data, str):
            return desc_data.strip()
        else:
            return ''
    except (json.JSONDecodeError, TypeError):
        # 如果解析失败，返回原始字符串或空
        return desc_str if isinstance(desc_str, str) else ''
    
def process_person_info(person_data, region_str, regions_count):
    """处理传承人信息字段，返回传承人列表"""
    processed_people = []
    
    if regions_count == 1:
        # 单地区处理方式
        for person in person_data:
            if not isinstance(person, dict):
                continue
            
            # 提取字段（过滤空值）
            fields = []
            name = person.get('name', '')
            gender = person.get('gender', '')
            ethnicity = person.get('ethnicity', '')
            birth_date = person.get('birth_date', '')
            
            if not name:  # 如果姓名为空，跳过
                continue
            
            # 构建有效字段列表
            fields.append(name)
            if gender:
                fields.append(gender)
            if ethnicity:
                fields.append(ethnicity)
            
            # 籍贯字段
            if region_str:
                fields.append(f"籍贯：{region_str}")
            
            # 出生日期字段
            if birth_date:
                fields.append(f"出生日期：{birth_date}")
            
            # 拼接结果（用中文逗号分隔）
            processed_people.append("，".join(fields))
    else:
        # 多地区处理方式
        for entry in person_data:
            if not isinstance(entry, dict) or 'position' not in entry:
                continue
            position = entry['position']
            people_list = entry.get('person', [])
            
            for person in people_list:
                if not isinstance(person, dict):
                    continue
                
                # 提取字段（过滤空值）
                fields = []
                name = person.get('name', '')
                gender = person.get('gender', '')
                ethnicity = person.get('ethnicity', '')
                birth_date = person.get('birth_date', '')
                
                if not name:
                    continue
                
                # 构建有效字段列表
                fields.append(name)
                if gender:
                    fields.append(gender)
                if ethnicity:
                    fields.append(ethnicity)
                
                # 籍贯字段（从position获取）
                if position:
                    fields.append(f"籍贯：{position}")
                
                # 出生日期字段
                if birth_date:
                    fields.append(f"出生日期：{birth_date}")
                
                # 拼接结果（用中文逗号分隔）
                processed_people.append("，".join(fields))
    
    return processed_people

def process_articles(articles_str):
    """处理相关文章字段，确保数组元素为字典"""
    try:
        articles = json.loads(articles_str.replace("'", '"'))
        if not isinstance(articles, list):
            articles = [articles]
        if len(articles) == 0:
            return ''
        processed = []
        for article in articles:
            if isinstance(article, dict):
                title = article.get('title', '')
                content = article.get('content', '')
                if title or content:  # 只有标题或内容不为空才保留
                    processed.append(f"{title}\n{content}")
        processed = [summarize_text("相关文章", item) for item in processed]
        return processed
    except (json.JSONDecodeError, TypeError):
        return ''

def main():
    with open('非遗项目_web.csv', 'r', encoding='utf-8') as infile, \
         open('非遗项目_web_clean.csv', 'w', encoding='utf-8-sig', newline='') as outfile:
        
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            # 处理申报地区或单位
            region_str, regions_count = process_region(row['申报地区或单位'])
            row['申报地区或单位'] = region_str

            # 处理传承人信息
            try:
                person_data = json.loads(row['传承人信息'].replace("'", '"')) if row['传承人信息'] else []
            except json.JSONDecodeError:
                person_data = []
                
            processed_people = process_person_info(person_data, region_str, regions_count)

            if row["项目名称"] == "斯":
                row["项目名称"] = "格萨（斯）尔"

            # 处理官网描述（新增）
            row['官网描述'] = process_description(row["项目名称"], row['官网描述'])

            # 处理相关文章（新增）
            row['相关文章'] = process_articles(row['相关文章'])

            # 处理传承人信息：单个不加序号，多个分行加序号
            if processed_people:
                if len(processed_people) > 1:
                    processed_people = [f"{i+1}. {person}" for i, person in enumerate(processed_people)]
                    row['传承人信息'] = '\n'.join(processed_people)
                else:
                    row['传承人信息'] = processed_people[0]
                writer.writerow(row)
            else:
                row['传承人信息'] = ''
                writer.writerow(row)

if __name__ == '__main__':
    main()
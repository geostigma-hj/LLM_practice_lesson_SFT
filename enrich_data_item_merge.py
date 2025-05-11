import csv
import json
from collections import defaultdict
import pandas as pd

def clean_project_name(original_name):
    """清洗项目名称，提取末尾括号中的别名"""
    import re
    # 匹配以中文括号结尾的别名，且确保括号不在名称中间
    match = re.search(r'^(.*?)\(([^)]+)\)$', original_name)  # 匹配英文括号
    if not match:
        match = re.search(r'^(.*?)（([^）]+)）$', original_name)  # 匹配中文括号
    
    if match:
        # 提取主名称和别名，当主名称为空时保留整个名称
        main_name, alias = match.groups()
        return alias if main_name else original_name
    return original_name

def process_heritage_data(input_file, output_file):
    # 读取CSV数据并分组
    grouped_data = defaultdict(list)
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            project_name = clean_project_name(row['项目名称'].strip())

            # 预处理JSON字段（改用 ast 安全解析）
            import ast
            def safe_json_parse(s):
                try:
                    return ast.literal_eval(s)  # 直接解析 Python 数据结构
                except Exception as e:
                    print(f"解析失败原始数据: {s}")
                    raise
            
            row['传承人信息'] = safe_json_parse(row['传承人信息'])
            row['相关文章'] = safe_json_parse(row['相关文章'])
            grouped_data[project_name].append(row)

    merged_rows = []
    for name, items in grouped_data.items():
        if len(items) == 1:
            # 单条数据直接保留原始格式
            raw_item = items[0]
            merged_rows.append({
                '项目名称': name,
                '项目类别': raw_item['项目类别'],
                '申报地区或单位': raw_item['申报地区或单位'],
                '详情链接': raw_item['详情链接'],
                '官网描述': raw_item['官网描述'],
                '传承人信息': json.dumps(raw_item['传承人信息'], ensure_ascii=False),
                '相关文章': json.dumps(raw_item['相关文章'], ensure_ascii=False)
            })
            continue

        # 多条数据执行合并逻辑
        merged = {
            '项目名称': name,
            '项目类别': items[0]['项目类别'],
            '详情链接': items[0]['详情链接'],
        }

        # 处理申报地区或单位（去重）
        regions = list({item['申报地区或单位'] for item in items})
        merged['申报地区或单位'] = json.dumps(regions, ensure_ascii=False)

        # 处理官网描述（过滤空值后去重）
        descriptions = list({item['官网描述'] for item in items if item['官网描述'].strip()})
        # 新增格式转换：单元素直接存字符串
        if len(descriptions) == 1:
            merged['官网描述'] = json.dumps(descriptions[0], ensure_ascii=False)
        else:
            merged['官网描述'] = json.dumps(descriptions, ensure_ascii=False) if descriptions else ''
        
        # 处理相关文章（标题去重）
        seen_titles = set()
        merged_articles = []
        for item in items:
            for article in item['相关文章']:
                if article['title'] not in seen_titles:
                    seen_titles.add(article['title'])
                    merged_articles.append(article)
        merged['相关文章'] = json.dumps(merged_articles, ensure_ascii=False)

        # 处理传承人信息
        unique_regions = set(item['申报地区或单位'] for item in items)
        if len(unique_regions) > 1:
            # 多地区分类格式
            region_persons = defaultdict(list)
            for item in items:
                region = item['申报地区或单位']
                for person in item['传承人信息']:
                    region_persons[region].append(person)
            
            # 去重（姓名+地区唯一）
            formatted_persons = []
            for region, persons in region_persons.items():
                seen_names = set()
                unique_persons = []
                for p in persons:
                    if p['name'] not in seen_names:
                        seen_names.add(p['name'])
                        unique_persons.append(p)
                formatted_persons.append({
                    'position': region,
                    'person': unique_persons
                })
            merged['传承人信息'] = json.dumps(formatted_persons, ensure_ascii=False)
        else:
            # 单地区保持原格式
            all_persons = [p for item in items for p in item['传承人信息']]
            seen_names = set()
            unique_persons = []
            for p in all_persons:
                if p['name'] not in seen_names:
                    seen_names.add(p['name'])
                    unique_persons.append(p)
            merged['传承人信息'] = json.dumps(unique_persons, ensure_ascii=False)

        merged_rows.append(merged)

    # 写入输出文件
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=merged_rows[0].keys())
        writer.writeheader()
        writer.writerows(merged_rows)

def main():
    # 处理 enrich_web_items.csv 中的全部 csv 文件
    TYPE_MAP = {
        1: "民间文学",
        2: "传统音乐",
        3: "传统舞蹈",
        4: "传统戏剧",
        5: "曲艺",
        6: "传统体育、游艺与杂技",
        7: "传统美术",
        8: "传统技艺",
        9: "传统医药",
        10: "民俗"
    }
    for project_type in range(1, 11):
        filename = f'非遗项目_{TYPE_MAP[project_type]}.csv'
        process_heritage_data(f'enrich_web_items/{filename}', f'merged_web_items/merged_{filename}')

    # 最后将处理后的所有文件合并（合并 merged_web_items 目录下的所有 csv 文件，保存为 非遗项目_web.csv）
    merged_files = [f'merged_web_items/merged_非遗项目_{TYPE_MAP[project_type]}.csv' for project_type in range(1, 11)]
    merged_df = pd.concat([pd.read_csv(file) for file in merged_files])
    merged_df.to_csv('非遗项目_web.csv', index=False, encoding='utf-8-sig')

if __name__ == "__main__":
    main()
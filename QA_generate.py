# 从 final_dataseet 构造 QA 数据集
import pandas as pd
import json
import ast
import random

# 定义问题模板
QA_TEMPLATES = {
    "项目类别": [
        "{name}属于什么类别的非遗文化？",
        "{name}是关于什么的非遗文化？",
        "{name}在非遗文化中属于什么类型？"
    ],
    "申报地区或单位": [
        "{name}的起源地是哪里？",
        "{name}是从哪里起源的？",
        "{name}主要流传于哪些地区？"
    ],
    "传承人信息": [
        "{name}的代表性传承人有哪些？",
        "谁是{name}的主要传承者？",
        "请列举出{name}的一些重要传承人物"
    ],
    "官网描述": [
        "请介绍{name}的基本情况",
        "简要说明{name}的特点",
        "请概述{name}的文化价值"
    ],
    "历史渊源": [
        "讲解{name}的历史发展过程",
        "介绍{name}的起源与演变",
        "梳理一下{name}的历史脉络"
    ],
    "相关文章": [
        "概述{name}近年来的社会动态",
        "介绍{name}的近期发展状况",
        "{name}近段时间的相关新闻有哪些？"
    ]
}

def parse_array_field(value):
    """安全解析数组字段"""
    if pd.isna(value) or value is None:
        return []
    if isinstance(value, str):
        if value.startswith('[') and value.endswith(']'):
            try:
                return ast.literal_eval(value)
            except:
                return value.split('\n')
        return [value]
    return list(value)

def generate_qa(data_row):
    """根据数据行生成QA对"""
    qa_pairs = []
    name = data_row['项目名称']
    
    # 处理项目类别
    if pd.notna(data_row['项目类别']):
        template = random.choice(QA_TEMPLATES["项目类别"])
        qa_pairs.append({
            "instruction": template.format(name=name),
            "input": "",
            "output": data_row['项目类别'].strip()
        })
    
    # 处理申报地区
    if pd.notna(data_row['申报地区或单位']):
        template = random.choice(QA_TEMPLATES["申报地区或单位"])
        qa_pairs.append({
            "instruction": template.format(name=name),
            "input": "",
            "output": data_row['申报地区或单位'].strip()
        })
    
    # 处理传承人信息
    if pd.notna(data_row['传承人信息']):
        template = random.choice(QA_TEMPLATES["传承人信息"])
        qa_pairs.append({
            "instruction": template.format(name=name),
            "input": "",
            "output": data_row['传承人信息'].strip()
        })
    
    # 处理官网描述（支持数组类型）
    descriptions = parse_array_field(data_row['官网描述'])
    for desc in descriptions:
        if desc.strip():
            template = random.choice(QA_TEMPLATES["官网描述"])
            cleaned_desc = '\n'.join([line.strip() for line in desc.split('\n') if line.strip()])
            qa_pairs.append({
                "instruction": template.format(name=name),
                "input": "",
                "output": cleaned_desc
            })
    
    # 处理历史渊源
    if pd.notna(data_row['历史渊源']):
        template = random.choice(QA_TEMPLATES["历史渊源"])
        cleaned_history = '\n'.join([line.strip() for line in str(data_row['历史渊源']).split('\n') if line.strip()])
        qa_pairs.append({
            "instruction": template.format(name=name),
            "input": "",
            "output": cleaned_history
        })
    
    # 处理相关文章（支持数组类型）
    articles = parse_array_field(data_row['相关文章'])
    for article in articles:
        if article.strip():
            template = random.choice(QA_TEMPLATES["相关文章"])
            cleaned_history = '\n'.join([line.strip() for line in str(data_row['相关文章']).split('\n') if line.strip()])
            qa_pairs.append({
                "instruction": template.format(name=name),
                "input": "",
                "output": article.strip()
            })
    
    return qa_pairs

def main():
    df = pd.read_csv("final_dataset.csv")
    all_qa = []
    
    # 设置随机种子（可选）
    # random.seed(42)  # 保证结果可复现
    
    for _, row in df.iterrows():
        all_qa.extend(generate_qa(row))
    
    with open("qa_dataset.json", "w", encoding="utf-8") as f:
        json.dump(all_qa, f, ensure_ascii=False, indent=2)
    
    print(f"成功生成{len(all_qa)}对QA数据！")

if __name__ == "__main__":
    main()
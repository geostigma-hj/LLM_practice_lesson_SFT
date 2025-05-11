import pandas as pd
import requests
from tqdm import tqdm
import time
import json
import os

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

def summarize_text(text: str, retries=3, delay=5) -> str:
    if not isinstance(text, str) or len(text.strip()) == 0:
        return text

    if len(text) <= MAX_LENGTH:
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

# 处理数组字段的函数
def process_array_field(arr):
    if not isinstance(arr, list):
        return arr
    return [summarize_text(item) if isinstance(item, str) else item for item in arr]

# 主函数：处理 CSV 文件
def process_csv(input_file="百度百科.csv", output_file="百度百科_clean.csv"):
    df = pd.read_csv(input_file)
    # 去除 status 字段
    if 'status' in df.columns:
        df.drop(columns=['status'], inplace=True)

    # 只处理历史渊源和相关介绍字段
    fields_to_process = ['相关介绍', '历史渊源']
    
    # 进度条处理
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Processing Rows"):
        for field in fields_to_process:
            if field in df.columns:
                value = row[field]
                df.at[idx, field] = summarize_text(value)

    # 保存结果
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"✅ 处理完成，已保存至 {output_file}")

# 执行
if __name__ == "__main__":
    process_csv()
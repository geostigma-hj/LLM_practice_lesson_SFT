import requests
import csv
from urllib.parse import urljoin
import time
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os

BASE_URL = 'https://www.ihchina.cn'
CSV_HEADERS = ['项目名称', '项目类别', '申报地区或单位', '详情链接']

def get_projects_by_type(project_type, csv_filename):
    page = 1
    session = requests.Session()
    retry = Retry(
        total=5,  # 增加重试次数
        backoff_factor=5,  # 指数退避: 5s, 10s, 20s...
        status_forcelist=[429, 500, 502, 503, 504]  # 新增429状态码
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    # 首次写入表头（优化文件存在性检查）
    if not os.path.isfile(csv_filename):
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            csv.DictWriter(f, fieldnames=CSV_HEADERS).writeheader()

    while True:
        url = f"{BASE_URL}/getProject.html"
        params = {
            'type': project_type,
            'category_id': 16,
            'p': page
        }

        try:
            response = session.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            # 检查数据结构
            projects = data.get('list', [])
            if not projects:
                print(f"分类 {project_type} 第 {page} 页无数据")
                break

            # 写入CSV（优化写入逻辑）
            with open(csv_filename, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
                for project in projects:
                    try:
                        writer.writerow({
                            '项目名称': project.get('title', 'N/A'),
                            '项目类别': project.get('type', 'N/A'),
                            '申报地区或单位': project.get('province', 'N/A'),
                            '详情链接': urljoin(BASE_URL, f"/project_details/{project.get('id', '')}.html")
                        })
                    except Exception as e:
                        print(f"写入数据时发生错误: {e}")
                        continue

            print(f"分类 {project_type} 第 {page} 页爬取完成，保存 {len(projects)} 条数据到 {csv_filename}")
            
            # 增强分页控制（使用正则提取数字）
            try:
                total_pages_text = data['links']['end']['text']
                total_pages = int(re.search(r'\d+', total_pages_text).group())
                print(f"检测到总页数: {total_pages}")
                if page >= total_pages:
                    break
            except (KeyError, TypeError, AttributeError):
                print("无法获取总页数，尝试继续下一页")
                total_pages = page + 1  # 强制继续
            
            page += 1
            time.sleep(2)  # 优化请求间隔

        except requests.exceptions.HTTPError as e:
            print(f"HTTP错误: {e}")
            if e.response.status_code == 429:
                print("触发反爬虫机制，等待30秒后重试...")
                time.sleep(30)
            else:
                print("未知HTTP错误，等待10秒后重试...")
                time.sleep(10)
        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"请求出错: {e}, 5秒后重试...")
            time.sleep(5)
            continue

def main():
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
        print(f"\n{'='*30} 开始爬取分类 {project_type} - {TYPE_MAP[project_type]} {'='*30}")
        get_projects_by_type(project_type, filename)
        print(f"{'='*30} 分类 {project_type} 爬取完成 {'='*30}\n")

if __name__ == '__main__':
    main()
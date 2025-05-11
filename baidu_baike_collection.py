import requests
from bs4 import BeautifulSoup
import re
import time
import random
import logging
import csv
from urllib.parse import quote
import os
from fake_useragent import UserAgent

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

cache_path = "fake_useragent_0.1.11.json"

def remove_references(text):
    """
    去除文本中的引用标记，如[[1]]、[[2-3]]等
    """
    # 匹配形如[[数字]]或[[数字-数字]]的引用标记
    pattern = re.compile(r'\[\[[^\]]*\]\]')
    cleaned_text = pattern.sub('', text)
    return cleaned_text.rstrip()

def extract_content_from_html(url=None, html_content=None):
    """
    从URL或HTML内容中提取内容，策略如下：
    1. 如果找到至少两个一级标题，则提取第一个和第二个一级标题之间的内容
    2. 如果只找到一个一级标题，则提取所有段落内容
    3. 检查并提取"传承人物"二级标题的内容
    """
    result = {"历史渊源":"", "传承人物": "", "相关介绍": "", "错误信息": ""}

    # 如果提供了URL，则从URL获取HTML内容
    if url and not html_content:
        REQUEST_CONFIG = {
            'base_delay': 5,
            'random_delay': 5,
            'max_retries': 3
        }
        for attempt in range(REQUEST_CONFIG["max_retries"]):
            try:
                delay = REQUEST_CONFIG['base_delay'] + random.uniform(0, REQUEST_CONFIG['random_delay'])
                time.sleep(delay)

                # 伪造请求头
                ua = UserAgent(
                    use_cache_server=False,  # 禁用在线获取
                    cache=True,  # 启用本地缓存
                    path=cache_path  # 指定缓存路径
                )

                headers = {
                    'User-Agent': ua.random,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
                    'Referer': 'https://www.baidu.com/',
                    "cookie": 'BAIDUID_BFESS=EA6DD46FA63803B13EC0F91F1BA140EE:FG=1; MCITY=-131%3A; jsdk-uuid=dd76eb04-dad2-410f-9d54-3bbfa4cbbfca; BAIDU_WISE_UID=wapp_1725622131279_885; __bid_n=192db11f3bd20166ef26a1; H_PS_PSSID=60278_61027_61091_60853_61130_61127_61141_61107_61216_61207_61211_61213_61208; H_WISE_SIDS=60278_61027_61091_60853_61130_61127_61141_61107_61216_61207_61211_61213_61208; H_WISE_SIDS_BFESS=60278_61027_61091_60853_61130_61127_61141_61107_61216_61207_61211_61213_61208; uc_login_unique=7ff7e01b7e8249edaa8e6b57d15cc0f7; uc_recom_mark=cmVjb21tYXJrXzUzNjM5OTU1; ZFY=2RiwFS:Aw:B1v4TZrHDfFLuHohdnMGNgGE08:B3SQompFM:C; BDUSS=lVwZlllVGlMQkMxalRqVTdrR3p-YlBsWjZNNDNNMHpUWFFuUHVPenB6bm5-eDVvRVFBQUFBJCQAAAAAAQAAAAEAAAD07yCWcGVuZ3hpbnl1ZXIxMjMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAOdy92fncvdnV; BDUSS_BFESS=lVwZlllVGlMQkMxalRqVTdrR3p-YlBsWjZNNDNNMHpUWFFuUHVPenB6bm5-eDVvRVFBQUFBJCQAAAAAAQAAAAEAAAD07yCWcGVuZ3hpbnl1ZXIxMjMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAOdy92fncvdnV; RT="z=1&dm=baidu.com&si=741efacd-10f1-402a-a86a-c2390c43ce4d&ss=m9b2aiq5&sl=7&tt=h5y&bcn=https%3A%2F%2Ffclog.baidu.com%2Flog%2Fweirwood%3Ftype%3Dperf&ld=aqlt&ul=bbmq&hd=bbph"; baikeVisitId=0db95556-4c47-48bc-bbf9-0f97cd08d5ae; ab_sr=1.0.1_ZDAyMmY1MzdkNmY4NDZhZDExNzQ1YjY2MTc5YTdlYjY0NmM4ZDMzNmQ1NDg1MjFjNjc5YTYzNzcxOWMzYzUxZGM5YWUyY2VlZTU0YzMxYjE3MzM4YWU0M2FmMDdmNjFmZTdmNGY2N2I2MWQ3Nzg5ZTkxMTNhMzBlNjc5NzAwMjNjZGZlNTYyNmZhMWVjNmU2YmZkMjY3ZDE5Yjg0ODFiZDBhMmM2MDYzZTJhYmNmMDYzZjY2ZDBkNGVjNmQ1MTVl'
                }
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                response.encoding = response.apparent_encoding
                html_content = response.text
                break

            except requests.exceptions.RequestException as e:
                logger.warning(f"第 {attempt+1} 次尝试失败: {str(e)}")
                if attempt == REQUEST_CONFIG["max_retries"] - 1:
                    logger.error(f"URL {url} 重试{REQUEST_CONFIG['max_retries']}次后失败")
                    result["错误信息"] = f"请求最终失败: {str(e)}"
                    return result
                time.sleep(2 ** attempt)  # 指数退避等待
    
    if html_content and os.path.exists(html_content):
        try:
            with open(html_content, 'r', encoding='utf-8') as f:
                html_content = f.read()
        except Exception as e:
            return "未提供HTML内容或URL"
    
    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    try:
        summary_section = soup.find('div', class_="lemmaSummary_kUDz3 J-summary")
        if summary_section:
            summary_text = ""
            summary_paras = summary_section.find_all('div', class_="para_wIHuD summary_GlHcs MARK_MODULE")
            for para in summary_paras if summary_paras else []:
                spans = para.find_all(class_="text_XlFoe")
                if spans:
                    para_text = "".join(span.get_text(strip=True) for span in spans)
                    summary_text += f"{para_text}\n\n"
            result["相关介绍"] = remove_references(summary_text.strip())
    except Exception as e:
        logger.error(f"解析摘要时出错: {str(e)}")
        result["错误信息"].append(f"摘要解析错误: {str(e)}")
    
    ### 定位历史渊源
    try:
        # 更精确地查找一级标题元素
        h1_elements = soup.find_all('div', class_="paraTitle_HIxYn level-1_ogcKG")
    except Exception as e:
        logger.error(f"查找一级标题时出错: {str(e)}")
        result["错误信息"].append(f"标题查找错误: {str(e)}")
    
    extracted_text = ""
    
    # 首先检查是否有传承人物这个二级标题
    heritage_people_section = extract_heritage_people_section(soup)
    
    # 查找"历史渊源"标题
    history_title = None
    for h1 in h1_elements:
        h2 = h1.find('h2')
        if h2 and "历史渊源" in h2.get_text():
            history_title = h1
            break
    
    if history_title:
        # 添加历史渊源标题
        h2_text = history_title.find('h2').get_text()
        # extracted_text += f"# {h2_text}\n\n"
        
        # 获取历史渊源标题之后的所有元素，直到下一个一级标题
        current_element = history_title.next_sibling
        while current_element:
            # 如果遇到另一个一级标题，则停止提取
            if current_element.name == 'div' and 'paraTitle_HIxYn' in current_element.get('class', []) and 'level-1_ogcKG' in current_element.get('class', []):
                break
            
            # 处理当前元素
            extracted_text += process_element(current_element)
            current_element = current_element.next_sibling
    else:
        # 如果没有找到历史渊源标题，使用原有逻辑
        if len(h1_elements) >= 2:
            first_h1 = h1_elements[0]
            second_h1 = h1_elements[1]
            
            h2_text = first_h1.find('h2').get_text() if first_h1.find('h2') else ""
            # extracted_text += f"# {h2_text}\n\n"
            
            current_element = first_h1.next_sibling
            while current_element and current_element != second_h1:
                extracted_text += process_element(current_element)
                current_element = current_element.next_sibling
        else:
            if len(h1_elements) == 1:
                first_h1 = h1_elements[0]
                h2_text = first_h1.find('h2').get_text() if first_h1.find('h2') else ""
                extracted_text += f"# {h2_text}\n\n"
            
            para_elements = soup.find_all('div', class_="para_wIHuD content_BCpkO MARK_MODULE")
            for element in para_elements:
                extracted_text += process_element(element)

    result["历史渊源"] = remove_references(extracted_text)

    # 如果找到了传承人物章节，附加到提取的内容后面
    if heritage_people_section:
        if extracted_text:
            # extracted_text += "\n\n"
            result["传承人物"] = remove_references(heritage_people_section)
        # extracted_text += heritage_people_section
    
    # 清理HTML实体
    # extracted_text = html.unescape(extracted_text)
    
    # return extracted_text.strip()
    return result

def extract_heritage_people_section(soup):
    """
    从网页中提取"传承人物"部分的内容
    """
    # 方案1: 首先尝试通过标题查找
    heritage_content = extract_by_title(soup)
    if heritage_content:
        return heritage_content
    
    # 方案2: 通过段落内容查找
    return extract_by_paragraph(soup)

def extract_by_title(soup):
    """通过标题查找传承人物部分"""
    # 首先检查目录中是否有传承人物这个条目
    has_heritage_people = False
    catalog = soup.find(class_="catalogWrapper_p_9NE")
    
    if catalog:
        catalog_links = catalog.find_all("a")
        for link in catalog_links:
            if "传承人物" in link.get_text() or "传承人" in link.get_text():
                has_heritage_people = True
                break
    
    if not has_heritage_people:
        # 直接尝试查找传承人物标题
        heritage_title = soup.find(lambda tag: tag.name == 'div' and 
                                  'paraTitle_HIxYn' in tag.get('class', []) and
                                  ('传承人物' in tag.get_text() or '传承人' in tag.get_text()))
        if not heritage_title:
            return ""
    
    # 查找传承人物的标题
    heritage_title = soup.find(lambda tag: tag.name == 'div' and 
                              'paraTitle_HIxYn' in tag.get('class', []) and
                              tag.get('class', []).count('level-2_uo4pB') > 0 and
                              ('传承人物' in tag.get_text() or '传承人' in tag.get_text()))
    
    if not heritage_title:
        return ""
    
    # 获取标题文本
    title_text = heritage_title.find('h3').get_text() if heritage_title.find('h3') else "传承人物"
    
    # 开始提取内容
    heritage_content = ""
    
    # 获取传承人物标题之后的段落
    current_element = heritage_title.next_sibling
    
    while current_element:
        # 如果遇到另一个标题，则停止提取
        if current_element.name == 'div' and 'paraTitle_HIxYn' in current_element.get('class', []):
            break
        
        # 如果是段落，则提取内容
        if current_element.name == 'div' and 'para_wIHuD' in current_element.get('class', []):
            heritage_content += process_element(current_element)
        
        current_element = current_element.next_sibling
    
    return heritage_content

def extract_by_paragraph(soup):
    """通过段落内容查找传承人物部分"""
    heritage_content = ""
    
    # 查找所有段落
    heritage_paras = soup.find_all('div', class_="para_wIHuD content_BCpkO MARK_MODULE")
    
    for para in heritage_paras:
        # 检查是否是"传承人物"标题段落（包含bold样式且文本匹配）
        bold_text = para.find('span', class_="bold_AfpN_")
        if bold_text and ("传承人物" in bold_text.get_text() or "传承人" in bold_text.get_text()):
            # 找到起始段落
            # heritage_content += process_element(para)
            
            # 继续查找后续段落，直到遇到字数<=4的段落或下一个bold标题
            next_element = para.next_sibling
            while next_element:
                if next_element.name == 'div' and 'para_wIHuD' in next_element.get('class', []):
                    # 检查是否是新的bold标题段落
                    next_bold = next_element.find('span', class_="bold_AfpN_")
                    if next_bold:
                        break
                    
                    next_text = next_element.get_text().strip()
                    if len(next_text) <= 4:  # 字数<=4视为结束标志
                        break
                    heritage_content += process_element(next_element)
                next_element = next_element.next_sibling
            break
    
    return heritage_content

def process_element(element):
    """处理单个HTML元素并返回格式化的文本"""
    result = ""
    
    # 处理二级标题
    if element.name == 'div' and 'paraTitle_HIxYn level-2_uo4pB' in element.get('class', []):
        h3_text = element.find('h3').get_text() if element.find('h3') else ""
        result += f"## {h3_text}\n\n"
    
    # 处理段落
    elif element.name == 'div' and 'para_wIHuD' in element.get('class', []):
        para_text = ""
        # 提取段落中的所有文本
        for span in element.find_all(class_="text_XlFoe"):
            para_text += span.get_text()
        
        # 添加脚注引用
        sup_tags = element.find_all('sup')
        for sup in sup_tags:
            # 避免重复添加已经在文本中的脚注
            if sup.get_text().strip() not in para_text:
                para_text += f" [{sup.get_text().strip()}]"
        
        if para_text.strip():
            result += f"{para_text}\n\n"
    
    # 处理图片
    elif element.find('img'):
        img = element.find('img')
        img_url = img.get('src', '')
        alt_text = img.get('alt', '图片')
        result += f"![{alt_text}]({img_url})\n\n"
    
    return result

def process_ich_csv(input_file='非遗项目_web.csv', output_file='非遗项目_百科数据补充.csv'):
    try:
        # 读取已存在的输出文件（如果有）
        processed_data = {}
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8-sig') as outfile:
                reader = csv.DictReader(outfile)
                for row in reader:
                    project_name = row.get('项目名称', '').strip()
                    if project_name:
                        processed_data[project_name] = row

        with open(input_file, 'r', encoding='utf-8-sig') as infile, \
             open(output_file, 'w', encoding='utf-8-sig', newline='') as outfile:
            
            reader = csv.DictReader(infile)
            input_rows = list(reader)
            total_count = len(input_rows)

            fieldnames = reader.fieldnames + ["相关介绍", "历史渊源", "传承人物", "爬取状态"]
            
            writer = csv.DictWriter(
                outfile, fieldnames=fieldnames, 
                quoting=csv.QUOTE_ALL,
                escapechar="\\"
            )
            writer.writeheader()
            
            cnt = 0 # 记录新爬取的数据量
            for idx, row in enumerate(input_rows):
                project_name = row.get('项目名称', '').strip()
                if not project_name:
                    continue
                
                # 检查是否已处理且成功
                existing_row = processed_data.get(project_name)
                if existing_row is not None and existing_row.get('爬取状态') == '成功':
                    # 直接使用已存在的数据
                    new_row = existing_row
                    print(f"跳过已处理项目: {project_name}")
                else:
                    # 处理新条目或失败条目
                    url = f'https://baike.baidu.com/item/{project_name}'
                    try:
                        logger.info(f"正在爬取 {project_name} 的百科信息 {idx+1}/{total_count}")
                        result = extract_content_from_html(url=url)
                    except Exception as e:
                        logger.error(f"爬取 {project_name} 失败: {str(e)}")
                        result = {"相关介绍": "", "历史渊源": "", "传承人物": "", "错误信息": str(e)}

                    # 合并数据
                    new_row = {
                        **row,  # 保留原始数据
                        "相关介绍": result.get("相关介绍", ""),
                        "历史渊源": result.get("历史渊源", ""),
                        "传承人物": result.get("传承人物", ""),
                        "爬取状态": "成功" if not result.get("错误信息") else "失败",
                    }
                    cnt += 1
                    time.sleep(random.uniform(4, 8)) # 每爬 1 条暂停一会，防止被检测
                
                writer.writerow(new_row)

                if cnt % 50 == 0 and cnt > 0:
                    time.sleep(random.uniform(60, 300))
                
    except Exception as e:
        logger.error(f"CSV处理失败: {str(e)}")

# 在原有函数后新增以下函数
def process_local_html_to_csv(web_csv='非遗项目_web.csv', output_csv='百度百科.csv', html_dir='baidu_html_files'):
    """处理本地HTML文件并生成带状态的新CSV"""
    try:
        with open(web_csv, 'r', encoding='utf-8-sig') as infile, \
             open(output_csv, 'w', encoding='utf-8-sig', newline='') as outfile:

            reader = csv.DictReader(infile)
            all_rows = list(reader)
            total_count = len(all_rows)

            writer = csv.DictWriter(
                outfile,
                fieldnames=['项目名称', '相关介绍', '历史渊源', '传承人物', 'status'],
                extrasaction='ignore'  # 忽略原始CSV中的其他列
            )
            writer.writeheader()

            # for idx, row in enumerate(reader, 1):
            for idx, row in enumerate(all_rows):

                project_name = row.get('项目名称', '').strip()
                if project_name == "斯":
                    project_name = "格萨（斯）尔"
                if not project_name:
                    continue
                # 生成HTML文件名
                html_path = os.path.join(html_dir, f"{project_name}.html")
                if not os.path.exists(html_path):
                    logger.warning(f"HTML文件不存在: {html_path}")
                    writer.writerow({
                        '项目名称': project_name,
                        '相关介绍': '',
                        '历史渊源': '',
                        '传承人物': '',
                        'status': 'Failed'
                    })
                    continue
                
                result = {}
                status = 'Success'
                
                try:
                    logger.info(f"正在解析 {project_name} ({idx}/{total_count})")
                    result = extract_content_from_html(html_content=html_path)
                    
                    # 只有全部为空时状态才为失败
                    if not result.get("相关介绍") and not result.get("历史渊源") and not result.get("传承人物"):
                        status = 'Failed'
                        
                except Exception as e:
                    logger.error(f"解析失败: {project_name} - {str(e)}")
                    status = 'Failed'
                    result = {
                        "相关介绍": "",
                        "历史渊源": "",
                        "传承人物": "",
                        "错误信息": str(e)
                    }

                # 写入结果
                writer.writerow({
                    '项目名称': project_name,
                    '相关介绍': result.get('相关介绍', ''),
                    '历史渊源': result.get('历史渊源', ''),
                    '传承人物': result.get('传承人物', ''),
                    'status': status
                })

    except Exception as e:
        logger.error(f"CSV处理失败: {str(e)}")

def main():
    process_local_html_to_csv()

if __name__ == "__main__":
    main()
import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
import os
import time
import random

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_inheritors_info(html_content):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 提取项目名称
        project_name, related_articles = "", []
        h30 = soup.find('div', class_='h30')
        if h30:
            project_name = h30.text.strip()

        # 提取官网描述
        description = extract_description_text(html_content)

        # 提取相关咨询文章
        related_articles = extract_related_articles(html_content, project_name)

        # 检查是否存在相关传承人部分
        inheritors_section = None
        
        # 找到"相关传承人"标题所在的div
        title_divs = soup.find_all('div', class_='h24')
        for div in title_divs:
            if '相关传承人' in div.text:
                # 找到标题后，定位到最近的x-tables
                inheritors_section = div.find_parent('div', class_='tit').find_next_sibling('div', class_='x-tables')
                break
        
        # 如果没有找到相关传承人部分，返回空列表
        if not inheritors_section:
            logger.info("未找到相关传承人信息")
            return {
            'web_description': description,
            'inheritors': [],
            'related_articles': related_articles
        }
        
        # 提取表格中的所有行（跳过表头）
        rows = inheritors_section.find_all('tr')[1:] if inheritors_section.find_all('tr') else []
        
        # 如果没有找到行数据，返回空列表
        if not rows:
            logger.info("相关传承人表格为空")
            return {
            'web_description': description,
            'inheritors': [],
            'related_articles': related_articles
        }
        
        inheritors_list = []  # 用于存储所有传承人信息

        for row in rows:
            cells = row.find_all('td')
            
            # 如果行数据不完整，跳过该行
            if len(cells) < 5:
                logger.warning(f"行数据不完整: {row}")
                continue
                
            # 提取名称（从a标签中提取）
            name_cell = cells[1]
            name_a = name_cell.find('a')
            name_a = cells[1].find('a')
            inheritors_list.append({
                'name': name_a.text.strip() if name_a else "",
                'gender': cells[2].text.replace('性别', '').strip(),
                'birth_date': cells[3].text.replace('出生日期', '').strip(),
                'ethnicity': cells[4].text.replace('民族', '').strip()
            })
        
        # 返回包含描述和传承人列表的字典
        return {
            'web_description': description,
            'inheritors': inheritors_list,
            'related_articles': related_articles
        }
    
    except Exception as e:
        logger.error(f"提取传承人信息时发生错误: {str(e)}")
        return []

def extract_related_articles(html_content, project_name):
    """提取包含项目名称的相关咨询文章"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        list_mod2 = soup.find('div', class_='list-mod2')
        if not list_mod2:
            return []
        
        related_articles = []
        for link in list_mod2.find_all('a', class_='list-link'):
            p_tag = link.find('div', class_='p')
            if p_tag and project_name in p_tag.text:
                article_url = 'https://www.ihchina.cn' + link['href']
                content = scrape_article(article_url)
                related_articles.append({
                    'title': p_tag.text.strip(),
                    'content': content
                })
        return related_articles
    
    except Exception as e:
        logger.error(f"提取相关链接时发生错误: {str(e)}")
        return []

def extract_description_text(html_content):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        inherit_div = soup.find('div', class_='inherit_xx1 article-mod2')
        if not inherit_div:
            logger.info("未找到inherit_xx1 article-mod2")
            return ""
            
        # 查找最终的text div
        text_div = inherit_div.find('div', class_='text')
        if not text_div:
            logger.info("未找到描述文本")
            return ""

        # 找到所有p标签
        p_tags = text_div.find_all('div', class_='p')
        if not p_tags:
            logger.info("未找到描述段落")
            return ""
        
        # 获取第一个p标签的文本
        first_p_text = p_tags[0].text.strip() if p_tags else ""
        
        # 检查第一行是否包含"申报地区或单位："
        if first_p_text.startswith("申报地区或单位："):
            # 提取第一个p标签的所有文本，但保留换行符
            text_content = first_p_text
            
            # 将文本按<br>标签分割
            lines = text_content.split('\n')
            
             # 处理每一行：删除\u3000并去除首尾空格
            cleaned_lines = [line.replace('\u3000', '').strip() for line in lines[2:]]

            # 过滤掉空行后合并
            result_text = '\n'.join(line for line in cleaned_lines if line)
        else:
            # 如果第一行不是"申报地区或单位："，则保留所有文本
            result_text = '\n'.join([p.text.replace('\u3000', '').strip() for p in p_tags])
        
        return result_text
    
    except Exception as e:
        logger.error(f"提取描述文本时发生错误: {str(e)}")
        return ""
    
def extract_article_content(html_content):
    """提取文章主体内容"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        article_div = soup.find('div', class_='article-cont')
        if not article_div:
            return ""
        
        # 提取所有段落文本
        paragraphs = []
        for p in article_div.find_all('p'):
            # 跳过空段落和图片说明
            text = p.get_text(strip=True)
            if text and not text.endswith(')'):  # 跳过图片说明
                paragraphs.append(text)
        
        # 合并段落并用换行符分隔
        return '\n'.join(paragraphs)
    
    except Exception as e:
        logger.error(f"提取文章内容时发生错误: {str(e)}")
        return ""

def scrape_article(url):
    """爬取文章内容"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=100)
        response.raise_for_status()
        
        # 处理编码问题
        if response.encoding == 'ISO-8859-1':
            for encoding in ['utf-8', 'gb2312', 'gbk']:
                try:
                    response.encoding = encoding
                    response.text
                    break
                except UnicodeDecodeError:
                    continue
        
        return extract_article_content(response.text)
    
    except Exception as e:
        logger.error(f"爬取文章时发生错误: {str(e)}")
        return ""

def scrape_url(url):
    REQUEST_CONFIG = {
        'base_delay': 3,
        'random_delay': 2,
        'max_retries': 5
    }
    for attempt in range(REQUEST_CONFIG["max_retries"]):
        try:
            delay = REQUEST_CONFIG['base_delay'] + random.uniform(0, REQUEST_CONFIG['random_delay'])
            time.sleep(delay)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()  # 如果响应状态码不是200，则抛出异常
            
            # 确保使用正确的编码
            if response.encoding == 'ISO-8859-1':
                possible_encodings = ['utf-8', 'gb2312', 'gbk']
                for encoding in possible_encodings:
                    try:
                        response.encoding = encoding
                        # 测试解码是否正常
                        response.text
                        break
                    except UnicodeDecodeError:
                        continue
            
            inheritors = extract_inheritors_info(response.text)
            
            return inheritors
        
        except requests.exceptions.RequestException as e:
            logger.warning(f"第 {attempt+1} 次尝试失败: {str(e)}")
            if attempt == REQUEST_CONFIG["max_retries"] - 1:
                logger.error(f"URL {url} 重试{REQUEST_CONFIG['max_retries']}次后失败")
                # return {'web_description': "", 'inheritors': [], 'related_articles': []}
                return {  # 确保返回完整数据结构
                    'web_description': "", 
                    'inheritors': [],
                    'related_articles': []
                }
            time.sleep(2 ** attempt)  # 指数退避等待

def save_to_csv(data, output_file='inheritors_info.csv'):
    if not data:
        logger.warning("网页解析错误，没有信息可以保存")
        return

    # 将数据转换为DataFrame
    df = pd.DataFrame([{
        'web_description': data['web_description'],
        'inheritors': str(data['inheritors']),  # 将列表转换为字符串格式
        'related_articles': data['related_articles']
    }])
    
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    logger.info(f"已保存传承人信息到 {output_file}")

def save_enriched_data(original_df, enriched_data, output_folder='enrich_web_items'):
    """将扩展后的数据保存到新文件"""
    try:
        # 合并原始数据和新字段
        merged_df = original_df.copy()
        merged_df['官网描述'] = [d['web_description'] for d in enriched_data]
        merged_df['传承人信息'] = [str(d['inheritors']) for d in enriched_data]
        merged_df['相关文章'] = [d['related_articles'] for d in enriched_data]
        
        # 创建输出目录
        os.makedirs(output_folder, exist_ok=True)
        
        # 保存文件
        output_path = os.path.join(output_folder, os.path.basename(original_df.attrs['source_file']))
        merged_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        logger.info(f"已保存扩展文件: {output_path}")
        return True
    
    except Exception as e:
        logger.error(f"保存扩展数据时出错: {str(e)}")
        return False

# 测试代码
if __name__ == "__main__":
    input_folder = 'raw_data_items'
    output_folder = 'enrich_web_items'
    
    try:
        # 获取所有CSV文件
        csv_files = [f for f in os.listdir(input_folder) if f.endswith('.csv')][3:]

        if not csv_files:
            logger.error(f"{input_folder} 中没有找到CSV文件")
            exit(1)

        # 处理每个文件
        for csv_file in csv_files:
            file_path = os.path.join(input_folder, csv_file)
            logger.info(f"开始处理文件: {csv_file}")
            
            try:
                # 读取原始数据
                df = pd.read_csv(file_path)
                df.attrs['source_file'] = file_path  # 保存源文件路径
                
                if '详情链接' not in df.columns:
                    logger.error(f"{csv_file} 中缺少详情链接列")
                    continue
                
                # 准备存储扩展数据
                enriched_data = []
                total_urls = len(df['详情链接'])
                
                # 处理每个URL
                for index, url in enumerate(df['详情链接'], 1):
                    try:
                        logger.info(f"正在处理 {csv_file} 的URL {index}/{total_urls}")
                        data = scrape_url(url)
                        if data:
                            enriched_data.append(data)
                    except Exception as e:
                        logger.error(f"处理URL失败: {url}，错误: {str(e)}")
                        enriched_data.append({  # 异常时填充空值
                            'web_description': "",
                            'inheritors': [],
                            'related_articles': []
                        })
                        continue
                        
                # 保存扩展数据
                if save_enriched_data(df, enriched_data, output_folder):
                    logger.info(f"文件处理完成: {csv_file}")
                else:
                    logger.error(f"文件保存失败: {csv_file}")
                    
            except Exception as e:
                logger.error(f"处理文件 {csv_file} 时发生严重错误: {str(e)}")
                continue
            
            # 每个种类处理完后休眠一会，防止过快请求
            time.sleep(random.uniform(120, 180))  # 随机等待2到3分钟
                
        logger.info("所有文件处理完成！")
        
    except Exception as e:
        logger.error(f"程序初始化失败: {str(e)}")
        exit(1)
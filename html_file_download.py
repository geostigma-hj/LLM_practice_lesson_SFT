from selenium import webdriver
import os
import time
import logging
import random 
from fake_useragent import UserAgent
import requests
import urllib3
import csv

# 抑制 InsecureRequestWarning 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

cache_path = "fake_useragent_0.1.11.json"

def download_html_with_selenium(url, save_path):
    """使用Selenium模拟浏览器下载页面"""
    # 伪造请求头
    ua = UserAgent(
        use_cache_server=False,  # 禁用在线获取
        cache=True,  # 启用本地缓存
        path=cache_path  # 指定缓存路径
    )
    option = webdriver.ChromeOptions()
    option.headless = True
    
    # 添加反反爬措施
    option.add_argument("--disable-blink-features=AutomationControlled")
    option.add_experimental_option("excludeSwitches", ["enable-automation"])
    option.add_experimental_option("useAutomationExtension", False)
    # # 使用代理
    # option.add_argument(f"--proxy-server=http://{proxy_ip}")
    
    # 添加用户代理
    option.add_argument(f"user-agent={ua.random}")
    
    driver = webdriver.Chrome(options=option)
    
    try:
        # 执行JavaScript代码隐藏自动化特征
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                  get: () => undefined
                })
            """
        })
        
        driver.get(url)
        # 随机等待时间更自然
        time.sleep(random.uniform(2, 5))
        
        # 模拟人类滚动行为
        for _ in range(3):
            driver.execute_script("window.scrollBy(0, window.innerHeight/2)")
            time.sleep(random.uniform(0.5, 1.5))
            
        html_content = driver.page_source
        
        # 保存到文件
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        return True
    except Exception as e:
        logger.error(f"Selenium下载失败: {str(e)}")
        return False
    finally:
        driver.quit()

def batch_download_from_csv(csv_file, output_dir):
    """从CSV文件批量下载HTML页面"""
    if not os.path.exists(csv_file):
        logger.error(f"CSV文件不存在: {csv_file}")
        return False
    
    try:
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):

                project_name = row.get('项目名称', '').strip()
                if not project_name:
                    continue
                
                save_path = os.path.join(output_dir, f"{project_name}.html")
                
                # 如果文件已存在则跳过
                if os.path.exists(save_path):
                    logger.info(f"跳过已下载项目 [{idx+1}]: {project_name}")
                    continue
                
                url = f'https://baike.baidu.com/item/{project_name}'
                logger.info(f"正在下载第 {idx+1} 个文件: {project_name}")
                
                if not download_html_with_selenium(url, save_path):
                    logger.warning(f"下载失败: {project_name}")
                
                time.sleep(random.uniform(2, 5))
                if idx > 0:
                    if idx % 50 == 0:
                        time.sleep(random.uniform(120, 240))
                    elif idx % 100 == 0:
                        time.sleep(random.uniform(240, 360))
                    else:
                        time.sleep(random.uniform(1, 2))
                
        return True
    except Exception as e:
        logger.error(f"批量下载出错: {str(e)}")
        return False

def main():
    # 配置参数
    # target_url = "https://baike.baidu.com/item/仰阿莎"
    # save_path = "html_files/仰阿莎.html"
    
    # download_html_with_selenium(target_url, save_path)

    csv_file = "非遗项目_web.csv"
    output_dir = "html_files"
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 批量下载
    batch_download_from_csv(csv_file, output_dir)

if __name__ == "__main__":
    main()
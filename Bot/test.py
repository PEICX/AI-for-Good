
'''
阅读我提供的内容，并做出以下操作：
第一步，提取文章的元数据
- 标题：
- 作者：
- 标签：（阅读文章内容后给文章打上标签，标签通常是领域、学科或专有名词）
第二步、一句话总结这篇文文章；
第三步，总结文章内容并写成摘要；
第四步，生成文章的关键词作为标签，标签以#开头；
下面是文章内容：
'''
url = "http://mp.weixin.qq.com/s?__biz=MzU2NTg3MjMwMg==&amp;mid=2247487058&amp;idx=1&amp;sn=79e1c599c6c22418697ce8fae1f8c412&amp;chksm=fcb45d93cbc3d4853d7e530ad063b10b2b880f87d332208320d8c6eaad15e2ab22f31dd83beb&amp;mpshare=1&amp;scene=1&amp;srcid=08140zrQAzEsFrzPBVPqHAMD&amp;sharer_shareinfo=ab24e589eb45606220e6e37769f3a122&amp;sharer_shareinfo_first=ab24e589eb45606220e6e37769f3a122#rd"

# from selenium import webdriver
# from selenium.webdriver.edge.service import Service
# from selenium.webdriver.common.by import By
# import time

# # 指定WebDriver的路径
# edge_driver_path = 'C:\\Users\\peichuangxin\\Documents\\msedgedriver.exe'

# # 创建Edge浏览器驱动服务
# service = Service(edge_driver_path)

# # 启动Edge浏览器
# options = webdriver.EdgeOptions()
# driver = webdriver.Edge(service=service, options=options)

# # 访问网页
# driver.get(url)

# # 等待页面加载完成
# wait = WebDriverWait(driver, 10)
# wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, 'body')))

# time.sleep(10)

# # 获取页面上所有可见元素的文本
# all_text = ""
# try:
#     # 尝试获取所有文本节点
#     elements = driver.find_elements(By.XPATH, '//body//*[not(self::script) and not(self::style)]')
#     for element in elements:
#         if element.is_displayed():
#             all_text += element.text + "\n"
# except NoSuchElementException:
#     print("No elements found")

# # 输出所有可见文本
# print(all_text)

# # 关闭浏览器
# driver.quit()


from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Edge
from selenium.webdriver.common.keys import Keys
from PIL import Image



def get_url_text(url):
    # 这里假设Edge浏览器正在运行且DevTools协议是可用的
    edge_browser_instance = "127.0.0.1:9222"
    # 设置Edge的选项以允许连接到正在运行的实例
    edge_options = Options()
    edge_options.debugger_address = edge_browser_instance

    # 创建Edge WebDriver实例并连接到现有实例
    driver = Edge(options=edge_options)

    # 现在你可以在现有的Edge窗口中执行操作了
    driver.get(url)  # 或者在现有窗口中加载新页面

    # 等待页面加载完成
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, 'body')))

    # 获取页面上所有可见元素的文本
    all_text = ""
    all_text = driver.find_element(By.XPATH, '//body').text

    # 打印获取到的文本
    all_text = all_text.replace("\n", "")
    print(all_text)

    # 关闭浏览器
    driver.quit()
    
    return all_text

def get_url_pic(url):
    # 这里假设Edge浏览器正在运行且DevTools协议是可用的
    edge_browser_instance = "127.0.0.1:9222"
    # 设置Edge的选项以允许连接到正在运行的实例
    edge_options = Options()
    edge_options.debugger_address = edge_browser_instance

    # 创建Edge WebDriver实例并连接到现有实例
    driver = Edge(options=edge_options)

    # 现在你可以在现有的Edge窗口中执行操作了
    driver.get(url)  # 或者在现有窗口中加载新页面

    # 等待页面加载完成
    wait = WebDriverWait(driver, 5)
    wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, 'body')))

    # # iPhone 15的视口尺寸
    # VIEWPORT_SIZE = {
    #     "width": 1050,  # iPhone 15的视口宽度
    #     "height": 2000   # iPhone 15的视口高度
    # }
    # # 设置浏览器窗口尺寸
    # driver.set_window_size(VIEWPORT_SIZE["width"], VIEWPORT_SIZE["height"])
    
    driver.save_screenshot('temp.png')
       
    # 关闭浏览器
    driver.quit()
    


url = "https://stock.10jqka.com.cn/fupan/"
print(get_url_pic(url))
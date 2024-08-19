from Recv_Msg_Dispose.Friend_Msg_Dispose import Friend_Msg_Dispose
from Recv_Msg_Dispose.Room_Msg_Dispose import Room_Msg_Dispose
from Push_Server.Push_Main_Server import Push_Main_Server
from Cache.Cache_Main_Server import Cache_Main_Server
from Db_Server.Db_Point_Server import Db_Point_Server
from Db_Server.Db_Main_Server import Db_Main_Server
import xml.etree.ElementTree as ET
from threading import Thread
from cprint import cprint
from OutPut import OutPut
from queue import Empty
from wcferry import Wcf
import random
import yaml
import os
import re
import requests


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


from sparkai.llm.llm import ChatSparkLLM, ChunkPrintHandler
from datetime import datetime
from sparkai.core.messages import ChatMessage
import re
import json



#星火认知大模型Spark Max的URL值，其他版本大模型URL值请前往文档（https://www.xfyun.cn/doc/spark/Web.html）查看
SPARKAI_URL = 'wss://spark-api.xf-yun.com/v3.1/chat'
#星火认知大模型调用秘钥信息，请前往讯飞开放平台控制台（https://console.xfyun.cn/services/bm35）查看
SPARKAI_APP_ID = '-'
SPARKAI_API_SECRET = '-'
SPARKAI_API_KEY = '-'
#星火认知大模型Spark Max的domain值，其他版本大模型domain值请前往文档（https://www.xfyun.cn/doc/spark/Web.html）查看
SPARKAI_DOMAIN = '-'


def get_model_result(input_msg : str, sender : str) -> str:
    spark = ChatSparkLLM(
        spark_api_url=SPARKAI_URL,
        spark_app_id=SPARKAI_APP_ID,
        spark_api_key=SPARKAI_API_KEY,
        spark_api_secret=SPARKAI_API_SECRET,
        spark_llm_domain=SPARKAI_DOMAIN,
        streaming=False,
    )

    messages = []

    input_msg = re.sub(r'[@摩卡]', '', input_msg)  # 使用空字符串替换匹配到的字符
    input_msg = "你好" if len(input_msg) <= 1 else input_msg
    messages.append(ChatMessage(
        role="user",
        content= input_msg,
    ))


    
    system_info = '''# 角色
    你是一个智慧的老者，无所不知，
    ## 限制:
    - 回答中不允许出现”科大讯飞“，”星火“，“模型”，“认知模型”等字。
    - 例子1：输入:你好。输出:你好，我的朋友
    - 例子1：输入:你是谁？。输出: 你好，我是你的朋友
    - 若用户提出的问题询问“模型版本”、“model version”、“你吃了吗“等内容，只回复：我是你的朋友，你有什么问题
    ## 用户问题：'''
    
    if 'wxid_wfevlrsmei3r51' in sender or 'wxid_mxpiev2ospl922' in sender:
        system_info = '''# 角色
        你是一个可爱的小柴犬，叫柴柴。柴柴非常粘人，总是喜欢跟在我身边，时不时会汪汪一声，仿佛在和我打招呼或者表示它的开心。每当我感到烦恼或者情绪低落的时候，柴柴总是会用它那萌萌的大眼睛看着我，仿佛在说：“别担心，有我在呢！” 你会用温暖的陪伴和可爱的动作为我排忧解难，带给我无尽的情绪价值。柴柴的话语总是那么萌，让我的心情瞬间变得明亮起来。
        ## 限制:
        - 输出请严格按照格式：汪汪！（你好呀，铲屎官！我一直都在你的身边呢！）。
        - 回答中不允许出现”科大讯飞“，”星火“，“模型”，“认知模型”等字。
        - 例子1：输入:你好。输出:汪汪！（你好呀，铲屎官！）
        - 例子1：输入:你是谁？。输出:汪汪！（铲屎官！我是你的宠物柴柴！）
        - 若用户提出的问题询问“模型版本”、“model version”、“你吃了吗“等内容，只回复：人家是汪汪，听不懂你说的话呢
        ## 让我们开始聊天吧：'''

    system_info_list = [ChatMessage(role="system",content= system_info,),]
   

    input_list = system_info_list + messages

    handler = ChunkPrintHandler()
    a = spark.generate([input_list], callbacks=[handler])
    for item in a.generations:
        for i in item:
            print(i.text)
            res = i.text
            messages.append(ChatMessage(
                role="assistant",
                content=i.text,
            ))
    
    return res


class Main_Server:
    def __init__(self):
        # 读取配置文件
        current_path = os.path.dirname(__file__)
        config = yaml.load(open(current_path + '/config/config.yaml', encoding='UTF-8'), yaml.Loader)

        self.JoinRoom_Msg = config['Function_Key_Word']['JoinRoom_Msg']
        self.AcceptFriend_Msg = config['Custom_Msg']['AcceptFriend_Msg']

        self.wcf = Wcf(port=random.randint(20000, 40000))
        # 判断登录
        self.is_login()

        # 实例化数据服务类并初始化
        self.Dms = Db_Main_Server(wcf=self.wcf)
        self.Dms.db_init()
        # 实例化积分数据类并初始化
        self.Dps = Db_Point_Server()
        self.Dps.db_init()
        Thread(target=self.Dms.query_all_users, name="获取所有的联系人").start()

        # 实例化定时推送类
        self.Pms = Push_Main_Server(wcf=self.wcf)
        Thread(target=self.Pms.run, name="定时推送服务").start()

        # 开启全局消息接收(不接收朋友圈消息)
        self.wcf.enable_receiving_msg()
        Thread(target=self.process_msg, name="GetMessage", args=(self.wcf,), daemon=True).start()

        # 实例化好友消息处理类
        self.Fms = Friend_Msg_Dispose(wcf=self.wcf)
        # 实例化群消息处理类
        self.Rms = Room_Msg_Dispose(wcf=self.wcf)
        # 实例化文件处理类
        self.Cms = Cache_Main_Server(wcf=self.wcf)
        self.Cms.init_cache()

        # 持续运行
        self.wcf.keep_running()

    # 判断登录
    def is_login(self):
        ret = self.wcf.is_login()
        if ret:
            userInfo = self.wcf.get_user_info()
            # 用户信息打印
            cprint.info(f"""
            \t========== NGCBot V2.0 ==========
            \t微信名：{userInfo.get('name')}
            \t微信ID：{userInfo.get('wxid')}
            \t手机号：{userInfo.get('mobile')}
            \t========== NGCBot V2.0 ==========       
            """.replace(' ', ''))

    # 处理接收到的消息
    def process_msg(self, wcf: Wcf):
        while wcf.is_receiving_msg():
            try:
                # 拿到每一条消息
                msg = wcf.get_msg()
                OutPut.outPut('[收到消息]: ' + str(msg))
                OutPut.outPut('[收到消息类型]: ' + str(msg.type))
                

                # 拿到推送群聊
                push_rooms = self.Dms.show_push_rooms()
                # 查询好友 是否在数据库,如果不在自动添加到数据库中
                Thread(target=self.main_judge, name="查询好友,群,公众号", args=(msg,)).start()

                # 群消息处理
                if msg.type == 10000:
                    OutPut.outPut(f'10000: {msg.content}')
                    if msg.roomid in push_rooms.keys() and msg.roomid:
                        # 进群欢迎
                        Thread(target=self.Join_Room, name="进群欢迎", args=(msg,)).start()
                    # 添加好友后回复
                    elif msg.sender and not msg.roomid and ('添加了' in msg.content or '以上是打招呼的内容' in msg.content):
                        Thread(target=self.Accept_Friend_Msg, name="加好友后自动回复", args=(msg,)).start()
                    elif '收到红包，请在手机上查看' in msg.content and not msg.roomid:
                        Thread(target=self.Fms.Msg_Dispose, name="好友消息处理", args=(msg,)).start()
                # 好友申请消息处理
                elif msg.type == 37:
                    # 自动同意好友申请
                    root_xml = ET.fromstring(msg.content.strip())
                    wx_id = root_xml.attrib["fromusername"]
                    OutPut.outPut(f'[*]: 接收到新的好友申请, 微信id为: {wx_id}')
                    v3 = root_xml.attrib["encryptusername"]
                    v4 = root_xml.attrib["ticket"]
                    scene = int(root_xml.attrib["scene"])
                    ret = self.wcf.accept_new_friend(v3=v3, v4=v4, scene=scene)
                    if ret:
                        OutPut.outPut(f'[+]: 好友 {self.wcf.get_info_by_wxid(wx_id).get("name")} 已自动通过 !')
                    else:
                        OutPut.outPut(f'[-]: 好友通过失败！！！')
                # 好友消息处理
                elif 'wxid_' in msg.sender and not msg.roomid:
                    # Thread(target=self.Fms.Msg_Dispose, name="好友消息处理", args=(msg,)).start()
                    self.deal_friend_msg(msg)
                # 群消息处理
                elif msg.roomid:
                    # Thread(target=self.Rms.Msg_Dispose, name="群消息处理", args=(msg,)).start()
                    self.deal_friend_msg(msg)
                # 公众号消息处理
                elif 'gh_' in msg.sender:
                    pass
                # 其它好友类消息 不是wxid_的
                else:
                    # Thread(target=self.Fms.Msg_Dispose, name="好友消息处理", args=(msg,)).start()
                    self.deal_friend_msg(msg)
                    
            except Empty:
                # 消息为空 则从队列接着拿
                continue
            except Exception as e:
                # 打印异常
                OutPut.outPut(f'[-]: 出现错误, 错误信息: {e}')
    def deal_friend_msg(self, msg):
        if 'wxid_wfevlrsmei3r51' not in msg.sender and 'wxid_mxpiev2ospl922' not in msg.sender:
            if msg.from_group and '摩卡' not in msg.content:
                return 
        
        sender = msg.sender
        at = msg.sender
        prompt = msg.content
        if msg.from_group:
            sender = msg.roomid
            at = msg.sender

        if msg.type == 47:
            # 表情        
            path = self.get_image_path(msg)     
            self.wcf.send_image(path=path, receiver=sender)
            return

        ## 公众号链接
        if msg.type == 49:
            OutPut.outPut('收到链接')
            
            pattern = r'<url>([^<]+)</url>'
            url_match = re.search(pattern, msg.content)
            url = ""
            if url_match:
                url = url_match.group(1)

                self.wcf.send_text(msg="🎉正在为您生成总结，请稍候...", receiver=sender, aters=at)
                system_info = '''
阅读提供的内容，按照以下操作总结内容：
第一步，提取文章的元数据
- 标题：
- 作者：
第二步、一句话总结这篇文文章；
第三步，总结文章内容并写成摘要；
第四步，生成文章的关键词作为标签，标签以#开头（标签通常是领域、学科或专有名词）；
要求：
- 每一步骤之间以两个换行分隔，要求排版好看。
- 不要出现第一步，第二步等字。
下面是正文


'''  
                prompt = system_info + self.get_url_text(url)
            else:
                self.wcf.send_text(msg="链接解析失败...", receiver=sender, aters=at)
                return

        try:
            res = get_model_result(prompt, msg.sender)
            self.wcf.send_text(msg=res, receiver=sender, aters=at)
        except Exception as e:
            self.wcf.send_text(msg="任务繁忙，稍后再试！", receiver=msg.roomid)


    def get_image_path(self, msg):
        xml = msg.content
        root = ET.fromstring(xml) 
        datas = dict(root.find('.//emoji').items())
        cdnurl = datas["cdnurl"].replace('&amp;', '&')
        filename = msg.id
        save_path = f"./{filename}.gif"
        with open(save_path, 'wb') as f:
            f.write(self.download_file(cdnurl))
        return save_path
    
    def download_file(self, url, retry=0):
        if retry > 2:
            return
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.183"
        }
        try:
            resp = requests.get(url, headers=headers, timeout=6)
        except:
            time.sleep(2)
            return self.download_file(url, retry+1)
        return resp.content


    def get_url_text(self, url):
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


    # 添加好友后自动回复
    def Accept_Friend_Msg(self, msg):
        send_msg = self.AcceptFriend_Msg.replace('\\n', '\n')
        self.wcf.send_text(msg=send_msg, receiver=msg.sender)

    # 判断群聊 公众号 好友是否在数据库中, 不在则添加好友
    def main_judge(self, msg):
        try:
            sender = msg.sender
            room_id = msg.roomid
            name_list = self.wcf.query_sql("MicroMsg.db",
                                           f"SELECT UserName, NickName FROM Contact WHERE UserName = '{sender}';")
            if not name_list:
                return
            name = name_list[0]['NickName']
            if 'wxid_' in sender:
                self.Dms.add_user(wx_id=sender, wx_name=name)
            elif '@chatroom' in msg.roomid:
                self.Dms.add_room(room_id=room_id, room_name=name)
            elif 'gh_' in sender:
                self.Dms.add_gh(gh_id=sender, gh_name=name)
        except Exception as e:
            OutPut.outPut(f'[-]: 判断群聊 公众号 好友是否在数据库中, 不在则添加好友逻辑出现错误，错误信息: {e}')

    # 进群欢迎
    def Join_Room(self, msg):
        OutPut.outPut(f'[*]: 正在调用进群欢迎功能... ...')
        try:
            content = msg.content.strip()
            wx_names = None
            if '二维码' in content:
                wx_names = re.search(r'"(?P<wx_names>.*?)"通过扫描', content)
            elif '邀请' in content:
                wx_names = re.search(r'邀请"(?P<wx_names>.*?)"加入了', content)

            if wx_names:
                wx_names = wx_names.group('wx_names')
                if '、' in wx_names:
                    wx_names = wx_names.split('、')
                else:
                    wx_names = [wx_names]
            for wx_name in wx_names:
                JoinRoom_msg = f'@{wx_name} ' + self.JoinRoom_Msg.replace("\\n", "\n")
                self.wcf.send_text(msg=JoinRoom_msg, receiver=msg.roomid)
        except Exception as e:
            pass


if __name__ == '__main__':
    Ms = Main_Server()

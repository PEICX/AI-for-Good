from sparkai.llm.llm import ChatSparkLLM, ChunkPrintHandler
from datetime import datetime
from sparkai.core.messages import ChatMessage

from settings import SPARKAI_URL, SPARKAI_APP_ID, SPARKAI_API_KEY, SPARKAI_API_SECRET, SPARKAI_DOMAIN
from settings import system_info_list, system_info_list_other
from settings import LOG, STOCK_NAME_LIST, MY_JSON_FILE_PATH
import re
import json
from wxauto import WeChat

history_chat = {}
# 股票列表


def get_model_result(sender : str, input_msg : str, is_need_history=True) -> str:
    spark = ChatSparkLLM(
        spark_api_url=SPARKAI_URL,
        spark_app_id=SPARKAI_APP_ID,
        spark_api_key=SPARKAI_API_KEY,
        spark_api_secret=SPARKAI_API_SECRET,
        spark_llm_domain=SPARKAI_DOMAIN,
        streaming=False,
    )

    messages = []
    if is_need_history == True :
        messages = history_chat.get(sender, [])

    messages = messages[2:] if len(messages) > 6 else messages

    input_msg = re.sub(r'[@摩卡]', '', input_msg)  # 使用空字符串替换匹配到的字符
    input_msg = "你好" if len(input_msg) <= 1 else input_msg
    messages.append(ChatMessage(
        role="user",
        content= input_msg,
    ))

    input_list = system_info_list_other + messages if sender != "如风" \
        else system_info_list + messages

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
    
    # 大于50个字不保存，解决总token数目
    if len(res) < 50:
        history_chat[sender] = messages
    return res

def update_json(content):
    my_dict = {}
    try:
        # 读取现有的字典数据
        with open(MY_JSON_FILE_PATH, 'r', encoding='utf-8') as read_file:
            my_dict = json.load(read_file)
    except FileNotFoundError:
        print("The file does not exist.")
    except json.JSONDecodeError:
        print("The file is not a valid JSON.")
    except Exception as e:
        print(f"An error occurred: {e}")
        # 更新字典
    blacklist = my_dict.get("blacklist", [])
    if content in blacklist:
        blacklist.remove(content)
    else :
        blacklist.append(content.strip())
    my_dict["blacklist"] = blacklist

    # 将更新后的字典写回文件
    with open(MY_JSON_FILE_PATH, 'w', encoding='utf-8') as write_file:
        json.dump(my_dict, write_file, indent=4, ensure_ascii=False)  # 添加缩进使输出更易读


import time
def wechat_run():
    MY_WECHAT = WeChat()
    while True:
        if datetime.now().hour < 8 or datetime.now().hour >= 24:
            time.sleep(60)
            continue
        msgs = MY_WECHAT.GetNextNewMessage()
        MY_WECHAT.UiaAPI.Minimize()
    
        for who in msgs:
            print(who)
            # 去除群后面的人数数字
            new_who = re.sub(r'\(\d{1,3}\)$', '', who).strip()
            print("去除人数后的群名：%s", new_who)
            
            for data in msgs.get(who):
                msg_type = data.type
                content = data.content
                sender = data[0]
                one_msg = data[1]
                LOG.info(f"msg_type:{msg_type}, who:{who}, sender:{sender}, one_msg:{one_msg}")
                
                if len(content) < 3:
                    # 长度小于5的文本不回复，比如”嗯嗯“， ”哦哦“。[表情]和[链接]也不回复了
                    continue
            
                # @开头，且不是摩卡，不回复
                if content.startswith('@'):
                    if '摩卡' in content:
                        pass
                    else :
                        continue
                    
                if content.strip() in STOCK_NAME_LIST:
                    # 将字典写入文件
                   update_json(content.strip())
                   continue

                if msg_type == 'sys':
                    if "加入了群聊" in content:
                        prefix = '当有一个新成员入群时，会收到一个通知：【系统消息】"如风"邀请"a5y0"加入了群聊。\n当收到入群通知时，请根据系统消息提取出用户名字，然后分析用户名字的含义，最后生成一段欢迎语。最好幽默诙谐，发人深省，深度思考。\n请根据下面消息按照上面要求生成欢迎语，输出结果中不要带“欢迎语”等字：'
                        try:
                            result = get_model_result(who, prefix + content + "\n", False)
                            MY_WECHAT.SendMsg(result, new_who, at=[sender])
                            MY_WECHAT.UiaAPI.Minimize()
                            
                        except Exception as e:
                            LOG.error(e)
                            try:
                                MY_WECHAT.SendMsg(prefix + "旺旺！(主人, 出错了，换个问题再问)", new_who, at=[sender])
                                MY_WECHAT.UiaAPI.Minimize()
                            except Exception as e:
                                LOG.error(e) 
                elif msg_type == 'friend':
                    try:
                        result = get_model_result(sender, content)
                        MY_WECHAT.SendMsg(result, new_who, at=[sender])
                        MY_WECHAT.UiaAPI.Minimize()
                    except Exception as e:
                        LOG.error(e)
                        try:
                            MY_WECHAT.SendMsg("旺旺！(主人, 出错了，换个问题再问)", new_who, at=[sender])
                            MY_WECHAT.UiaAPI.Minimize()
                        except Exception as e:
                            LOG.error(e) 
        time.sleep(3)
                
if __name__ == "__main__":
    wechat_run()

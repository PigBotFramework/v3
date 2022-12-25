import re, hashlib, pymysql, yaml, traceback, time, random, requests, sys, hmac, os, json, math, datetime, pytz, urllib, threading
from urllib.request import urlopen
from io import BytesIO
from PIL import Image, ImageFont, ImageDraw, ImageFilter
import matplotlib.pyplot as plt
from apscheduler.schedulers.blocking import BlockingScheduler
from googletrans import Translator as googleTranslator
from imageutils.build_image import BuildImage, Text2Image
from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer as ChatterBotListTrainer
googleTranslatorIns = googleTranslator()
# 打开yaml文件
fs = open("data.yaml",encoding="UTF-8")
yamldata = yaml.load(fs,Loader=yaml.FullLoader)
requests.adapters.DEFAULT_RETRIES = 5
headers = {
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36'
}

from apscheduler.schedulers.background import BackgroundScheduler
scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
commandListener = []
commandPluginsList = {}
messagelist = []
commandlist = []
messageListenerList = []
metaEventListenerList = []
requestListenerList = []
noticeListenerList = []
pluginsList = []
ChatterBot = None
ListTrainer = None
# importFlag = True

def varsInit(commandPluginsListVar, commandlistVar, messageListenerListVar, metaEventListenerListVar, requestListenerListVar, noticeListenerListVar, pluginsListVar, ChatterBotListenerVar, pluginsLDataVar, port, flag):
    global commandPluginsList, commandlist, messageListenerList, metaEventListenerList, requestListenerList, noticeListenerList, pluginsList, ChatterBotListener, ChatterBot, ListTrainer, scheduler, importFlag
    commandPluginsList = commandPluginsListVar
    commandlist = commandlistVar
    messageListenerList = messageListenerListVar
    metaEventListenerList = metaEventListenerListVar
    requestListenerList = requestListenerListVar
    noticeListenerList = noticeListenerListVar
    pluginsList = pluginsListVar
    ChatterBotListener = ChatterBotListenerVar
    ChatterBot = ChatBot(
        "小猪比机器人",
        storage_adapter='chatterbot.storage.SQLStorageAdapter',
        database_uri='sqlite:///chatterbot_addons/db.sqlite3',
        logic_adapters=[
            {'import_path': 'chatterbot_addons.adapter.MyLogicAdapter'},
            {"import_path": "chatterbot.logic.BestMatch"}
        ],
        listener = ChatterBotListenerVar,
        botIns = bot()
    )
    ListTrainer = ChatterBotListTrainer(ChatterBot)
    
    if flag and int(port)==1000:
        bot().CrashReport("import", "varsInit")
        for i in pluginsLDataVar:
            if i.get("init", False):
                bot().execPlugin(i.get("init"))
            for l in i.get("require", []):
                exec("from plugins.{}.main import {}".format(i.get("cwd"), l))
        
        try:
            scheduler.start()
        except Exception:
            pass
    
        importFlag = False

class bot:
    args = None
    messageType = 'qn'
    botSettings = None
    userCoin = None
    userInfo = None
    pluginsList = []
    port = 0
    se = {}
    message = None
    ocrImage = None
    isGlobalBanned = None
    uuid = None
    runningProgram = "BOT"
    groupSettings = None
    
    sql_config = "SELECT * FROM `botSettings` WHERE `uuid` = %s and {}"
    sql_coinlist = "SELECT * FROM `botCoin` WHERE `uuid` = %s and {}"
    sql_quanjing = "SELECT * FROM `botQuanping` WHERE {}"
    sql_keywordListSql = "SELECT * FROM `botKeyword` WHERE `uuid` = %s and `state`=0"
    
    weijin = None
    rclOb = None
    kwrlist = None
    settingName = None
    commandmode = []
    ChatterBot = None
    ListTrainer = None
    
    def __init__(self):
        pass
    
    def WriteCommandListener(self, func=None, args=None, step=1, sendTime=time.time()):
        global commandListener
        num = self.findObject("uid", self.se.get('user_id'), commandListener).get('num')
        if num == -1:
            if step == None:
                step = 1
            commandListener.append({
                "func": func,
                "step": step,
                "args": args,
                "time": sendTime,
                "uid": self.se.get('user_id'),
                "gid": self.se.get('group_id')
            })
        else:
            if func != None:
                commandListener[num]['func'] = func
            if args != None:
                commandListener[num]['args'] = args
            if step != None and step != 1 and step != '1':
                commandListener[num]['step'] = step
            else:
                commandListener[num]['step'] = int(commandListener[num]['step']) + 1
            commandListener[num]['time'] = sendTime
        
    def ReadCommandListener(self):
        if self.rclOb == None:
            return self.findObject("uid", self.se.get('user_id'), commandListener).get('object')
        else:
            return self.rclOb
        
    def RemoveCommandListener(self):
        global commandListener
        
        num = self.findObject("uid", self.se.get('user_id'), commandListener).get('num')
        if num == -1:
            return False
        else:
            commandListener.pop(num)
            return True
    
    def requestInit(self, se, uuid, port):
        self.port = port
        self.se = se
        self.message = se.get('message')
        try:
            if se.get('meta_event_type') == 'heartbeat':
                print('忽略心跳事件')
                return None
            
            # 不处理其他机器人的消息
            if se.get('user_id') and se.get("message_type") == "group":
                if self.selectx('SELECT * FROM `botBotconfig` WHERE `myselfqn`=%s', (se.get('user_id'))):
                    return None
            #入站第二步：初始化各项
            self.weijin = self.selectx("SELECT * FROM `botWeijin` WHERE `state`=0 or `state`=3;")
            self.kwrlist = self.selectx("SELECT * FROM `botReplace`")
            self.settingName = self.selectx("SELECT * FROM `botSettingName`")
            
            self.args = se.get("message").split() if se.get('message') else None # 初始化参数
            self.messageType = 'cid' if se.get('channel_id') else 'qn' # 消息来源（频道或群组）
            self.botSettings = self.selectx('SELECT * FROM `botBotconfig` WHERE `uuid`=%s;', (uuid)) # 机器人实例设置
            self.groupSettings = self.GetConfig(uuid, self.messageType, se.get('group_id'), self.sql_config) if se.get('group_id') else None # 加载群聊设置
            if se.get('user_id'):
                self.userCoin = self.GetConfig(uuid, self.messageType, se.get('user_id'), self.sql_coinlist) # 初始化好感度
            if self.userCoin != None:
                try:
                    self.userInfo = self.userCoin[0]
                    self.userCoin = self.userInfo.get('value')
                    if not self.userCoin:
                        self.userCoin = -1
                except Exception as e:
                    self.userInfo = self.userCoin
                    self.userCoin = self.userInfo.get('value')
            else:
                self.userCoin = -1
                self.userInfo = None
            
            self.pluginsList = self.selectx('SELECT * FROM `botPlugins` WHERE `uuid` = %s', (uuid)) # 插件列表
            if se.get('user_id'):
                self.isGlobalBanned = self.GetConfig(None, self.messageType, se.get('user_id'), self.sql_quanjing) if self.messageType != 'cid' else None
            self.uuid = uuid
            
            if self.groupSettings:
                try:
                    self.groupSettings = self.groupSettings[0]
                except Exception as e:
                    pass
            
            if self.botSettings:
                try:
                    self.botSettings = self.botSettings[0]
                except Exception as e:
                    pass
            
            if not self.groupSettings: # 初始化群聊设置
                if se.get("group_id"):
                    print(self.se.get("user_id"), se.get("group_id"))
                    self.GroupInit()
                    return None
            
            print(self.groupSettings)
            print(self.botSettings)
            
            self.SessionStart()
        except Exception as e: # 出错了
            msg = '在处理群：{0} 用户：{1} 的消息时出现异常！\n{2}\n'.format(se.get('group_id'), se.get('user_id'), traceback.format_exc())
            self.CrashReport(msg)
    
    def GetPswd(self, uuid):
        if not uuid:
            return 'Please give a non-empty string as a uuid.'
        botOb = self.selectx('SELECT * FROM `botBotconfig` WHERE `uuid`=%s;', (uuid))
        if not botOb:
            return 'Cannot find the right secret. Is the uuid right?'
        else:
            return botOb[0].get('secret')
            
    def GetConfig(self, uuid, key, value, template, sql=None):
        if sql == None:
            sql = '`{0}`=%s'.format(key)
            template = template.format(sql)
            if uuid:
                ob = self.selectx(template, (uuid, value))
            else:
                ob = self.selectx(template, (value))
        else:
            template = template.format(sql)
            if uuid:
                ob = self.selectx(template, (uuid))
            else:
                ob = self.selectx(template)
        
        return None if not ob else ob
    
    def encryption(self, data, secret):
        key = secret.encode('utf-8')
        obj = hmac.new(key, msg=data, digestmod='sha1')
        return obj.hexdigest()
        
    def selectx(self, sqlstr, params=(), host=yamldata.get('database').get('dbhost'), user=yamldata.get('database').get('dbuser'), password=yamldata.get('database').get('dbpassword'), database=yamldata.get('database').get('dbname')):
        conn = pymysql.connect(host=host, user=user, password=password, database=database)
        cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
        try:
            row = cursor.execute(sqlstr, params)
        except Exception as e:
            self.CrashReport("selectx execute error\nsql: {}\nparams: {}\nerror: {}".format(sqlstr, params, e), "selectx", level="WARNING")
            raise Exception(e)
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return result
    
    def commonx(self, sqlstr, params=(), host=yamldata.get('database').get('dbhost'), user=yamldata.get('database').get('dbuser'), password=yamldata.get('database').get('dbpassword'), database=yamldata.get('database').get('dbname')):
        connect = pymysql.connect(host=host, user=user, password=password, database=database)
        cursor = connect.cursor(cursor=pymysql.cursors.DictCursor)
        try:
            rows = cursor.execute(sqlstr, params)
        except Exception as e:
            self.CrashReport("commonx execute error\nsql: {}\nparams: {}\nerror: {}".format(sqlstr, params, e), "commonx", level="WARNING")
            raise Exception(e)
        connect.commit()
        cursor.close()
        connect.close()
        
    def sendRawMessage(self, content):
        if self.se.get('group_id') == None:
            data = self.CallApi('send_msg', {'user_id':self.se.get('user_id'),'message':content})
        else:
            data = self.CallApi('send_msg', {'group_id':self.se.get('group_id'),'message':content})
        return data
    
    def sendChannel(self, content):
        data = self.CallApi('send_guild_channel_msg', {'guild_id':self.se.get('guild_id'),'channel_id':self.se.get('channel_id'),'message':content})
        return data

    def sendInsertStr(self, content):
        sendStr = 'abcdefghijklmnopqrstuvwxyz'
        if '[CQ:' not in content:
            for i in range(math.floor(len(content)/15)):
                pos = random.randint(0, len(content))
                content = content[:pos] + sendStr[random.randint(0, 25)] + content[pos:]
        return content

    def send(self, content, coinFlag=True, insertStrFlag=False, retryFlag=True, translateFlag=True):
        uid = self.se.get("user_id")
        gid = self.se.get("group_id")
        uuid = self.uuid
        botSettings = self.botSettings
        groupSettings = self.groupSettings
        content = str(content)
        
        # 随机好感度
        try:
            if random.randint(1, botSettings.get('coinPercent')) == 1 and coinFlag:
                userCoin = self.addCoin()
                if userCoin != False:
                    content += '\n\n『谢谢陪我聊天，好感度加{0}』'.format(userCoin)
        except Exception:
            pass
        
        # 插入字符和翻译
        try:
            if groupSettings.get('translateLang') != "zh-cn" or insertStrFlag == True:
                if "[" in content and "]" in content:
                    content = content.replace("\n", "[\n]").replace("face54", "[face54]")
                    newcon = ""
                    for i in content.split("["):
                        if "]" in i:
                            i = i.split("]")
                            newcon += "[{0}]".format(i.pop(0))
                            for l in i:
                                if l:
                                    l = self.translator(l, to_lang=groupSettings.get('translateLang')) if translateFlag and groupSettings.get('translateLang') != "zh-cn" else l
                                    l = self.sendInsertStr(l) if insertStrFlag and groupSettings.get('translateLang') == "zh-cn" else l
                                newcon += str(l)
                        else:
                            if i:
                                i = self.translator(i, to_lang=groupSettings.get('translateLang')) if translateFlag and groupSettings.get('translateLang') != "zh-cn" else i
                                i = self.sendInsertStr(i) if insertStrFlag and groupSettings.get('translateLang') == "zh-cn" else i
                            newcon += str(i)
                    content = newcon
                    content = content.replace("[\n]", "\n").replace("[|", "").replace("|]", "").replace("[face54]", "[CQ:face,id=54]")
                else:
                    content = self.translator(content, to_lang=groupSettings.get('translateLang')) if translateFlag and groupSettings.get('translateLang') != "zh-cn" else content
                    content = self.sendInsertStr(content) if insertStrFlag and groupSettings.get('translateLang') == "zh-cn" else content
            else:
                raise CatchError("Need replace.")
                
        except Exception:
            content = content.replace("[|", "").replace("|]", "").replace("face54", "[CQ:face,id=54]")
        
        # 频道消息
        if self.se.get('channel_id') != None:
            return self.sendChannel(content)
        
        dataa = self.sendRawMessage(content)
        try:
            if dataa.get('status') == 'failed' and self.se.get('post_type') == 'message':
                mid = None
                if retryFlag:
                    self.sendRawMessage('消息发送失败，尝试转图片发送...')
                    self.message = content
                    self.se['user_id'] = botSettings.get('myselfqn')
                    self.se['sender']['nickname'] = botSettings.get('name')
                    return self.sendImage()
            else:
                mid = dataa.get('data').get('message_id')
                return mid
        except Exception:
            pass

    def SendOld(self, uid, content, gid=None, timeout=10):
        # 随机插入字符
        # content = sendInsertStr(content)
        
        if gid == None:
            dataa = self.CallApi('send_msg', {'user_id':uid,'message':content})
        else:
            dataa = self.CallApi('send_msg', {'group_id':gid,'message':content})
        if dataa.get('status') != 'failed':
            mid = dataa.get('data').get('message_id')
        else:
            mid = None
        return mid
        
    def CrashReport(self, message, title='异常报告', level="info", sendFlag=False):
        now = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
        ctime = now.strftime("%Y-%m-%d %H:%M:%S")
        str = "[{}] [{}/{}/{}/{}] [{}] {}\n".format(ctime, self.runningProgram, level, self.uuid, self.port, title, message)
        print(str)
        fileName = now.strftime("./logs/%Y-%m-%d.log")
        f = open(fileName, "a")
        f.write(str)
        f.close()
        if sendFlag:
            self.SendOld(self.botSettings.get('owner'), '[CQ:face,id=189] '+str(title)+'\n'+str(message), self.botSettings.get('CrashReport'))
    
    def CallApi(self, api, parms={}, timeout=10):
        botSettings = self.botSettings
        if not botSettings:
            botSettings = self.selectx('SELECT * FROM `botBotconfig` WHERE `uuid`="{0}";'.format(self.uuid))[0]
            self.botSettings = botSettings
        return requests.post(url='{0}/{1}?access_token={2}'.format(botSettings.get('httpurl'), api, botSettings.get('secret')), json=parms, timeout=timeout).json()
        
    def weijinWhileFunc(self, message):
        for l in self.weijin:
            i = l.get('content')
            if i in message and i != '' and (l.get("qn") == 0 or l.get("qn") == self.se.get("group_id")):
                return i
        return False
    
    def checkWeijin(self, weijinFlag):
        se = self.se
        uid = se.get('user_id')
        gid = se.get('group_id')
        message = self.message
        
        if message == None:
            return False
        
        messageReplace = message.replace(' ','')
        i = self.weijinWhileFunc(messageReplace)
        if i != False:
            if weijinFlag == 1 and gid != None and self.se.get("sender").get("role") == "member":
                self.send('[CQ:face,id=151] [CQ:at,qq={2}] {0}不喜欢您使用（{1}）这种词语哦，请换一种表达方式吧！'.format(self.botSettings.get('name'), i, self.se.get("user_id")))
                self.delCoin()
                self.CallApi('delete_msg', {'message_id':self.se.get('message_id')})
                
            # 如果辱骂机器人则骂回去
            if ('[CQ:at,qq='+str(self.botSettings.get('myselfqn'))+']' in messageReplace) or (self.botSettings.get('name') in messageReplace) or ('猪比' in messageReplace) or ('猪逼' in messageReplace) or ('猪鼻' in messageReplace) or ('机器人' in messageReplace) or (gid == None):
                repeatnum = self.botSettings.get('yiyan')
                while repeatnum > 0:
                    self.delCoin()
                    dataa = requests.get(url=self.botSettings.get('duiapi'))
                    dataa.enconding = "utf-8"
                    if repeatnum == self.botSettings.get('yiyan'):
                        replymsg = '[CQ:reply,id='+str(se.get('message_id'))+'] 你骂我？好啊\n'+str(dataa.text)
                    else:
                        replymsg = dataa.text
                    self.send(replymsg)
                    repeatnum -= 1
        
            # break 
            return True
    
    def GroupInit(self):
        gid = self.se.get('group_id')
        print(gid, "groupinit")
        if gid == None:
            self.CrashReport("cancel", "group_init")
            return 
        self.commonx('INSERT INTO `botSettings` (`qn`, `uuid`, `power`, `connectQQ`) VALUES (%s, %s, %s, %s);', (gid, self.uuid, self.botSettings.get('defaultPower'), self.se.get("user_id")))
        if self.botSettings.get('defaultPower'):
            self.send('[CQ:face,id=189] [|机器人已初始化，发送“菜单”可以查看全部指令|]\n[|发送“群聊设置”可以查看本群的初始设置|]\n[|如果不会使用机器人请发送“新手教程”查看教程！|]')
        else:
            self.send('[CQ:face,id=189] [|机器人已初始化，当前已关机，发送“开机”可以开启机器人|]\n[|开机后，发送“菜单”可以查看指令！|]')
        
    def checkCoin(self):
        for i in self.coinlist:
            if str(self.se.get('user_id')) == str(i.get(self.messageType)):
                return i.get('value')
        return -1

    def addCoin(self, value=None):
        if value == None:
            value=random.randint(self.botSettings.get('lowRandomCoin'), self.botSettings.get('highRandomCoin'))
        
        uid = self.se.get('user_id')
        
        if self.userCoin == -1:
            return 0
        if self.userCoin == False:
            return False
        
        try:
            self.commonx('UPDATE `botCoin` SET `value`=%s WHERE `qn`=%s', (int(self.userCoin)+int(value), uid))
        except Exception as e:
            pass
        return value
    
    def delCoin(self, value=None):
        if value == None:
            value = random.randint(self.botSettings.get('lowRandomCoin'), self.botSettings.get('highRandomCoin'))
        
        uid = self.se.get('user_id')
        
        if self.userCoin == -1:
            return 0
        if self.userCoin == False:
            return False
        
        try:
            self.commonx('UPDATE `botCoin` SET `value`=%s WHERE `qn`=%s', (int(self.userCoin)-int(value), uid))
        except Exception as e:
            pass
        return value

    def getCQValue(self, key, message):
        return self.findObject('key', key, self.getCQArr(message)).get('object').get('value')

    def getCQArr(self, message):
        # message = message.replace('[', '').replace(']', '')
        message1 = message.split('[')
        message2 = message1[1].split(']')
        message = message2[0]
        message = message.split(',')
        arr = []
        for i in message:
            if i == message[0]:
                continue
            message1 = i.split('=')
            arr.append({"key":message1[0], "value":message1[1]})
        return arr

    # 查找键值对并返回对象
    def findObject(self, key, value, ob):
        num = 0
        for i in ob:
            if str(i.get(str(key))) == str(value):
                return {"num":num,"object":i}
            num += 1
        return {"num":-1,"object":404}
    
    # 查找键值对并返回在数组中的下标
    def getNumByObject(self, key, value, ob):
        num = 0
        for i in ob:
            if i.get(str(key)) == value:
                return num
            num += 1
        return -1
    
    def generate_code(self, num):
        '''generate_code方法主要用于生成指定长度的验证码，有一个num函数,需要传递一个int类型的数值,其return返回结果为num'''
        #定义字符串
        str1= "23456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        #循环num次生成num长度的字符串
        code =''
        for i in range(num):
            index = random.randint(0,len(str1)-1)
            code += str1[index]
        return code
    
    def openFile(self, path):
        with open(path, 'r') as f:
            return f.read()
        
    def writeFile(self, path, content):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

    def reply(self):
        def replyFunc():
            try:
                message = str(ChatterBot.get_response(self.message))
                if message != "你是吹牛":
                    if '菲菲' in message:
                        message = message.replace('菲菲', self.botSettings.get("name"))
                    if random.randint(0,5) == 3:
                        if '{face:' in message:
                            message = message.replace('{face:', "表情").replace("}", " ")
                        self.send("[CQ:tts,text={}]".format(message))
                    else:
                        if '{face:' in message:
                            message = message.replace('{face:', "[CQ:face,id=").replace("}", "]")
                        self.send('[CQ:reply,id={}]{}'.format(self.se.get('message_id'), message))
            except Exception as e:
                self.CrashReport(traceback.format_exc(), "reply")
        self.CrashReport("Getting Response", "reply")
        threading.Thread(target=replyFunc).start()
    
    # 注意！本函数需要使用 imageutils
    def sendImage(self):
        userid = self.se.get('user_id')
        name = self.se.get('sender').get('nickname')
        texts = self.message
        
        def load_image(path: str):
            return BuildImage.open("./resources/images/" + path).convert("RGBA")
        
        # 获取头像
        url = "http://q1.qlogo.cn/g?b=qq&nk="+str(userid)+"&s=640"
        image_bytes = urlopen(url).read()
        # internal data file
        data_stream = BytesIO(image_bytes)
        # open as a PIL image object
        #以一个PIL图像对象打开
        img = BuildImage.open(data_stream).convert("RGBA").square().circle().resize((100, 100))
    
        name_img = Text2Image.from_text(name, 25, fill="#868894").to_image()
        name_w, name_h = name_img.size
        if name_w >= 700:
            raise ValueError(NAME_TOO_LONG)
    
        corner1 = load_image("my_friend/corner1.png")
        corner2 = load_image("my_friend/corner2.png")
        corner3 = load_image("my_friend/corner3.png")
        corner4 = load_image("my_friend/corner4.png")
        label = load_image("my_friend/label.png")
    
        def make_dialog(text: str) -> BuildImage:
            text_img = Text2Image.from_text(text, 40).wrap(700).to_image()
            text_w, text_h = text_img.size
            box_w = max(text_w, name_w + 15) + 140
            box_h = max(text_h + 103, 150)
            box = BuildImage.new("RGBA", (box_w, box_h))
            box.paste(corner1, (0, 0))
            box.paste(corner2, (0, box_h - 75))
            box.paste(corner3, (text_w + 70, 0))
            box.paste(corner4, (text_w + 70, box_h - 75))
            box.paste(BuildImage.new("RGBA", (text_w, box_h - 40), "white"), (70, 20))
            box.paste(BuildImage.new("RGBA", (text_w + 88, box_h - 150), "white"), (27, 75))
            box.paste(text_img, (70, 16 + (box_h - 40 - text_h) // 2), alpha=True)
        
            dialog = BuildImage.new("RGBA", (box.width + 130, box.height + 60), "#eaedf4")
            dialog.paste(img, (20, 20), alpha=True)
            dialog.paste(box, (130, 60), alpha=True)
            dialog.paste(label, (160, 25))
            dialog.paste(name_img, (260, 22 + (35 - name_h) // 2), alpha=True)
            return dialog
        dialogs = [make_dialog(texts)]
        frame_w = max((dialog.width for dialog in dialogs))
        frame_h = sum((dialog.height for dialog in dialogs))
        frame = BuildImage.new("RGBA", (frame_w, frame_h), "#eaedf4")
        current_h = 0
        for dialog in dialogs:
            frame.paste(dialog, (0, current_h))
            current_h += dialog.height
        self.sendRawMessage('[CQ:image,file=https://resourcesqqbot.xzy.center/createimg/{0}]'.format(frame.save_jpg()))
    
    def chushihuacd(self):
        for i in commandlist:
            flag = True
            cwd = i.get('eval').split('.')[0]
            if self.findObject('path', cwd, self.pluginsList).get('num') == -1:
                continue
            for l in self.commandmode:
                if i.get("mode") == l.get("name"):
                    if cwd not in l.get("cwd"):
                        l['cwd'].append(cwd)
                    flag = False
            if flag:
                self.commandmode.append({"name": i.get("mode"), "cwd": [cwd]})
    
    def cd3(self, mode):
        uid = self.se.get('user_id')
        gid = self.se.get('group_id')
        
        message = '[CQ:face,id=151]{0}-菜单：[|{1}|]'.format(self.botSettings.get('name'), mode)
        for i in commandlist:
            if i.get('promise') != 'xzy' and i.get('mode') == mode and self.findObject('path', i.get("eval").split(".")[0], self.pluginsList).get('num') != -1:
                if i.get('isHide') == 0:
                    if isinstance(i.get('content'), list):
                        name = i.get("content")[0]
                        for item in i.get("content"):
                            if item != i.get("content")[0]:
                                name += " 或 {}".format(item)
                    else:
                        name = i.get("content")
                    message += '\n[CQ:face,id=54] [|'+str(name)+'|]\n用法：[|'+str(i.get('usage'))+'|]\n解释：'+str(i.get('description'))+'\n权限：'
                    if i.get('promise') == 'admin' or i.get('promise') == 'ao':
                        message += '管理员'
                    elif i.get('promise') == 'owner':
                        message += '我的主人'
                    elif i.get('promise') == 'anyone':
                        message += '任何人'
                    elif i.get('promise') == 'ro':
                        message += '真正的主人'
                elif i.get('isHide') == 2:
                    message += '\n[CQ:face,id=54] [|'+str(i.get('usage'))+'|]'
        message += '\n\n[|解锁更多功能请机器人主人安装其他插件|]\n[ {0} POWERED BY PIGBOTFRAMEWORK ]'.format(self.botSettings.get('name'))
            
        self.send(message)

    def KeywordExcept(self, replyKey, message):
        if ('$1' in replyKey) and ('$2' in replyKey):
            replyKey = replyKey.split('$1')[1]
            replyKey = replyKey.split('$2')[0]
            if ',' in replyKey:
                replyKey = replyKey.split(',')
                for i in replyKey:
                    if i in message:
                        return 1
            elif replyKey in message:
                return 1
        else:
            return 0
    
    def KeywordReplace(self, replyContent):
        uid = self.se.get('user_id')
        gid = self.se.get('group_id')
        se = self.se
        coin = self.userCoin
        
        if coin == -1:
            coin = '用户未注册！'
        for i in self.kwrlist:
            if i.get('key') in replyContent:
                replyContent = replyContent.replace(i.get('key'), str(eval(i.get('value'))))
        return replyContent
    
    def KeywordOr(self, replyKey, message):
        if '|' in replyKey:
            splitKey = replyKey.split('|')
            for sk in splitKey:
                if sk in message:
                    return 1
                elif '&amp;' in sk:
                    if self.KeywordAnd(sk, message):
                        return 1
            return 0
        elif '&amp;' in replyKey:
            return self.KeywordAnd(replyKey, message)
        else:
            return 0
    
    def KeywordAnd(self, replyKey, message):
        if '&amp;' in replyKey:
            msgandflag = 0
            msgand = replyKey.split('&amp;')
            for msgandi in msgand:
                if msgandi not in message:
                    return 0
            return 1
        else:
            return 0
    
    def sendKeyword(self, replyContent):
        uid = self.se.get('user_id')
        gid = self.se.get('group_id')
        se = self.se
        coin = self.userCoin
        
        replyContent = self.KeywordReplace(replyContent)
        if ('|' in replyContent) and ('|]' not in replyContent) and ('[|' not in replyContent):
            replyContentList = replyContent.split('|')
            for rcl in replyContentList:
                self.send(rcl, insertStrFlag=False)
        else:
            self.send(replyContent, insertStrFlag=False)
    
    def translator(self, text, from_lang="zh-cn", to_lang="en"):
        if from_lang == to_lang or not text.lstrip().rstrip():
            return text
        self.CrashReport("from_lang: {0}\tto_lang: {1}\ntext: {2}".format(from_lang, to_lang, text), "translator")
        try:
            return googleTranslatorIns.translate(text, dest=to_lang).text
        except Exception as e:
            self.CrashReport(e, "translator")
            return text
    
    def execPluginThread(self, func):
        return self.execPlugin(func)
        threading.Thread(target=self.execPlugin,args=(func,)).start()
    
    def execPlugin(self, func):
        try:
            exec('from plugins.{0}.main import {0} as {0}'.format(func.split('.')[0]))
            loc = locals()
            exec('{0}Cla = {0}()'.format(func.split('.')[0]))
            for i in dir(self):
                if i[0:2] != '__' and callable(eval('self.'+str(i))) == False:
                    exec('{1}Cla.{0} = self.{0}'.format(i, func.split('.')[0]))
            exec('{0}Cla.runningProgram = "{0}"'.format(func.split('.')[0]))
            exec('resData = {0}Cla.{1}'.format(func.split('.')[0], func.split('.')[1]))
            return loc['resData']
        except Exception as e:
            msg = '在处理群：{0} 用户：{1} 的消息时出现异常！\n{2}\n'.format(self.se.get('group_id'), self.se.get('user_id'), traceback.format_exc())
            self.CrashReport(msg)
        
    def checkPromiseAndRun(self, i, echoFlag=False, senderFlag=False, content=None):
        runFlag = True
        for item in self.pluginsList:
            if item.get("path") == i.get("eval").split(".")[0]:
                runFlag = False
                break
        if runFlag:
            return 
        
        uid = self.se.get('user_id')
        gid = self.se.get('group_id')
        se = self.se
        botSettings = self.botSettings
        evalFunc = i.get('eval')
        content = content if content else i.get("content")
        
        if gid:
            commandCustom = self.selectx('SELECT * FROM `botPromise` WHERE `uuid`=%s and `gid`=%s and `command`=%s', (self.uuid, gid, content.lstrip(' ')))
        else:
            commandCustom = None
        if commandCustom:
            promise = commandCustom[0].get('promise')
        else:
            promise = i.get('promise')
        
        if promise == 'anyone':
            return self.execPluginThread(evalFunc)
        elif promise == 'owner':
            if uid == botSettings.get('owner') or uid == botSettings.get('second_owner'):
                return self.execPluginThread(evalFunc)
            elif echoFlag == True:
                self.send('[CQ:face,id=151] 你不是我的主人，哼ꉂ(ˊᗜˋ*)')
        elif promise == 'ro':
            if uid == botSettings.get('owner'):
                return self.execPluginThread(evalFunc)
            elif echoFlag == True:
                self.send('[CQ:face,id=151] 你不是我真正的主人，哼ꉂ(ˊᗜˋ*)')
        elif promise == 'xzy':
            if uid == yamldata.get('chat').get('owner') and self.uuid == yamldata.get('self').get('defaultUuid'):
                return self.execPluginThread(evalFunc)
            elif echoFlag == True:
                self.send('[CQ:face,id=151] 该指令只有最高管理员可以使用！并且实例必须为官方默认实例')
        
        if senderFlag == True:
            if promise == 'admin':
                if se.get('sender').get('role') != 'member':
                    return self.execPluginThread(evalFunc)
                elif echoFlag == True:
                    self.send('[CQ:face,id=151] 就你？先拿到管理员再说吧！')
            elif promise == 'ao':
                if se.get('sender').get('role') != 'member' or uid == botSettings.get('owner') or uid == botSettings.get('second_owner'):
                    return self.execPluginThread(evalFunc)
                elif echoFlag == True:
                    self.send('[CQ:face,id=151] 就你？先拿到管理员再说吧！')
    
    def keywordPair(self, replyKey, message):
        if self.KeywordExcept(replyKey, message):
            return False
        if ('$1' in replyKey) and ('$2' in replyKey):
            replyKey = replyKey.split('$1')[0] + replyKey.split('$2')[1]
        if self.KeywordOr(replyKey, message) or replyKey in message:
            return True
        return False
    
    def SessionStart(self):
        if self.isGlobalBanned == None:
            self.groupSettings = {} if not self.groupSettings else self.groupSettings
            if not self.groupSettings.get("power", True):
                if self.message == '开机':
                    if self.se.get('sender').get('role') != 'member' or self.se.get('user_id') == self.botSettings.get('owner') or self.se.get('user_id') == self.botSettings.get('second_owner'):
                        self.commonx('UPDATE `botSettings` SET `power`=1 WHERE `qn`=%s', (self.se.get('group_id')))
                        self.send('{0}-开机成功！'.format(self.botSettings.get('name')))
                    else:
                        self.send('[CQ:face,id=151] 就你？先拿到管理员再说吧！')
                elif self.message:
                    if ('[CQ:at,qq='+str(self.botSettings.get('myselfqn'))+']' in self.message) or (self.botSettings.get('name') in self.message) or ('机器人' in self.message):
                        self.send('{0}还没有开机哦~\n发送“开机”可以开启机器人！'.format(self.botSettings.get('name')))
                self.checkWeijin(0)
                return 
        else:
            return 
        
        userCoin = self.userCoin
        se = self.se
        gid = se.get('group_id')
        cid = se.get('channel_id')
        uid = se.get('user_id')
        message = se.get('message')
        settings = self.groupSettings
        uuid = self.uuid
        botSettings = self.botSettings
        
        if se.get('post_type') == 'notice':
            # 群通知
            for i in noticeListenerList:
                self.checkPromiseAndRun(i)
            return 
        
        elif se.get('post_type') == 'request':
            # 请求
            for i in requestListenerList:
                self.checkPromiseAndRun(i)
            return 
        
        elif se.get('post_type') == 'meta_event':
            for i in metaEventListenerList:
                self.checkPromiseAndRun(i)
            return 
        
        elif se.get('channel_id') == None and gid != None:
            for i in messageListenerList:
                self.checkPromiseAndRun(i)
                
            # 以下是还未来得及移走的
            # 上报消息
            # reportMessage(se)
            
            # 防刷屏
            mlob = self.findObject('qn', gid, messagelist)
            mlo = mlob.get('object')
            if mlo == 404:
                messagelist.append({'qn':gid, 'uid':uid, 'times':1})
            else:
                arrnum = mlob.get('num')
                if mlo.get('uid') == uid:
                    if mlo.get('times') >= int(settings.get('AntiswipeScreen')):
                        messagelist[arrnum]['times'] = 1
                        if se.get('sender').get('role') == "member":
                            datajson = self.CallApi('set_group_ban', {"group_id":gid,"user_id":uid,"duration":600})
                            if datajson['status'] != 'ok':
                                self.send('[CQ:face,id=151] 检测到刷屏，但禁言失败！')
                            else:
                                self.send('[CQ:face,id=54] 检测到刷屏，已禁言！')
                    else:
                        messagelist[arrnum]['times'] += 1
                    # 禁言警告
                    if mlo.get('times') == int(settings.get('AntiswipeScreen'))-1 and se.get('sender').get('role') == "member":
                        self.send('刷屏禁言警告！\n请不要连续发消息超过设定数量！', coinFlag=False)
                else:
                    messagelist[arrnum]['times'] = 1
                    messagelist[arrnum]['uid'] = uid
            
            # 功能函数
            # self.bot()
        
        else:
            for i in messageListenerList:
                self.checkPromiseAndRun(i)
            
            # self.bot()
        
        global commandPluginsList
        userCoin = self.userCoin if self.userCoin else -1
        se = self.se
        gid = se.get('group_id')
        cid = se.get('channel_id')
        uid = se.get('user_id')
        message = se.get('message')
        settings = self.groupSettings
        uuid = self.uuid
        botSettings = self.botSettings
        
        # 跟班模式
        only_for_uid = True
        if se.get("group_id"):
            if botSettings.get("only_for_uid") and botSettings.get("only_for_uid") == uid:
                # self.CrashReport("botSettings")
                only_for_uid = False
            if len(settings.get("only_for_uid")) != 0 and str(uid) in settings.get("only_for_uid").split():
                # self.CrashReport("groupSettings")
                only_for_uid = False
            if (not botSettings.get("only_for_uid")) and (len(settings.get("only_for_uid")) == 0):
                # self.CrashReport("settings")
                only_for_uid = False
            if uid == yamldata.get("chat").get("owner"):
                # self.CrashReport("yamldata")
                only_for_uid = False
            # if (botSettings.get("only_for_uid") != 0 and botSettings.get("only_for_uid") != uid) and (str(uid) not in self.groupSettings.get("only_for_uid") and self.groupSettings.get("only_for_uid")) and (str(uid) != str(yamldata.get("chat").get("owner"))):
                # only_for_uid = True
        else:
            only_for_uid = False
        
        if uid != botSettings.get('owner') and se.get('channel_id') == None and gid == None and botSettings.get("reportPrivate"):
            self.SendOld(botSettings.get('owner'), '[CQ:face,id=151] 主人，有人跟我说话话\n内容：'+str(message)+'\n回复请对我说：\n\n回复|'+str(se.get('user_id'))+'|'+str(se.get('message_id'))+'|<回复内容>')
            if uid != botSettings.get('second_owner'):
                self.SendOld(botSettings.get('second_owner'), '[CQ:face,id=151] 副主人，有人跟我说话话\n内容：'+str(message)+'\n回复请对我说：\n\n回复|'+str(se.get('user_id'))+'|'+str(se.get('message_id'))+'|<回复内容>')
                # self.send('请尽量在群中使用机器人，否则因为风控，机器人可能无法向你发送消息')
        
        if '[CQ:at,qq='+str(botSettings.get('owner'))+']' in message and botSettings.get("reportAt"):
            self.SendOld(botSettings.get('owner'), '[CQ:face,id=151] 主人，有人艾特你awa\n消息内容：'+str(message)+'\n来自群：'+str(gid)+'\n来自用户：'+str(uid))
            
        if '[CQ:at,qq='+str(botSettings.get('second_owner'))+']' in message and botSettings.get("reportAt"):
            self.SendOld(botSettings.get('second_owner'), '[CQ:face,id=151]副主人，有人艾特你awa\n消息内容：'+str(message)+'\n来自群：'+str(gid)+'\n来自用户：'+str(uid))
        
        
        if ('[CQ:at,qq='+str(botSettings.get('myselfqn'))+']' in message) and (userCoin == -1) and not only_for_uid:
            self.send('[CQ:reply,id='+str(se.get('message_id'))+'] '+str(botSettings.get('name'))+'[|想起来你还没有注册哦~|]\n[|发送“注册”可以让机器人认识你啦QAQ|]')
        
        if '[CQ:image,' in message:
            try:
                dataa = self.CallApi('ocr_image', {'image':self.getCQValue('file', message)})
                message = ' '
                datajson = dataa.get('data').get('texts')
                for i in datajson:
                    message += i.get('text')
                # CrashReport(message, '图片OCR内容')
            except Exception as e:
                pass
        
        try:
            if gid != None:
                if settings.get('increase_verify') != 0:
                    if self.execPlugin('basic.getVerifyStatus()') == True and '人机验证 ' not in message:
                        self.CallApi('delete_msg', {'message_id':self.se.get('message_id')})
        except Exception as e:
            self.CrashReport(settings, e)
            pass
        
        # 指令监听器
        self.rclOb = self.ReadCommandListener()
        if self.rclOb != 404:
            if message == '退出':
                self.RemoveCommandListener()
                return self.send('退出！')
            else:
                self.execPlugin(self.rclOb.get('func'))
                return True
        
        # 指令
        self.noticeFlag = False
        def runCommand(i, content):
            lengthmx = len(content)
            if self.message[0:lengthmx] == content:
                # 提示<>
                for args in self.args:
                    if '>' in args or '<' in args:
                        self.send('温馨提示，指令列表中的<>符号请忽略！')
                        break
                self.message = self.message.replace(content, '', 1).replace('  ', ' ').lstrip().rstrip()
                self.ocrImage = message
                self.se['message'] = self.message
                self.checkPromiseAndRun(i, True, True, content)
                return True
            
            # 检测
            lengthmx = len(content.lstrip().rstrip())
            if self.message[0:lengthmx] == content.lstrip().rstrip():
                self.noticeFlag = True
            return False
        
        atStr = '[CQ:at,qq='+str(botSettings.get('myselfqn'))+'] '
        if message[0:len(atStr)] == atStr:
            message = message.replace(atStr, '', 1)
        
        if self.groupSettings.get("v_command"):
            v_command_list = self.groupSettings.get("v_command").split()
        else:
            v_command_list = []
        # self.CrashReport("{} {} {}".format(v_command_list, uid, only_for_uid), "command")
        if (not only_for_uid) or (v_command_list):
            for l in self.pluginsList:
                if commandPluginsList.get(l.get('path')) == None:
                    continue
                for i in commandPluginsList.get(l.get('path')):
                    # 识别指令
                    if isinstance(i.get("content"), list):
                        for content in i.get("content"):
                            if (not only_for_uid) or (content.lstrip().rstrip() in v_command_list):
                                if runCommand(i, content):
                                    return 
                    else:
                        if (not only_for_uid) or (i.get("content").lstrip().rstrip() in v_command_list):
                            if runCommand(i, i.get("content")):
                                return 
        if self.noticeFlag and not only_for_uid:
            self.send("请注意指令每一部分之间有一个空格！！！")
        
        if self.message[0:10] == '[CQ:reply,' and '撤回' in message:
            if uid == botSettings.get('owner') or uid == botSettings.get('second_owner') or se.get('sender').get('role') != 'member':
                self.CallApi('delete_msg', {'message_id':self.getCQValue('id', message)})
                self.CallApi('delete_msg', {'message_id':self.se.get('message_id')})
                return 
            else:
                self.send('[CQ:face,id=151] 就你？先拿到管理员再说吧！')
        
        # 违禁词检查
        if settings != None:
            weijinFlag = 1 if settings.get('weijinCheck') else 0
        else:
            weijinFlag = 1
        if self.checkWeijin(weijinFlag) == True and not only_for_uid:
            return 'OK.'
        
        # 关键词回复
        if settings != None:
            kwFlag = 1 if settings.get('keywordReply') else 0
        else:
            kwFlag = 1
        if kwFlag and not only_for_uid:
            keywordlist = self.selectx(self.sql_keywordListSql, (uuid))
            for i in keywordlist:
                replyFlag = False
                if userCoin >= i.get('coin') and (i.get("qn") == 0 or gid == i.get("qn")):
                    replyFlag = True
                if replyFlag == True:
                    replyKey = self.KeywordReplace(i.get('key'))
                    if self.keywordPair(replyKey, message):
                        self.sendKeyword(i.get('value'))
        
        # 分类菜单
        if len(self.commandmode) == 0:
            self.chushihuacd()
        
        if (not only_for_uid) or ("菜单" in v_command_list):
            for i in self.commandmode:
                if message == i.get('name'):
                    self.cd3(i.get("name"))
        
        # 回复
        if not only_for_uid:
            if gid != None or cid != None:
                if gid != None:
                    randnum = settings.get('replyPercent')
                elif cid != None:
                    randnum = 100
                rand = random.randint(1, randnum)
                if (rand == 1) or ('[CQ:at,qq='+str(botSettings.get('myselfqn'))+']' in self.message):
                    self.message = self.se['message'] = self.message.replace('[CQ:at,qq='+str(botSettings.get('myselfqn'))+']', "")
                    self.reply()
            else:
                self.reply()
    
    def chatterbot(self):
        if not self.ChatterBot:
            self.ChatterBot = ChatBot(
                self.botSettings.get("name"),
                storage_adapter='chatterbot.storage.SQLStorageAdapter',
                database_uri='sqlite:///chatterbot/db.sqlite3'
            )
        if not self.ListTrainer:
            self.ListTrainer = ListTrainer(self.ChatterBot)
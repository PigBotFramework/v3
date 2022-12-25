from fastapi import FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Union
import uvicorn, asyncio, yaml, traceback, time, random, requests, sys, hmac, os, json, math, datetime, pytz, urllib
from bot import bot, varsInit
from urllib.request import urlopen
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
# 打开yaml文件
fs = open("data.yaml",encoding="UTF-8")
yamldata = yaml.load(fs,Loader=yaml.FullLoader)
# 解决“Max retries exceeded with url”问题
s = requests.session()
s.keep_alive = False
requests.adapters.DEFAULT_RETRIES = 5

headers = {
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36'
}
description = '''
> PigBotFramework is built on FastApi, all APIs are listed below and provide query parameters  
**Notice: 以下接口默认使用1000处理器，其他处理器用法相同**
'''
tags_metadata = [
    {
        "name": "上报接口",
        "description": "OneBot(v11)标准上报接口",
        "externalDocs": {
            "description": "OneBot Docs",
            "url": "https://onebot.dev/",
        },
    },
    {
        "name": "GOCQ接口",
        "description": "GOCQ操作接口",
        "externalDocs": {
            "description": "Go-CQHttp Docs",
            "url": "https://docs.go-cqhttp.org/",
        },
    },
    {
        "name": "其他接口",
        "description": "其他接口",
    },
]
app = FastAPI(
    title="PigBotFramework API",
    description=description,
    openapi_tags=tags_metadata,
    version="4.1.0",
    contact={
        "name": "xzyStudio",
        "url": "https://xzy.center",
        "email": "gingmzmzx@gmail.com",
    },
)

# 初始化 slowapi，注册进 fastapi
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
port = str(sys.argv[1])


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许访问的源
    allow_credentials=True,  # 支持 cookie
    allow_methods=["*"],  # 允许使用的请求方法
    allow_headers=["*"]  # 允许携带的 Headers
)

@app.post("/{}".format(port), tags=['上报接口'])
async def post_data(request: Request, X_Signature: Union[str, None] = Header(default=None)):
    """
    描述：**机器人事件POST上报接口**  
    身份验证：可通过`GET`参数`pswd`验证，或**通过header中的`X_Signature`验证身份**（OneBot标准）  
    上报数据：在Request请求体中以json格式  
    """
    try:
        # sha1校验防伪上报
        params = request.query_params
        botPswd = botIns.GetPswd(params.get("uuid"))
        if botPswd == params.get("pswd"):
            sig = botPswd
            received_sig = botPswd
        else:
            sig = botIns.encryption(await request.body(), botPswd)
            received_sig = X_Signature[len('sha1='):] if X_Signature else False
        if sig == received_sig:
            se = await request.json()
            # botIns.CrashReport(se, params.get("uuid"))
            bot().requestInit(se, params.get("uuid"), port)
        else:
            return {"code":403}
    except Exception as e:
        bot().CrashReport(traceback.format_exc())
        return traceback.format_exc()

@app.get("/{}/get".format(port), tags=['上报接口'])
async def get_data(uuid:str, pswd:str, params:str):
    """
    描述：**机器人事件GET上报接口**  
    身份验证：需提供`UUID`和`pswd`，**不可通过`X_Signature`验证身份**（不是OneBot规定的上报接口，可用于其他情况的上报）  
    上报数据：**`params`参数为`json_encode()`且`urlencode()`后的上报数据**  
    """
    if botIns.GetPswd(uuid) == pswd:
        bot().requestInit(json.loads(params), uuid, port)
        return json.loads(params)
    else:
        return {"code":403}

@app.post("/{}/testSpeed".format(port), tags=['其他接口'])
@app.get("/{}/testSpeed".format(port), tags=['其他接口'])
@limiter.limit("12/minute")
async def webtestSpeed(request: Request, X_Forwarded_For: Union[str, None] = Header(default=None)):
    """
    描述：测试指令执行速度和延迟  
    频率限制：**12次/分钟**  
    测试方法：模拟执行`菜单`指令  
    """
    timeStart = time.time()
    message = "菜单 noreply"
    bot().requestInit({'post_type': 'message', 'message_type': 'group', 'self_id': 3558267090, 'sub_type': 'normal', 'group_id': 763432519, 'message': message, 'sender': {'age': 0, 'area': '', 'card': '', 'level': '', 'nickname': '', 'role': 'owner', 'sex': 'unknown', 'title': '', 'user_id': 66600000}, 'user_id': 66600000, 'font': 0, 'raw_message': message}, "123456789", port)
    timeEnd = time.time()
    report = {"code":200,"port":int(port)%1000,"startTime":timeStart,"endTime":timeEnd,"cost":timeEnd-timeStart}
    # botIns.CrashReport("From IP:{}".format(X_Forwarded_For), "testSpeed")
    return report

@app.post("/{}/status".format(port), tags=['其他接口'])
@app.get("/{}/status".format(port), tags=['其他接口'])
async def webstatus():
    """
    描述：获取处理器状态  
    返回值：`{"code":200}`  
    """
    return json.dumps({"code":200}, ensure_ascii=False)

@app.post("/{}/webhook".format(port), tags=['其他接口'])
async def webhook(request: Request, X_Hub_Signature: Union[str, None] = Header(default=None)):
    """
    描述：WebHooks接口  
    身份验证：header中的`X_Hub_Signature`  
    用途：用于自动pull插件  
    """
    # github加密是将post提交的data和WebHooks的secret通过hmac的sha1加密，放到HTTP headers的X-Hub-Signature参数中
    body = await request.json()
    token = botIns.encryption(body, '123456')
    # 认证签名是否有效
    signature = X_Hub_Signature.split('=')[-1]
    if signature != token:
        return "token认证无效", 401
    data = json.loads(str(body, encoding = "utf8"))
    # 运行shell脚本，更新代码
    os.system('./pull.sh {0} {1} {2}'.format(data.get('repository').get('name'), data.get('repository').get('url'), data.get('repository').get('full_name')))
    return jsonify({"status": 200})

@app.get("/{}/overview".format(port), tags=['GOCQ接口'])
@app.post("/{}/overview".format(port), tags=['GOCQ接口'])
async def weboverview(uuid:str):
    """
    描述：获取机器人GOCQ数据概览  
    参数：`UUID` 机器人实例uuid  
    返回值：data[] 具体内容可以请求后查看  
    """
    try:
        botSettings = botIns.selectx('SELECT * FROM `botBotconfig` WHERE `uuid`="{0}";'.format(uuid))[0]
        
        # 尝试请求gocq获取gocq信息
        try:
            gocq = CallApi("get_version_info", {}, ob=botSettings, timeout=5).get("data")
            if gocq.get('app_name') != "go-cqhttp":
                return {'code':502}
        except Exception as e:
            print(e)
            return {'code':502}
        
        data = {'code':200,'go-cqhttp':gocq,'time':time.time()}
        # 获取各项数据
        # 1. 群聊列表
        groupList = CallApi('get_group_list', {}, ob=botSettings).get('data')
        data['groupCount'] = len(groupList)
        # 2. 好友列表
        friendList = CallApi('get_friend_list', {}, ob=botSettings).get('data')
        data['friendCount'] = len(friendList)
        # 3. 网络信息
        network = CallApi('get_status', {}, ob=botSettings).get('data')
        data['network'] = network.get('stat')
        
        return data
    except Exception as e:
        return traceback.format_exc()
    
@app.get("/{}/getFriendAndGroupList".format(port), tags=['GOCQ接口'])
async def webgetFriendAndGroupList(pswd:str, uuid:str):
    """
    描述：获取机器人好友和群聊列表  
    参数：`pswd:str` 密钥    `uuid:str` 实例uuid  
    返回值：`{"friendList":..., "groupList":...}`  
    """
    try:
        if pswd == botIns.GetPswd(uuid):
            groupList = CallApi('get_group_list', {}, uuid).get('data')
            friendList = CallApi('get_friend_list', {}, uuid).get('data')
            return {'friendList':friendList,'groupList':groupList}
        else:
            return 'Password error.'
    except Exception as e:
        return traceback.format_exc()

@app.get("/{}/getFriendList".format(port), tags=['GOCQ接口'])
async def webgetFriendList(pswd:str, uuid:str):
    """获取机器人好友列表"""
    if pswd == botIns.GetPswd(uuid):
        return CallApi('get_friend_list', {}, uuid).get('data')
    else:
        return 'Password error.'

@app.get("/{}/kickUser".format(port), tags=['GOCQ接口'])
async def webkickUser(pswd:str, uuid:str, gid:int, uid:int):
    """踢出某人"""
    if pswd == botIns.GetPswd(uuid):
        data = CallApi('set_group_kick', {'group_id':gid,'user_id':uid}, uuid)
        if data['status'] == 'ok':
            return 'OK.'
        else:
            return 'failed.'
    else:
        return 'Password error.'

@app.get("/{}/banUser".format(port), tags=['GOCQ接口'])
async def webBanUser(pswd:str, uuid:str, uid:int, gid:int, duration:int):
    """禁言某人"""
    if pswd == botIns.GetPswd(uuid):
        CallApi('set_group_ban', {'group_id':gid,'user_id':uid,'duration':duration}, uuid)
        return 'OK.'
    else:
        return 'Password error.'

@app.get("/{}/delete_msg".format(port), tags=['GOCQ接口'])
async def webDeleteMsg(pswd:str, uuid:str, message_id:str):
    """撤回消息"""
    if pswd == botIns.GetPswd(uuid):
        CallApi('delete_msg', {'message_id':message_id}, uuid)
        # commonx('DELETE FROM `botChat` WHERE `mid`="{0}"'.format(mid))
        return 'OK.'
    else:
        return 'Password error.'

@app.get("/{}/getMessage".format(port), tags=['GOCQ接口'])
async def webGetMessage(uuid:str, message_id:int):
    """获取消息"""
    try:
        return CallApi('get_msg', {'message_id':message_id}, uuid)
    except Exception as e:
        return traceback.format_exc()

@app.get("/{}/getForwardMessage".format(port), tags=['GOCQ接口'])
async def webGetForwardMessage(uuid:str, message_id:str):
    """获取合并转发消息"""
    try:
        return CallApi('get_forward_msg', {'message_id':message_id}, uuid)
    except Exception as e:
        return traceback.format_exc()

@app.get("/{}/getGroupHistory".format(port), tags=['GOCQ接口'])
async def webGetGroupHistory(uuid:str, group_id:int, message_seq:int=0):
    """获取群聊聊天记录"""
    try:
        if message_seq == 0:
            return CallApi('get_group_msg_history', {'group_id':group_id}, uuid)
        else:
            return CallApi('get_group_msg_history', {'group_id':group_id, "message_seq":message_seq}, uuid)
    except Exception as e:
        return traceback.format_exc()

@app.get("/{}/sendMessage".format(port), tags=['GOCQ接口'])
@app.post("/{}/sendMessage".format(port), tags=['GOCQ接口'])
async def webSendMessage(pswd:str, uuid:str, uid:int, gid:int, message:str):
    """发送消息"""
    if pswd == botIns.GetPswd(uuid):
        SendOld(uuid, uid, message, gid)
        return 'OK.'
    else:
        return 'Password error.'
        
@app.get("/{}/callApi".format(port), tags=['GOCQ接口'])
@app.post("/{}/callApi".format(port), tags=['GOCQ接口'])
async def webCallApi(uuid:str, name:str, pswd:str, params={}):
    """发送消息"""
    if pswd == botIns.GetPswd(uuid):
        return CallApi(name, json.loads(params), uuid)
    else:
        return 'Password error.'

@app.get("/{}/getGroupList".format(port), tags=['GOCQ接口'])
async def getGroupList(uuid:str):
    """获取某机器人群聊列表"""
    return CallApi('get_group_list', {}, uuid)
    
# @app.get("/{}/getGroupDe".format(port), tags=['GOCQ接口'])
# @limiter.limit("6/minute")
# async def webgetGroupDe(uuid:str, request: Request):
#     """
#     获取某机器人群聊列表加最新一条消息
#     频率限制6次每分钟
#     """
#     try:
#         dataList = CallApi('get_group_list', {}, uuid)['data']
#         for i in dataList:
#             messages = CallApi('get_group_msg_history', {'group_id':i.get("group_id")}, uuid).get("data").get("messages")
#             message = messages[-1].get("message")
#             i['message'] = message
#         return dataList
#     except Exception as e:
#         return e

@app.get("/{}/MCServer".format(port), tags=['其他接口'])
async def MCServer(msg:str, uuid:str, qn:int):
    """MC服务器消息同步"""
    print('服务器消息：')
    msg = msg[2:-1]
    
    if msg != '' and '[Server] <' not in msg:
        msg = '[CQ:face,id=151] 服务器消息：'+str(msg)
        if 'logged in with entityid' in msg:
            msg1 = msg[0:msg.find('logged in with entityid')-1]
            msg = msg1 + '进入了游戏'
        
        SendOld(uuid, None, msg, qn)
    
    return '200 OK.'

@app.get('/{}/getGroupMemberList'.format(port), tags=['GOCQ接口'])
async def webGetGroupMemberList(uuid:str, gid:int):
    """获取群聊成员列表"""
    return CallApi('get_group_member_list', {'group_id':gid}, uuid)

@app.get('/{}/getPluginsData'.format(port), tags=['其他接口'])
async def webgetPluginsData():
    """刷新插件数据"""
    return pluginsData

@app.get('/{}/getGOCQConfig'.format(port), tags=['其他接口', 'GOCQ接口'])
async def webgetGOCQConfig(uin:int, host:str, port:int, uuid:str, secret:str, password:str="null", url:str="https://qqbot.xzy.center/1000/?uuid={0}"):
    '''生成GOCQ配置'''
    try:
        gocqConfig = json.loads('{"account": {"uin": 123, "password": null, "encrypt": false, "status": 0, "relogin": {"delay": 3, "interval": 3, "max-times": 0}, "use-sso-address": true, "allow-temp-session": false}, "heartbeat": {"interval": -1}, "message": {"post-format": "string", "ignore-invalid-cqcode": false, "force-fragment": false, "fix-url": false, "proxy-rewrite": "", "report-self-message": false, "remove-reply-at": false, "extra-reply-data": false, "skip-mime-scan": false}, "output": {"log-level": "trace", "log-aging": 1, "log-force-new": true, "log-colorful": false, "debug": false}, "default-middlewares": {"access-token": "", "filter": "", "rate-limit": {"enabled": false, "frequency": 1, "bucket": 1}}, "database": {"leveldb": {"enable": true}, "cache": {"image": "data/image.db", "video": "data/video.db"}}, "servers": [{"http": {"host": "1.1.1.1", "port": 2222, "timeout": 10, "long-polling": {"enabled": false, "max-queue-size": 2000}, "middlewares": {"access-token": "", "filter": "", "rate-limit": {"enabled": false, "frequency": 1, "bucket": 1}}, "post": [{"url": "http://127.0.0.1:8000/", "secret": "123456", "max-retries": 0, "retries-interval": 0}]}}]}')
        gocqConfig['account']['password'] = password
        gocqConfig['account']['uin'] = uin
        gocqConfig['servers'][0]['http']['host'] = host
        gocqConfig['servers'][0]['http']['port'] = port
        gocqConfig['servers'][0]['http']['post'][0]['url'] = url.format(uuid)
        gocqConfig['servers'][0]['http']['post'][0]['secret'] = secret
        gocqConfig['default-middlewares']['access-token'] = secret
        gocqConfig['servers'][0]['http']['middlewares']['access-token'] = secret
        filename = 'config-{0}.yml'.format(uuid)
        file = open("./resources/createimg/{0}".format(filename), 'w+', encoding='utf-8')
        yaml.dump(gocqConfig, file)
        file.close()
        return json.dumps(filename, ensure_ascii=False)
    except Exception as e:
        return e

@app.get("/{}/reloadPlugins".format(port), tags=['其他接口'])
async def webreloadPlugins():
    '''刷新插件及指令列表'''
    return reloadPlugins(port)

@app.get("/{}/sendAll".format(port), tags=['其他接口', 'GOCQ接口'])
async def websendAll(message:str, pswd:str):
    '''机器人通知机器人主人'''
    if pswd == yamldata.get("self").get("pswd"):
        # message = '请注意！机器人上报地址有更新，请将gocq的config.yml中的servers中的http中的post中的url改为以下值：\nhttps://qqbot.xzy.center/1000/?uuid={}\n如不及时更改会造成机器人无法使用，请注意！\n如有疑问，请联系 2417481092'.format(i.get("uuid"))
        for i in botIns.selectx('SELECT * FROM `botBotconfig`'):
            try:
                SendOld(i.get('uuid'), i.get('owner'), message)
            except Exception as e:
                pass
        return "OK"
    else:
        return "pswd error."

def reloadPlugins(port, flag=False):
    global pluginsData, commandPluginsList, commandlist, noticeListenerList, requestListenerList, metaEventListenerList, messageListenerList, ChatterBotListener
    commandlist = []
    pluginsData = []
    commandPluginsList = {}
    pluginsList = getPluginsList()
    
    # 引入
    for i in pluginsList:
        try:
            # 只能使用exec函数引入
            '''
            moduleName = 'plugins.{0}.main'.format(i)
            print(moduleName in sys.modules)
            if moduleName not in sys.modules:
                exec('import plugins.{0}.main as {0}'.format(i))
            '''
            
            # 加载json
            clist = json.loads(openFile('./plugins/{0}/commands.json'.format(i)))
            if not commandPluginsList.get(i):
                commandPluginsList[i] = []
            commandPluginsList[i] += clist
            for l in clist:
                if l.get('type') == "command":
                    commandlist.append(l)
                elif l.get('type') == "message":
                    messageListenerList.append(l)
                elif l.get('type') == "notice":
                    noticeListenerList.append(l)
                elif l.get('type') == "request":
                    requestListenerList.append(l)
                elif l.get('type') == "meta_event":
                    metaEventListenerList.append(l)
                elif l.get('type') == "chatterbot":
                    ChatterBotListener.append(l)
                else:
                    # CrashReport(yamldata.get('self').get('defaultUuid'), '无效的指令TYPE：{0}'.format(i), '无效的指令TYPE')
                    pass
            
            clist = json.loads(openFile('./plugins/{0}/data.json'.format(i)))
            clist['cwd'] = i
            pluginsData.append(clist)
        except Exception as e:
            msg = traceback.format_exc()
            botIns.CrashReport('在引入插件 {0} 时遇到错误：\n{1}'.format(i, msg), '插件警告⚠')
            pluginsList.remove(i)
    
    varsInit(commandPluginsList, commandlist, messageListenerList, metaEventListenerList, requestListenerList, noticeListenerList, pluginsList, ChatterBotListener, pluginsData, port, flag)
    return {"code":200}

def getPluginsList():
    # 生成插件列表
    # global pluginsList
    pluginsList = os.listdir('plugins')
    for dbtype in pluginsList[::]:
        if os.path.isfile(os.path.join('plugins',dbtype)):
            pluginsList.remove(dbtype)
    return pluginsList

def openFile(path):
    with open(path, 'r') as f:
        return f.read()

def CallApi(api, parms, uuid=None, httpurl=None, access_token=None, ob=None, timeout=10):
    if ob != None:
        httpurl = ob.get("httpurl")
        access_token = ob.get("secret")
    elif httpurl != None and access_token != None:
        pass
    elif uuid != None:
        ob = botIns.selectx('SELECT * FROM `botBotconfig` WHERE `uuid`="{0}";'.format(uuid))[0]
        httpurl = ob.get("httpurl")
        access_token = ob.get("secret")
    
    data = requests.post(url='{0}/{1}?access_token={2}'.format(httpurl, api, access_token), json=parms, timeout=timeout)
    return data.json()

def SendOld(uuid, uid, content, gid=None):
    if gid == None:
        dataa = CallApi('send_msg', {'user_id':uid,'message':content}, uuid)
    else:
        dataa = CallApi('send_msg', {'group_id':gid,'message':content}, uuid)
    if dataa.get('status') != 'failed':
        mid = dataa.get('data').get('message_id')
    else:
        mid = None
    return mid


# -------------------全局变量-----------------
commandListener = []
pluginsData = []
commandPluginsList = {}
messagelist = []
commandlist = []
messageListenerList = []
metaEventListenerList = []
requestListenerList = []
noticeListenerList = []
ChatterBotListener = []
pluginsList = getPluginsList()
# scheduler = BlockingScheduler()
botIns = bot()
try:
    reloadPlugins(port)
except Exception as e:
    print("reloadPlugins error.\n{}".format(e))

def serve(port):
    reloadPlugins(int(port), True)
    uvicorn.run(app="fabot:app",  host=yamldata.get('run').get('host'), port=int(port), reload=True, debug=True)
if __name__ == '__main__':
    serve(port)
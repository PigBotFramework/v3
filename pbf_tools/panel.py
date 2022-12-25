from fastapi import FastAPI, Request, HTTPException, status
import uvicorn, sys, secrets, threading, requests, json
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
try:
    from pbf import run, kill, restart
except Exception:
    from cli import run, kill, restart
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
count = 4
status = {}
description = '''
## Web Control Panel of PBF
'''
app = FastAPI(
    title="PigBotFramework Panel",
    description=description,
    openapi_url="/control/openapi.json",
    version="1.0.0",
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许访问的源
    allow_credentials=True,  # 支持 cookie
    allow_methods=["*"],  # 允许使用的请求方法
    allow_headers=["*"]  # 允许携带的 Headers
)

def checkPassword(password):
    current_password_bytes = password.encode("utf8")
    correct_password_bytes = b"Xu015300"
    is_correct_password = secrets.compare_digest(
        current_password_bytes, correct_password_bytes
    )
    if not is_correct_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )

@app.get("/")
async def indexFunc():
    return 'Oops! How do you find this website?!'

@app.get("/api/start")
@limiter.limit("12/minute")
async def startFunc(request: Request, port:int, password:str):
    checkPassword(password)
    run(int(port))
    return 200

@app.get("/api/stop")
@limiter.limit("12/minute")
async def stopFunc(request: Request, port:int, password:str):
    checkPassword(password)
    kill(int(port))
    return 200
    
@app.get("/api/restart")
@limiter.limit("12/minute")
async def restartFunc(request: Request, password:str):
    checkPassword(password)
    threading.Thread(target=restart).start()
    return 200

def protect():
    for i in range(count+1):
        port = '{}'.format(i+1000)
        try:
            if int(requests.get('http://127.0.0.1:{0}/{0}/testSpeed'.format(port), timeout=10).json().get('cost')) < 2:
                status[port] = 0
        except Exception:
            status[port] = status.get(port)+1 if status.get(port) else 1
            if status.get(port) > 1:
                try:
                    kill(int(port))
                finally:
                    run(int(port))

if __name__ == '__main__':
    scheduler.add_job(protect, 'interval', seconds=20, id='protect', replace_existing=True)
    scheduler.start()
    uvicorn.run(app="panel:app",  host="0.0.0.0", port=int(sys.argv[1]), reload=True, debug=True)
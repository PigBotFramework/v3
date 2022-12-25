from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer
import os, yaml

try:
    os.remove("db.sqlite3")
except Exception:
    pass

bot = ChatBot('Pig Bot')
trainer = ListTrainer(bot)

path = 'chinese'
for dir in os.listdir(path):
    dir = os.path.join(path, dir)
    # 判断当前目录是否为文件夹
    if not os.path.isdir(dir):
        print(dir)
        fs = open(dir, encoding="UTF-8")
        yamldata = yaml.load(fs, Loader=yaml.FullLoader).get("conversations")
        for i in yamldata:
            trainer.train(i)
print("finish")

#导入语料库
file = open("qingyun.csv",'r',encoding='utf-8')
times = 0
print('开始加载语料！')
while True:
    try:
        line = file.readline()
        if not line:
            break
        trainer.train(line.split(" | "))
    except:
        pass
file.close()
print('语料加载完毕')

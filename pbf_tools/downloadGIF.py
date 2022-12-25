from bs4 import BeautifulSoup
import requests, sys

res = BeautifulSoup(requests.get("https://github.com/kyubotics/coolq-http-api/wiki/%E8%A1%A8%E6%83%85-CQ-%E7%A0%81-ID-%E8%A1%A8").content.decode(), 'lxml')
res = res.find(name="table", attrs={"role": "table"}).tbody.select("tr")
for i in res:
    i = i.select("td")
    id = i[0].text
    src = i[2].img.attrs.get("src")
    with open(f"../resources/cqcode/{id}.gif", "wb") as f:
        f.write(requests.get(src).content)
        print(f"{id}: saved!")

# 写了个PY脚本，爬取了所有的cq表情，使用方法： https://resourcesqqbot.xzy.center/cqcode/{cqcode face id}.gif
# 例如： https://resourcesqqbot.xzy.center/cqcode/221.gif
# 所有CQ码表情表见： https://github.com/kyubotics/coolq-http-api/wiki/%E8%A1%A8%E6%83%85-CQ-%E7%A0%81-ID-%E8%A1%A8
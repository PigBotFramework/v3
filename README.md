# PigBotFramework
小猪比机器人

[官网](https://qb.xzy.center) | [开发文档](https://docsqqbot.xzy.center)

# 介绍
小猪比机器人是使用Python构建的OneBot机器人极速响应框架。默认使用`FastAPI`创建HTTP服务器

# 特性
- 多实例模式，各机器人实例之间互不影响
- 异步FastAPI与简洁的处理流程，多线程快速响应
- 扩展功能丰富，内置NSFW、定时任务、utils等各种辅助功能
- API全面、易用，可塑性极高（（
- OneBot(v11)标准，偏向兼容gocq

# 搭建
您可以在本地轻松搭建机器人，后续将推出Docker方式搭建  

## 先决条件
首先请确保本地已安装`Python3`。推荐版本为`Python3.8`

## 本地搭建
- 创建`/pbf`文件夹，并将源码克隆进去  
  由于脚手架中写死的路径，您需要使用`/pbf`而不能用其他路径代替
- 安装依赖。确保您位于pbf文件夹，然后使用指令`pip install -r rms.txt`
- 安装脚手架。确保您位于pbf文件夹，然后使用指令`python setup.py install`
- 将`data.yaml.example`重命名为`data.yaml`，然后编辑其中的配置
- 程序并不会自动创建数据库结构，所以需要您自行导入`mysql`文件夹中的文件
- 以上全部到位后，您就可以启动机器人了。不过在这之前，我们建议您安装一些插件
  - 创建`/pbf/plugins`文件夹
  - 所有插件开源在[PigBotFrameworkPlugins](https://github.com/PigBotFrameworkPlugins)中，选择您想要安装的插件，然后克隆到plugins文件夹中，重命名为对应的仓库名

# 声明
不建议本地部署该版本，因为多实例模式，加之设计之初并没有考虑过开源，如果不结合官网的实例管理等功能会非常难用。  
如果您有意向开发插件，可以使用PBFLauncher

# 启动
确保您的Python环境变量正确，然后就可以使用指令`pbf start <port>`  
记得将`<port>`替换为运行端口  
  
有关pbf脚手架的其他用法可以使用`pbf --help`查看

# 二次开发
作者写作习惯非常差，这个项目只是我学习Python的练手项目，写的并不好，请多多包涵。  
我写代码从来不考虑效率和安全问题，所以这个项目可能漏洞百出  
与其骂作者垃圾，还不如来一起贡献代码，欢迎提交pr  

# 开源协议
本仓库采用`Apache Licence 2.0`协议，补充条款：不得商用
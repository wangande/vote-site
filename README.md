## 简单投票网站
# 后台admin管理创建投票(暂不支持用户自己上传，后期改进会支持用户上传，后台进行审核)，用户页面进行投票
# 同一IP用户，每小时只能投票一次


## 框架简介
# 后端使用tornado，前端使用bootstrap(暂定，后期也考虑使用react.js)
# 存储使用mongodb
# 缓存使用redis
# 文件存储使用七牛(没有使用七牛提供的python-sdk，七牛提供的python-sdk不支持异步，使用了自己修改后的异步sdk
# tornaoqiniu：https://github.com/wangande/tornadoqiniu.git)

## 构建
两个配置文件：
```
cp manage.bak.py manage.py
cp setting.vote.py setting.py

python manage.py
```

## 使用docker进行打包，发布
# 安装docker
# 新建vote-site-base基础镜像
# 对当前版本进行打tag(VERSION_ID)
# sh build_se.sh VERSION_ID(tag)
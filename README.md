# markdown-to-wechat

代码中有硬编码部分，请自行更改。

## 安装

```bash
pip3 install markdown Pygments werobot pyquery
```

## 配置白名单和 token

公众号后台路径：设置和开发 -> 基本配置 ：填入服务器 IP，生成 token。

在 sync.py 中通过环境变量获取 app_id 和 secret:

```python
robot.config["APP_ID"] = os.getenv('WECHAT_APP_ID')
robot.config["APP_SECRET"] = os.getenv('WECHAT_APP_SECRET')
```

把 token 配置到服务器环境变量，然后在服务器上运行 `python3 sync.py` 即可。


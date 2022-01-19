##public/upload_news.py
# -*- coding: utf-8 -*-
"""
推送文章到微信公众号
"""
from datetime import datetime ,timedelta
from weakref import ref
from pyquery import PyQuery
import time
import urllib
import markdown
import os
import sys
from werobot import WeRoBot
robot = WeRoBot()
robot.config["APP_ID"] = os.getenv('WECHAT_APP_ID')
robot.config["APP_SECRET"] = os.getenv('WECHAT_APP_SECRET')
client = robot.client
token = client.grant_token()

def upload_image_from_path(image_path):
  media_json = client.upload_permanent_media("image", open(image_path, "rb")) ##永久素材
  media_id = media_json['media_id']
  media_url = media_json['url']  
  return media_id, media_url

def upload_image(img_url):
  """
  * 上传临时素菜
  * 1、临时素材media_id是可复用的。
  * 2、媒体文件在微信后台保存时间为3天，即3天后media_id失效。
  * 3、上传临时素材的格式、大小限制与公众平台官网一致。
  """
  resource = urllib.request.urlopen(img_url)
  name = img_url.split("/")[-1]
  f_name = "/tmp/{}".format(name)
  with open(f_name, 'wb') as f:
    f.write(resource.read())
  return upload_image_from_path(f_name)

def get_images_from_markdown(content):
    lines = content.split('\n')
    images = []
    for line in lines:
        line = line.strip()
        if line.startswith('![') and line.endswith(')'):
            image = line.split(']')[0]
            image = image[2:]
            images.append(image)
    return images

def fetch_attr(content, key):
    """
    从markdown文件中提取属性
    """
    lines = content.split('\n')
    for line in lines:
        if line.startswith(key):
            return line.split(':')[1].strip()

def render_markdown(content):
    exts = ['markdown.extensions.extra', 'markdown.extensions.codehilite',
            'markdown.extensions.tables','markdown.extensions.toc']
    post =  "".join(content.split("---\n")[2:])
    html = markdown.markdown(post, extensions=exts)
    open("origi.html", "w").write(html)
    return css_beautify(html)

def update_images_urls(content, uploaded_images):
    for image, meta in uploaded_images.items():
        orig = "({})".format(image)
        new = "({})".format(meta[1])
        #print("{} -> {}".format(orig, new))
        content = content.replace(orig, new)
    return content

def replace_para(content):
    new = """<p style="font-size: 16px; padding-top: 8px; padding-bottom: 8px; margin: 0; line-height: 26px; color: rgb(89,89,89);">"""
    res = []
    for line in content.split("\n"):
        if line.startswith("<p>"):
            line = line.replace("<p>", new)
        res.append(line)
    return "\n".join(res)

def replace_header(content):
    res = []
    for line in content.split("\n"):
        l = line.strip()
        if l.startswith("<h") and l.endswith(">") > 0:
            tag = l.split(' ')[0].replace('<', '')
            value = l.split('>')[1].split('<')[0]            
            digit = tag[1]
            font =  (18 + (4 - int(tag[1])) * 2) if (digit >= '0' and digit <= '9') else 18
            new = "<{} style=\"margin-top: 30px; margin-bottom: 15px; padding: 0px; font-weight: bold; color: black; font-size: {}px;\"><span class=\"prefix\" style=\"display: none;\"></span><span class=\"content\">{}</span><span class=\"suffix\"></span></{}>".format(tag, font, value, tag)
            res.append(new)
        else:
            res.append(line)
    return "\n".join(res)

def replace_links(content):
    pq = PyQuery(open('origi.html').read())
    links = pq('a')
    refs = []
    index = 1
    for l in links.items():
        new = "<span class=\"footnote-word\" style=\"color: #1e6bb8; font-weight: bold;\">{}</span><sup class=\"footnote-ref\" style=\"line-height: 0; color: #1e6bb8; font-weight: bold;\">[{}]</sup>".format(l.text(), index)
        index += 1
        refs.append([l.attr('href'), l.text(), new])

    for r in refs:
        orig = "<a href=\"{}\">{}</a>".format(r[0], r[1])
        content = content.replace(orig, r[2])
    content = content + "\n" + """<h3 class="footnotes-sep" style="margin-top: 30px; margin-bottom: 15px; padding: 0px; font-weight: bold; color: black; font-size: 20px;"><span style="display: block;">参考资料</span></h3>\n"""
    content = content + """<section class="footnotes">"""
    index = 1
    for r in refs:
        l = r[2]
        line = "<span id=\"fn1\" class=\"footnote-item\" style=\"display: flex;\"><span class=\"footnote-num\" style=\"display: inline; width: 10%; background: none; font-size: 80%; opacity: 0.6; line-height: 26px; font-family: ptima-Regular, Optima, PingFangSC-light, PingFangTC-light, 'PingFang SC', Cambria, Cochin, Georgia, Times, 'Times New Roman', serif;\">[{}] </span><p style=\"padding-top: 8px; padding-bottom: 8px; display: inline; font-size: 14px; width: 90%; padding: 0px; margin: 0; line-height: 26px; color: black; word-break: break-all; width: calc(100%-50);\">{}: <em style=\"font-style: italic; color: black;\">{}</em></p>".format(index, r[1], r[0])
        index += 1
        content = content + line + "\n"
    content = content + "</section>"
    return content

def css_beautify(content):
    header = """<section id="nice" style="font-size: 16px; color: black; padding: 0 10px; line-height: 1.6; word-spacing: 0px; letter-spacing: 0px; word-break: break-word; word-wrap: break-word; text-align: left; font-family: Optima-Regular, Optima, PingFangSC-light, PingFangTC-light, 'PingFang SC', Cambria, Cochin, Georgia, Times, 'Times New Roman', serif;">"""
    content = replace_para(content)
    content = replace_header(content)
    content = replace_links(content)
    content = header + content + "</section>"
    return content


def upload_media_news(string_date, post_path):
    """
    上传到微信公众号素材
    """
    string_date = datetime.strptime(string_date, '%Y%m%d')
    print(string_date)
    content = open (post_path , 'r').read()
    TITLE = fetch_attr(content, 'title').strip('"').strip('\'')
    images = get_images_from_markdown(content)
    print(TITLE)
    print(images)
    uploaded_images = {}
    for image in images:
        media_id, media_url = upload_image_from_path("./blog-source/source" + image)
        uploaded_images[image] = [media_id, media_url]
    
    content = update_images_urls(content, uploaded_images)

    THUMB_MEDIA_ID = (len(images) > 0 and uploaded_images[images[0]][0]) or ''
    AUTHOR = 'yukang'
    RESULT = render_markdown(content)
    link = os.path.basename(post_path).replace('.md', '.html')
    date = fetch_attr(content, 'date').strip().strip('"').strip('\'').split( )[0].replace("-", "/")    
    CONTENT_SOURCE_URL = 'https://catcoding.me/{}/{}'.format(date, link)    

    articles = [{
      "title": TITLE,
      "thumb_media_id": THUMB_MEDIA_ID,
      "author": AUTHOR,
      "digest": '',
      "show_cover_pic": 1,
      "content": RESULT,
      "content_source_url": CONTENT_SOURCE_URL
    }
    # 若新增的是多图文素材，则此处应有几段articles结构，最多8段
    ]

    fp = open('./result.html', 'w')
    fp.write(RESULT)
    fp.close()

    news_json = client.add_news(articles)    
    media_id = news_json['media_id']
    return news_json

def run(string_date):
    post_path = "./blog-source/source/_posts/fakerjs-is-deleted.md"
    news_json = upload_media_news(string_date, post_path)
    print(news_json);
    print('successful')

if __name__ == '__main__':
    start_time = time.time() # 开始时间
    today = datetime.today() 
    string_date = today.strftime('%Y%m%d')
    try:
        run(string_date)
    except:
        run(string_date)
    end_time = time.time() #结束时间
    print("程序耗时%f秒." % (end_time - start_time))
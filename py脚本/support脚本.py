import requests
import base64
import os
import re
import html2text

def sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*]', '_', name)

# 初始化 HTML 转换器
html_to_md = html2text.HTML2Text()
html_to_md.ignore_links = False  # 保留链接
html_to_md.ignore_images = False  # 保留图片
html_to_md.body_width = 0  # 不自动换行

# 用户信息
username = "jasmine.xie@snapmaker.com/token"
api_token = "1vQwYoPB0GhURF2o49wl4xB4KP3LMs8QEoOISkyM"

credentials = f"{username}:{api_token}"
token = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
headers = {
    "Authorization": f"Basic {token}",
    "Content-Type": "application/json"
}

# 文章 Section
section_id = "4420716996119"
url = f"https://support.snapmaker.com/api/v2/help_center/sections/{section_id}/articles.json"

response = requests.get(url, headers=headers)
data = response.json()

output_dir = "pre_sales_articles"
os.makedirs(output_dir, exist_ok=True)

for article in data.get("articles", []):
    title = sanitize_filename(article["title"].strip())
    body_html = article.get("body", "")
    article_url = article.get("html_url", "")

    # 将 HTML 转换为 Markdown
    body_md = html_to_md.handle(body_html)

    markdown_content = f"# {title}\n\nURL: {article_url}\n\n{body_md}"

    filename = os.path.join(output_dir, f"{title}.md")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    print(f"Saved: {filename}")

import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from pydantic import BaseModel
import markdownify
from crawl4ai import *


class Article(BaseModel):
    title: str
    img: str
    url:str
async def run():
    # 配置 LLM 提取策略
    strategy = LLMExtractionStrategy(
        llm_config=LLMConfig(
            base_url='https://api.siliconflow.cn/v1/chat/completions',
            provider='deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B',
            api_token="sk-pkmlrazejztsiibznrjshbyiiuslrhdersufutdasjycrahh",  # <-- 替换成你的 token
        ),
        instruction="从页面中提取标题和图片链接和模型对应链接",
        extract_type="schema",
        schema=Article.model_json_schema(),
        extra_args={
            "temperature": 0.0,
            "max_tokens": 4096,
        },
        verbose=True,
    )

    url = "https://makerworld.com.cn/zh/3d-models"
    config = CrawlerRunConfig(extraction_strategy=strategy)
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url=url,
            config=config,
            bypass_cache=True
        )
        print(result.extracted_content)
        # if result.extracted_content:
        #     article_data = Article.model_validate(result.extracted_content[0])
        #
        #     # 使用 markdownify 将 HTML 转为 Markdown（可选）
        #     markdown_body = markdownify.markdownify(article_data.article)
        #
        #     # 保存为 .md 文件
        #     filename = f"{article_data.title.strip().replace(' ', '_')}.md"
        #     with open(filename, "w", encoding="utf-8") as f:
        #         f.write(f"# {article_data.title}\n\n")
        #         f.write(markdown_body)
        #
        #     print(f"✅ 已保存为 Markdown 文件：{filename}")
        # else:
        #     print("❌ 没有提取到内容")

if __name__ == "__main__":
    asyncio.run(run())

"""AI摘要生成器"""
import httpx
import json
from typing import List, Dict, Optional
from datetime import datetime
from .collectors.base_collector import NewsItem


class AISummarizer:
    """使用Qwen API生成摘要"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1", model: str = "qwen-plus"):
        """
        初始化AI摘要生成器
        
        Args:
            api_key: Qwen API密钥（DashScope API Key）
            base_url: API基础URL，默认使用阿里云灵积模型服务
            model: 使用的模型名称，可选: qwen-turbo, qwen-plus, qwen-max 等
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.url = f"{self.base_url}/chat/completions"
    
    async def generate_daily_summary(
        self,
        date: str,
        news_items: List[NewsItem],
        stock_name: str
    ) -> str:
        """
        生成单日新闻摘要
        
        Args:
            date: 日期
            news_items: 该日期的新闻列表
            stock_name: 股票名称
            
        Returns:
            摘要文本
        """
        if not news_items:
            return ""
        
        # 构建新闻列表文本
        news_text = []
        for i, item in enumerate(news_items, 1):
            importance = item.importance
            title = item.title
            content = item.content[:200] if item.content else ""
            news_text.append(f"{i}. [{importance}] {title}\n   {content}")
        
        news_content = "\n\n".join(news_text)
        
        # 构建prompt
        prompt = f"""请为以下关于{stock_name}在{date}的新闻进行总结和分析：

{news_content}

请提供：
1. 核心要点（2-3句话）
2. 重要事件（如有）
3. 对股票可能的影响（简要）

请用简洁、专业的语言回答，不超过200字。"""
        
        try:
            summary = await self._call_api(prompt)
            return summary
        except Exception as e:
            print(f"生成{date}摘要失败: {e}")
            return f"包含{len(news_items)}条消息"
    
    async def generate_period_summary(
        self,
        news_items: List[NewsItem],
        stock_name: str,
        start_date: str,
        end_date: str
    ) -> str:
        """
        生成时段总结
        
        Args:
            news_items: 新闻列表
            stock_name: 股票名称
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            总结文本
        """
        if not news_items:
            return ""
        
        # 统计信息
        total = len(news_items)
        importance_stats = {}
        for item in news_items:
            importance_stats[item.importance] = importance_stats.get(item.importance, 0) + 1
        
        # 提取高重要性新闻
        high_importance = [item for item in news_items if item.importance == "高"][:10]
        
        news_text = []
        for i, item in enumerate(high_importance, 1):
            news_text.append(f"{i}. {item.date.strftime('%Y-%m-%d')} {item.title}")
        
        news_list = "\n".join(news_text) if news_text else "无特别重要的事件"
        
        prompt = f"""请总结{stock_name}在{start_date}至{end_date}期间的重要情况：

统计信息：
- 总消息数：{total}条
- 高重要性：{importance_stats.get('高', 0)}条
- 中重要性：{importance_stats.get('中', 0)}条

重要事件：
{news_list}

请提供：
1. 整体概况（这段时期的主要动态）
2. 关键事件或里程碑（如有）
3. 值得关注的趋势或变化

请用简洁、专业的语言回答，不超过300字。"""
        
        try:
            summary = await self._call_api(prompt)
            return summary
        except Exception as e:
            print(f"生成时段总结失败: {e}")
            return f"该时段包含{total}条消息，其中高重要性{importance_stats.get('高', 0)}条"
    
    async def _call_api(self, prompt: str) -> str:
        """
        调用Qwen API
        
        Args:
            prompt: 提示词
            
        Returns:
            AI回复
        """
        if not self.api_key:
            raise ValueError("需要Qwen API密钥（DashScope API Key）")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的金融分析师，擅长分析股票新闻和公告。请用简洁、专业的语言提供分析。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 800,
            "top_p": 0.8
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.url,
                headers=headers,
                json=data
            )
            
            if response.status_code != 200:
                raise Exception(f"API调用失败: {response.status_code} {response.text}")
            
            result = response.json()
            
            # 解析返回结果
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"].strip()
            else:
                raise Exception(f"无法解析API响应: {result}")
    
    def is_available(self) -> bool:
        """检查是否可用"""
        return self.api_key is not None and len(self.api_key) > 0

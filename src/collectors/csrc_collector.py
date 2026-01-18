"""证监会公告收集器"""
import re
from datetime import datetime, timedelta
from typing import List
import httpx
from bs4 import BeautifulSoup

from .base_collector import BaseCollector, NewsItem


class CSRCCollector(BaseCollector):
    """证监会(CSRC)公告收集器"""
    
    BASE_URL = "http://www.csrc.gov.cn"
    SEARCH_URL = f"{BASE_URL}/csrc/c101981/common_list.shtml"
    
    async def collect(self, days: int = 365) -> List[NewsItem]:
        """
        从证监会网站收集公告
        
        Args:
            days: 收集最近多少天的消息
            
        Returns:
            新闻消息列表
        """
        news_items = []
        start_date = datetime.now() - timedelta(days=days)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 搜索关键词：股票代码或股票名称
                search_keywords = [self.stock_code]
                if self.stock_name:
                    search_keywords.append(self.stock_name)
                
                for keyword in search_keywords:
                    items = await self._search_by_keyword(client, keyword, start_date)
                    news_items.extend(items)
        
        except Exception as e:
            print(f"证监会数据收集失败: {str(e)}")
        
        # 去重
        seen = set()
        unique_items = []
        for item in news_items:
            if item.url not in seen:
                seen.add(item.url)
                unique_items.append(item)
        
        self.news_items = unique_items
        return unique_items
    
    async def _search_by_keyword(
        self, 
        client: httpx.AsyncClient, 
        keyword: str, 
        start_date: datetime
    ) -> List[NewsItem]:
        """通过关键词搜索"""
        items = []
        
        try:
            # 证监会网站搜索逻辑（需要根据实际网站结构调整）
            # 这里提供基本框架
            response = await client.get(
                self.SEARCH_URL,
                params={"keywords": keyword}
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # 根据实际HTML结构解析
                # 示例代码，需要根据实际情况调整
                for article in soup.select('.article-item'):
                    try:
                        title_elem = article.select_one('.title')
                        date_elem = article.select_one('.date')
                        link_elem = article.select_one('a')
                        
                        if not all([title_elem, date_elem, link_elem]):
                            continue
                        
                        title = title_elem.text.strip()
                        date_str = date_elem.text.strip()
                        url = link_elem.get('href', '')
                        
                        if not url.startswith('http'):
                            url = self.BASE_URL + url
                        
                        # 解析日期
                        date = self._parse_date(date_str)
                        if date and date >= start_date:
                            items.append(NewsItem(
                                title=title,
                                date=date,
                                source="证监会",
                                url=url,
                                importance="高",
                                category="监管公告"
                            ))
                    except Exception as e:
                        continue
        
        except Exception as e:
            print(f"搜索关键词 '{keyword}' 失败: {str(e)}")
        
        return items
    
    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        """解析日期字符串"""
        try:
            # 常见日期格式
            formats = [
                '%Y-%m-%d',
                '%Y/%m/%d',
                '%Y年%m月%d日',
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
        except Exception:
            pass
        return None

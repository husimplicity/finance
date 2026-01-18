"""东方财富收集器"""
from datetime import datetime, timedelta
from typing import List
import httpx
import re
from bs4 import BeautifulSoup

from .base_collector import BaseCollector, NewsItem


class EastMoneyCollector(BaseCollector):
    """东方财富消息收集器 - 网页爬虫版本"""
    
    BASE_URL = "https://so.eastmoney.com"
    STOCK_URL = "https://guba.eastmoney.com"
    NEWS_URL = "https://finance.eastmoney.com"
    
    async def collect(self, days: int = 365) -> List[NewsItem]:
        """
        从东方财富收集消息
        
        Args:
            days: 收集最近多少天的消息
            
        Returns:
            新闻消息列表
        """
        news_items = []
        start_date = datetime.now() - timedelta(days=days)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 搜索股票代码和名称
                search_keywords = [self.stock_code]
                if self.stock_name:
                    search_keywords.append(self.stock_name)
                
                for keyword in search_keywords:
                    items = await self._search_news(client, keyword, start_date)
                    news_items.extend(items)
        
        except Exception as e:
            print(f"东方财富数据收集失败: {str(e)}")
        
        # 去重
        seen = set()
        unique_items = []
        for item in news_items:
            if item.url not in seen:
                seen.add(item.url)
                unique_items.append(item)
        
        self.news_items = unique_items
        return unique_items
    
    async def _search_news(
        self, 
        client: httpx.AsyncClient, 
        keyword: str,
        start_date: datetime
    ) -> List[NewsItem]:
        """搜索新闻 - 爬取网页版本"""
        items = []
        
        try:
            # 方法1: 爬取股吧页面
            guba_items = await self._crawl_guba(client, keyword, start_date)
            items.extend(guba_items)
            
            # 方法2: 爬取新闻搜索页面
            search_items = await self._crawl_news_search(client, keyword, start_date)
            items.extend(search_items)
        
        except Exception as e:
            print(f"    东方财富爬取失败: {str(e)}")
        
        return items
    
    async def _crawl_guba(
        self,
        client: httpx.AsyncClient,
        keyword: str,
        start_date: datetime
    ) -> List[NewsItem]:
        """爬取东方财富股吧"""
        items = []
        
        try:
            # 构建股吧URL
            guba_url = f"{self.STOCK_URL}/list,{self.stock_code}.html"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Referer': 'https://guba.eastmoney.com/'
            }
            
            print(f"    正在爬取东方财富股吧: {guba_url}")
            response = await client.get(guba_url, headers=headers)
            print(f"    响应状态: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'lxml')
                
                # 查找帖子列表
                posts = soup.find_all(['div', 'tr'], class_=re.compile(r'articleh|list-item', re.I))
                print(f"    找到 {len(posts)} 个帖子")
                
                for post in posts[:30]:  # 限制数量
                    try:
                        link = post.find('a', href=True)
                        if not link:
                            continue
                        
                        title = link.get_text(strip=True)
                        if not title or len(title) < 5:
                            continue
                        
                        # 过滤掉明显的灌水贴
                        if any(word in title for word in ['。。', '？？', '！！']):
                            continue
                        
                        href = link['href']
                        if not href.startswith('http'):
                            href = self.STOCK_URL + href
                        
                        # 查找日期
                        date_elem = post.find(['span', 'td'], class_=re.compile(r'time|date', re.I))
                        if date_elem:
                            date_text = date_elem.get_text(strip=True)
                            date = self._parse_date(date_text)
                            
                            if date and date >= start_date:
                                # 使用基类方法判断重要性和分类
                                importance = self._judge_importance(title)
                                category = self._judge_category(title)
                                
                                # 如果是股吧帖子且未匹配到特定分类,则标记为社区讨论
                                if category == "其他":
                                    category = "社区讨论"
                                    # 社区讨论类降低一级重要性（除非已经是高）
                                    if importance == "中":
                                        importance = "低"
                                
                                items.append(NewsItem(
                                    title=title,
                                    date=date,
                                    source="东方财富",
                                    url=href,
                                    importance=importance,
                                    category=category
                                ))
                    except Exception:
                        continue
                
                print(f"    从股吧解析到 {len(items)} 条信息")
        
        except Exception as e:
            print(f"    股吧爬取失败: {e}")
        
        return items
    
    async def _crawl_news_search(
        self,
        client: httpx.AsyncClient,
        keyword: str,
        start_date: datetime
    ) -> List[NewsItem]:
        """爬取新闻搜索结果"""
        items = []
        
        try:
            # 搜索URL
            search_url = f"{self.BASE_URL}/news"
            params = {
                'keyword': keyword,
                'type': 'news'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Referer': 'https://so.eastmoney.com/'
            }
            
            print(f"    正在搜索东方财富新闻: {keyword}")
            response = await client.get(search_url, params=params, headers=headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'lxml')
                
                # 查找新闻列表
                news_items = soup.find_all(['div', 'li'], class_=re.compile(r'news-item|result-item', re.I))
                
                for news in news_items[:20]:
                    try:
                        link = news.find('a', href=True)
                        if not link:
                            continue
                        
                        title = link.get_text(strip=True)
                        href = link['href']
                        
                        # 查找日期
                        date_elem = news.find(['span', 'time'], class_=re.compile(r'date|time', re.I))
                        if date_elem:
                            date = self._parse_date(date_elem.get_text(strip=True))
                            if date and date >= start_date:
                                items.append(NewsItem(
                                    title=title,
                                    date=date,
                                    source="东方财富",
                                    url=href,
                                    importance=self._judge_importance(title),
                                    category=self._judge_category(title)
                                ))
                    except Exception:
                        continue
                
                print(f"    从新闻搜索解析到 {len(items)} 条信息")
        
        except Exception as e:
            print(f"    新闻搜索失败: {e}")
        
        return items
    
    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        """解析日期字符串"""
        try:
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M',
                '%Y-%m-%d',
                '%Y/%m/%d',
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
        except Exception:
            pass
        return None

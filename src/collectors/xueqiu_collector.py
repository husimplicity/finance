"""雪球收集器"""
from datetime import datetime, timedelta
from typing import List
import httpx

from .base_collector import BaseCollector, NewsItem


class XueqiuCollector(BaseCollector):
    """雪球消息收集器"""
    
    BASE_URL = "https://xueqiu.com"
    API_URL = "https://stock.xueqiu.com/v5/stock"
    
    async def collect(self, days: int = 365) -> List[NewsItem]:
        """
        从雪球收集消息
        
        Args:
            days: 收集最近多少天的消息
            
        Returns:
            新闻消息列表
        """
        news_items = []
        start_date = datetime.now() - timedelta(days=days)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 获取雪球token
                await self._init_cookies(client)
                
                # 收集公告
                announcements = await self._collect_announcements(client, start_date)
                news_items.extend(announcements)
                
                # 收集热门讨论
                discussions = await self._collect_discussions(client, start_date)
                news_items.extend(discussions)
        
        except Exception as e:
            print(f"雪球数据收集失败: {str(e)}")
        
        self.news_items = news_items
        return news_items
    
    async def _init_cookies(self, client: httpx.AsyncClient):
        """初始化cookies（雪球需要先访问主页）"""
        try:
            await client.get(
                self.BASE_URL,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
        except Exception:
            pass
    
    def _get_symbol(self) -> str:
        """获取雪球股票代码格式"""
        code = self.stock_code
        
        # 上交所：SH开头
        if code.startswith('6'):
            return f"SH{code}"
        # 深交所：SZ开头
        elif code.startswith('0') or code.startswith('3'):
            return f"SZ{code}"
        
        return code
    
    async def _collect_announcements(
        self, 
        client: httpx.AsyncClient, 
        start_date: datetime
    ) -> List[NewsItem]:
        """收集公告"""
        items = []
        
        try:
            symbol = self._get_symbol()
            url = f"{self.API_URL}/announce.json"
            
            params = {
                'symbol': symbol,
                'count': 100,
                'page': 1
            }
            
            response = await client.get(
                url,
                params=params,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                for item in data.get('items', []):
                    try:
                        # 时间戳转换
                        timestamp = item.get('release_time', 0) / 1000
                        date = datetime.fromtimestamp(timestamp)
                        
                        if date >= start_date:
                            items.append(NewsItem(
                                title=item.get('title', ''),
                                date=date,
                                source="雪球-公告",
                                url=self.BASE_URL + item.get('url', ''),
                                importance="高",
                                category="公司公告"
                            ))
                    except Exception:
                        continue
        
        except Exception as e:
            print(f"雪球公告收集失败: {str(e)}")
        
        return items
    
    async def _collect_discussions(
        self, 
        client: httpx.AsyncClient, 
        start_date: datetime
    ) -> List[NewsItem]:
        """收集热门讨论"""
        items = []
        
        try:
            symbol = self._get_symbol()
            url = f"https://xueqiu.com/statuses/stock_timeline.json"
            
            params = {
                'symbol_id': symbol,
                'count': 50,
                'source': 'all'
            }
            
            response = await client.get(
                url,
                params=params,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                for item in data.get('list', []):
                    try:
                        # 只收集高热度讨论
                        if item.get('like_count', 0) < 10:
                            continue
                        
                        timestamp = item.get('created_at', 0) / 1000
                        date = datetime.fromtimestamp(timestamp)
                        
                        if date >= start_date:
                            items.append(NewsItem(
                                title=item.get('title') or item.get('text', '')[:50] + '...',
                                date=date,
                                source="雪球-讨论",
                                url=f"{self.BASE_URL}/status/{item.get('id')}",
                                content=item.get('text', ''),
                                importance="低",
                                category="社区讨论"
                            ))
                    except Exception:
                        continue
        
        except Exception as e:
            print(f"雪球讨论收集失败: {str(e)}")
        
        return items

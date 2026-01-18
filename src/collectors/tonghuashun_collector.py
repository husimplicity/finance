"""同花顺收集器"""
from datetime import datetime, timedelta
from typing import List
import httpx
import re
from bs4 import BeautifulSoup

from .base_collector import BaseCollector, NewsItem


class TongHuaShunCollector(BaseCollector):
    """同花顺消息收集器 - 网页爬虫版本"""
    
    BASE_URL = "http://www.10jqka.com.cn"
    NEWS_URL = "http://news.10jqka.com.cn"
    STOCK_URL = "http://stockpage.10jqka.com.cn"
    
    async def collect(self, days: int = 365) -> List[NewsItem]:
        """
        从同花顺收集消息
        
        Args:
            days: 收集最近多少天的消息
            
        Returns:
            新闻消息列表
        """
        news_items = []
        start_date = datetime.now() - timedelta(days=days)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 获取股票页面新闻
                items = await self._collect_stock_news(client, start_date)
                news_items.extend(items)
        
        except Exception as e:
            print(f"同花顺数据收集失败: {str(e)}")
        
        self.news_items = news_items
        return news_items
    
    async def _collect_stock_news(
        self, 
        client: httpx.AsyncClient, 
        start_date: datetime
    ) -> List[NewsItem]:
        """收集股票相关新闻 - 爬取网页版本"""
        items = []
        
        try:
            # 方法1: 爬取股票个股页面
            stock_url = f"{self.STOCK_URL}/{self.stock_code}/"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Referer': 'http://www.10jqka.com.cn/'
            }
            
            print(f"    正在爬取同花顺个股页面: {stock_url}")
            response = await client.get(stock_url, headers=headers)
            print(f"    响应状态: {response.status_code}")
            
            if response.status_code == 200:
                # 同花顺网站现在使用UTF-8编码
                soup = BeautifulSoup(response.text, 'lxml')
                
                # 查找新闻/公告板块
                news_sections = soup.find_all(['div', 'ul'], class_=re.compile(r'news|notice|announcement|gglist', re.I))
                
                for section in news_sections:
                    news_items = section.find_all(['li', 'a'], limit=30)
                    
                    for news_elem in news_items:
                        try:
                            if news_elem.name == 'a':
                                link = news_elem
                            else:
                                link = news_elem.find('a', href=True)
                            
                            if not link:
                                continue
                            
                            title = link.get_text(strip=True)
                            if not title or len(title) < 5:
                                continue
                            
                            href = link.get('href', '')
                            if not href:
                                continue
                            
                            # 检查标题和URL是否与股票相关
                            if not self._is_relevant(title, href):
                                continue
                            
                            if not href.startswith('http'):
                                if href.startswith('/'):
                                    href = self.BASE_URL + href
                                else:
                                    href = self.BASE_URL + '/' + href
                            
                            # 查找日期
                            date = None
                            
                            # 首先尝试从URL中提取日期（最可靠）
                            url_date_match = re.search(r'/(\d{8})/', href)
                            if url_date_match:
                                date_str = url_date_match.group(1)
                                try:
                                    date = datetime.strptime(date_str, '%Y%m%d')
                                except:
                                    pass
                            
                            # 如果URL中没有，从页面元素中查找
                            if not date:
                                date_elem = news_elem.find(['span', 'em'], class_=re.compile(r'date|time', re.I))
                                if date_elem:
                                    date_str = date_elem.get_text(strip=True)
                                    date = self._parse_date(date_str)
                                else:
                                    # 尝试从文本中提取日期
                                    text = news_elem.get_text()
                                    date_match = re.search(r'(\d{2}-\d{2}|\d{4}-\d{2}-\d{2})', text)
                                    if date_match:
                                        date = self._parse_date(date_match.group(1))
                            
                            if not date:
                                date = datetime.now()  # 如果没有日期，使用当前日期
                            
                            if date >= start_date:
                                items.append(NewsItem(
                                    title=title,
                                    date=date,
                                    source="同花顺",
                                    url=href,
                                    importance=self._judge_importance(title),
                                    category=self._judge_category(title)
                                ))
                        except Exception as e:
                            continue
                
                print(f"    从个股页面解析到 {len(items)} 条信息")
            
            # 方法2: 爬取资讯中心搜索结果
            if len(items) < 5:  # 如果数据太少，补充搜索结果
                search_items = await self._search_news(client, start_date)
                items.extend(search_items)
        
        except Exception as e:
            print(f"    同花顺爬取失败: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return items
    
    async def _search_news(
        self,
        client: httpx.AsyncClient,
        start_date: datetime
    ) -> List[NewsItem]:
        """搜索新闻"""
        items = []
        
        try:
            # 使用同花顺新闻搜索
            keyword = self.stock_name if self.stock_name else self.stock_code
            search_url = f"{self.NEWS_URL}/cjxx/search.html"
            
            params = {
                'keyword': keyword,
                'page': 1
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Referer': 'http://news.10jqka.com.cn/'
            }
            
            print(f"    正在搜索同花顺新闻: {keyword}")
            response = await client.get(search_url, params=params, headers=headers)
            
            if response.status_code == 200:
                # 同花顺网站使用UTF-8编码
                soup = BeautifulSoup(response.text, 'lxml')
                
                news_list = soup.find_all(['li', 'div'], class_=re.compile(r'list|item', re.I), limit=20)
                
                for news in news_list:
                    try:
                        link = news.find('a', href=True)
                        if not link:
                            continue
                        
                        title = link.get_text(strip=True)
                        href = link['href']
                        
                        if not href.startswith('http'):
                            href = self.NEWS_URL + href
                        
                        # 检查标题和URL是否与股票相关
                        if not self._is_relevant(title, href):
                            continue
                        
                        # 查找日期 - 首先尝试从URL中提取
                        date = None
                        url_date_match = re.search(r'/(\d{8})/', href)
                        if url_date_match:
                            try:
                                date = datetime.strptime(url_date_match.group(1), '%Y%m%d')
                            except:
                                pass
                        
                        # 如果URL中没有，从页面元素中查找
                        if not date:
                            date_elem = news.find(['span', 'time'], class_=re.compile(r'date|time', re.I))
                            if date_elem:
                                date = self._parse_date(date_elem.get_text(strip=True))
                        
                        if date and date >= start_date:
                            items.append(NewsItem(
                                title=title,
                                date=date,
                                source="同花顺",
                                url=href,
                                importance=self._judge_importance(title),
                                category=self._judge_category(title)
                            ))
                    except Exception:
                        continue
                
                print(f"    从搜索结果解析到 {len(items)} 条信息")
        
        except Exception as e:
            print(f"    搜索失败: {e}")
        
        return items
    
    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        """解析日期字符串"""
        try:
            # 处理相对时间
            now = datetime.now()
            if '分钟前' in date_str:
                minutes = int(date_str.replace('分钟前', ''))
                return now - timedelta(minutes=minutes)
            elif '小时前' in date_str:
                hours = int(date_str.replace('小时前', ''))
                return now - timedelta(hours=hours)
            elif '天前' in date_str:
                days = int(date_str.replace('天前', ''))
                return now - timedelta(days=days)
            elif '今天' in date_str:
                time_str = date_str.replace('今天', '').strip()
                return datetime.combine(now.date(), datetime.strptime(time_str, '%H:%M').time())
            elif '昨天' in date_str:
                time_str = date_str.replace('昨天', '').strip()
                yesterday = now - timedelta(days=1)
                return datetime.combine(yesterday.date(), datetime.strptime(time_str, '%H:%M').time())
            
            # 标准格式
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M',
                '%Y-%m-%d',
                '%m-%d %H:%M',
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
    
    def _is_relevant(self, title: str, url: str = "") -> bool:
        """
        判断标题和URL是否与该股票相关
        
        Args:
            title: 新闻标题
            url: 新闻URL
            
        Returns:
            是否相关
        """
        # 如果标题包含股票名称或代码，直接返回相关
        if self.stock_name and self.stock_name in title:
            return True
        if self.stock_code in title:
            return True
        
        # 如果URL包含股票代码，也认为相关
        if url and self.stock_code in url:
            return True
        
        # 只排除明确是其他公司的新闻（其他公司为主角）
        # 且标题和URL都不包含本公司信息
        other_companies = [
            '药明生物', '药明康德', '信达生物', '科伦博泰', '百济神州', 
            '恒瑞医药', '复星医药', '石药集团', '君实生物', '康方生物',
            '三生制药', '和黄医药', '基石药业', '再鼎医药', '天境生物',
            '亚盛医药', '贝达药业', '歌礼制药', '前沿生物', '艾力斯',
            '泽璟制药', '诺诚健华', '康宁杰瑞', '迈威生物', '神州细胞',
            '华领医药', '开拓药业', '盟科医药', '永泰生物', '传奇生物',
            '安龙生物', '沃森生物', '智飞生物', '康希诺'
        ]
        
        # 只有当标题以其他公司名开头，且URL也不包含本公司代码时才排除
        for company in other_companies:
            if title.startswith(company):
                # 即使以其他公司开头，如果URL包含本公司代码，也保留（可能是对比新闻）
                if not (url and self.stock_code in url):
                    return False
        
        # 默认相关（宽松过滤，保留行业新闻）
        return True

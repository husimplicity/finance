"""交易所数据采集器 - 使用真实HTML页面抓取"""
from datetime import datetime, timedelta
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup

from .base_collector import BaseCollector, NewsItem


class ExchangeCollector(BaseCollector):
    """交易所数据采集器"""
    
    def __init__(self, stock_code: str, stock_name: str = "", exchange: Optional[str] = None):
        """
        初始化
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            exchange: 交易所类型 ('SSE' 或 'SZSE')，如果不提供则自动判断
        """
        super().__init__(stock_code, stock_name)
        if exchange:
            self.exchange = exchange.upper()
        else:
            self.exchange = self._detect_exchange(stock_code)
    
    @staticmethod
    def _detect_exchange(stock_code: str) -> str:
        """
        根据股票代码自动判断交易所
        
        Args:
            stock_code: 股票代码
            
        Returns:
            'SSE' 或 'SZSE'
        """
        code = stock_code.strip()
        # 移除可能的后缀
        if '.' in code:
            code = code.split('.')[0]
        
        # 上交所: 6开头(主板)，688开头(科创板)
        if code.startswith('6') or code.startswith('688'):
            return 'SSE'
        # 深交所: 0开头(主板)，002开头(中小板)，300开头(创业板)
        elif code.startswith('0') or code.startswith('002') or code.startswith('300'):
            return 'SZSE'
        else:
            # 默认上交所
            return 'SSE'
    
    def get_source_name(self) -> str:
        """获取数据源名称"""
        return "上交所" if self.exchange == 'SSE' else "深交所"
        
    async def collect(self, days: int = 365) -> List[NewsItem]:
        """
        采集数据
        
        Args:
            days: 收集最近多少天的消息
            
        Returns:
            新闻项列表
        """
        start_date = datetime.now() - timedelta(days=days)
        
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            if self.exchange == 'SSE':
                items = await self._collect_sse(client, start_date)
            elif self.exchange == 'SZSE':
                items = await self._collect_szse(client, start_date)
            else:
                items = []
        
        self.news_items = items
        return items
    
    async def _collect_sse(
        self,
        client: httpx.AsyncClient,
        start_date: datetime
    ) -> List[NewsItem]:
        """采集上交所数据 - 使用真实API"""
        items = []
        
        try:
            # 使用真实的公告API
            api_url = "https://query.sse.com.cn/security/stock/queryCompanyBulletinNew.do"
            
            now = datetime.now()
            
            params = {
                'jsonCallBack': 'jsonpCallback',
                'isPagination': 'true',
                'pageHelp.pageSize': '50',
                'pageHelp.cacheSize': '1',
                'pageHelp.pageNo': '1',
                'pageHelp.beginPage': '1',
                'pageHelp.endPage': '1',
                'START_DATE': start_date.strftime('%Y-%m-%d'),
                'END_DATE': now.strftime('%Y-%m-%d'),
                'SECURITY_CODE': self.stock_code,
                'TITLE': '',
                'BULLETIN_TYPE': '',
                '_': str(int(now.timestamp() * 1000))
            }
            
            headers = {
                'Referer': 'https://www.sse.com.cn/',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = await client.get(api_url, params=params, headers=headers, timeout=15.0)
            
            if response.status_code == 200:
                text = response.text
                
                # 提取JSONP数据
                import re
                import json
                match = re.search(r'jsonpCallback\w*\((.*)\)', text)
                
                if match:
                    data = json.loads(match.group(1))
                    result = data.get('result', [])
                    
                    if result:
                        # result可能是列表的列表，需要展平
                        bulletins = []
                        if result and isinstance(result[0], list):
                            for sublist in result:
                                if isinstance(sublist, list):
                                    bulletins.extend(sublist)
                        else:
                            bulletins = result
                        
                        print(f"    上交所API返回 {len(bulletins)} 条公告")
                        
                        for item in bulletins:
                            if not isinstance(item, dict):
                                continue
                            
                            title = item.get('TITLE', '')
                            url_path = item.get('URL', '')
                            date_str = item.get('SSE_DATE', '')
                            
                            if not title:
                                continue
                            
                            # 解析日期
                            try:
                                if date_str:
                                    pub_date = datetime.strptime(date_str[:10], '%Y-%m-%d')
                                else:
                                    pub_date = datetime.now()
                            except Exception:
                                pub_date = datetime.now()
                            
                            # 检查日期范围
                            if pub_date < start_date:
                                continue
                            
                            # 构造完整URL
                            if url_path:
                                if url_path.startswith('//'):
                                    full_url = 'https:' + url_path
                                elif url_path.startswith('/'):
                                    full_url = 'https://www.sse.com.cn' + url_path
                                else:
                                    full_url = url_path
                            else:
                                full_url = f"https://www.sse.com.cn/assortment/stock/list/info/company/index.shtml?COMPANY_CODE={self.stock_code}"
                            
                            news_item = NewsItem(
                                title=title,
                                url=full_url,
                                source="上交所",
                                publish_date=pub_date,
                                importance=self._judge_importance(title),
                                category=self._judge_category(title)
                            )
                            items.append(news_item)
                    else:
                        print("    上交所API返回空数据")
                else:
                    print("    上交所JSONP解析失败")
            else:
                print(f"    上交所API请求失败: {response.status_code}")
                
        except Exception as e:
            print(f"    上交所数据采集失败: {e}")
            import traceback
            traceback.print_exc()
        
        return items
    
    async def _collect_szse(
        self,
        client: httpx.AsyncClient,
        start_date: datetime
    ) -> List[NewsItem]:
        """采集深交所数据"""
        items = []
        
        try:
            # 深交所信息披露API
            url = "http://www.szse.cn/api/disc/announcement/annList"
            
            headers = {
                'Referer': 'http://www.szse.cn/',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Content-Type': 'application/json',
            }
            
            # 格式化日期
            end_date = datetime.now()
            
            data = {
                'seDate': [
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')
                ],
                'stock': [self.stock_code],
                'pageSize': 30,
                'pageNum': 1,
            }
            
            response = await client.post(url, json=data, headers=headers, timeout=10.0)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('data'):
                    announcements = result['data']
                    print(f"    深交所返回 {len(announcements)} 条公告")
                    
                    for item in announcements:
                        title = item.get('title', '') or item.get('announcementTitle', '')
                        
                        # 公告URL
                        attach_path = item.get('attachPath', '') or item.get('pdfPath', '')
                        if attach_path:
                            if attach_path.startswith('http'):
                                pdf_url = attach_path
                            else:
                                pdf_url = f"http://disc.szse.cn{attach_path}"
                        else:
                            pdf_url = ''
                        
                        # 发布时间
                        date_str = item.get('publishTime', '') or item.get('announcementTime', '')
                        
                        try:
                            if date_str:
                                pub_date = datetime.strptime(date_str[:10], '%Y-%m-%d')
                            else:
                                pub_date = datetime.now()
                        except Exception:
                            pub_date = datetime.now()
                        
                        if title:
                            news_item = NewsItem(
                                title=title,
                                url=pdf_url,
                                source="深交所",
                                publish_date=pub_date,
                                importance=self._judge_importance(title),
                                category=self._judge_category(title)
                            )
                            items.append(news_item)
                            
        except Exception as e:
            print(f"    深交所数据采集失败: {e}")
            import traceback
            traceback.print_exc()
        
        return items

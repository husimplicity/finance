"""上交所API数据采集器 - 直接调用API支持分页"""
from datetime import datetime, timedelta
from typing import List
import httpx
import json
import re

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.collectors.base_collector import BaseCollector, NewsItem


class SSEAPICollector(BaseCollector):
    """上交所API数据采集器 - 支持分页"""
    
    def __init__(self, stock_code: str, stock_name: str = ""):
        super().__init__(stock_code, stock_name)
    
    def get_source_name(self) -> str:
        """获取数据源名称"""
        return "上交所"
    
    async def collect(self, days: int = 365) -> List[NewsItem]:
        """采集数据"""
        start_date = datetime.now() - timedelta(days=days)
        items = []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 分页获取数据
                page_size = 50
                max_pages = 20  # 最多获取20页
                
                for page_no in range(1, max_pages + 1):
                    page_items = await self._collect_page(
                        client,
                        start_date,
                        page_no,
                        page_size
                    )
                    
                    if not page_items:
                        break  # 没有更多数据
                    
                    items.extend(page_items)
                    
                    # 检查是否所有数据都早于起始日期
                    if all(item.date < start_date for item in page_items):
                        print(f"    已获取到所需时间范围的数据，停止翻页")
                        break
                    
                    print(f"    已获取第 {page_no} 页，共 {len(items)} 条")
        
        except Exception as e:
            print(f"    上交所数据采集失败: {e}")
            import traceback
            traceback.print_exc()
        
        self.news_items = items
        return items
    
    async def _collect_page(
        self,
        client: httpx.AsyncClient,
        start_date: datetime,
        page_no: int,
        page_size: int
    ) -> List[NewsItem]:
        """采集单页数据"""
        items = []
        
        try:
            url = 'http://query.sse.com.cn/security/stock/queryCompanyBulletinNew.do'
            
            params = {
                'jsonCallBack': f'jsonpCallback{page_no}',
                'isPagination': 'true',
                'pageHelp.pageSize': str(page_size),
                'pageHelp.cacheSize': '1',
                'pageHelp.pageNo': str(page_no),
                'pageHelp.beginPage': str(page_no),
                'pageHelp.endPage': str(page_no + 5),
                'START_DATE': '',
                'END_DATE': '',
                'SECURITY_CODE': self.stock_code,
                'TITLE': '',
                'BULLETIN_TYPE': '',
                '_': str(int(datetime.now().timestamp() * 1000))
            }
            
            headers = {
                'Referer': 'http://www.sse.com.cn/',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = await client.get(url, params=params, headers=headers)
            
            if response.status_code == 200:
                # 移除JSONP包装
                text = response.text
                if 'jsonpCallback' in text:
                    match = re.search(r'jsonpCallback\w*\((.*)\)', text)
                    if match:
                        data = json.loads(match.group(1))
                    else:
                        return items
                else:
                    data = response.json()
                
                # 提取结果 - 数据在pageHelp.data中，是嵌套数组
                page_help = data.get('pageHelp', {})
                data_list = page_help.get('data', [])
                
                # data是二维数组，每个元素又是一个数组
                result = []
                if data_list and isinstance(data_list, list):
                    for item in data_list:
                        if isinstance(item, list):
                            result.extend(item)
                        else:
                            result.append(item)
                
                if page_no == 1:
                    total = page_help.get('total', 0)
                    print(f"    上交所搜索到 {total} 条相关公告")
                
                for item_data in result:
                    try:
                        if not isinstance(item_data, dict):
                            continue
                        
                        title = item_data.get('TITLE', '')
                        date_str = item_data.get('SSEDATE', '')
                        url_path = item_data.get('URL', '')
                        
                        if not title:
                            continue
                        
                        # 解析日期
                        if date_str:
                            try:
                                pub_date = datetime.strptime(date_str[:10], '%Y-%m-%d')
                            except:
                                pub_date = datetime.now()
                        else:
                            # 尝试从URL提取日期
                            if url_path and ('/2025-' in url_path or '/2024-' in url_path):
                                match = re.search(r'/(\d{4}-\d{2}-\d{2})/', url_path)
                                if match:
                                    pub_date = datetime.strptime(match.group(1), '%Y-%m-%d')
                                else:
                                    pub_date = datetime.now()
                            else:
                                pub_date = datetime.now()
                        
                        # 检查日期范围 - 只过滤太旧的数据
                        if pub_date < start_date:
                            continue
                        
                        # 构造完整URL
                        if url_path.startswith('//'):
                            full_url = 'https:' + url_path
                        elif url_path.startswith('/'):
                            full_url = 'https://www.sse.com.cn' + url_path
                        else:
                            full_url = url_path
                        
                        news_item = NewsItem(
                            title=title,
                            url=full_url,
                            source="上交所",
                            date=pub_date,
                            importance=self._judge_importance(title),
                            category=self._judge_category(title)
                        )
                        items.append(news_item)
                    
                    except Exception as e:
                        print(f"    解析单条数据失败: {e}")
                        continue
        
        except Exception as e:
            print(f"    获取第 {page_no} 页失败: {e}")
        
        return items


# 测试函数
async def test_sse_collector():
    """测试上交所采集器"""
    print("="*60)
    print("测试上交所API采集器 - 荣昌生物(688331)")
    print("="*60)
    
    collector = SSEAPICollector(stock_code="688331", stock_name="荣昌生物")
    items = await collector.collect(days=180)
    
    print(f"\n共获取 {len(items)} 条公告\n")
    
    if items:
        print("最新10条公告:")
        for i, item in enumerate(items[:10], 1):
            print(f"{i}. [{item.date.strftime('%Y-%m-%d')}] {item.title[:60]}")
    
    return items


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_sse_collector())

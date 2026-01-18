"""深交所数据采集器 - 使用官方API"""
from datetime import datetime, timedelta
from typing import List
import httpx
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.collectors.base_collector import BaseCollector, NewsItem


class SZSEAPICollector(BaseCollector):
    """深交所API数据采集器"""
    
    def __init__(self, stock_code: str, stock_name: str = ""):
        super().__init__(stock_code, stock_name)
    
    def get_source_name(self) -> str:
        """获取数据源名称"""
        return "深交所"
    
    async def collect(self, days: int = 365) -> List[NewsItem]:
        """采集数据"""
        start_date = datetime.now() - timedelta(days=days)
        items = []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 使用分页获取更多数据
                page_size = 50
                current_page = 1
                max_pages = 10  # 最多获取10页
                
                while current_page <= max_pages:
                    page_items = await self._collect_page(
                        client, 
                        start_date, 
                        current_page, 
                        page_size
                    )
                    
                    if not page_items:
                        break  # 没有更多数据了
                    
                    items.extend(page_items)
                    
                    # 如果这一页数据都早于起始日期，停止获取
                    if all(item.date < start_date for item in page_items):
                        break
                    
                    current_page += 1
                    print(f"    已获取第 {current_page-1} 页，共 {len(items)} 条")
        
        except Exception as e:
            print(f"    深交所数据采集失败: {e}")
            import traceback
            traceback.print_exc()
        
        self.news_items = items
        return items
    
    async def _collect_page(
        self, 
        client: httpx.AsyncClient,
        start_date: datetime,
        current_page: int,
        page_size: int
    ) -> List[NewsItem]:
        """采集单页数据"""
        items = []
        
        try:
            # 使用深交所的搜索API
            url = "https://www.szse.cn/api/search/content"
            
            # API参数
            data = {
                'keyword': self.stock_code,
                'range': 'title',  # 在标题中搜索
                'time': '1',  # 时间范围（1=一年内）
                'orderby': 'time',  # 按时间排序
                'currentPage': str(current_page),
                'pageSize': str(page_size),
                'openChange': 'true',
                'searchtype': '1'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Referer': f'https://www.szse.cn/application/search/index.html?keyword={self.stock_code}',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'X-Requested-With': 'XMLHttpRequest'
            }
            
            response = await client.post(url, data=data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                total_size = result.get('totalSize', 0)
                data_list = result.get('data', [])
                
                if current_page == 1:
                    print(f"    深交所搜索到 {total_size} 条相关记录")
                
                for item_data in data_list:
                    try:
                        # 提取标题（移除HTML标签）
                        title = item_data.get('doctitle', '')
                        title = title.replace('<span class="keyword">', '').replace('</span>', '')
                        title = title.strip()
                        
                        if not title:
                            continue
                        
                        # 提取URL
                        url_path = item_data.get('docpuburl', '')
                        if not url_path:
                            continue
                        
                        # 构造完整URL
                        if url_path.startswith('http'):
                            full_url = url_path
                        elif url_path.startswith('//'):
                            full_url = 'https:' + url_path
                        else:
                            full_url = 'https://www.szse.cn' + url_path
                        
                        # 提取日期 - docpubtime是Unix时间戳（毫秒）
                        timestamp = item_data.get('docpubtime', 0)
                        if timestamp:
                            try:
                                # 转换毫秒时间戳为datetime
                                pub_date = datetime.fromtimestamp(timestamp / 1000)
                            except:
                                pub_date = datetime.now()
                        else:
                            pub_date = datetime.now()
                        
                        # 检查日期范围
                        if pub_date < start_date:
                            continue
                        
                        news_item = NewsItem(
                            title=title,
                            url=full_url,
                            source="深交所",
                            date=pub_date,
                            importance=self._judge_importance(title),
                            category=self._judge_category(title)
                        )
                        items.append(news_item)
                    
                    except Exception as e:
                        print(f"    解析单条数据失败: {e}")
                        continue
        
        except Exception as e:
            print(f"    获取第 {current_page} 页失败: {e}")
        
        return items


# 测试函数
async def test_szse_collector():
    """测试深交所采集器"""
    print("="*60)
    print("测试深交所API采集器 - 万科A(000002)")
    print("="*60)
    
    collector = SZSEAPICollector(stock_code="000002", stock_name="万科A")
    items = await collector.collect(days=180)
    
    print(f"\n共获取 {len(items)} 条公告\n")
    
    if items:
        print("最新10条公告:")
        for i, item in enumerate(items[:10], 1):
            print(f"{i}. [{item.date.strftime('%Y-%m-%d')}] {item.title[:60]}")
            print(f"   {item.url}")
    
    return items


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_szse_collector())

"""使用Playwright的交易所数据采集器"""
from datetime import datetime, timedelta
from typing import List
import asyncio
import re
import json

from playwright.async_api import async_playwright, Page

from .base_collector import BaseCollector, NewsItem


class PlaywrightExchangeCollector(BaseCollector):
    """使用Playwright的交易所数据采集器"""
    
    def __init__(self, stock_code: str, exchange: str, stock_name: str = ""):
        super().__init__(stock_code, stock_name)
        self.exchange = exchange.upper()
    
    def get_source_name(self) -> str:
        """获取数据源名称"""
        return "上交所" if self.exchange == 'SSE' else "深交所"
        
    async def collect(self, days: int = 365) -> List[NewsItem]:
        """采集数据"""
        start_date = datetime.now() - timedelta(days=days)
        
        if self.exchange == 'SSE':
            items = await self._collect_sse(start_date)
        elif self.exchange == 'SZSE':
            items = await self._collect_szse(start_date)
        else:
            items = []
        
        self.news_items = items
        return items
    
    async def _collect_sse(self, start_date: datetime) -> List[NewsItem]:
        """采集上交所数据 - 使用Playwright监听API请求"""
        items = []
        captured_data = []
        
        try:
            async with async_playwright() as p:
                # 使用无头模式
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                
                # 监听API响应
                async def handle_response(response):
                    if 'queryCompanyBulletinNew.do' in response.url:
                        try:
                            text = await response.text()
                            # 提取JSONP数据
                            match = re.search(r'jsonpCallback\w*\((.*)\)', text)
                            if match:
                                data = json.loads(match.group(1))
                                result = data.get('result')
                                if result:
                                    # 处理不同的返回结构
                                    if isinstance(result, list):
                                        # 检查列表元素是否为字典
                                        for item in result:
                                            if isinstance(item, dict):
                                                captured_data.append(item)
                                            elif isinstance(item, list):
                                                # 如果是嵌套列表，展开
                                                captured_data.extend([i for i in item if isinstance(i, dict)])
                                    elif isinstance(result, dict):
                                        captured_data.append(result)
                        except Exception as e:
                            print(f"    解析响应失败: {e}")
                            import traceback
                            traceback.print_exc()
                
                page.on('response', handle_response)
                
                # 访问页面
                url = f"https://www.sse.com.cn/assortment/stock/list/info/company/index.shtml?COMPANY_CODE={self.stock_code}&tabActive=1"
                
                await page.goto(url, wait_until="networkidle", timeout=30000)
                
                # 等待数据加载
                await asyncio.sleep(2)
                
                # 尝试点击"相关公告"标签来触发更多数据加载
                try:
                    await page.click('a[data-id="1"]', timeout=3000)
                    await asyncio.sleep(2)
                except:
                    pass  # 可能已经在该标签页
                
                # 翻页获取更多数据（最多获取10页）
                max_pages = 10
                for page_num in range(2, max_pages + 1):
                    try:
                        # 查找"下一页"按钮或特定页码按钮
                        # 上交所的分页通常使用 class="next" 或类似的选择器
                        next_button = await page.query_selector('.pagination .next:not(.disabled)')
                        if not next_button:
                            # 尝试查找页码链接
                            page_link = await page.query_selector(f'.pagination a:has-text("{page_num}")')
                            if page_link:
                                await page_link.click()
                            else:
                                print(f"    未找到第{page_num}页，停止翻页")
                                break
                        else:
                            await next_button.click()
                        
                        # 等待新数据加载
                        await asyncio.sleep(2)
                        print(f"    已翻到第{page_num}页，继续获取...")
                        
                        # 检查是否已收集足够的历史数据
                        if captured_data:
                            # 检查最旧的数据日期
                            oldest_date = None
                            for item in captured_data:
                                if isinstance(item, dict):
                                    date_str = item.get('SSEDATE', '')
                                    if date_str:
                                        try:
                                            item_date = datetime.strptime(date_str[:10], '%Y-%m-%d')
                                            if oldest_date is None or item_date < oldest_date:
                                                oldest_date = item_date
                                        except:
                                            pass
                            
                            # 如果最旧的数据已经超出时间范围，停止翻页
                            if oldest_date and oldest_date < start_date:
                                print(f"    已获取到 {start_date.strftime('%Y-%m-%d')} 之前的数据，停止翻页")
                                break
                    
                    except Exception as e:
                        print(f"    翻页失败: {e}")
                        break
                
                await browser.close()
            
            # 处理捕获的数据
            print(f"    上交所捕获到 {len(captured_data)} 条公告")
            
            for item in captured_data:
                # 确保item是字典类型
                if not isinstance(item, dict):
                    print(f"    跳过非字典类型数据: {type(item)}")
                    continue
                    
                title = item.get('TITLE', '')
                date_str = item.get('SSEDATE', '')  # 正确的字段名是SSEDATE
                url_path = item.get('URL', '')
                
                if not title:
                    continue
                
                # 解析日期
                try:
                    if date_str:
                        pub_date = datetime.strptime(date_str[:10], '%Y-%m-%d')
                    else:
                        # 如果没有日期，尝试从URL中提取
                        if url_path and '/2025-' in url_path or '/2024-' in url_path:
                            match = re.search(r'/(\d{4}-\d{2}-\d{2})/', url_path)
                            if match:
                                pub_date = datetime.strptime(match.group(1), '%Y-%m-%d')
                            else:
                                pub_date = datetime.now()
                        else:
                            pub_date = datetime.now()
                except Exception as e:
                    print(f"    日期解析失败: {date_str}, {e}")
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
                    full_url = url
                
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
            print(f"    上交所数据采集失败: {e}")
            import traceback
            traceback.print_exc()
        
        return items
    
    async def _collect_szse(self, start_date: datetime) -> List[NewsItem]:
        """采集深交所数据"""
        items = []
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                
                # 深交所信息披露页面
                url = f"http://www.szse.cn/disclosure/listed/fixed/index.html?stock={self.stock_code}"
                
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(2)
                
                # 等待表格加载
                try:
                    await page.wait_for_selector('table', timeout=5000)
                    
                    # 提取表格数据
                    rows = await page.query_selector_all('table tbody tr')
                    
                    print(f"    深交所找到 {len(rows)} 行数据")
                    
                    for row in rows:
                        try:
                            cells = await row.query_selector_all('td')
                            if len(cells) >= 3:
                                # 通常格式: 日期 | 公告标题 | 相关公告
                                date_elem = cells[0]
                                title_elem = await cells[1].query_selector('a')
                                
                                if title_elem:
                                    title = await title_elem.inner_text()
                                    href = await title_elem.get_attribute('href')
                                    date_text = await date_elem.inner_text()
                                    
                                    # 解析日期
                                    try:
                                        pub_date = datetime.strptime(date_text.strip(), '%Y-%m-%d')
                                    except:
                                        pub_date = datetime.now()
                                    
                                    # 检查日期范围
                                    if pub_date < start_date:
                                        continue
                                    
                                    # 构造完整URL
                                    if href:
                                        if href.startswith('http'):
                                            full_url = href
                                        else:
                                            full_url = f"http://www.szse.cn{href}"
                                    else:
                                        full_url = url
                                    
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
                            continue
                            
                except Exception as e:
                    print(f"    等待表格失败: {e}")
                
                await browser.close()
                
        except Exception as e:
            print(f"    深交所数据采集失败: {e}")
            import traceback
            traceback.print_exc()
        
        return items

"""北京证券交易所（北交所）数据采集器"""
from datetime import datetime, timedelta
from typing import List
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

from .base_collector import BaseCollector, NewsItem


class BSECollector(BaseCollector):
    """北交所消息收集器 - 通过搜索页面抓取"""
    
    BASE_URL = "https://www.bse.cn"
    SEARCH_URL = "https://www.bse.cn/select/index/searchInfo.do"
    
    async def collect(self, days: int = 365) -> List[NewsItem]:
        """
        从北交所收集消息
        
        Args:
            days: 收集最近多少天的消息
            
        Returns:
            新闻消息列表
        """
        news_items = []
        start_date = datetime.now() - timedelta(days=days)
        
        try:
            # 使用Playwright抓取JavaScript渲染的页面
            async with async_playwright() as p:
                # 启动浏览器（使用headless模式）
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                
                try:
                    # 使用股票名称搜索（股票名称通常更准确）
                    if self.stock_name:
                        items = await self._search_with_playwright(page, self.stock_name, start_date)
                        news_items.extend(items)
                    
                    # 如果没有找到结果，尝试股票代码
                    if not news_items and self.stock_code:
                        items = await self._search_with_playwright(page, self.stock_code, start_date)
                        news_items.extend(items)
                
                finally:
                    await browser.close()
        
        except Exception as e:
            print(f"北交所数据收集失败: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # 去重
        seen = set()
        unique_items = []
        for item in news_items:
            if item.url not in seen:
                seen.add(item.url)
                unique_items.append(item)
        
        self.news_items = unique_items
        return unique_items
    
    async def _search_with_playwright(
        self,
        page,
        keyword: str,
        start_date: datetime,
        max_pages: int = 10
    ) -> List[NewsItem]:
        """使用Playwright搜索新闻"""
        items = []
        
        try:
            print(f"    正在搜索北交所: {keyword}")
            
            # 访问搜索页面
            await page.goto(self.BASE_URL, wait_until='networkidle', timeout=30000)
            
            # 等待iframe加载
            await page.wait_for_timeout(2000)
            
            # 在iframe中的搜索框输入关键词
            iframe = page.frame_locator('iframe').first
            search_box = iframe.locator('input[placeholder*="搜"]').first
            await search_box.fill(keyword)
            await search_box.press('Enter')
            
            # 等待页面跳转到搜索结果页
            await page.wait_for_url('**/searchInfo.do', timeout=10000)
            await page.wait_for_timeout(2000)
            
            # 点击时间排序
            try:
                time_sort = page.locator('text=时间排序').first
                await time_sort.click()
                await page.wait_for_timeout(2000)
            except:
                print("    未找到时间排序按钮，使用默认排序")
            
            # 抓取当前页
            page_items = await self._extract_items_from_page(page, start_date)
            items.extend(page_items)
            print(f"    第1页获取 {len(page_items)} 条")
            
            # 翻页
            for page_num in range(2, max_pages + 1):
                try:
                    # 检查是否还有下一页
                    next_button = page.locator('text=">"|text="下一页"').first
                    
                    # 检查按钮是否可见
                    is_visible = await next_button.is_visible(timeout=2000)
                    if not is_visible:
                        print(f"    已到最后一页")
                        break
                    
                    # 点击下一页
                    await next_button.click(timeout=5000)
                    await page.wait_for_timeout(2000)
                    
                    # 抓取页面
                    page_items = await self._extract_items_from_page(page, start_date)
                    items.extend(page_items)
                    print(f"    第{page_num}页获取 {len(page_items)} 条")
                    
                    # 如果没有找到符合日期的，停止翻页
                    if len([item for item in page_items if item.date >= start_date]) == 0:
                        print(f"    第{page_num}页无符合日期的数据，停止翻页")
                        break
                
                except Exception as e:
                    # 可能已经是最后一页
                    print(f"    翻页结束或出错: {type(e).__name__}")
                    break
        
        except Exception as e:
            print(f"    搜索失败: {e}")
            import traceback
            traceback.print_exc()
        
        return items
    
    async def _extract_items_from_page(self, page, start_date: datetime) -> List[NewsItem]:
        """从当前页面提取新闻项"""
        items = []
        
        try:
            # 获取页面HTML
            html = await page.content()
            soup = BeautifulSoup(html, 'lxml')
            
            # 查找quotationTable中的所有结果项
            quotation_table = soup.find('div', id='quotationTable')
            if not quotation_table:
                print("    未找到quotationTable")
                return items
            
            # 每个结果在 div.main-show 中
            result_divs = quotation_table.find_all('div', class_='main-show')
            
            for result_div in result_divs:
                try:
                    # 查找标题链接 - 在tit-cell中
                    tit_cell = result_div.find('div', class_='tit-cell')
                    if not tit_cell:
                        continue
                    
                    link = tit_cell.find('a', href=True)
                    if not link:
                        continue
                    
                    # 获取标题 - 在p.tit1的title属性中
                    title_p = link.find('p', class_='tit1')
                    if title_p and title_p.get('title'):
                        title = title_p.get('title').strip()
                    else:
                        # 备用：从链接文本提取
                        title_text = link.get_text(strip=True)
                        # 移除末尾的日期
                        title = re.sub(r'\s*\d{4}[-/]\d{1,2}[-/]\d{1,2}\s*$', '', title_text).strip()
                    
                    if not title:
                        continue
                    
                    # 获取URL
                    href = link.get('href', '')
                    if not href:
                        continue
                    
                    # 处理相对URL
                    if not href.startswith('http'):
                        href = urljoin(self.BASE_URL, href)
                    
                    # 查找日期 - 在span.time中
                    date_span = result_div.find('span', class_=re.compile(r'time', re.I))
                    if date_span:
                        date_str = date_span.get_text(strip=True)
                    else:
                        date_str = None
                    
                    # 解析日期
                    pub_date = self._parse_date(date_str) if date_str else datetime.now()
                    
                    # 只添加符合日期范围的
                    if pub_date < start_date:
                        continue
                    
                    # 判断重要性和分类
                    importance = self._judge_importance(title)
                    category = self._judge_category(title)
                    
                    news_item = NewsItem(
                        title=title,
                        date=pub_date,
                        source="北交所",
                        url=href,
                        importance=importance,
                        category=category
                    )
                    items.append(news_item)
                
                except Exception as e:
                    # 单条解析失败不影响其他条目
                    continue
        
        except Exception as e:
            print(f"    提取页面内容失败: {e}")
        
        return items
    
    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        """解析日期字符串"""
        if not date_str:
            return datetime.now()
        
        try:
            # 清理日期字符串
            date_str = date_str.strip()
            
            # 尝试多种日期格式
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M',
                '%Y-%m-%d',
                '%Y/%m/%d',
                '%Y年%m月%d日',
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            # 如果都不匹配，尝试提取日期部分
            date_match = re.search(r'(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})', date_str)
            if date_match:
                year, month, day = date_match.groups()
                return datetime(int(year), int(month), int(day))
        
        except Exception:
            pass
        
        return datetime.now()

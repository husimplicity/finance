"""
东方财富公告API收集器
通过官方API收集股票公告信息
"""
import httpx
import json
import re
from urllib.parse import quote
from datetime import datetime, timedelta
from typing import List, Dict
from .base_collector import BaseCollector, NewsItem

class EastmoneyAPICollector(BaseCollector):
    """东方财富公告API收集器"""
    
    def __init__(self, stock_code: str, stock_name: str):
        super().__init__(stock_code, stock_name)
        self.source_name = "东方财富"
    
    async def collect(self, days: int = 30) -> List[NewsItem]:
        """收集东方财富公告"""
        results = []
        start_date = datetime.now() - timedelta(days=days)
        stock_name = self.stock_name
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            page_index = 1
            page_size = 20
            total_count = 0
            
            while True:
                # 构建参数
                param = {
                    "uid": "",
                    "keyword": stock_name,
                    "type": ["noticeWeb"],
                    "client": "web",
                    "clientVersion": "curr",
                    "clientType": "web",
                    "param": {
                        "noticeWeb": {
                            "preTag": "<em class=\"red\">",
                            "postTag": "</em>",
                            "pageSize": page_size,
                            "pageIndex": page_index
                        }
                    }
                }
                
                # URL编码参数
                param_str = json.dumps(param, separators=(',', ':'), ensure_ascii=False)
                param_encoded = quote(param_str, safe='')
                
                timestamp = str(int(datetime.now().timestamp() * 1000))
                url = f"https://search-api-web.eastmoney.com/search/jsonp?cb=jQuery&param={param_encoded}&_={timestamp}"
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    'Referer': f'https://so.eastmoney.com/ann/s?keyword={quote(stock_name)}'
                }
                
                try:
                    print(f"正在获取第 {page_index} 页...")
                    response = await client.get(url, headers=headers)
                    text = response.text
                    
                    # 解析JSONP响应
                    # jQuery(...) 格式
                    json_start = text.find('(')
                    json_end = text.rfind(')')
                    if json_start == -1 or json_end == -1:
                        print(f"无法解析响应格式")
                        break
                    
                    json_str = text[json_start + 1:json_end]
                    data = json.loads(json_str)
                    
                    if data.get('code') != 0:
                        print(f"API返回错误: {data.get('msg')}")
                        break
                    
                    hits_total = data.get('hitsTotal', 0)
                    if page_index == 1:
                        total_count = hits_total
                        print(f"{self.source_name}搜索到 {total_count} 条相关公告")
                    
                    notices = data.get('result', {}).get('noticeWeb', [])
                    if not notices:
                        break
                    
                    page_results = []
                    for notice in notices:
                        try:
                            # 解析日期
                            date_str = notice.get('date', '')  # "2025-11-25 00:00:00"
                            pub_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                            
                            # 检查日期范围
                            if pub_date < start_date:
                                print(f"已获取第 {page_index} 页，共 {len(page_results)} 条（已到达时间边界）")
                                results.extend(page_results)
                                return results
                            
                            # 清理标题（移除HTML标签）
                            title = notice.get('title', '')
                            title = re.sub(r'<[^>]+>', '', title)
                            
                            # 获取URL
                            url = notice.get('url', '')
                            
                            # 清理内容（移除HTML标签）
                            content = notice.get('content', '')
                            content = re.sub(r'<[^>]+>', '', content)
                            
                            news_item = NewsItem(
                                title=title,
                                url=url,
                                date=pub_date,
                                source=self.source_name,
                                importance=self._judge_importance(title),
                                content=content[:100] if content else ""
                            )
                            
                            page_results.append(news_item)
                            
                        except Exception as e:
                            print(f"解析公告失败: {e}, 数据: {notice}")
                            continue
                    
                    print(f"已获取第 {page_index} 页，共 {len(page_results)} 条")
                    results.extend(page_results)
                    
                    # 检查是否还有更多页
                    if len(results) >= hits_total:
                        break
                    
                    page_index += 1
                    
                except Exception as e:
                    print(f"请求失败: {e}")
                    break
        
        return results

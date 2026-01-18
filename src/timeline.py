"""时间线整理模块"""
from datetime import datetime
from typing import List, Dict, Optional
from collections import defaultdict
import json
import asyncio
import re

from .collectors.base_collector import NewsItem
from .ai_summarizer import AISummarizer


class Timeline:
    """时间线管理器"""
    
    def __init__(self, stock_code: str, stock_name: str = "", ai_api_key: Optional[str] = None, ai_model: str = "qwen-plus"):
        """
        初始化时间线
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            ai_api_key: Qwen API密钥（可选，用于生成摘要）
            ai_model: Qwen模型名称（默认qwen-plus）
        """
        self.stock_code = stock_code
        self.stock_name = stock_name
        self.news_items: List[NewsItem] = []
        self.ai_summarizer = AISummarizer(api_key=ai_api_key, model=ai_model) if ai_api_key else None
        self.daily_summaries: Dict[str, str] = {}  # 存储每日摘要
        self.period_summary: str = ""  # 存储时段总结
    
    def add_news(self, news_items: List[NewsItem]):
        """
        添加新闻到时间线
        
        Args:
            news_items: 新闻列表
        """
        self.news_items.extend(news_items)
    
    def sort(self, reverse: bool = True):
        """
        按时间排序
        
        Args:
            reverse: True为降序（最新在前），False为升序
        """
        self.news_items.sort(key=lambda x: x.date, reverse=reverse)
    
    def filter_by_importance(self, importance: str) -> List[NewsItem]:
        """
        按重要性筛选
        
        Args:
            importance: 重要性级别（高、中、低）
            
        Returns:
            筛选后的新闻列表
        """
        return [item for item in self.news_items if item.importance == importance]
    
    def filter_by_category(self, category: str) -> List[NewsItem]:
        """
        按分类筛选
        
        Args:
            category: 分类名称
            
        Returns:
            筛选后的新闻列表
        """
        return [item for item in self.news_items if item.category == category]
    
    def filter_by_source(self, source: str) -> List[NewsItem]:
        """
        按来源筛选
        
        Args:
            source: 来源名称
            
        Returns:
            筛选后的新闻列表
        """
        return [item for item in self.news_items if item.source == source]
    
    def get_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[NewsItem]:
        """
        获取指定日期范围的新闻
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            新闻列表
        """
        return [
            item for item in self.news_items 
            if start_date <= item.date <= end_date
        ]
    
    @staticmethod
    def _markdown_to_html(text: str) -> str:
        """将Markdown格式转换为HTML"""
        if not text:
            return text
        
        # 转换 **粗体** 为 <strong>粗体</strong>
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        
        # 转换换行为 <br>
        text = text.replace('\n', '<br>\n')
        
        return text
    
    def group_by_date(self) -> Dict[str, List[NewsItem]]:
        """
        按日期分组
        
        Returns:
            日期为键，新闻列表为值的字典
        """
        grouped = defaultdict(list)
        for item in self.news_items:
            date_key = item.date.strftime('%Y-%m-%d')
            grouped[date_key].append(item)
        return dict(grouped)
    
    def group_by_month(self) -> Dict[str, List[NewsItem]]:
        """
        按月份分组
        
        Returns:
            月份为键，新闻列表为值的字典
        """
        grouped = defaultdict(list)
        for item in self.news_items:
            month_key = item.date.strftime('%Y-%m')
            grouped[month_key].append(item)
        return dict(grouped)
    
    def get_statistics(self) -> Dict:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        if not self.news_items:
            return {
                'total': 0,
                'sources': {},
                'categories': {},
                'importance': {}
            }
        
        sources = defaultdict(int)
        categories = defaultdict(int)
        importance = defaultdict(int)
        
        for item in self.news_items:
            sources[item.source] += 1
            if item.category:
                categories[item.category] += 1
            importance[item.importance] += 1
        
        return {
            'total': len(self.news_items),
            'sources': dict(sources),
            'categories': dict(categories),
            'importance': dict(importance),
            'date_range': {
                'start': min(item.date for item in self.news_items).strftime('%Y-%m-%d'),
                'end': max(item.date for item in self.news_items).strftime('%Y-%m-%d')
            }
        }
    
    async def generate_summaries(self):
        """
        生成AI摘要（每日摘要和时段总结）
        """
        if not self.ai_summarizer or not self.ai_summarizer.is_available():
            print("AI摘要功能未启用（需要API密钥）")
            return
        
        if not self.news_items:
            print("没有新闻数据，无法生成摘要")
            return
        
        print("\n正在生成AI摘要...")
        
        # 生成每日摘要
        grouped = self.group_by_date()
        total_days = len(grouped)
        
        for i, (date, items) in enumerate(sorted(grouped.items(), reverse=True), 1):
            print(f"  生成{date}的摘要... ({i}/{total_days})")
            try:
                summary = await self.ai_summarizer.generate_daily_summary(
                    date=date,
                    news_items=items,
                    stock_name=self.stock_name or self.stock_code
                )
                self.daily_summaries[date] = summary
            except Exception as e:
                print(f"    失败: {e}")
        
        # 生成时段总结
        print("  生成时段总结...")
        try:
            stats = self.get_statistics()
            start_date = stats['date_range']['start']
            end_date = stats['date_range']['end']
            
            self.period_summary = await self.ai_summarizer.generate_period_summary(
                news_items=self.news_items,
                stock_name=self.stock_name or self.stock_code,
                start_date=start_date,
                end_date=end_date
            )
        except Exception as e:
            print(f"    失败: {e}")
        
        print(f"✓ 摘要生成完成\n")
    
    def to_dict(self) -> Dict:
        """
        转换为字典格式
        
        Returns:
            字典格式的时间线数据
        """
        return {
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'statistics': self.get_statistics(),
            'timeline': [
                {
                    'date': item.date.strftime('%Y-%m-%d %H:%M:%S'),
                    'title': item.title,
                    'source': item.source,
                    'url': item.url,
                    'importance': item.importance,
                    'category': item.category,
                    'content': item.content
                }
                for item in self.news_items
            ]
        }
    
    def to_json(self, filepath: str = None) -> str:
        """
        转换为JSON格式
        
        Args:
            filepath: 如果提供，将保存到文件
            
        Returns:
            JSON字符串
        """
        data = self.to_dict()
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(json_str)
        
        return json_str
    
    def to_markdown(self, filepath: str = None) -> str:
        """
        转换为Markdown格式
        
        Args:
            filepath: 如果提供，将保存到文件
            
        Returns:
            Markdown字符串
        """
        lines = []
        
        # 标题
        title = f"# {self.stock_name}({self.stock_code}) 消息时间线\n\n"
        lines.append(title)
        
        # 统计信息
        stats = self.get_statistics()
        lines.append("## 统计信息\n\n")
        lines.append(f"- 总消息数: {stats['total']}\n")
        lines.append(f"- 时间范围: {stats.get('date_range', {}).get('start', 'N/A')} ~ {stats.get('date_range', {}).get('end', 'N/A')}\n")
        lines.append(f"- 数据来源: {', '.join(stats['sources'].keys())}\n\n")
        
        # 时段总结（如果有AI摘要）
        if self.period_summary:
            lines.append("## 📊 时段总结\n\n")
            lines.append(f"{self.period_summary}\n\n")
        
        # 按日期分组的时间线
        lines.append("## 时间线\n\n")
        grouped = self.group_by_date()
        
        for date in sorted(grouped.keys(), reverse=True):
            items = grouped[date]
            lines.append(f"### {date}\n\n")
            
            # 添加每日AI摘要
            if date in self.daily_summaries:
                lines.append(f"**📝 每日摘要:** {self.daily_summaries[date]}\n\n")
            
            for item in items:
                importance_emoji = {
                    '高': '🔴',
                    '中': '🟡',
                    '低': '⚪'
                }.get(item.importance, '⚪')
                
                lines.append(f"{importance_emoji} **[{item.source}]** [{item.title}]({item.url})\n")
                if item.category:
                    lines.append(f"   - 分类: {item.category}\n")
                if item.content:
                    content_preview = item.content[:100] + '...' if len(item.content) > 100 else item.content
                    lines.append(f"   - 摘要: {content_preview}\n")
                lines.append("\n")
        
        markdown = ''.join(lines)
        
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(markdown)
        
        return markdown
    
    def to_html(self, filepath: str = None) -> str:
        """
        转换为HTML格式
        
        Args:
            filepath: 如果提供，将保存到文件
            
        Returns:
            HTML字符串
        """
        html_lines = []
        
        # HTML头部
        html_lines.append("""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{} 消息时间线</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            margin: 0;
        }}
        .stats {{
            display: flex;
            gap: 20px;
            margin-top: 15px;
            flex-wrap: wrap;
        }}
        .stat-item {{
            background-color: #f8f9fa;
            padding: 10px 15px;
            border-radius: 4px;
        }}
        .timeline {{
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .date-group {{
            margin-bottom: 30px;
        }}
        .date-header {{
            font-size: 1.2em;
            font-weight: bold;
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 5px;
            margin-bottom: 15px;
        }}
        .news-item {{
            padding: 15px;
            border-left: 3px solid #ddd;
            margin-bottom: 15px;
            background-color: #fafafa;
        }}
        .news-item.high {{
            border-left-color: #e74c3c;
        }}
        .news-item.medium {{
            border-left-color: #f39c12;
        }}
        .news-item.low {{
            border-left-color: #95a5a6;
        }}
        .news-title {{
            font-size: 1.1em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }}
        .news-title a {{
            color: #3498db;
            text-decoration: none;
        }}
        .news-title a:hover {{
            text-decoration: underline;
        }}
        .news-meta {{
            color: #7f8c8d;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        .news-content {{
            margin-top: 10px;
            color: #555;
            font-size: 0.95em;
        }}
        .source-badge {{
            display: inline-block;
            background-color: #3498db;
            color: white;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 0.85em;
            margin-right: 10px;
        }}
        .summary-section {{
            background-color: #e8f4f8;
            border-left: 4px solid #3498db;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 4px;
        }}
        .summary-title {{
            font-size: 1.1em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
        }}
        .summary-title::before {{
            content: "📊";
            margin-right: 8px;
            font-size: 1.2em;
        }}
        .summary-content {{
            color: #34495e;
            line-height: 1.8;
            white-space: pre-wrap;
        }}
        .daily-summary {{
            background-color: #fff9e6;
            border-left: 3px solid #f39c12;
            padding: 12px;
            margin-bottom: 15px;
            border-radius: 4px;
        }}
        .daily-summary-title {{
            font-weight: bold;
            color: #e67e22;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
        }}
        .daily-summary-title::before {{
            content: "📝";
            margin-right: 6px;
        }}
        .daily-summary-content {{
            color: #555;
            line-height: 1.6;
        }}
    </style>
</head>
<body>
""".format(f"{self.stock_name}({self.stock_code})"))
        
        # 统计信息
        stats = self.get_statistics()
        html_lines.append(f"""
    <div class="header">
        <h1>{self.stock_name}({self.stock_code}) 消息时间线</h1>
        <div class="stats">
            <div class="stat-item">总消息数: {stats['total']}</div>
            <div class="stat-item">时间范围: {stats.get('date_range', {}).get('start', 'N/A')} ~ {stats.get('date_range', {}).get('end', 'N/A')}</div>
        </div>
    </div>
""")
        
        # 时段总结（如果有AI摘要）
        if self.period_summary:
            html_lines.append("""
    <div class="summary-section">
        <div class="summary-title">时段总结</div>
        <div class="summary-content">{}</div>
    </div>
""".format(self._markdown_to_html(self.period_summary)))
        
        # 时间线
        html_lines.append('    <div class="timeline">\n')
        grouped = self.group_by_date()
        
        for date in sorted(grouped.keys(), reverse=True):
            items = grouped[date]
            html_lines.append(f'        <div class="date-group">\n')
            html_lines.append(f'            <div class="date-header">{date}</div>\n')
            
            # 添加每日AI摘要
            if date in self.daily_summaries:
                html_lines.append(f"""            <div class="daily-summary">
                <div class="daily-summary-title">每日摘要</div>
                <div class="daily-summary-content">{self._markdown_to_html(self.daily_summaries[date])}</div>
            </div>
""")
            
            for item in items:
                importance_class = {
                    '高': 'high',
                    '中': 'medium',
                    '低': 'low'
                }.get(item.importance, 'low')
                
                html_lines.append(f'            <div class="news-item {importance_class}">\n')
                html_lines.append(f'                <div class="news-title">\n')
                html_lines.append(f'                    <span class="source-badge">{item.source}</span>\n')
                html_lines.append(f'                    <a href="{item.url}" target="_blank">{item.title}</a>\n')
                html_lines.append(f'                </div>\n')
                
                if item.category:
                    html_lines.append(f'                <div class="news-meta">分类: {item.category} | 重要性: {item.importance}</div>\n')
                
                if item.content:
                    content_preview = item.content[:200] + '...' if len(item.content) > 200 else item.content
                    html_lines.append(f'                <div class="news-content">{content_preview}</div>\n')
                
                html_lines.append(f'            </div>\n')
            
            html_lines.append(f'        </div>\n')
        
        html_lines.append('    </div>\n')
        html_lines.append('</body>\n</html>')
        
        html = ''.join(html_lines)
        
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html)
        
        return html

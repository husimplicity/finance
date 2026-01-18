"""基础收集器抽象类"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class NewsItem:
    """新闻消息数据结构"""
    title: str
    date: datetime
    source: str
    url: str
    content: Optional[str] = None
    importance: str = "中"  # 高、中、低
    category: Optional[str] = None
    
    def __str__(self):
        return f"[{self.date.strftime('%Y-%m-%d')}] {self.title} - {self.source}"


class BaseCollector(ABC):
    """消息收集器基类"""
    
    def __init__(self, stock_code: str, stock_name: str = ""):
        """
        初始化收集器
        
        Args:
            stock_code: 股票代码，如 "600519" 或 "000001.SZ"
            stock_name: 股票名称
        """
        self.stock_code = self._normalize_code(stock_code)
        self.stock_name = stock_name
        self.news_items: List[NewsItem] = []
    
    @staticmethod
    def _normalize_code(code: str) -> str:
        """标准化股票代码"""
        code = code.strip()
        # 移除可能的后缀
        if '.' in code:
            code = code.split('.')[0]
        return code
    
    @abstractmethod
    async def collect(self, days: int = 365) -> List[NewsItem]:
        """
        收集新闻消息
        
        Args:
            days: 收集最近多少天的消息
            
        Returns:
            新闻消息列表
        """
        pass
    
    def get_source_name(self) -> str:
        """获取数据源名称"""
        return self.__class__.__name__.replace('Collector', '')
    
    def _judge_importance(self, title: str) -> str:
        """
        根据标题判断消息重要性
        
        Args:
            title: 消息标题
            
        Returns:
            "高"、"中"、"低"
        """
        title_upper = title.upper()
        
        # 先检查是否包含本公司名称/代码
        is_directly_related = False
        if self.stock_name and self.stock_name in title:
            is_directly_related = True
        if self.stock_code in title:
            is_directly_related = True
        
        # 不相关新闻的关键词（其他公司、行业泛泛而谈）
        irrelevant_keywords = [
            '暗盘', '战争', '界商业', '行业观察', '市场盘点',
            '十大', '排行', '榜单', '集锦', '盘点'
        ]
        
        # 其他公司名称（如果标题主要讲其他公司）
        other_companies = [
            '瑞博生物', '药明生物', '药明康德', '信达生物', '科伦博泰', '百济神州',
            '恒瑞医药', '复星医药', '石药集团', '君实生物', '康方生物'
        ]
        
        # 如果标题中包含其他公司且不包含本公司，判定为不相关
        has_other_company = any(company in title for company in other_companies)
        if has_other_company and not is_directly_related:
            return "低"
        
        # 检查不相关关键词
        for keyword in irrelevant_keywords:
            if keyword in title:
                return "低"
        
        # 财务报告类始终为高重要性（无论是否直接相关，因为这些是官方公告）
        financial_report_keywords = [
            '年报', '中报', '季报', '财报', '业绩预告', '业绩快报',
            '定期报告', '一季度报告', '三季度报告', '半年度报告', '年度报告'
        ]
        for keyword in financial_report_keywords:
            if keyword in title:
                return "高"
        
        # 高重要性关键词（只对直接相关的新闻有效）
        if is_directly_related:
            high_keywords = [
                '重大', '处罚', '调查', '立案', '停牌', '复牌', '退市',
                '重组', '并购', '收购', '增发', '配股', '分红', '送股',
                '业绩', '预告', '快报',
                '违规', '违法', '诉讼', '仲裁', '风险', '警示',
                '董事会', '股东大会', '股权', '控股', '变更',
                '亏损', '盈利', '扭亏', '减持', '增持', '回购'
            ]
            
            for keyword in high_keywords:
                if keyword in title or keyword in title_upper:
                    return "高"
        
        # 低重要性关键词
        low_keywords = [
            '广告', '推广', '营销', '宣传', '点评', '评论',
            '讨论', '猜测', '预测', '传闻', '网友', '据说'
        ]
        
        for keyword in low_keywords:
            if keyword in title or keyword in title_upper:
                return "低"
        
        # 如果不是直接相关的新闻，默认为低重要性
        if not is_directly_related:
            return "低"
        
        return "中"
    
    def _judge_category(self, title: str) -> str:
        """
        根据标题判断消息分类
        
        Args:
            title: 消息标题
            
        Returns:
            分类字符串
        """
        title_upper = title.upper()
        
        # 公司治理
        if any(kw in title for kw in ['董事会', '股东大会', '监事会', '高管', '任命', '辞职', '选举']):
            return "公司治理"
        
        # 财务报告
        if any(kw in title for kw in ['年报', '中报', '季报', '业绩', '财报', '快报', '预告']):
            return "财务报告"
        
        # 股权变动
        if any(kw in title for kw in ['股权', '增持', '减持', '回购', '股份', '解禁', '质押']):
            return "股权变动"
        
        # 重大事项
        if any(kw in title for kw in ['重组', '并购', '收购', '出售', '投资', '合作', '签约']):
            return "重大事项"
        
        # 监管信息
        if any(kw in title for kw in ['处罚', '调查', '立案', '违规', '问询', '关注函', '警示']):
            return "监管信息"
        
        # 交易提示
        if any(kw in title for kw in ['停牌', '复牌', '退市', '风险', '提示', '公告']):
            return "交易提示"
        
        # 经营动态
        if any(kw in title for kw in ['中标', '项目', '产品', '研发', '技术', '专利', '订单']):
            return "经营动态"
        
        # 市场评论
        if any(kw in title for kw in ['点评', '分析', '解读', '观点', '评论', '讨论']):
            return "市场评论"
        
        return "其他"

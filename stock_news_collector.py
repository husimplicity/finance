"""股票消息收集器主程序"""
import asyncio
import argparse
import sys
from datetime import datetime
from pathlib import Path

from src.collectors import (
    CSRCCollector,
    PlaywrightExchangeCollector,
    EastMoneyCollector,
    TongHuaShunCollector,
    XueqiuCollector,
    BSECollector
)
from src.collectors.szse_api_collector import SZSEAPICollector
from src.collectors.sse_api_collector import SSEAPICollector
from src.collectors.eastmoney_api_collector import EastmoneyAPICollector
from src.timeline import Timeline


async def collect_stock_news(
    stock_code: str,
    stock_name: str = "",
    days: int = 365,
    output_format: str = "markdown",
    output_file: str = None,
    ai_api_key: str = None,
    ai_model: str = "qwen-plus",
    enable_ai_summary: bool = False
):
    """
    收集股票公开消息并生成时间线
    
    Args:
        stock_code: 股票代码
        stock_name: 股票名称（可选）
        days: 收集最近多少天的消息
        output_format: 输出格式（markdown/json/html）
        output_file: 输出文件路径
        ai_api_key: Qwen API密钥（可选）
        ai_model: Qwen模型名称
        enable_ai_summary: 是否启用AI摘要
    """
    print(f"\n{'='*60}")
    print(f"开始收集股票 {stock_name}({stock_code}) 的公开消息")
    print(f"时间范围: 最近 {days} 天")
    print(f"{'='*60}\n")
    
    # 创建时间线
    timeline = Timeline(
        stock_code, 
        stock_name, 
        ai_api_key=ai_api_key if enable_ai_summary else None,
        ai_model=ai_model
    )
    
    # 判断交易所
    code = stock_code.strip().split('.')[0]
    is_bse = code.startswith('4') or code.startswith('8')  # 北交所：4xxxxx或8xxxxx
    
    if is_bse:
        # 北交所股票
        exchange = 'BSE'
        exchange_collector = BSECollector(stock_code, stock_name)
        collectors = [
            CSRCCollector(stock_code, stock_name),
            exchange_collector,
            EastmoneyAPICollector(stock_code, stock_name),
            TongHuaShunCollector(stock_code, stock_name),
            XueqiuCollector(stock_code, stock_name)
        ]
    elif code.startswith('6') or code.startswith('688'):
        # 上交所股票
        exchange = 'SSE'
        exchange_collector = SSEAPICollector(stock_code, stock_name)
        collectors = [
            CSRCCollector(stock_code, stock_name),
            exchange_collector,
            EastmoneyAPICollector(stock_code, stock_name),
            TongHuaShunCollector(stock_code, stock_name),
            XueqiuCollector(stock_code, stock_name)
        ]
    else:
        # 深交所股票
        exchange = 'SZSE'
        exchange_collector = SZSEAPICollector(stock_code, stock_name)
        collectors = [
            CSRCCollector(stock_code, stock_name),
            exchange_collector,
            EastmoneyAPICollector(stock_code, stock_name),
            TongHuaShunCollector(stock_code, stock_name),
            XueqiuCollector(stock_code, stock_name)
        ]
    
    # 并发收集数据
    print("正在从多个数据源收集消息...\n")
    tasks = []
    for collector in collectors:
        source_name = collector.get_source_name()
        print(f"  - {source_name}: 开始收集...")
        tasks.append(collector.collect(days))
    
    # 等待所有任务完成
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 处理结果
    total_news = 0
    for i, result in enumerate(results):
        collector = collectors[i]
        source_name = collector.get_source_name()
        
        if isinstance(result, Exception):
            print(f"  - {source_name}: ❌ 失败 - {str(result)}")
        elif result is None:
            print(f"  - {source_name}: ⚠️  无返回数据")
        else:
            count = len(result)
            total_news += count
            print(f"  - {source_name}: ✓ 成功收集 {count} 条消息")
            timeline.add_news(result)
    
    print(f"\n总共收集到 {total_news} 条消息")
    
    # 去重
    print("正在去重和整理...")
    # 简单去重：基于URL
    seen_urls = set()
    unique_items = []
    for item in timeline.news_items:
        if item.url not in seen_urls:
            seen_urls.add(item.url)
            unique_items.append(item)
    
    timeline.news_items = unique_items
    print(f"去重后剩余 {len(unique_items)} 条消息\n")
    
    # 排序
    timeline.sort(reverse=True)
    
    # 生成AI摘要（如果启用）
    if enable_ai_summary and ai_api_key:
        await timeline.generate_summaries()
    
    # 显示统计信息
    stats = timeline.get_statistics()
    print(f"{'='*60}")
    print("统计信息:")
    print(f"  - 总消息数: {stats['total']}")
    if stats.get('date_range'):
        print(f"  - 时间范围: {stats['date_range']['start']} ~ {stats['date_range']['end']}")
    print(f"  - 数据来源分布:")
    for source, count in stats['sources'].items():
        print(f"    * {source}: {count} 条")
    print(f"  - 重要性分布:")
    for importance, count in stats['importance'].items():
        print(f"    * {importance}: {count} 条")
    print(f"{'='*60}\n")
    
    # 生成输出
    if not output_file:
        # 自动生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        ext = {'markdown': 'md', 'json': 'json', 'html': 'html'}.get(output_format, 'txt')
        output_file = f"timeline_{stock_code}_{timestamp}.{ext}"
    
    print(f"正在生成 {output_format} 格式的时间线...")
    
    if output_format == 'markdown':
        timeline.to_markdown(output_file)
    elif output_format == 'json':
        timeline.to_json(output_file)
    elif output_format == 'html':
        timeline.to_html(output_file)
    else:
        print(f"不支持的输出格式: {output_format}")
        return
    
    print(f"✓ 时间线已保存到: {output_file}\n")
    
    # 显示部分内容预览
    print("最新消息预览:")
    print("-" * 60)
    for i, item in enumerate(timeline.news_items[:5], 1):
        print(f"{i}. [{item.date.strftime('%Y-%m-%d')}] {item.title}")
        print(f"   来源: {item.source} | 重要性: {item.importance}")
        print()
    
    if len(timeline.news_items) > 5:
        print(f"... 还有 {len(timeline.news_items) - 5} 条消息")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='股票公开消息收集和时间线生成工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 收集贵州茅台最近一年的消息
  python main.py 600519 -n 贵州茅台
  
  # 收集平安银行最近180天的消息，输出为HTML
  python main.py 000001 -n 平安银行 -d 180 -f html
  
  # 指定输出文件
  python main.py 600519 -n 贵州茅台 -o timeline.md
        """
    )
    
    parser.add_argument(
        'stock_code',
        help='股票代码，如 600519 或 000001'
    )
    
    parser.add_argument(
        '-n', '--name',
        dest='stock_name',
        default='',
        help='股票名称（可选）'
    )
    
    parser.add_argument(
        '-d', '--days',
        type=int,
        default=365,
        help='收集最近多少天的消息（默认365天）'
    )
    
    parser.add_argument(
        '-f', '--format',
        choices=['markdown', 'json', 'html'],
        default='markdown',
        help='输出格式（默认markdown）'
    )
    
    parser.add_argument(
        '-o', '--output',
        dest='output_file',
        help='输出文件路径（可选，默认自动生成）'
    )
    
    parser.add_argument(
        '--ai-summary',
        action='store_true',
        help='启用AI摘要生成（需要Qwen API密钥）'
    )
    
    parser.add_argument(
        '--api-key',
        dest='api_key',
        help='Qwen API密钥（从环境变量QWEN_API_KEY或DASHSCOPE_API_KEY读取，或通过此参数指定）'
    )
    
    parser.add_argument(
        '--model',
        dest='model',
        default='qwen-plus',
        help='Qwen模型名称（默认qwen-plus，可选qwen-turbo/qwen-max等）'
    )
    
    args = parser.parse_args()
    
    # 获取API密钥（支持多个环境变量）
    import os
    api_key = args.api_key or os.environ.get('QWEN_API_KEY') or os.environ.get('DASHSCOPE_API_KEY')
    
    # 运行异步任务
    try:
        asyncio.run(collect_stock_news(
            stock_code=args.stock_code,
            stock_name=args.stock_name,
            days=args.days,
            output_format=args.format,
            output_file=args.output_file,
            ai_api_key=api_key,
            ai_model=args.model,
            enable_ai_summary=args.ai_summary
        ))
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

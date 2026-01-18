# 股票消息收集器

一个功能强大的股票公开消息自动收集和分析工具，支持AI智能摘要生成。

## ✨ 主要特性

- 🔍 **多数据源收集**：整合上交所、深交所、东方财富、同花顺等多个数据源
- 📊 **智能去重**：自动去除重复消息，确保信息准确
- 🎯 **重要性评级**：自动判断消息重要程度（高/中/低）
- 📈 **时间线整理**：按时间顺序组织消息，清晰展现股票动态
- 🤖 **AI智能摘要**：使用免费AI API生成每日摘要和时段总结（新功能）
- 📝 **多格式输出**：支持Markdown、JSON、HTML多种输出格式

## 🚀 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate  # Windows

# 安装依赖
pip install httpx playwright beautifulsoup4
```

### 2. 基本使用

```bash
# 收集股票消息（不带AI摘要）
python stock_news_collector.py 688331 -n 荣昌生物 --days 30

# 收集并生成AI摘要（需要Qwen API密钥）
export QWEN_API_KEY="sk-your-api-key"
python stock_news_collector.py 688331 -n 荣昌生物 --days 30 --ai-summary
```

### 3. 查看结果

生成的时间线文件（Markdown格式）将自动保存到当前目录，包含：
- 统计信息
- 时段总结（如启用AI）
- 按日期组织的消息列表
- 每日摘要（如启用AI）

## 📖 详细文档

- **[完整使用指南](USAGE_GUIDE.md)** - 详细的命令行参数和使用示例
- **[AI摘要功能说明](AI_SUMMARY_README.md)** - 如何获取和使用免费AI API

## 💡 使用示例

### 场景1：快速查看最近动态

```bash
python stock_news_collector.py 000002 -n 万科A --days 30
```

### 场景2：深度分析半年情况（带AI摘要）

```bash
python stock_news_collector.py 688331 -n 荣昌生物 --days 180 --ai-summary
```

### 场景3：导出为JSON格式

```bash
python stock_news_collector.py 603259 -n 药明康德 --days 90 -f json
```

## 📊 数据来源

| 数据源 | 类型 | 覆盖范围 | 特点 |
|--------|------|----------|------|
| 上交所 | 官方公告 | 上交所股票 | 权威、完整 |
| 深交所 | 官方公告 | 深交所股票 | 权威、完整 |
| 东方财富 | 公告搜索 | 全市场 | 数据量大、查询便捷 |
| 同花顺 | 新闻资讯 | 全市场 | 时效性强 |

## 🤖 AI摘要功能

### API获取 - 阿里云灵积（DashScope）

1. 访问 [阿里云灵积](https://dashscope.aliyun.com/) 开通服务（新用户免费额度）
2. 获取API密钥（格式：sk-xxx）
3. 设置环境变量或使用 `--api-key` 参数

**优势**：通义千问（Qwen）系列模型，中文理解能力强，响应快速

### 生成内容

- **时段总结**：整体概况、关键事件、趋势分析
- **每日摘要**：核心要点、重要事件、影响评估

### 使用示例

```bash
# 设置API密钥
export QWEN_API_KEY="sk-xxx"

# 启用AI摘要（默认使用qwen-plus模型）
python stock_news_collector.py 688331 -n 荣昌生物 --days 30 --ai-summary

# 使用更快的模型
python stock_news_collector.py 688331 -n 荣昌生物 --days 30 --ai-summary --model qwen-turbo

# 使用最高质量模型
python stock_news_collector.py 688331 -n 荣昌生物 --days 30 --ai-summary --model qwen-max
```
python stock_news_collector.py 688331 -n 荣昌生物 --days 30 --ai-summary
```

## 📁 项目结构

```
finance/
├── stock_news_collector.py    # 主程序
├── src/
│   ├── collectors/            # 数据收集器
│   │   ├── sse_api_collector.py       # 上交所
│   │   ├── szse_api_collector.py      # 深交所
│   │   ├── eastmoney_api_collector.py # 东方财富
│   │   └── tonghuashun_collector.py   # 同花顺
│   ├── timeline.py            # 时间线管理
│   └── ai_summarizer.py       # AI摘要生成（Qwen）
├── USAGE_GUIDE.md            # 使用指南
├── AI_SUMMARY_README.md      # AI功能说明
└── demo_ai_summary.py        # AI功能演示
```

## 🛠️ 高级功能

### 自定义时间范围

```bash
python stock_news_collector.py 688331 -n 荣昌生物 --days 180
```

### 指定输出文件

```bash
python stock_news_collector.py 688331 -n 荣昌生物 --days 30 -o my_timeline.md
```

### 批量处理

```bash
# 创建批处理脚本
for code in 688331 000002 603259; do
    python stock_news_collector.py $code --days 180 --ai-summary
    sleep 5
done
```

## 📈 性能指标

### 数据量（以万科A为例，180天）

- 收集消息：300-1000+ 条
- 去重后：200-900+ 条
- 数据源：3-4个

### 处理时间

- 基础收集：30-60秒
- AI摘要生成：额外1-3分钟

## ⚠️ 注意事项

1. **数据时效**：数据来自公开渠道，存在一定延迟
2. **API限制**：注意API调用频率，避免被限流
3. **网络依赖**：需要稳定的网络连接
4. **AI摘要**：仅供参考，不构成投资建议

## 🔧 故障排除

### 常见问题

**Q: 东方财富收集失败？**
A: 检查网络连接，稍后重试或减少天数

**Q: AI摘要未生成？**
A: 确认已添加 `--ai-summary` 参数且API密钥正确

**Q: 数据量很少？**
A: 可能该股票确实新闻较少，或扩大天数范围

详见 [完整故障排除指南](USAGE_GUIDE.md#故障排除)

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- 感谢各数据源提供的公开数据
- 感谢硅基流动提供的免费AI API

## 📮 联系方式

- 项目地址：[GitHub仓库]
- 问题反馈：[创建Issue]

---

**免责声明**：本工具仅用于信息收集和整理，所有数据来自公开渠道。AI生成的摘要仅供参考，不构成任何投资建议。投资有风险，决策需谨慎。

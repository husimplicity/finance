# 股票消息收集器

一个功能强大的股票公开消息自动收集和分析工具，支持**北交所、上交所、深交所**三大交易所，集成AI智能摘要生成。

## ✨ 主要特性

- 🏛️ **全市场覆盖**：支持北交所、上交所、深交所三大交易所全部股票
- 🔍 **多数据源收集**：整合官方交易所、东方财富、同花顺、雪球等多个数据源
- 🚀 **北交所专属**：使用Playwright技术处理动态网页，完美支持北交所公告采集
- 📊 **智能去重**：自动去除重复消息，确保信息准确
- 🎯 **重要性评级**：自动判断消息重要程度（高/中/低），财务报告自动标为高重要性
- 📈 **时间线整理**：按时间顺序组织消息，清晰展现股票动态
- 🤖 **AI智能摘要**：使用阿里云通义千问API生成每日摘要和时段总结
- 📝 **多格式输出**：支持Markdown、JSON、HTML多种输出格式

## 🚀 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境（推荐使用uv）
uv venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate  # Windows

# 安装依赖
uv pip install httpx playwright beautifulsoup4 lxml

# 安装Playwright浏览器（用于北交所数据采集）
playwright install chromium
```

### 2. 基本使用

```bash
# 示例1：收集北交所股票（锦波生物）
python stock_news_collector.py 832982 -n 锦波生物 --days 90

# 示例2：收集上交所股票（荣昌生物）
python stock_news_collector.py 688331 -n 荣昌生物 --days 30

# 示例3：生成HTML格式报告
python stock_news_collector.py 832982 -n 锦波生物 --days 90 --format html

# 示例4：启用AI摘要（需要Qwen API密钥）
export DASHSCOPE_API_KEY="sk-your-api-key"
python stock_news_collector.py 832982 -n 锦波生物 --days 90 --format html --ai-summary
```

### 3. 查看结果

生成的时间线文件将自动保存到当前目录：

- **Markdown格式** (`.md`)：纯文本，方便阅读和分享
- **HTML格式** (`.html`)：网页样式，支持浏览器直接打开，带颜色标记
- **JSON格式** (`.json`)：结构化数据，便于程序处理

**包含内容：**
- 📊 统计信息（消息数量、时间范围、数据来源分布）
- 🎯 时段总结（如启用AI）
- 📅 按日期组织的消息列表（带重要性标记）
- 💡 每日摘要（如启用AI）

## 📖 详细文档

- **[快速开始指南](QUICKSTART.md)** - 5分钟上手指南
- **[完整使用指南](USAGE_GUIDE.md)** - 详细的命令行参数和使用示例
- **[AI摘要功能说明](AI_SUMMARY_README.md)** - 如何获取和使用通义千问API
- **[北交所采集器说明](BSE_COLLECTOR_README.md)** - 北交所数据采集技术细节
- **[HTML输出功能](HTML_AI_SUMMARY.md)** - HTML格式报告说明

## 💡 使用示例

### 场景1：快速查看北交所股票最近动态

```bash
python stock_news_collector.py 832982 -n 锦波生物 --days 30
```

### 场景2：深度分析上交所股票（带AI摘要和HTML输出）

```bash
export DASHSCOPE_API_KEY="sk-your-api-key"
python stock_news_collector.py 688331 -n 荣昌生物 --days 90 --format html --ai-summary
```

### 场景3：导出深交所股票数据为JSON格式

```bash
python stock_news_collector.py 000002 -n 万科A --days 180 -f json
```

### 场景4：批量收集多只股票

```bash
#!/bin/bash
export DASHSCOPE_API_KEY="sk-your-api-key"

# 北交所
python stock_news_collector.py 832982 -n 锦波生物 --days 90 --format html --ai-summary

# 上交所
python stock_news_collector.py 688331 -n 荣昌生物 --days 90 --format html --ai-summary

# 深交所
python stock_news_collector.py 000002 -n 万科A --days 90 --format html --ai-summary
```

## 📊 数据来源

| 数据源 | 类型 | 覆盖范围 | 特点 | 技术 |
|--------|------|----------|------|------|
| 北交所 | 官方公告 | 北交所股票 | 权威、完整 | Playwright动态渲染 |
| 上交所 | 官方公告 | 上交所股票 | 权威、完整 | API接口 |
| 深交所 | 官方公告 | 深交所股票 | 权威、完整 | API接口 |
| 东方财富 | 公告搜索 | 全市场 | 数据量大、查询便捷 | API接口 |
| 同花顺 | 新闻资讯 | 全市场 | 时效性强、内容丰富 | 网页爬取 |
| 雪球 | 社交讨论 | 全市场 | 市场情绪、用户观点 | API接口 |
| CSRC | 监管公告 | 全市场 | 重大事项、监管动态 | 网页爬取 |

**股票代码识别：**
- 北交所：4xxxxx（老三板精选层）、8xxxxx（北交所新股）
- 上交所：6xxxxx、688xxx（科创板）
- 深交所：0xxxxx、002xxx（中小板）、300xxx（创业板）

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
│   ├── collectors/             # 数据收集器
│   │   ├── bse_collector.py            # 北交所（使用Playwright）
│   │   ├── sse_api_collector.py        # 上交所
│   │   ├── szse_api_collector.py       # 深交所
│   │   ├── eastmoney_api_collector.py  # 东方财富
│   │   ├── tonghuashun_collector.py    # 同花顺
│   │   ├── xueqiu_collector.py         # 雪球
│   │   ├── csrc_collector.py           # 证监会
│   │   └── base_collector.py           # 基础类
│   ├── timeline.py             # 时间线管理
│   └── ai_summarizer.py        # AI摘要生成（通义千问）
├── QUICKSTART.md               # 快速开始
├── USAGE_GUIDE.md              # 使用指南
├── AI_SUMMARY_README.md        # AI功能说明
├── BSE_COLLECTOR_README.md     # 北交所采集器说明
├── HTML_AI_SUMMARY.md          # HTML输出功能
└── pyproject.toml              # 项目配置
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

### 数据量（以锦波生物为例，90天）

- 收集消息：60+ 条（原始）
- 去重后：54 条
- 数据源：5个（北交所、东方财富、同花顺、CSRC、雪球）
- 重要性分布：高14条、中34条、低6条

### 处理时间

- 北交所数据收集：20-40秒（Playwright渲染）
- 其他数据源收集：10-30秒
- AI摘要生成：1-3分钟（13个日期）
- 总计：约3-5分钟（含AI摘要）

## ⚠️ 注意事项

1. **数据时效**：数据来自公开渠道，存在一定延迟
2. **API限制**：注意API调用频率，避免被限流
3. **网络依赖**：需要稳定的网络连接
4. **浏览器依赖**：北交所数据采集需要Playwright浏览器支持
5. **AI摘要**：仅供参考，不构成投资建议
6. **重要性判断**：财务报告（年报、季报等）自动标记为高重要性

## 🔧 故障排除

### 常见问题

**Q: 北交所数据收集失败？**
A: 确保已安装Playwright浏览器：`playwright install chromium`

**Q: 东方财富收集失败？**
A: 检查网络连接，稍后重试或减少天数

**Q: AI摘要未生成？**
A: 确认已添加 `--ai-summary` 参数且API密钥正确（DASHSCOPE_API_KEY或QWEN_API_KEY）

**Q: 数据量很少？**
A: 可能该股票确实新闻较少，或扩大天数范围

**Q: 三季度报告标记为中重要性？**
A: 已修复，所有财务报告（年报、中报、季报）现在都自动标记为高重要性

详见 [完整故障排除指南](USAGE_GUIDE.md#故障排除)

## 🤝 贡献

欢迎提交Issue和Pull Request！

**贡献指南：**
1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- 感谢各数据源提供的公开数据
- 感谢阿里云灵积（DashScope）提供的通义千问API
- 感谢Playwright项目提供的浏览器自动化工具

## 📮 联系方式

- 项目地址：[https://github.com/husimplicity/finance](https://github.com/husimplicity/finance)
- 问题反馈：[创建Issue](https://github.com/husimplicity/finance/issues)

## 🌟 Star History

如果这个项目对你有帮助，请给个⭐️支持一下！

---

**免责声明**：本工具仅用于信息收集和整理，所有数据来自公开渠道。AI生成的摘要仅供参考，不构成任何投资建议。投资有风险，决策需谨慎。

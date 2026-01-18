# 股票消息收集器 - 完整使用指南

## 功能概览

本工具可以自动收集股票的公开消息，包括：
- 交易所公告（上交所、深交所）
- 东方财富公告搜索
- 同花顺新闻
- 生成按时间线组织的报告
- **【新增】AI智能摘要生成**

## 数据来源

1. **上海证券交易所（SSE）** - 上交所股票（6/688开头）
2. **深圳证券交易所（SZSE）** - 深交所股票（0/3开头）
3. **东方财富** - 全市场公告搜索
4. **同花顺** - 补充新闻和资讯

## 基本使用

### 1. 简单收集（不带AI摘要）

```bash
# 收集荣昌生物最近30天的消息
python stock_news_collector.py 688331 -n 荣昌生物 --days 30

# 收集万科A最近180天的消息
python stock_news_collector.py 000002 -n 万科A --days 180

# 收集药明康德最近一年的消息
python stock_news_collector.py 603259 -n 药明康德 --days 365
```

### 2. 带AI摘要收集（推荐）

#### 步骤1：获取免费API密钥

访问 [硅基流动](https://siliconflow.cn) 注册并获取免费API密钥。

#### 步骤2：设置环境变量

**macOS/Linux:**
```bash
export SILICONFLOW_API_KEY="your-api-key-here"
```

**Windows (PowerShell):**
```powershell
$env:SILICONFLOW_API_KEY="your-api-key-here"
```

#### 步骤3：运行带摘要的收集

```bash
# 添加 --ai-summary 参数启用AI摘要
python stock_news_collector.py 688331 -n 荣昌生物 --days 30 --ai-summary

# 或者直接在命令中指定API密钥
python stock_news_collector.py 688331 -n 荣昌生物 --days 30 --ai-summary --api-key "your-key"
```

## 命令行参数说明

```
必需参数:
  stock_code              股票代码（如 688331, 000002）

可选参数:
  -n, --name             股票名称
  -d, --days             收集天数（默认365天）
  -f, --format           输出格式: markdown, json, html（默认markdown）
  -o, --output           指定输出文件路径
  --ai-summary           启用AI摘要生成
  --api-key              AI API密钥（也可从环境变量读取）
```

## 输出文件

### 不带AI摘要的输出

```markdown
# 荣昌生物(688331) 消息时间线

## 统计信息
- 总消息数: 68
- 时间范围: 2025-11-03 ~ 2025-11-30
- 数据来源: 同花顺, 上交所, 东方财富

## 时间线

### 2025-11-30

🔴 **[上交所]** [关于XX的公告](url)
   - 摘要: ...

🟡 **[东方财富]** [XX消息](url)
   - 摘要: ...
```

### 带AI摘要的输出

```markdown
# 荣昌生物(688331) 消息时间线

## 统计信息
- 总消息数: 68
- 时间范围: 2025-11-03 ~ 2025-11-30
- 数据来源: 同花顺, 上交所, 东方财富

## 📊 时段总结

【AI生成的时段总结】
荣昌生物在2025年11月整体表现...主要关注点包括...
值得注意的趋势...

## 时间线

### 2025-11-30

**📝 每日摘要:** 【AI生成】本日荣昌生物披露了...核心要点...

🔴 **[上交所]** [关于XX的公告](url)
   - 摘要: ...

🟡 **[东方财富]** [XX消息](url)
   - 摘要: ...
```

## 实际使用示例

### 场景1：快速了解最近动态

```bash
# 收集最近30天，快速查看
python stock_news_collector.py 688331 -n 荣昌生物 --days 30
```

### 场景2：深度分析半年情况

```bash
# 收集180天，启用AI摘要深度分析
python stock_news_collector.py 688331 -n 荣昌生物 --days 180 --ai-summary
```

### 场景3：批量处理多只股票

```bash
#!/bin/bash
# 批量收集脚本 collect_batch.sh

stocks=(
    "688331:荣昌生物"
    "000002:万科A"
    "603259:药明康德"
)

for stock in "${stocks[@]}"; do
    code="${stock%%:*}"
    name="${stock##*:}"
    echo "正在收集 ${name} (${code})..."
    python stock_news_collector.py "${code}" -n "${name}" --days 180 --ai-summary
    sleep 5  # 避免API请求过快
done
```

## AI摘要特性

### 每日摘要内容

- **核心要点**：当天2-3句话总结
- **重要事件**：筛选高重要性事件
- **影响分析**：简要评估对股票的可能影响

### 时段总结内容

- **整体概况**：时间段内的主要动态
- **关键事件**：重要公告和里程碑
- **趋势分析**：值得关注的变化

## 性能说明

### 数据量（以万科A为例，180天）

- 上交所/深交所：100+ 条公告
- 东方财富：数百至上千条
- 同花顺：20-50 条新闻
- **总计**：300-1000+ 条消息

### 处理时间

- 不带AI摘要：30-60秒
- 带AI摘要：
  - 基础收集：30-60秒
  - AI摘要生成：额外1-3分钟（取决于天数）

## 注意事项

1. **数据时效性**：数据来自公开渠道，存在一定延迟
2. **数据完整性**：已覆盖主要数据源，但可能遗漏部分信息
3. **AI摘要**：AI生成内容仅供参考，不构成投资建议
4. **API限制**：注意API调用额度，避免短时间大量请求
5. **网络依赖**：需要稳定的网络连接

## 故障排除

### 问题：东方财富收集失败

**可能原因**：网络问题或API限流

**解决方法**：
```bash
# 稍后重试，或减少天数
python stock_news_collector.py 688331 -n 荣昌生物 --days 30
```

### 问题：AI摘要未生成

**检查清单**：
1. 是否添加了 `--ai-summary` 参数？
2. API密钥是否正确设置？
3. 网络是否能访问API服务？

**测试方法**：
```bash
# 打印环境变量检查
echo $SILICONFLOW_API_KEY

# 或使用命令行直接指定
python stock_news_collector.py 688331 -n 荣昌生物 --days 7 --ai-summary --api-key "your-key"
```

### 问题：收集到的数据很少

**可能原因**：
- 时间范围内确实没有太多公告
- 该股票较冷门，新闻较少
- 数据源暂时不可用

**解决方法**：
- 扩大天数范围
- 检查股票代码是否正确
- 查看各数据源的具体错误信息

## 高级用法

### 自定义输出格式

```bash
# 输出为JSON格式
python stock_news_collector.py 688331 -n 荣昌生物 --days 30 -f json -o output.json

# 输出为HTML格式
python stock_news_collector.py 688331 -n 荣昌生物 --days 30 -f html -o output.html
```

### 定时自动收集

**使用crontab（Linux/macOS）：**
```bash
# 编辑crontab
crontab -e

# 每天晚上10点收集
0 22 * * * cd /path/to/finance && .venv/bin/python stock_news_collector.py 688331 -n 荣昌生物 --days 30 --ai-summary
```

**使用Task Scheduler（Windows）：**
创建计划任务，运行：
```
python C:\path\to\stock_news_collector.py 688331 -n 荣昌生物 --days 30 --ai-summary
```

## 更多信息

- AI摘要功能详细说明：[AI_SUMMARY_README.md](AI_SUMMARY_README.md)
- 项目源码：`src/` 目录
- 问题反馈：创建Issue

## 免责声明

本工具仅用于信息收集和整理，所有数据来自公开渠道。AI生成的摘要仅供参考，不构成任何投资建议。投资有风险，决策需谨慎。

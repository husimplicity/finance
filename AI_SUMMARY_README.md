# AI摘要功能使用说明

## 功能介绍

新增AI摘要功能，可以为收集的股票新闻自动生成：
1. **每日摘要**：总结每天的重要新闻和事件
2. **时段总结**：分析整个时间段的趋势和关键事件

## API获取 - 阿里云灵积（DashScope）

### 获取步骤

1. 访问 [阿里云灵积模型服务](https://dashscope.aliyun.com/)
2. 登录/注册阿里云账号（免费）
3. 开通灵积模型服务（DashScope）
4. 进入控制台，创建API Key
5. 复制API密钥（格式：sk-xxx）

**优势**：
- 新用户赠送免费额度（百万tokens）
- 使用阿里云通义千问系列模型（Qwen）
- 高质量中文理解和生成能力
- 响应速度快，稳定性好
- API兼容OpenAI格式

### 可选模型

- **qwen-turbo**：速度快，适合大批量处理
- **qwen-plus**：平衡性能和质量（推荐）
- **qwen-max**：最高质量，适合深度分析
- **qwen-long**：超长上下文支持

## 使用方法

### 方法一：环境变量（推荐）

```bash
# 设置API密钥到环境变量
export QWEN_API_KEY="sk-your-api-key-here"
# 或使用
export DASHSCOPE_API_KEY="sk-your-api-key-here"

# 运行时添加 --ai-summary 参数
python stock_news_collector.py 000002 -n 万科A --days 180 --ai-summary

# 指定模型（可选）
python stock_news_collector.py 000002 -n 万科A --days 180 --ai-summary --model qwen-max
```

### 方法二：命令行参数

```bash
# 直接在命令行指定API密钥
python stock_news_collector.py 000002 -n 万科A --days 180 --ai-summary --api-key "sk-xxx"

# 同时指定模型
python stock_news_collector.py 000002 -n 万科A --days 180 --ai-summary --api-key "sk-xxx" --model qwen-turbo
```

## 示例

### 生成带AI摘要的时间线

```bash
# 收集万科A最近180天的消息，生成AI摘要
python stock_news_collector.py 000002 -n 万科A --days 180 --ai-summary

# 收集荣昌生物最近180天的消息，生成AI摘要
python stock_news_collector.py 688331 -n 荣昌生物 --days 180 --ai-summary
```

### 不使用AI摘要（默认）

```bash
# 不添加 --ai-summary 参数，不会生成摘要
python stock_news_collector.py 000002 -n 万科A --days 180
```

## 输出格式

启用AI摘要后，Markdown文件会包含：

1. **时段总结**：在统计信息后，展示整个时间段的总体分析
2. **每日摘要**：在每个日期下，展示该日的重点总结

示例：
```markdown
## 📊 时段总结

万科A在2025-06-04至2025-11-30期间...
（AI生成的总结内容）

## 时间线

### 2025-11-30

**📝 每日摘要:** 本日万科A披露了...
（AI生成的每日摘要）

🔴 **[深交所]** [关于...的公告](url)
...
```

## 注意事项

1. **API密钥安全**：不要将API密钥提交到代码仓库
2. **生成时间**：启用AI摘要会增加处理时间（约每天1-2秒）
3. **API额度**：注意查看API使用额度，避免超额
4. **网络连接**：需要稳定的网络连接访问API

## 费用说明

- **阿里云灵积**：新用户赠送免费额度（百万tokens），足够日常使用
- 免费额度用完后可以按需付费，价格透明
- 不启用AI摘要功能，系统仍可正常使用

### 价格参考（供参考）

- qwen-turbo: 约 0.3元/百万tokens（输入）
- qwen-plus: 约 0.8元/百万tokens（输入）
- qwen-max: 约 4元/百万tokens（输入）

## 故障排除

### 问题：AI摘要功能未启用
**解决**：检查是否正确设置了API密钥和 `--ai-summary` 参数

```bash
# 检查环境变量
echo $QWEN_API_KEY

# 测试命令
python stock_news_collector.py 688331 -n 荣昌生物 --days 7 --ai-summary
```

### 问题：API调用失败
**可能原因**：
1. API密钥错误或过期
2. 网络连接问题
3. API额度不足
4. 模型名称错误

**解决方法**：
1. 访问 https://dashscope.console.aliyun.com/ 验证API密钥
2. 检查网络连接
3. 查看控制台确认余额
4. 使用正确的模型名称（qwen-turbo/qwen-plus/qwen-max）
5. 临时禁用AI摘要继续使用系统

### 问题：摘要质量不理想
**可调整项**：
- 使用更高级的模型：`--model qwen-max`
- 修改 `src/ai_summarizer.py` 中的prompt模板
- 调整temperature参数（0.1-1.0，默认0.7）

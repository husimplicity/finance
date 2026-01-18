# 快速入门清单 ✅

## 第一次使用（5分钟）

### ✅ 步骤1：基本测试（无需API密钥）

```bash
# 测试基本功能
python stock_news_collector.py 688331 -n 荣昌生物 --days 7
```

**预期结果**：
- 收集消息成功
- 生成 `timeline_688331_XXXXXX.md` 文件
- 包含统计信息和时间线

---

### ✅ 步骤2：获取免费API密钥（2分钟）

1. 访问：https://dashscope.aliyun.com/
2. 登录阿里云账号（可免费注册）
3. 开通灵积模型服务（DashScope）
4. 创建API Key（格式：sk-xxx）
5. 复制API密钥

**新用户赠送免费额度（百万tokens），足够测试使用！**

---

### ✅ 步骤3：启用AI摘要

```bash
# 设置API密钥
export QWEN_API_KEY="sk-your-key-here"

# 运行带AI摘要的收集
python stock_news_collector.py 688331 -n 荣昌生物 --days 7 --ai-summary

# 可选：指定模型
python stock_news_collector.py 688331 -n 荣昌生物 --days 7 --ai-summary --model qwen-turbo
```

**预期结果**：
- 显示"正在生成AI摘要..."
- Markdown文件包含📊时段总结和📝每日摘要

---

## 常用命令速查

### 基础使用
```bash
# 收集30天数据（快速）
python stock_news_collector.py <股票代码> -n <股票名称> --days 30

# 收集180天数据（深度分析）
python stock_news_collector.py <股票代码> -n <股票名称> --days 180
```

### 带AI摘要
```bash
# 添加 --ai-summary 参数
python stock_news_collector.py <股票代码> -n <股票名称> --days 30 --ai-summary
```

### 示例股票代码
- 上交所：`688331`（荣昌生物）、`603259`（药明康德）
- 深交所：`000002`（万科A）、`000001`（平安银行）

---

## 检查清单

### 基本功能 ✅
- [ ] 能正常收集消息
- [ ] 生成Markdown文件
- [ ] 文件包含统计信息
- [ ] 消息按日期组织

### AI摘要功能 ✅
- [ ] 已获取API密钥
- [ ] 设置环境变量
- [ ] 添加 `--ai-summary` 参数
- [ ] 生成的文件包含AI摘要

---

## 测试命令

### 测试1：基本功能
```bash
python stock_news_collector.py 688331 -n 荣昌生物 --days 7
```
**预期时间**：20-30秒

### 测试2：AI摘要演示
```bash
python demo_ai_summary.py
```
**说明**：如果未设置API密钥，会显示获取指南

### 测试3：完整功能
```bash
export QWEN_API_KEY="sk-your-key"
python stock_news_collector.py 688331 -n 荣昌生物 --days 7 --ai-summary
```
**预期时间**：1-2分钟（包含AI生成时间）

### 测试4：不同模型对比
```bash
# 快速模型
python stock_news_collector.py 688331 -n 荣昌生物 --days 7 --ai-summary --model qwen-turbo

# 最高质量
python stock_news_collector.py 688331 -n 荣昌生物 --days 7 --ai-summary --model qwen-max
```

---

## 故障排除

### ❌ 问题：命令找不到
```bash
# 确保在正确目录
cd /path/to/finance

# 激活虚拟环境
source .venv/bin/activate
```

### ❌ 问题：没有生成AI摘要
```bash
# 检查环境变量
echo $QWEN_API_KEY

# 如果为空，设置它
export QWEN_API_KEY="sk-your-key"

# 确保添加了参数
python stock_news_collector.py 688331 -n 荣昌生物 --days 7 --ai-summary
```

### ❌ 问题：API调用失败
- 检查API密钥是否正确
- 检查网络连接
- 查看 https://dashscope.console.aliyun.com/ 控制台确认额度
- 尝试使用不同的模型：`--model qwen-turbo`

---

## 下一步

### 📚 深入学习
- 阅读 [USAGE_GUIDE.md](USAGE_GUIDE.md) 了解所有功能
- 阅读 [AI_SUMMARY_README.md](AI_SUMMARY_README.md) 了解AI详情

### 🎯 实际应用
- 定期收集关注的股票
- 建立自己的监控脚本
- 尝试批量处理多只股票

### 🔧 自定义
- 修改 `src/ai_summarizer.py` 中的prompt
- 调整时间范围和输出格式
- 集成到自己的工作流

---

## 需要帮助？

- 查看文档：`README.md`, `USAGE_GUIDE.md`
- 查看示例：`demo_ai_summary.py`
- 查看实现：`IMPLEMENTATION_SUMMARY.md`

---

**祝使用愉快！** 🎉

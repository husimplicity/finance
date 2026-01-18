# 使用Qwen API进行AI摘要 - 改造说明

## 改造概述

已将AI摘要功能从SiliconFlow改为使用**阿里云灵积（DashScope）的通义千问（Qwen）API**。

## 主要变化

### 1. API提供商变更

**之前**：SiliconFlow（硅基流动）
**现在**：阿里云灵积 DashScope（通义千问 Qwen）

### 2. API密钥环境变量

**之前**：
```bash
export SILICONFLOW_API_KEY="your-key"
```

**现在**：
```bash
export QWEN_API_KEY="sk-xxx"
# 或
export DASHSCOPE_API_KEY="sk-xxx"
```

### 3. 支持的模型

现在可以选择不同的Qwen模型：

- **qwen-turbo**：速度快，适合大批量处理
- **qwen-plus**：平衡性能和质量（**默认**）
- **qwen-max**：最高质量，适合深度分析
- **qwen-long**：超长上下文支持

### 4. 新增命令行参数

```bash
# 指定模型
--model qwen-turbo
--model qwen-plus  # 默认
--model qwen-max
```

## 使用方法

### 基础使用

```bash
# 1. 设置API密钥
export QWEN_API_KEY="sk-your-dashscope-api-key"

# 2. 运行带AI摘要
python stock_news_collector.py 688331 -n 荣昌生物 --days 30 --ai-summary
```

### 指定模型

```bash
# 使用快速模型（推荐大批量处理）
python stock_news_collector.py 688331 -n 荣昌生物 --days 180 --ai-summary --model qwen-turbo

# 使用默认模型（平衡）
python stock_news_collector.py 688331 -n 荣昌生物 --days 30 --ai-summary --model qwen-plus

# 使用最高质量模型（深度分析）
python stock_news_collector.py 688331 -n 荣昌生物 --days 7 --ai-summary --model qwen-max
```

### 直接指定API密钥

```bash
python stock_news_collector.py 688331 -n 荣昌生物 --days 30 --ai-summary --api-key "sk-xxx"
```

## 获取API密钥

### 步骤

1. 访问 [阿里云灵积](https://dashscope.aliyun.com/)
2. 登录/注册阿里云账号
3. 开通灵积模型服务（DashScope）
4. 进入控制台：https://dashscope.console.aliyun.com/
5. 创建API Key
6. 复制密钥（格式：sk-xxxxxxxx）

### 免费额度

- 新用户赠送**百万tokens**免费额度
- 足够进行大量测试和日常使用

### 价格（免费额度用完后）

- qwen-turbo: ~0.3元/百万tokens
- qwen-plus: ~0.8元/百万tokens
- qwen-max: ~4元/百万tokens

## 技术改造细节

### 修改的文件

1. **src/ai_summarizer.py**
   - 移除provider配置系统
   - 直接使用DashScope OpenAI兼容接口
   - API端点：`https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions`
   - 支持模型参数配置

2. **src/timeline.py**
   - 添加`ai_model`参数
   - 传递模型名称给AISummarizer

3. **stock_news_collector.py**
   - 更新环境变量读取：`QWEN_API_KEY`或`DASHSCOPE_API_KEY`
   - 添加`--model`参数
   - 传递模型参数到Timeline

4. **demo_ai_summary.py**
   - 更新环境变量检查
   - 更新获取API密钥的提示信息

5. **文档更新**
   - README.md
   - AI_SUMMARY_README.md
   - QUICKSTART.md
   - USAGE_GUIDE.md（需要更新）

### API调用示例

```python
# 构建请求
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

data = {
    "model": "qwen-plus",  # 可配置
    "messages": [
        {
            "role": "system",
            "content": "你是一个专业的金融分析师..."
        },
        {
            "role": "user",
            "content": prompt
        }
    ],
    "temperature": 0.7,
    "max_tokens": 800,
    "top_p": 0.8
}

response = await client.post(
    "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
    headers=headers,
    json=data
)
```

## 优势

### 相比之前的改进

1. **官方服务**：阿里云官方服务，稳定性更好
2. **中文优化**：Qwen模型专门优化中文理解
3. **模型选择**：可根据需求选择不同性能模型
4. **价格透明**：官方定价，按需付费
5. **免费额度**：新用户百万tokens免费

### Qwen模型特点

- **高质量中文**：专门针对中文优化
- **金融领域**：在金融文本理解上表现优秀
- **响应快速**：qwen-turbo模型速度很快
- **长上下文**：qwen-long支持超长文本

## 兼容性说明

### 向后兼容

- 不使用AI摘要功能的用户不受影响
- 仍然支持`--ai-summary`参数
- 仍然支持`--api-key`参数

### 迁移指南

如果之前使用SiliconFlow，迁移步骤：

1. 获取新的Qwen API密钥
2. 更新环境变量：
   ```bash
   # 删除旧的
   unset SILICONFLOW_API_KEY
   
   # 设置新的
   export QWEN_API_KEY="sk-xxx"
   ```
3. 正常使用，命令行参数不变

## 测试

### 基础测试

```bash
# 设置API密钥
export QWEN_API_KEY="sk-xxx"

# 测试qwen-turbo（快速）
python stock_news_collector.py 688331 -n 荣昌生物 --days 7 --ai-summary --model qwen-turbo

# 测试qwen-plus（默认）
python stock_news_collector.py 688331 -n 荣昌生物 --days 7 --ai-summary

# 测试qwen-max（高质量）
python stock_news_collector.py 688331 -n 荣昌生物 --days 7 --ai-summary --model qwen-max
```

### 演示脚本

```bash
python demo_ai_summary.py
```

## 故障排除

### 问题：找不到API密钥

```bash
# 检查环境变量
echo $QWEN_API_KEY

# 设置环境变量
export QWEN_API_KEY="sk-your-key"
```

### 问题：API调用失败

1. 检查API密钥格式（应为sk-开头）
2. 访问控制台确认服务已开通
3. 检查免费额度是否充足
4. 确认网络可以访问阿里云服务

### 问题：模型名称错误

使用正确的模型名称：
- qwen-turbo
- qwen-plus
- qwen-max
- qwen-long

## 下一步

- [ ] 测试各个模型的摘要质量
- [ ] 根据实际使用调整prompt
- [ ] 优化token使用（减少费用）
- [ ] 添加更多错误处理

## 相关链接

- [阿里云灵积官网](https://dashscope.aliyun.com/)
- [控制台](https://dashscope.console.aliyun.com/)
- [API文档](https://help.aliyun.com/zh/dashscope/)
- [Qwen模型介绍](https://qwenlm.github.io/)

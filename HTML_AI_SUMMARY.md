# HTML可视化增强 - AI摘要集成

## 新增功能

HTML可视化网页现已集成AI摘要功能，自动显示：
1. **时段总结** - 整体趋势和关键事件分析
2. **每日摘要** - 每天的重点新闻总结

## 视觉效果

### 时段总结
- 蓝色背景区域（`#e8f4f8`）
- 蓝色左边框强调
- 📊 图标标识
- 显示在统计信息下方

### 每日摘要
- 浅黄色背景（`#fff9e6`）
- 橙色左边框
- 📝 图标标识
- 显示在每个日期下方，新闻列表上方

## 使用方法

### 不带AI摘要（普通HTML）

```bash
python stock_news_collector.py 688331 -n 荣昌生物 --days 7 -f html
```

生成的HTML只包含新闻列表，无摘要信息。

### 带AI摘要（增强HTML）

```bash
# 设置Qwen API密钥
export QWEN_API_KEY="sk-your-key"

# 生成带AI摘要的HTML
python stock_news_collector.py 688331 -n 荣昌生物 --days 7 -f html --ai-summary

# 使用不同模型
python stock_news_collector.py 688331 -n 荣昌生物 --days 7 -f html --ai-summary --model qwen-turbo
```

生成的HTML包含完整的AI摘要信息。

## HTML结构

```html
<!-- 页面头部 -->
<div class="header">
    <h1>股票名称(代码) 消息时间线</h1>
    <div class="stats">统计信息</div>
</div>

<!-- 时段总结（仅当启用AI摘要时显示） -->
<div class="summary-section">
    <div class="summary-title">📊 时段总结</div>
    <div class="summary-content">
        AI生成的时段分析内容...
    </div>
</div>

<!-- 时间线 -->
<div class="timeline">
    <div class="date-group">
        <div class="date-header">2026-01-09</div>
        
        <!-- 每日摘要（仅当启用AI摘要时显示） -->
        <div class="daily-summary">
            <div class="daily-summary-title">📝 每日摘要</div>
            <div class="daily-summary-content">
                AI生成的每日总结内容...
            </div>
        </div>
        
        <!-- 新闻列表 -->
        <div class="news-item high">...</div>
        <div class="news-item medium">...</div>
    </div>
</div>
```

## CSS样式

### 时段总结样式

```css
.summary-section {
    background-color: #e8f4f8;
    border-left: 4px solid #3498db;
    padding: 15px;
    margin-bottom: 20px;
    border-radius: 4px;
}

.summary-title {
    font-size: 1.1em;
    font-weight: bold;
    color: #2c3e50;
    margin-bottom: 10px;
}

.summary-title::before {
    content: "📊";
    margin-right: 8px;
}

.summary-content {
    color: #34495e;
    line-height: 1.8;
    white-space: pre-wrap;
}
```

### 每日摘要样式

```css
.daily-summary {
    background-color: #fff9e6;
    border-left: 3px solid #f39c12;
    padding: 12px;
    margin-bottom: 15px;
    border-radius: 4px;
}

.daily-summary-title {
    font-weight: bold;
    color: #e67e22;
    margin-bottom: 8px;
}

.daily-summary-title::before {
    content: "📝";
    margin-right: 6px;
}

.daily-summary-content {
    color: #555;
    line-height: 1.6;
}
```

## 完整示例

### 生成7天数据并查看

```bash
# 1. 设置API密钥
export QWEN_API_KEY="sk-xxx"

# 2. 生成HTML（带AI摘要）
python stock_news_collector.py 688331 -n 荣昌生物 --days 7 -f html --ai-summary

# 3. 在浏览器中打开
open timeline_688331_*.html
```

### 批量生成多只股票

```bash
#!/bin/bash
export QWEN_API_KEY="sk-xxx"

stocks=(
    "688331:荣昌生物"
    "000002:万科A"
    "603259:药明康德"
)

for stock in "${stocks[@]}"; do
    code="${stock%%:*}"
    name="${stock##*:}"
    echo "生成 ${name} 的HTML..."
    python stock_news_collector.py "${code}" -n "${name}" --days 30 -f html --ai-summary
    sleep 3
done

echo "所有HTML已生成！"
```

## 对比效果

### 不带AI摘要
- 页面简洁，仅显示新闻列表
- 快速生成（20-30秒）
- 适合快速浏览

### 带AI摘要
- 页面丰富，包含智能分析
- 生成较慢（1-3分钟）
- 适合深度研究

## 响应式设计

HTML已优化移动端显示：
- 自适应布局
- 最大宽度1200px
- 统计信息自动换行
- 适合手机、平板、电脑查看

## 浏览器兼容性

支持所有现代浏览器：
- Chrome/Edge（推荐）
- Safari
- Firefox
- 移动浏览器

## 技术实现

修改的文件：
- `src/timeline.py` 中的 `to_html()` 方法

新增的CSS类：
- `.summary-section` - 时段总结容器
- `.summary-title` - 时段总结标题
- `.summary-content` - 时段总结内容
- `.daily-summary` - 每日摘要容器
- `.daily-summary-title` - 每日摘要标题
- `.daily-summary-content` - 每日摘要内容

## 优势

1. **即开即用**：无需安装，浏览器直接打开
2. **美观大方**：专业的UI设计
3. **信息丰富**：AI摘要 + 完整新闻
4. **易于分享**：单个HTML文件包含所有内容
5. **离线可用**：保存后可离线查看

## 下一步优化

可能的增强方向：
- [ ] 添加筛选功能（按来源、重要性）
- [ ] 添加搜索功能
- [ ] 添加打印优化样式
- [ ] 添加深色模式
- [ ] 添加图表可视化

## 使用建议

1. **日常监控**：使用7-30天数据，快速了解动态
2. **深度分析**：使用180天数据 + AI摘要，全面研究
3. **定期存档**：定期生成HTML，建立历史记录
4. **多屏查看**：电脑看全局，手机看重点

## 示例输出

查看当前目录中的 `timeline_688331_20260109_012327.html` 文件即可看到效果！

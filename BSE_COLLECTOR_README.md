# 北交所数据采集器文档

## 概述
已成功为股票消息收集系统增加了**北京证券交易所（北交所）**数据采集渠道，可以收集北交所上市公司的公告信息。

## 功能特点

### 1. 使用 Playwright 渲染页面
- 北交所网站使用 JavaScript 动态加载数据
- 采用 Playwright 浏览器自动化工具获取渲染后的 HTML
- 支持无头模式运行，节省资源

### 2. 智能搜索
- 通过公司名称或股票代码搜索
- 自动点击时间排序，按最新到最旧排列
- 支持翻页，默认最多抓取 10 页

### 3. 准确解析
- 解析结果容器 `#quotationTable`
- 提取标题、URL、发布日期
- 正确处理相对 URL
- 自动过滤不符合日期范围的公告

### 4. 完整集成
- 已集成到主程序 `stock_news_collector.py`
- 自动识别北交所股票（代码以 4 或 8 开头）
- 与其他采集器并行运行

## 技术实现

### 文件结构
```
src/collectors/
├── bse_collector.py          # 北交所采集器
├── __init__.py               # 已添加 BSECollector 导入
stock_news_collector.py        # 主程序（已集成）
test_bse_collector.py          # 测试脚本
test_bse_complete.py          # 完整流程测试
```

### 核心代码逻辑

#### 1. 采集流程
```python
async def collect(self, days: int = 365):
    # 1. 启动 Playwright 浏览器
    # 2. 访问北交所首页
    # 3. 在搜索框输入公司名称/代码
    # 4. 等待跳转到搜索结果页
    # 5. 点击时间排序
    # 6. 逐页抓取数据
    # 7. 解析并过滤结果
```

#### 2. HTML 解析
```python
# 查找结果容器
quotation_table = soup.find('div', id='quotationTable')

# 查找所有结果项
result_divs = quotation_table.find_all('div', class_='main-show')

# 对每一项：
# - 提取标题：<p class="tit1" title="...">
# - 提取链接：<a href="...">
# - 提取日期：<span class="time">
```

#### 3. 网页结构
北交所搜索结果页面的关键结构：
```html
<div id="quotationTable" class="data-box">
    <div class="main">
        <div class="main-show">
            <div class="num-cell"><span class="num">01</span></div>
            <div class="tit-cell">
                <a href="/disclosure/2026/...pdf">
                    <p class="tit1" title="[临时公告]五新隧装:...">...</p>
                    <span class="time">2026-01-16</span>
                </a>
            </div>
        </div>
        <!-- 更多结果 -->
    </div>
</div>
```

## 使用方法

### 方法1：直接调用采集器
```python
from src.collectors.bse_collector import BSECollector

collector = BSECollector(stock_code="430639", stock_name="五新隧装")
items = await collector.collect(days=30)

for item in items:
    print(f"{item.date}: {item.title}")
```

### 方法2：通过主程序（推荐）
```bash
# 北交所股票会自动使用 BSECollector
python stock_news_collector.py 430639 -n 五新隧装 --days 30
```

### 方法3：使用测试脚本
```bash
# 测试采集器
python test_bse_collector.py

# 测试完整流程
python test_bse_complete.py
```

## 北交所股票代码识别

系统自动识别北交所股票：
- **4xxxxx**：原新三板精选层股票
- **8xxxxx**：北交所新股

主程序会自动判断并使用相应的采集器。

## 示例：五新隧装

**股票代码**: 430639  
**公司名称**: 五新隧装

### 测试结果
成功采集到五新隧装的公告信息，包括：
1. [2026-01-16] 投资者关系活动记录表
2. [2025-12-29] 关于发行股份及支付现金购买资产...公告
3. [2025-12-22] 关于向银行申请并购贷款的公告
4. [2025-12-22] 第四届董事会第十九次会议决议公告
... 等等

### 采集到的数据包括
- ✅ 临时公告
- ✅ 定期报告
- ✅ 重大事项公告
- ✅ 董事会/股东大会决议
- ✅ 财务报告
- ✅ 监管文件

## 特性说明

### 1. 自动分类
- 公司治理
- 财务报告
- 股权变动
- 重大事项
- 监管信息
- 交易提示
- 经营动态

### 2. 重要性判断
- **高**：重大资产重组、并购、业绩预告等
- **中**：一般公告
- **低**：例行公告

### 3. 时间范围过滤
- 支持指定天数（如 30 天、90 天、365 天）
- 自动过滤超出范围的公告

### 4. 翻页支持
- 默认最多抓取 10 页
- 如果某页无符合日期的数据，自动停止
- 支持自定义最大页数

## 注意事项

### 1. Playwright 依赖
需要安装 Playwright 及其浏览器：
```bash
pip install playwright
playwright install chromium
```

### 2. 性能考虑
- 使用无头浏览器模式
- 每次翻页有适当延迟（避免请求过快）
- 建议不要设置过大的天数范围

### 3. 网站变化
如果北交所网站结构发生变化，可能需要更新选择器：
- `#quotationTable`: 结果容器
- `.main-show`: 结果项
- `.tit-cell`: 标题单元格
- `.time`: 日期

## 故障排除

### 问题1：未找到结果
**原因**：网站结构可能变化  
**解决**：查看 `bse_result_playwright.html` 文件，分析实际的 HTML 结构

### 问题2：浏览器启动失败
**原因**：Playwright 浏览器未安装  
**解决**：
```bash
playwright install chromium
```

### 问题3：搜索超时
**原因**：网络问题或网站响应慢  
**解决**：增加超时时间或检查网络连接

## 未来改进

### 可能的优化方向
1. **性能优化**
   - 缓存搜索结果
   - 减少不必要的页面等待时间
   
2. **功能增强**
   - 支持更多搜索条件（如公告类型筛选）
   - 支持下载 PDF 文件内容
   
3. **稳定性**
   - 增加重试机制
   - 更好的错误处理
   
4. **API 方式**
   - 如果北交所提供 API，可以切换到 API 方式

## 总结

✅ **已完成**
- 北交所采集器开发
- 集成到主程序
- 测试验证
- 支持时间排序和翻页
- 准确解析标题、URL、日期

✅ **流程跑通**
- 以五新隧装 (430639) 为例
- 成功采集到多条公告信息
- 数据格式与其他采集器一致

✅ **文档齐全**
- 技术实现文档
- 使用说明
- 故障排除指南

## 🤖 项目名称：基于 LangChain ReAct Agent 的扫地机器人智能客服系统

## 🎯 业务痛点与解决方案

### 1. 推理决策：从硬编码流程到 ReAct 自主规划
* **痛点**：传统客服机器人按固定 if-else 流程走，用户问"我的机器最近扫不干净怎么办"时，系统不知道该先查故障知识库、还是先拉使用记录、还是先看天气环境因素，不同场景需要不同工具组合，硬编码流程根本覆盖不全。
* **解法**：基于 LangChain 的 create_agent 构建 ReAct Agent，内建 Think→Act→Observe 循环。Agent 拿到问题后先推理"我需要什么信息才能回答"，再自主选择调用哪个工具，拿到结果后再判断信息够不够，不够继续调，够了才输出。**从"预设流程驱动"变成"模型自主决策驱动"**。

### 2. 多场景冲突：动态提示词切换让一个 Agent 干两份活
* **痛点**：系统需要同时支持两种业务场景——普通客服咨询（口语化、互动、简短）和个性化使用报告生成（正式、结构化、Markdown 格式）。两套要求写在一个 Prompt 里互相打架，写两套 Agent 又维护成本翻倍。
* **解法**：设计了"信号工具 → 中间件 → Runtime Context → Prompt 替换"三段式切换链路。Agent 判断用户要生成报告时，调用 fill_context_for_report 信号工具，中间件 monitor_tool 拦截后在 Runtime Context 插入标记位，另一个中间件 report_prompt_switch 在每次模型调用前检测标记，自动把系统提示词从"智能客服"切为"报告写手"。**一个 Agent 实例，两套 Prompt，零重启无缝切换**。

### 3. 前端交互：Generator 异步解耦实现真流式输出
* **痛点**：Agent 的 .stream() 返回迭代器，前端消费完后迭代器即空，无法再用于追加对话历史。直接 .invoke() 又会让前端长时间阻塞等待，体验僵硬。
* **解法**：在 app.py 中自设计 capture() 生成器代理函数。利用 Python 的 yield 机制，在实时向前端推送 Token 的同时，后台同步将每块内容缓存到外部列表中，最后取完整内容写入 session_state 历史。**完美兼顾了逐字流式体验与消息历史持久化**。

### 4. 会话状态：Streamlit 热重载下的状态保持
* **痛点**：Streamlit 每当用户操作就会重新执行整个脚本，如果不做持久化处理，对话历史、Agent 实例全部丢失，页面变成空白，用户体验断崖。
* **解法**：将 Agent 实例和消息历史挂载到 st.session_state 上，页面每次重载时遍历历史消息列表重新渲染，对话连续性完全不受页面刷新影响。

### 5. 向量库防膨胀：MD5 内容指纹增量去重
* **痛点**：知识库文件（PDF/TXT）在开发阶段频繁更新，如果无脑全量加载，同一文件的不同版本会重复入库，导致向量库膨胀、检索噪声增大。
* **解法**：引入 hashlib.md5 指纹层。加载文档前计算文件全量 MD5，与本地 md5.text 清单比对，已入库的直接跳过。**从源头过滤掉 100% 的冗余向量计算与存储空间**。

### 6. 模型层耦合风险：抽象工厂解耦
* **痛点**：直接在各模块中硬编码 ChatTongyi() 和 DashScopeEmbeddings()，换模型需要全局搜索替换，容易遗漏导致线上事故。
* **解法**：定义 BaseModelFactory 抽象基类，ChatModelFactory 和 EmbeddingsFactory 分别实现。所有业务模块统一从 model/factory.py 拿模型实例，切换模型只改 YAML 配置项和工厂类一行代码。**模型层与业务层完全解耦**。

## 🚀 快速开始

### 1. 克隆项目与环境准备
```
git clone https://github.com/你的用户名/你的仓库名.git
cd 你的仓库名
pip install -r requirements.txt
```
> 依赖包括：streamlit, langchain, langchain-chroma, langchain-community, dashscope, pyyaml, pypdf 等

### 2. 配置环境变量
在系统环境或项目根目录下配置阿里百炼平台 API Key：
```
export DASHSCOPE_API_KEY="your-api-key-here"
```

### 3. 初始化知识库（首次运行）
```
python rag/vector_store.py
```
该步骤将 `data/` 目录下的 TXT/PDF 知识文档分片、嵌入后存入 Chroma 向量库，后续启动 Agent 时自动跳过已入库文件。

### 4. 启动智能客服对话端
```
streamlit run app.py
```
打开浏览器进入网页，即可向"智扫通"发起多轮对话。试试问：
- 小户型适合哪些扫地机器人？
- 给我生成我的使用报告

## 🛠️ 技术栈

**前端与交互层**
* ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=Streamlit&logoColor=white) 核心 Web 框架，session_state 会话管理 + 流式输出交互
* **Generator (生成器)**：Python 原生 yield 机制，解决流式消费与历史存储的互斥问题

**AI Agent 与编排层**
* ![LangChain](https://img.shields.io/badge/LangChain-FFFFFF?style=flat-square&logo=langchain&logoColor=black) 核心框架，ReAct Agent 构建 + LCEL 管道编排 + 自定义中间件
* **LangGraph**：Runtime Context 上下文管理，支撑动态提示词切换
* **Qwen3-Max (通义千问)**：核心对话大模型，负责推理决策与内容生成
* **DashScope Embeddings (text-embedding-v4)**：阿里百炼文本向量化模型

**数据与存储层**
* ![Chroma](https://img.shields.io/badge/ChromaDB-F37F58?style=flat-square) 本地向量数据库，语义相似度检索 Top-3 文档片段
* **SQLite3**：Chroma 文档元数据存储
* **YAML**：全量配置集中管理（模型、向量库、提示词、外部数据路径）

**工程化组件**
* **自定义中间件**：wrap_tool_call 工具调用监控 + before_model 模型调用追踪 + dynamic_prompt 动态提示词切换
* **抽象工厂模式**：BaseModelFactory 解耦模型层，替换模型零改动业务代码
* **RecursiveCharacterTextSplitter**：智能文本分片（200 字/块，20 字重叠）
* **Hashlib (MD5)**：文件指纹校验，知识库增量去重
* **双通道日志**：控制台 INFO + 文件 DEBUG 按日切割，全链路可观测



<img width="814" height="823" alt="image" src="https://github.com/user-attachments/assets/b6e27cdc-2380-4008-be58-68d2a3938f8f" />
<img width="803" height="680" alt="image" src="https://github.com/user-attachments/assets/943eda37-5089-495a-b848-35a849e380c6" />


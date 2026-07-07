# /literature — 学术文献趋势分析 Skill

一个 Claude Code 技能 / 命令行工具，帮助研究生、博士生分析任意学术课题的研究趋势。

同时从 5 个免费学术 API 并行获取数据，按 **CCF-A/B 顶会/顶刊标准筛选论文**，产出带证据链的结构化趋势分析报告。

核心原则：**每个结论都必须附带证据链，用户可追溯到原始论文。**

```
/literature 少样本图像分类
/literature vision transformer --categories cs.CV cs.LG --years 2023 2026
```

---

## 它能回答什么问题？

| 问题 | 回答方式 |
|------|---------|
| **这个课题近 3 年大家都在做什么方向？** | 按方法分类统计（foundation model、transformer、meta-learning 等） |
| **哪个方向在增长、哪个在饱和？** | 论文量趋势 + 引用增长曲线 + benchmark SOTA 变化 |
| **我现在做这个方向还有空间吗？** | 基于竞争程度和引用表现给出建议 |
| **高引论文在做什么？** | TOP 高影响力论文及其共同点 |
| **这些结论可靠吗？** | 每项结论带置信度标注和数据来源 |

---

## 快速开始

### 一、安装

#### 方式 A：Claude Code 安装（推荐）

在 Claude Code 中运行：

```
/plugin marketplace add zhaoweihua001/literature-trends
```

或者：

```bash
npx skills add zhaoweihua001/literature-trends -g
```

#### 方式 B：本地运行

```bash
git clone https://github.com/zhaoweihua001/literature-trends.git
cd literature-trends
pip install -r requirements.txt
```

### 二、配置

#### 2.1 配置 Semantic Scholar API Key（推荐）

Semantic Scholar 的引用数据能让分析更精准。免费申请：

> 1. 打开 https://www.semanticscholar.org/product/api
> 2. 往下翻找到 "Request an API Key" 按钮
> 3. 填写申请表（参考下方模板）
> 4. Key 会发到你的邮箱

**申请表填写参考：**

| 字段 | 填写内容 |
|------|---------|
| **First Name** | 你的名 |
| **Last Name** | 你的姓 |
| **Email** | 学校/公司邮箱（建议用 xxx@xxx.edu.cn 或 Gmail） |
| **Affiliation** | 你的学校或公司 |
| **Application Purpose** | `Private` |
| **Project Description（50字以上）** | This is an open-source Claude Code skill that helps graduate students analyze research trends for academic topics. The engine collects papers from arXiv, then enriches them with citation data from Semantic Scholar. It queries papers by their arXiv ID to get citation counts, influential citation counts, publication venues, and paper metadata. This data is used to classify research methods, identify trending directions, and suggest promising research areas. Usage is personal/educational, estimated at ~200 requests per day. |
| **Endpoints** | GET https://api.semanticscholar.org/graph/v1/paper/ArXiv:{id} — query citation count, venue, publication types by arXiv ID; POST https://api.semanticscholar.org/graph/v1/paper/batch — batch query (backup) |
| **Daily Request Volume** | Requests are rate-limited to 0.6s intervals internally. We query arXiv IDs sequentially and use the minimum necessary fields. Expected usage is well under 1 RPS. |

拿到 Key 后，放入 `~/.config/literature/.env`：

```bash
echo "SS_API_KEY=你的Key" >> ~/.config/literature/.env
```

#### 2.2 配置 Python 3.12+

```bash
# Windows
winget install Python.Python.3.12

# Mac
brew install python@3.12

# Linux
sudo apt install python3.12
```

#### 2.3 安装依赖

```bash
pip install -r requirements.txt
```

### 三、使用

#### 在 Claude Code 中使用

```
/literature 少样本图像分类
/literature vision transformer --years 2023 2026 --max-results 200
/literature 少样本图像分类 --min-venue ccf-ab
```

#### 在命令行直接运行

```bash
python scripts/engine.py --topic "few-shot image classification" \
  --categories cs.CV --years 2023 2026 --max-results 100
```

引擎将输出结构化 JSON，包含：
- 论文列表（含引用数、venue 信息）
- 方法分类统计
- 年度趋势
- 关键词热度
- benchmark 变化
- 高引论文排行

#### 可选：安装 Firecrawl MCP（追问论文详情用）

当你想进一步查看某篇具体论文的引用来源、代码仓库或详细元数据时，可以用 Firecrawl MCP 来爬取。

1. 注册 https://www.firecrawl.dev/ 获取 API Key

2. 配置 MCP：

```bash
claude mcp add --transport http firecrawl https://mcp.firecrawl.dev/v2/mcp
```

3. 在 `~/.claude.json` 或项目 `.claude.json` 中添加你的 Firecrawl API Key

4. 之后可以在 Claude Code 中用 Firecrawl 工具来爬取具体论文信息（例如 Google Scholar 页面、GitHub 仓库等）

> 注意：Firecrawl 免费版每月 500 次调用，适合在得到趋势报告后对特定论文做深度追问。它不替代主流程的数据抓取。

---

## 数据源

| 来源 | 提供数据 | 认证 | 限流 |
|------|---------|------|------|
| **arXiv API** | 论文标题、摘要、作者、分类标签 | 不需要 | 1 req/3s |
| **Semantic Scholar API** | 引用数、高影响力引用、venue 信息 | 免费 Key（推荐） | 100 req/min（有 Key） |
| **CrossRef API** | 期刊/出版社信息、DOI 元数据 | 不需要（建议设 mailto） | 50 req/s |
| **Papers With Code API** | Benchmark 排行榜、SOTA 趋势、代码链接 | 不需要 | 无限制 |
| **DBLP API** | 会议/期刊收录统计 | 不需要 | 1 req/s |

---

## CCF 论文筛选规则

引擎默认只保留 **CCF-A 和 CCF-B** 的论文：

| 类别 | CCF-A 会议 | CCF-B 会议 | CCF-A 期刊 | CCF-B 期刊 |
|------|-----------|-----------|-----------|-----------|
| **列表** | CVPR / ICCV / NeurIPS / ICML / AAAI / IJCAI / ACM MM | ECCV / ICRA / ICIP / BMVC / 3DV / IROS / ICASSP | IEEE TPAMI / IJCV / IEEE TIP | IEEE TNNLS / CVIU / Pattern Recognition 等 |

- CCF-A/B **会议论文**：只要有接收记录即纳入
- CCF-A/B **期刊论文**：只有已发表的才纳入（预印本不纳入）
- **CCF-C 及以下**的论文：不纳入
- **纯 arXiv 无发表记录**的论文：不纳入

---

## 方法分类

引擎根据标题和摘要中的关键词，将论文自动分类为：

| 分类 | 中文 | 典型关键词 |
|------|------|-----------|
| foundation_model | 基石模型 | CLIP、VLM、foundation model、pretrained |
| transformer_based | Transformer | transformer、ViT、self-attention |
| meta_learning | 元学习 | MAML、meta-training、episodic |
| prompt_tuning | 提示调优 | prompt tuning、soft prompt、visual prompt |
| data_augmentation | 数据增强 | data augmentation、synthetic、GAN、diffusion |
| transfer_learning | 迁移学习 | fine-tune、transfer learning、domain adaptation |
| generative | 生成式 | generative model、diffusion、VAE |
| graph_neural_network | 图神经网络 | GNN、graph convolution、GCN |
| metric_learning | 度量学习 | siamese、contrastive、prototypical |
| ensemble | 集成方法 | ensemble、multi-view、boosting |
| other | 其他 | 未命中以上分类 |

---

## 输出结构

引擎输出的 JSON 包含以下部分：

| 字段 | 说明 |
|------|------|
| `meta` | 查询参数、源统计、耗时、CCF 过滤统计 |
| `papers` | 完整论文列表，每篇含引用数、venue 缩写、方法分类 |
| `method_categories` | 各方法类别的论文数、平均引用、趋势方向 |
| `yearly_stats` | 每年论文数、平均引用、top venue |
| `keyword_trends` | 跟踪的关键词逐年出现频次 |
| `benchmark_trends` | 各 benchmark 的 SOTA 变化 |
| `high_impact_papers` | 引用 TOP 论文 |
| `venue_distribution` | 发表渠道统计 |

---

## 常见问题

### Q：Semantic Scholar 返回 0 条数据？

免费无 Key 的调用会被限流。去 https://www.semanticscholar.org/product/api 申请 API Key，然后配置到 `~/.config/literature/.env` 中。

### Q：CCF 过滤后论文太少？

某些新兴方向在 CCF-A/B 上的论文本来就不多，这是正常现象。可以调大 `--max-results` 获取更多候选论文；或者等待 Semantic Scholar Key 配置好以获取更全的 venue 信息。

### Q：如何查看某篇论文的更多详情？

安装 Firecrawl MCP（见上方说明），然后在大报告中追问具体论文的信息，Claude 会通过 Firecrawl 爬取论文的 Google Scholar 或 arXiv 页面的详细数据。

---

## 项目结构

```
literature-trends/
├── SKILL.md               # Skill 入口（Claude Code 读取）
├── scripts/
│   └── engine.py          # 主编排器
├── engine/
│   ├── __init__.py
│   ├── ccf_rankings.py    # CCF 排名 + venue 标准化
│   ├── fetchers/          # 5 个数据源 API 封装
│   │   ├── arxiv.py
│   │   ├── semanticscholar.py
│   │   ├── crossref.py
│   │   ├── paperswithcode.py
│   │   └── dblp.py
│   ├── merge.py           # 去重 + 合并 + CCF 过滤
│   ├── classify.py        # 方法分类
│   └── output.py          # JSON 输出组装
├── tests/                 # 23+ 测试
│   ├── test_arxiv.py
│   ├── test_merge.py
│   └── ...
└── requirements.txt
```

---

## License

MIT

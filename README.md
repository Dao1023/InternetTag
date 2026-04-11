# InternetTag

互联网关键词分析项目 - 通过分析各领域关键词了解互联网动向

预览：https://github.com/Dao1023/InternetTag

## 项目结构

```
InternetTag/
├── data/                   # 原始数据
│   └── kanmeiba-tag.txt
├── src/                    # 源代码
│   ├── classifiers/        # 分类器模块
│   │   ├── rule_based.py       # 基于规则的分类
│   │   ├── clustering.py       # TF-IDF + K-means聚类
│   │   ├── qwen_embedding.py   # Qwen3-Embedding分类
│   │   └── qwen_clustering.py  # Qwen3-Embedding + K-means聚类
│   ├── utils/              # 工具模块
│   │   └── serve.py        # HTTP服务器工具
│   ├── analyze_tags.py     # 分析脚本
│   └── main.py             # 主入口
├── results/                # 分析结果
│   ├── analysis_result.json         # 规则匹配结果
│   ├── clustering_result.json       # TF-IDF聚类结果
│   ├── qwen_embedding_result.json   # Qwen3-Embedding结果
│   └── qwen_clustering_result.json  # Qwen3聚类结果
├── docs/                   # 可视化文档
│   └── index.html          # 分析结果查看器
├── .gitignore
├── .python-version
├── pyproject.toml
└── README.md
```

## 使用方法

### 运行分析

```bash
# 使用主入口（交互式选择分类方法）
python src/main.py

# 运行特定分析器
python src/analyze_tags.py          # 规则匹配
python src/classifiers/clustering.py          # TF-IDF聚类
python src/classifiers/qwen_embedding.py      # Qwen3-Embedding
python src/classifiers/qwen_clustering.py     # Qwen3聚类
```

### 查看分析结果

#### 方式一：可视化查看器（推荐）

```bash
# 启动HTTP服务器
cd docs && python -m http.server 8080

# 或使用项目根目录的serve工具
python -m src.utils.serve

# 然后浏览器访问 http://localhost:8080
```

可视化查看器支持：
- 下拉菜单选择并切换不同的结果文件
- 拖拽上传本地JSON文件
- 搜索关键词
- 查看分类统计和详情

#### 方式二：直接查看JSON

所有分析结果保存在 `results/` 目录下，可直接打开JSON文件查看。

## 分类方法对比

| 方法 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| **规则匹配** | 预定义分类词典，关键词包含匹配 | 可解释性强，准确率高 | 需要手动维护词典 |
| **TF-IDF聚类** | 提取关键词特征，使用K-means聚类 | 自动发现类别 | 需要预设聚类数量 |
| **Qwen3-Embedding** | 使用Qwen3模型生成embedding，语义相似度分类 | 语义理解能力强 | 依赖外部API |
| **Qwen3聚类** | Qwen3-Embedding + K-means降维聚类 | 结合语义和自动聚类 | 计算成本较高 |

## 分析结果示例

### 规则匹配结果
- 成人/擦边内容: ~16%
- 社交媒体/平台: ~12%
- AI/技术工具: ~5%
- 游戏/动漫: ~4%

### TF-IDF聚类结果
自动发现高频词组合，如"美女"、"视频"、"直播"等相关词聚为一类。

### Qwen3-Embedding结果
基于语义相似度分类，能识别同义词和语义相关词。

## 依赖安装

```bash
pip install -e .
```

主要依赖：
- jieba (中文分词)
- scikit-learn (TF-IDF, K-means)
- requests (API调用)
- numpy/pandas (数据处理)

## TODO

- [x] 实现TF-IDF + K-means聚类
- [x] 实现Qwen3-Embedding分类
- [x] 实现Qwen3-Embedding + K-means聚类
- [x] 添加可视化分析查看器
- [ ] 优化分类准确率
- [ ] 添加更多数据源
- [ ] 实现增量分析

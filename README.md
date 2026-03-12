# InternetTag

互联网关键词分析项目 - 通过分析各领域关键词了解互联网动向

## 项目结构

```
InternetTag/
├── data/               # 原始数据
│   └── kanmeiba-tag.txt
├── src/                # 源代码
│   ├── analyze_tags.py # 分析脚本
│   └── main.py         # 主入口
├── results/            # 分析结果
│   └── analysis_result.json
├── .gitignore
├── .python-version
├── pyproject.toml
└── README.md
```

## 使用方法

```bash
# 运行分析
python src/analyze_tags.py

# 或使用主入口
python src/main.py
```

## 当前分类方法

目前使用基于规则的分类方法：
- 预定义11个分类类别
- 关键词包含匹配
- 手动维护分类词典

**分类结果占比：**
- 成人/擦边内容: 16.04%
- 社交媒体/平台: 12.21%
- AI/技术工具: 4.95%
- 游戏/动漫: 4.13%
- 日本艺人/偶像: 3.72%

## TODO

- [ ] 实现关键词相似度聚类（TF-IDF + K-means）
- [ ] 优化分类准确率
- [ ] 添加可视化分析图表

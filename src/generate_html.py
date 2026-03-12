#!/usr/bin/env python3
"""生成包含数据的HTML文件，避免CORS问题"""

import json
import os
from pathlib import Path

# 读取数据
with open('results/analysis_result.json', 'r', encoding='utf-8') as f:
    rule_data = json.load(f)

with open('results/clustering_result.json', 'r', encoding='utf-8') as f:
    cluster_data = json.load(f)

# 计算聚类的总权重
cluster_total_weight = sum(c['total_weight'] for c in cluster_data['clusters'].values())

# 读取模板
with open('docs/rule-based.html', 'r', encoding='utf-8') as f:
    rule_template = f.read()

with open('docs/clustering.html', 'r', encoding='utf-8') as f:
    cluster_template = f.read()

# 注入数据到规则匹配页面
rule_script = f'''
// 数据已嵌入，无需跨域请求
const data = {json.dumps(rule_data, ensure_ascii=False)};
let filteredData = data;

document.addEventListener('DOMContentLoaded', function() {{
    document.getElementById('loading').style.display = 'none';
    document.getElementById('totalKeywords').textContent = data.total_keywords.toLocaleString();
    document.getElementById('totalWeight').textContent = data.total_weight.toLocaleString();
    document.getElementById('categoryCount').textContent = Object.keys(data.category_stats).length;

    renderCategories(data.category_stats);
}});
'''

# 替换脚本部分
rule_template = rule_template.replace(
    "async function loadData() {\n        try {\n            const response = await fetch('../results/analysis_result.json');\n            if (!response.ok) throw new Error('无法加载数据');\n            data = await response.json();\n            filteredData = data;\n            renderData();\n        } catch (error) {\n            document.getElementById('loading').style.display = 'none';\n            document.getElementById('error').style.display = 'block';\n            document.getElementById('error').textContent = '加载失败: ' + error.message;\n            console.error('Error loading data:', error);\n        }\n    }\n\n    function renderData() {\n        document.getElementById('loading').style.display = 'none';\n        document.getElementById('totalKeywords').textContent = data.total_keywords.toLocaleString();\n        document.getElementById('totalWeight').textContent = data.total_weight.toLocaleString();\n        document.getElementById('categoryCount').textContent = Object.keys(data.category_stats).length;\n\n        renderCategories(filteredData.category_stats);\n    }",
    rule_script.strip()
)

rule_template = rule_template.replace("        // 加载数据\n        loadData();", "")

# 注入数据到聚类页面
cluster_script = f'''
// 数据已嵌入，无需跨域请求
const data = {json.dumps(cluster_data, ensure_ascii=False)};
const totalWeight = {cluster_total_weight};
let filteredData = data;

document.addEventListener('DOMContentLoaded', function() {{
    document.getElementById('loading').style.display = 'none';
    document.getElementById('clusterCount').textContent = data.n_clusters;
    document.getElementById('inertia').textContent = data.inertia.toFixed(2);

    renderClusters(data.clusters);
}});
'''

cluster_template = cluster_template.replace(
    "async function loadData() {\n        try {\n            const response = await fetch('../results/clustering_result.json');\n            if (!response.ok) throw new Error('无法加载数据');\n            data = await response.json();\n\n            // 计算总权重\n            totalWeight = Object.values(data.clusters)\n                .reduce((sum, cluster) => sum + cluster.total_weight, 0);\n\n            filteredData = data;\n            renderData();\n        } catch (error) {\n            document.getElementById('loading').style.display = 'none';\n            document.getElementById('error').style.display = 'block';\n            document.getElementById('error').textContent = '加载失败: ' + error.message;\n            console.error('Error loading data:', error);\n        }\n    }\n\n    function renderData() {\n        document.getElementById('loading').style.display = 'none';\n        document.getElementById('clusterCount').textContent = data.n_clusters;\n        document.getElementById('inertia').textContent = data.inertia.toFixed(2);\n\n        renderClusters(data.clusters);\n    }",
    cluster_script.strip()
)

cluster_template = cluster_template.replace("        // 加载数据\n        loadData();", "")

# 保存生成的新文件
with open('docs/rule-based-standalone.html', 'w', encoding='utf-8') as f:
    f.write(rule_template)

with open('docs/clustering-standalone.html', 'w', encoding='utf-8') as f:
    f.write(cluster_template)

print("✅ 生成独立HTML文件完成!")
print("📁 docs/rule-based-standalone.html")
print("📁 docs/clustering-standalone.html")
print("\n这两个文件包含内嵌数据，无需HTTP服务器即可直接打开")

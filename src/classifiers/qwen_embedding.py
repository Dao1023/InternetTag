#!/usr/bin/env python3
"""使用Qwen3-Embedding进行关键词分类"""

import json
import re
from pathlib import Path
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.cluster import KMeans
from collections import defaultdict
from tqdm import tqdm

# 定义分类模板
CATEGORY_TEMPLATES = {
    "成人内容": [
        "色情 成人 情色 性感 裸聊 约炮 一夜情",
        "成人视频 成人网站 成人图片 成人小说",
        "AV 成人电影 激情电影 性爱视频"
    ],
    "社交媒体": [
        "微信 微博 QQ 抖音 快手 小红书 B站",
        "社交平台 社交软件 聊天工具 即时通讯",
        "朋友圈 粉丝 关注 点赞 评论"
    ],
    "购物电商": [
        "淘宝 京东 天猫 拼多多 苏宁易购",
        "网购 网上购物 电子商务 购物平台",
        "商城 商城购物 在线商城 购物网站"
    ],
    "新闻资讯": [
        "新闻 新闻网 资讯 今日头条 新浪新闻",
        "新闻报道 时事新闻 新闻资讯 新闻媒体",
        "新闻门户 新闻网站 新闻平台"
    ],
    "视频娱乐": [
        "视频 视频网 视频网站 在线视频",
        "电影 电视剧 动漫 综艺 纪录片",
        "娱乐 娱乐网 娱乐新闻 明星 影视"
    ],
    "音乐": [
        "音乐 音乐网 音乐播放器 在线音乐",
        "歌曲 歌词 专辑 歌手 乐队",
        "Mp3 音乐下载 音乐网站 听歌"
    ],
    "游戏": [
        "游戏 网游 网页游戏 手机游戏",
        "游戏平台 游戏下载 游戏网站 游戏攻略",
        "王者荣耀 英雄联盟 绝地求生 我的世界"
    ],
    "小说文学": [
        "小说 小说网 小说网站 在线小说",
        "言情小说 玄幻小说 都市小说 武侠小说",
        "网络小说 起点小说 小说阅读 小说下载"
    ],
    "教育培训": [
        "教育 教育网 培训 培训机构 在线教育",
        "学习 学习网 课程 培训课程 教育培训",
        "学校 大学 考试 题库 教程"
    ],
    "搜索引擎": [
        "搜索 搜索引擎 百度 谷歌 搜狗",
        "搜索工具 搜索网站 网页搜索 信息搜索",
        "问答 知道 百度知道 搜搜问问"
    ],
    "其他工具": [
        "工具 工具箱 实用工具 在线工具",
        "软件 下载 应用 App",
        "浏览器 输入法 杀毒 压缩"
    ]
}


def parse_keywords(file_path):
    """解析关键词文件 - 使用与analyze_tags.py相同的正确解析逻辑"""
    keywords = {}

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # 跳过空行和字母标题行 (A-Z)
            if not line or re.match(r'^[A-Z]$', line):
                continue

            # 使用正则提取所有 关键词(数字) 模式
            pattern = r'([^\(]+)\((\d+)\)'
            matches = re.findall(pattern, line)

            for keyword, count in matches:
                keyword = keyword.strip()
                if keyword:
                    keywords[keyword] = int(count)

    return keywords


def classify_with_embeddings(keywords):
    """使用Qwen3-Embedding进行分类"""
    print("📦 加载Qwen3-Embedding模型...")
    model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")

    # 准备类别模板的嵌入
    print("🔤 生成类别模板嵌入...")
    category_embeddings = {}
    for category, templates in CATEGORY_TEMPLATES.items():
        # 合并同一类别的所有模板
        combined_template = " ".join(templates)
        category_embeddings[category] = model.encode(combined_template, normalize_embeddings=True)

    # 对关键词进行分类
    print(f"🏷️  对 {len(keywords)} 个关键词进行分类...")

    results = defaultdict(list)
    uncategorized = []

    # 批量编码关键词以提高效率
    keyword_list = list(keywords.keys())
    batch_size = 128
    total_batches = (len(keyword_list) + batch_size - 1) // batch_size

    with tqdm(total=len(keyword_list), desc="分类进度", unit="关键词") as pbar:
        for i in range(0, len(keyword_list), batch_size):
            batch = keyword_list[i:i + batch_size]
            keyword_embeddings = model.encode(batch, normalize_embeddings=True)

            for kw, emb in zip(batch, keyword_embeddings):
                # 计算与每个类别的余弦相似度
                similarities = {}
                for category, cat_emb in category_embeddings.items():
                    # 余弦相似度（因为向量已归一化，直接点积）
                    sim = np.dot(emb, cat_emb)
                    similarities[category] = sim

                # 选择相似度最高的类别
                best_category = max(similarities, key=similarities.get)
                best_score = similarities[best_category]

                # 设置阈值，低于阈值的归为"其他"
                threshold = 0.3
                if best_score >= threshold:
                    results[best_category].append((kw, keywords[kw]))
                else:
                    uncategorized.append((kw, keywords[kw]))

                pbar.update(1)

    # 添加"其他"类别
    if uncategorized:
        results["其他"] = uncategorized

    return results


def main():
    # 读取关键词数据
    data_file = Path(__file__).parent.parent / "data" / "kanmeiba-tag.txt"
    print(f"📂 读取数据文件: {data_file}")

    keywords = parse_keywords(data_file)
    print(f"✅ 解析完成，共 {len(keywords)} 个关键词")
    print(f"📊 总权重: {sum(keywords.values()):,}")

    # 使用嵌入模型分类
    results = classify_with_embeddings(keywords)

    # 计算统计信息
    total_keywords = len(keywords)
    total_weight = sum(keywords.values())

    print(f"\n{'='*60}")
    print(f"📊 分类统计 (Qwen3-Embedding)")
    print(f"{'='*60}")

    # 按权重排序
    sorted_results = sorted(results.items(), key=lambda x: sum(w for _, w in x[1]), reverse=True)

    category_stats = {}
    category_keywords = {}

    for category, items in sorted_results:
        category_weight = sum(weight for _, weight in items)
        percentage = (category_weight / total_weight) * 100

        # 按权重排序关键词
        sorted_items = sorted(items, key=lambda x: x[1], reverse=True)

        category_stats[category] = category_weight
        category_keywords[category] = sorted_items

        print(f"\n📌 {category}:")
        print(f"   关键词数: {len(items):,}")
        print(f"   权重: {category_weight:,} ({percentage:.2f}%)")
        print(f"   Top 10: {', '.join([kw for kw, _ in sorted_items[:10]])}")

    # 保存结果
    output = {
        "method": "Qwen3-Embedding",
        "model": "Qwen/Qwen3-Embedding-0.6B",
        "total_keywords": total_keywords,
        "total_weight": total_weight,
        "category_stats": category_stats,
        "category_keywords": category_keywords,
        "threshold": 0.3
    }

    output_file = Path(__file__).parent.parent / "results" / "qwen_embedding_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"✅ 结果已保存到: {output_file}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

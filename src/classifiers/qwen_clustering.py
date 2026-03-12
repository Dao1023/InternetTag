#!/usr/bin/env python3
"""使用Qwen3-Embedding + K-means聚类进行关键词分类"""

import json
import re
from pathlib import Path
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from collections import defaultdict
from tqdm import tqdm


def parse_keywords(file_path):
    """解析关键词文件"""
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


def determine_optimal_clusters(embeddings, max_clusters=20):
    """使用肘部法则确定最佳聚类数量"""
    print("📊 分析最佳聚类数量...")
    inertias = []
    K_range = range(5, max_clusters + 1)

    for k in K_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(embeddings)
        inertias.append(kmeans.inertia_)

    # 计算拐点 - 简单方法：找下降幅度最大的点
    deltas = np.diff(inertias)
    # 归一化下降幅度
    delta_ratios = deltas[:-1] / deltas[1:]
    optimal_k = K_range[np.argmax(delta_ratios) + 1]

    print(f"   建议聚类数: {optimal_k}")
    return optimal_k


def auto_name_category(keywords_with_weights, embeddings, cluster_center, top_n=5):
    """自动生成类别名称（基于与聚类中心最接近的关键词）"""
    # 计算该簇内关键词与聚类中心的相似度
    keywords_list = [kw for kw, _ in keywords_with_weights]

    # 提取这些关键词的嵌入
    indices = [i for i, kw in enumerate(keywords_list)]
    keyword_embeddings = embeddings[indices]

    # 计算与聚类中心的余弦相似度
    similarities = np.dot(keyword_embeddings, cluster_center)

    # 获取最接近中心的前N个关键词
    top_indices = np.argsort(similarities)[-top_n:][::-1]

    # 组合类别名：前3个最相关的关键词
    top_keywords = [keywords_list[i] for i in top_indices[:3]]

    # 过滤掉太短或太长的关键词
    filtered = [kw for kw in top_keywords if 2 <= len(kw) <= 6]

    if filtered:
        return "+".join(filtered[:2])
    else:
        return top_keywords[0] if top_keywords else f"类别_{len(keywords_with_weights)}"


def classify_with_clustering(keywords, n_clusters=None, pca_components=50, use_cache=True):
    """使用Qwen3-Embedding + K-means聚类进行分类"""
    keyword_list = list(keywords.keys())
    cache_dir = Path(__file__).parent.parent.parent / "results" / "cache"
    cache_dir.mkdir(exist_ok=True)
    cache_file = cache_dir / "qwen_embeddings_cache.npy"

    # 检查缓存
    embeddings = None
    if use_cache and cache_file.exists():
        print(f"📥 发现缓存文件: {cache_file}")
        try:
            cached_data = np.load(cache_file, allow_pickle=True).item()
            cached_keywords = cached_data['keywords']
            cached_embeddings = cached_data['embeddings']

            # 验证缓存是否匹配
            if cached_keywords == keyword_list:
                print("✅ 缓存有效，跳过编码")
                embeddings = cached_embeddings
            else:
                print("⚠️  缓存关键词不匹配，重新编码")
        except Exception as e:
            print(f"⚠️  缓存读取失败: {e}")

    # 如果没有缓存或缓存无效，进行编码
    if embeddings is None:
        print("📦 加载Qwen3-Embedding模型...")
        model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")

        # 批量编码所有关键词
        print(f"🔤 编码 {len(keywords)} 个关键词...")
        batch_size = 128

        all_embeddings = []
        with tqdm(total=len(keyword_list), desc="编码进度", unit="关键词") as pbar:
            for i in range(0, len(keyword_list), batch_size):
                batch = keyword_list[i:i + batch_size]
                batch_embeddings = model.encode(batch, normalize_embeddings=True)
                all_embeddings.append(batch_embeddings)
                pbar.update(len(batch))

        embeddings = np.vstack(all_embeddings)

        # 保存缓存
        print(f"💾 保存缓存到: {cache_file}")
        cache_data = {
            'keywords': keyword_list,
            'embeddings': embeddings
        }
        np.save(cache_file, cache_data)
        print("✅ 缓存已保存")

    print(f"📐 原始维度: {embeddings.shape}")

    # PCA降维
    if pca_components and pca_components < embeddings.shape[1]:
        print(f"🔽 PCA降维: {embeddings.shape[1]} → {pca_components}")
        pca = PCA(n_components=pca_components, random_state=42)
        embeddings = pca.fit_transform(embeddings)
        print(f"   解释方差比: {pca.explained_variance_ratio_.sum():.2%}")
        print(f"📐 降维后: {embeddings.shape}")

    # 确定聚类数量
    if n_clusters is None:
        n_clusters = determine_optimal_clusters(embeddings, max_clusters=20)

    # 执行K-means聚类
    print(f"🎯 执行K-means聚类 (k={n_clusters})...")
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=20)
    labels = kmeans.fit_predict(embeddings)

    # 整理聚类结果
    print("📋 整理聚类结果...")
    clusters = defaultdict(list)

    for keyword, label in zip(keyword_list, labels):
        clusters[label].append((keyword, keywords[keyword]))

    # 为每个聚类自动命名
    print("🏷️  自动生成类别名称...")
    results = {}
    category_names = {}

    for cluster_id, items in clusters.items():
        cluster_center = kmeans.cluster_centers_[cluster_id]

        # 自动命名
        category_name = auto_name_category(
            items, embeddings, cluster_center, top_n=10
        )

        # 确保名称唯一
        if category_name in category_names:
            suffix = 1
            while f"{category_name}_{suffix}" in category_names:
                suffix += 1
            category_name = f"{category_name}_{suffix}"

        category_names[category_name] = True
        results[category_name] = sorted(items, key=lambda x: x[1], reverse=True)

    return results


def main():
    # 读取关键词数据
    data_file = Path(__file__).parent.parent.parent / "data" / "kanmeiba-tag.txt"
    print(f"📂 读取数据文件: {data_file}")

    keywords = parse_keywords(data_file)
    print(f"✅ 解析完成，共 {len(keywords)} 个关键词")
    print(f"📊 总权重: {sum(keywords.values()):,}")

    # 使用聚类分类（带PCA降维）
    results = classify_with_clustering(keywords, n_clusters=15, pca_components=50)

    # 计算统计信息
    total_keywords = len(keywords)
    total_weight = sum(keywords.values())

    print(f"\n{'='*60}")
    print(f"📊 聚类统计 (Qwen3-Embedding + PCA + K-means)")
    print(f"{'='*60}")

    # 按权重排序
    sorted_results = sorted(results.items(), key=lambda x: sum(w for _, w in x[1]), reverse=True)

    category_stats = {}
    category_keywords = {}

    for category, items in sorted_results:
        category_weight = sum(weight for _, weight in items)
        percentage = (category_weight / total_weight) * 100

        category_stats[category] = category_weight
        category_keywords[category] = items

        print(f"\n📌 {category}:")
        print(f"   关键词数: {len(items):,}")
        print(f"   权重: {category_weight:,} ({percentage:.2f}%)")
        print(f"   Top 10: {', '.join([kw for kw, _ in items[:10]])}")

    # 保存结果
    output = {
        "method": "Qwen3-Embedding + PCA + K-means 聚类",
        "model": "Qwen/Qwen3-Embedding-0.6B + PCA(50维) + K-means (k=15)",
        "total_keywords": total_keywords,
        "total_weight": total_weight,
        "category_stats": category_stats,
        "category_keywords": category_keywords
    }

    output_file = Path(__file__).parent.parent.parent / "results" / "qwen_clustering_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"✅ 结果已保存到: {output_file}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

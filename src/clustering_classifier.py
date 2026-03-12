#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""基于TF-IDF + K-means的关键词聚类分类"""

import re
import json
import jieba
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy as np

def parse_line(line):
    """解析一行，提取关键词和权重"""
    if re.match(r'^[A-Z]$', line.strip()):
        return {}

    result = {}
    pattern = r'([^\(]+)\((\d+)\)'
    matches = re.findall(pattern, line)

    for keyword, count in matches:
        keyword = keyword.strip()
        if keyword:
            result[keyword] = int(count)
    return result

def load_keywords(filepath):
    """加载所有关键词"""
    keywords = []
    weights = []

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or re.match(r'^[A-Z]$', line):
                continue

            parsed = parse_line(line)
            for keyword, count in parsed.items():
                keywords.append(keyword)
                weights.append(count)

    return keywords, weights

def segment_keywords(keywords):
    """对关键词进行分词"""
    segmented = []

    for kw in keywords:
        # 英文/数字直接保留，中文进行分词
        if re.match(r'^[a-zA-Z0-9\s\-\(\)\.]+$', kw):
            segmented.append(kw.lower())
        else:
            # 中文分词
            words = jieba.lcut(kw)
            # 过滤单字和停用词
            words = [w for w in words if len(w) > 1]
            if words:
                segmented.append(' '.join(words))
            else:
                segmented.append(kw)

    return segmented

def perform_clustering(keywords, n_clusters=15):
    """执行TF-IDF + K-means聚类"""
    print(f"加载 {len(keywords)} 个关键词...")

    # 分词
    print("分词中...")
    segmented = segment_keywords(keywords)

    # TF-IDF向量化
    print("计算TF-IDF...")
    vectorizer = TfidfVectorizer(
        max_features=2000,
        min_df=2,
        max_df=0.8,
        ngram_range=(1, 2),
        token_pattern=r'(?u)\b\w+\b|[a-zA-Z0-9\-\(\)]+'
    )

    tfidf_matrix = vectorizer.fit_transform(segmented)

    print(f"TF-IDF矩阵形状: {tfidf_matrix.shape}")
    print(f"特征词数量: {len(vectorizer.vocabulary_)}")

    # K-means聚类
    print(f"执行K-means聚类 (K={n_clusters})...")
    kmeans = KMeans(
        n_clusters=n_clusters,
        random_state=42,
        n_init=10,
        max_iter=300
    )

    clusters = kmeans.fit_predict(tfidf_matrix)

    print(f"聚类完成，惯性值: {kmeans.inertia_:.2f}")

    return clusters, vectorizer, kmeans

def analyze_clusters(keywords, weights, clusters, vectorizer, kmeans, top_n=20):
    """分析每个聚类，提取代表性关键词"""
    cluster_info = {}

    for cluster_id in range(len(np.unique(clusters))):
        # 获取该聚类的所有关键词索引
        indices = np.where(clusters == cluster_id)[0]

        # 按权重排序
        cluster_keywords = [(keywords[i], weights[i]) for i in indices]
        cluster_keywords.sort(key=lambda x: x[1], reverse=True)

        # 获取聚类的中心特征词
        center = kmeans.cluster_centers_[cluster_id]
        top_feature_indices = center.argsort()[-top_n:][::-1]
        feature_names = vectorizer.get_feature_names_out()
        top_features = [feature_names[i] for i in top_feature_indices]

        cluster_info[cluster_id] = {
            'size': len(indices),
            'total_weight': sum(w for _, w in cluster_keywords),
            'top_features': top_features,
            'top_keywords': cluster_keywords[:top_n],
            'all_keywords': cluster_keywords
        }

    return cluster_info

def print_cluster_report(cluster_info, total_weight):
    """打印聚类报告"""
    print("\n" + "=" * 80)
    print("聚类分析报告")
    print("=" * 80)

    # 按权重排序
    sorted_clusters = sorted(
        cluster_info.items(),
        key=lambda x: x[1]['total_weight'],
        reverse=True
    )

    print(f"\n{'聚类':<5} {'大小':<6} {'总权重':<10} {'占比':<8} {'核心特征词'}")
    print("-" * 80)

    for cluster_id, info in sorted_clusters:
        percentage = (info['total_weight'] / total_weight) * 100
        features = ', '.join(info['top_features'][:5])
        print(f"{cluster_id:<5} {info['size']:<6} {info['total_weight']:<10,} {percentage:>6.2f}%  {features}")

    print("\n" + "=" * 80)
    print("各聚类的Top关键词")
    print("=" * 80)

    for cluster_id, info in sorted_clusters:
        print(f"\n【聚类 {cluster_id}】(共{info['size']}个关键词, 权重{info['total_weight']})")
        print(f"  核心特征: {', '.join(info['top_features'][:10])}")
        print(f"  Top关键词:")
        for i, (kw, w) in enumerate(info['top_keywords'][:15], 1):
            print(f"    {i:2}. {kw:<40} {w:>6}")

def name_clusters(cluster_info):
    """人工为每个聚类命名"""
    cluster_names = {}

    print("\n" + "=" * 80)
    print("请为每个聚类命名（按回车使用默认名称）")
    print("=" * 80)

    sorted_clusters = sorted(
        cluster_info.items(),
        key=lambda x: x[1]['total_weight'],
        reverse=True
    )

    for cluster_id, info in sorted_clusters:
        features = ', '.join(info['top_features'][:5])
        top_kws = ', '.join([kw for kw, _ in info['top_keywords'][:5]])

        print(f"\n聚类 {cluster_id}:")
        print(f"  特征: {features}")
        print(f"  Top: {top_kws}")

        default_name = features.split(',')[0] if features else f"类别{cluster_id}"
        name = input(f"  命名 [{default_name}]: ").strip()

        cluster_names[cluster_id] = name if name else default_name

    return cluster_names

def main():
    filepath = r"C:\Users\Dao\Code\InternetTag\data\kanmeiba-tag.txt"

    # 加载关键词
    print("加载关键词数据...")
    keywords, weights = load_keywords(filepath)
    total_weight = sum(weights)

    print(f"共 {len(keywords)} 个关键词，总权重 {total_weight}")

    # 执行聚类
    n_clusters = 15  # 聚类数量
    clusters, vectorizer, kmeans = perform_clustering(keywords, n_clusters)

    # 分析聚类
    cluster_info = analyze_clusters(keywords, weights, clusters, vectorizer, kmeans)

    # 打印报告
    print_cluster_report(cluster_info, total_weight)

    # 自动命名（基于核心特征词）
    cluster_names = {}
    for cluster_id, info in cluster_info.items():
        # 使用第一个核心特征词作为类别名
        if info['top_features']:
            cluster_names[cluster_id] = info['top_features'][0]
        else:
            cluster_names[cluster_id] = f"聚类{cluster_id}"

    # 保存结果
    result = {
        'n_clusters': n_clusters,
        'inertia': float(kmeans.inertia_),
        'clusters': {}
    }

    for cluster_id, info in cluster_info.items():
        result['clusters'][cluster_names[cluster_id]] = {
            'size': info['size'],
            'total_weight': info['total_weight'],
            'top_features': info['top_features'],
            'top_keywords': [(kw, w) for kw, w in info['top_keywords']],
            'all_keywords': [(kw, w) for kw, w in info['all_keywords']]
        }

    output_path = r"C:\Users\Dao\Code\InternetTag\results\clustering_result.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n结果已保存到: {output_path}")

if __name__ == "__main__":
    main()

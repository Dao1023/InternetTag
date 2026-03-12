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

# 定义分类模板 - 重新设计，减少重叠，特征更明确
CATEGORY_TEMPLATES = {
    "成人内容": [
        # 明确的成人内容关键词
        "AV 女优 番号 FANZA FC2 S1 MOODYZ SOD",
        "波多野结衣 三上悠亚 深田咏美 苍井空 吉泽明步",
        "福利姬 福利 福利吧 写真 比基尼 泳装",
        "微密圈 付费定制 资源 番号 种子 磁力",
        "性感 诱惑 激情 裸聊 约炮 一夜情",
        "ASMR 助眠 萝莉 御姐 人妻 熟女",
        "黑丝 白丝 长腿 美腿 胸 臀 胸罩",
        "大胸 巨乳 美乳 贫乳 F罩杯 罩杯",
        "JinriCP 王动 国产传媒 麻豆 传媒",
        "裸体 全裸 半裸 脱衣 偷拍 盗摄"
    ],
    "网盘存储": [
        # 明确的网盘和存储工具
        "夸克网盘 百度网盘 阿里云盘 115网盘",
        "云盘 网盘 不限速 秒传 分享",
        "蓝奏云 蓝奏 云盘 下载 上传",
        "百度云 夸克 115 夸克网盘 百度网盘",
        "存储 备份 同步 云存储"
    ],
    "视频平台": [
        # 明确的视频平台
        "B站 哔哩哔哩 爱奇艺 优酷 腾讯视频",
        "抖音 快手 小红书 TikTok 抖音视频",
        "YouTube Netflix 视频网站 视频网",
        "电视剧 电影 综艺 动漫 在线视频",
        "短视频 网剧 自制剧 娱乐视频"
    ],
    "社交社区": [
        # 明确的社交和社区
        "微信 微博 QQ 聊天 即时通讯",
        "知乎 豆瓣 贴吧 论坛 社区",
        "Instagram Twitter 推特 微博",
        "朋友圈 公众号 分享 转发",
        "粉丝 关注 点赞 评论 互动"
    ],
    "动漫游戏": [
        # 明确的动漫游戏
        "动漫 动画 漫画 游戏 王者荣耀",
        "原神 碧蓝航线 绝地求生 英雄联盟",
        "Steam 游戏 电竞 游戏",
        "cosplay cosplay Cos COS",
        "动漫游戏 游戏平台 主机游戏 PC游戏"
    ],
    "偶像明星": [
        # 明确的偶像和明星
        "AKB48 乃木坂46 欅坂46 日向坂46 偶像团体",
        "明星 演员 娱乐圈 影视",
        "偶像 女团 男团 练习生",
        "JPOP KPOP 韩国偶像 日本偶像",
        "演艺圈 娱乐明星 影视明星"
    ],
    "购物电商": [
        "淘宝 京东 天猫 拼多多 购物",
        "网购 电商 优惠 促销 折扣",
        "商品 店铺 买家 卖家 评价",
        "快递 物流 配送 退货"
    ],
    "小说文学": [
        "小说 网络小说 言情小说 玄幻小说",
        "起点小说 晋江 小说阅读",
        "文学 电子书 阅读 读书",
        "作者 写作 小说网站"
    ],
    "新闻资讯": [
        "新闻 新闻网 资讯 新闻资讯",
        "今日头条 新浪新闻 搜狐新闻",
        "新闻报道 时事新闻 财经新闻",
        "新闻门户 媒体 记者"
    ],
    "音乐": [
        "音乐 歌曲 歌手 专辑 乐队",
        "音乐下载 音乐平台 音乐播放器",
        "流行音乐 摇滚 说唱 古典音乐"
    ],
    "教育培训": [
        "教育 培训 在线教育 课程",
        "学习 学校 大学 考试",
        "高考 中考 考研 公务员",
        "教师 老师 学生 教程"
    ],
    "搜索工具": [
        "搜索 搜索引擎 百度 谷歌",
        "搜狗 360搜索 必应 Bing",
        "浏览器 插件 扩展 工具",
        "SEO 优化 网页搜索"
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
                # 提高阈值以减少误分类
                threshold = 0.4
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
    data_file = Path(__file__).parent.parent.parent / "data" / "kanmeiba-tag.txt"
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
        "threshold": 0.4
    }

    output_file = Path(__file__).parent.parent.parent / "results" / "qwen_embedding_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"✅ 结果已保存到: {output_file}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""分析kanmeiba-tag.txt关键词分类统计 - 完善版"""

import re
from collections import defaultdict
import json

# 定义关键词分类规则 - 更完善的版本
CATEGORIES = {
    "AI/技术工具": [
        "AI", "ChatGPT", "chatGPT", "GPT", "Grok", "GitHub", "Copilot", "API", "app", "工具", "软件",
        "下载器", "插件", "扩展", "脚本", "代码", "python", "AI换脸", "AI视频", "AI作画", "AI写歌",
        "AI配音", "ai抠图", "抠图", "civitai", "Chrome", "Firefox", "Cloudflare", "云端", "云盘",
        "阿里云盘", "百度网盘", "夸克网盘", "115网盘", "不限速", "秒传", "会员", "超级会员", "账号",
        "共享", "签到", "自动", "SEO", "搜索", "磁力", "BT", "种子", "解析", "提取", "转换", "编辑",
        "助手", "推荐", "榜单", "DeepSeek", "豆包", "Gemini", "Bard", "coze", "二维码", "链接", "源码",
        "爬虫", "破解", "教程", "指南", "攻略", "脚本", "编程", "开发", "技术", "算法", "模型", "训练"
    ],

    "社交媒体/平台": [
        "抖音", "B站", "哔哩哔哩", "微博", "小红书", "快手", "微信", "QQ", "Telegram", "电报",
        "Youtube", "TikTok", "Instagram", "Twitter", "INS", "推特", "知乎", "豆瓣", "贴吧", "论坛",
        "直播", "主播", "网红", "博主", "up主", "UP主", "视频", "短视频", "vlog", "粉丝", "关注", "点赞",
        "女网红", "男网红", "网红美女", "抖音网红", "女主播", "男主播", "美女主播", "女主播", "up主",
        "自媒体", "公众号", "订阅号", "服务号", "朋友圈", "群聊", "私聊", "私信", "评论", "弹幕"
    ],

    "游戏/动漫": [
        "游戏", "动漫", "动画", "漫画", "番剧", "碧蓝航线", "原神", "王者荣耀", "LOL", "英雄联盟",
        "DNF", "CS:GO", "csgo", "我的世界", "Minecraft", "Steam", "Epic", "任天堂", "索尼",
        "PlayStation", "Xbox", "Switch", "艾尔登法环", "鬼灭之刃", "进击的巨人", "间谍过家家",
        "孤独摇滚", "oc", "cosplay", "cos", "COS", "COSER", "COS作品", "COS小姐姐", "二次元",
        "声优", "虚拟主播", "VTuber", "初音", "初音未来", "洛天依", "游戏王", "宝可梦", "皮卡丘",
        "赛博朋克", "巫师", "刺客信条", "GTA", "侠盗猎车", "生化危机", "怪物猎人", "塞尔达"
    ],

    "影视/娱乐": [
        "电影", "电视剧", "剧集", "综艺", "番号", "AV", "av", "女优", "AV女优", "波多野结衣",
        "三上悠亚", "深田咏美", "河北彩花", "枫可怜", "东尼大木", "东京热", "一本道", "S1", "S1",
        "MOODYZ", "IdeaPocket", "Attackers", "FANZA", "FC2", "JAV", "有码", "无码", "短片",
        "奥斯卡", "戛纳", "柏林", "威尼斯", "金像奖", "金马奖", "艾美奖", "Netflix", "网飞",
        "Disney+", "HBO", "爱奇艺", "优酷", "腾讯视频", "Bilibili", "芒果TV", "大片", "影院",
        "剧场版", "OVA", "OAD", "SP", "特典", "映像", "作品", "番号", "女优", "专属女优",
        "引退", "出道", " debut", "出道作", "引退作", "纪念作"
    ],

    "成人/擦边内容": [
        "ASMR", "asmr", "福利姬", "福利", "擦边", "大尺度", "写真", "写真集", "写真视频", "比基尼",
        "泳装", "丝袜", "白丝", "黑丝", "长腿", "美腿", "腿", "大胸", "F罩杯", "巨乳", "萝莉",
        "御姐", "人妻", "女仆", "护士", "学生妹", "JK", "制服", "微密圈", "付费", "定制", "资源",
        "福利社", "电车", "痴汉", "NTR", "催眠", "调教", "捆绑", "凌辱", "陵辱", "露出", "偷拍",
        "盗摄", "素人", "主播", "网红", "模特", "写真集", "写真视频", "按摩", "推油", "精油", "SM",
        "高潮", "自慰", "手淫", "口交", "性交", "做爱", "爱爱", "肉便器", "便器", "奴", "主人",
        "M属性", "S属性", "女王", "女神", "美少女", "少女", "美腿", "内衣", "内裤", "胸罩", "乳",
        "臀", "屁股", "大屁股", "翘臀", "爆乳", "贫乳", "微乳", "美乳", "母乳", "授乳", "泳装",
        "死库水", "校服", "体操服", "和服", "浴衣", "裸体", "全裸", "半裸", "脱衣", "脱衣麻将",
        "性感", "诱惑", "撩人", "火辣", "豪放", "大胆", "露出", "公然", "羞耻", "陵辱", "轮奸",
        "痴女", "肉食", "草食", "优良", "女子", "女子大生", "短大", "高生", "中学生", "女子校"
    ],

    "日本艺人/偶像": [
        "阿朱", "冯提莫", "呆妹儿", "PDD", "大司马", "茄子", "山泥若", "狗头萝莉", "古阿扎", "过气",
        "过期米线", "蠢沫沫", "陈妮妮", "陈佩奇", "狗老师", "波多野结衣", "三上悠亚", "深田咏美",
        "纱仓真菜", "天使萌", "桥本有菜", "深田えいみ", "波多野結衣", "吉泽明步", "苍井空", "小泽玛利亚",
        "Rio", "柚木提娜", "麻美由真", "西野翔", "松岛枫", "吉川爱美", "白石麻衣", "西野七瀬",
        "斋藤飞鸟", "桥本环奈", "永野芽郁", "滨边美波", "今田美樱", "福田轮", "Angelababy",
        "迪丽热巴", "杨幂", "刘亦菲", "赵丽颖", "杨紫", "唐嫣", "刘诗诗", "baby", "热巴", "娜扎",
        "佟丽娅", "乃木坂46", "AKB48", "SKE48", "NMB48", "HKT48", "欅坂46", "日向坂46", "早安少女",
        "ももクロ", "桃草", "perfume", "Perfume", "霞", "aura", "伊藤", "佐佐木", "田中", "高桥",
        "渡边", "中村", "小川", "松本", "山本", "吉田", "山田", "佐藤", "小野", "大桥", "永野",
        "滨边", "白石", "斋藤", "西野", "桥本", "新垣", "上户", "深田", "三上", "波多野", "吉泽",
        "苍井", "小泽", "柚木", "麻美", "纱仓", "天使", "枫", "河北", "东尼", "Rio"
    ],

    "生活/购物": [
        "淘宝", "天猫", "京东", "拼多多", "抖音电商", "直播带货", "购物", "优惠", "优惠券",
        "折扣", "促销", "秒杀", "特价", "便宜", "好物", "种草", "拔草", "评测", "开箱",
        "使用心得", "体验", "对比", "选购", "生活", "美食", "旅游", "旅行", "摄影", "穿搭",
        "时尚", "美妆", "护肤", "化妆", "减肥", "健身", "运动", "瑜伽", "跑步", "健康", "养生",
        "医疗", "疾病", "症状", "健身房", "健身私教", "健身美女", "健身女神", "美食节目", "生活"
    ],

    "日本文化/ACG": [
        "日本", "东京", "大阪", "京都", "北海道", "冲绳", "AKB", "偶像团体", "宅男", "宅男女神",
        "宅", "Otaku", "ACG", "动漫", "漫画", "同人", "同人志", "Comiket", "Comic Market",
        "秋叶原", "秋叶", "女仆咖啡厅", "声优", "アイドル", "アニメ", "日本妹子", "东京奥运",
        "迷失东京", "东京大学", "乃木坂", "欅坂", "日向坂", "早安", "モーニング娘", "偶像", "女仆"
    ],

    "网盘/存储": [
        "网盘", "云盘", "阿里云盘", "百度网盘", "夸克网盘", "115网盘", "115生活", "115", "Lanzou",
        "蓝奏云", "天翼云盘", "移动云盘", "微云", "坚果云", "onedrive", "google drive", "dropbox",
        "不限速", "秒传", "分享", "链接", "提取码", "密码", "解压", "压缩", "rar", "zip", "7z",
        "上传", "下载", "存储", "备份", "同步", "会员", "超级会员", "账号", "共享", "签到", "自动签到"
    ],

    "身材/外貌描述": [
        "好身材", "身材", "女神", "美少女", "美女", "妹子", "颜值", "脸", "眼睛", "鼻子", "嘴巴",
        "长发", "短发", "卷发", "直发", "黑发", "金发", "皮肤", "白皙", "小麦", "健康", "苗条",
        "丰满", "瘦", "胖", "高", "矮", "模特", "颜值", "美女", "女神", "妹子", "少女", "萝莉"
    ],

    "其他": []
}

def parse_line(line):
    """解析一行，提取关键词和权重"""
    # 跳过字母行
    if re.match(r'^[A-Z]$', line.strip()):
        return {}

    result = {}
    # 匹配 关键词(数字) 格式
    pattern = r'([^\(]+)\((\d+)\)'
    matches = re.findall(pattern, line)

    for keyword, count in matches:
        keyword = keyword.strip()
        if keyword:
            result[keyword] = int(count)
    return result

def categorize_keyword(keyword):
    """对关键词进行分类 - 改进版，使用更精确的匹配"""
    keyword_lower = keyword.lower()

    # 特殊数字和符号处理
    if re.match(r'^\d+$', keyword):
        return "其他"

    # 优先匹配特定类别
    for category, keywords in CATEGORIES.items():
        if category == "其他":
            continue
        for kw in keywords:
            kw_lower = kw.lower()
            # 完全匹配或包含匹配
            if keyword_lower == kw_lower or kw_lower in keyword_lower or keyword_lower in kw_lower:
                return category

    # 根据特征进一步分类
    if any(c in keyword_lower for c in ['女优', 'av', 'AV', 'S1', 'MOODYZ', 'FANZA', 'FC2', 'IdeaPocket', 'Attackers', 'prestige', 'E-BODY']):
        return "影视/娱乐"
    if any(c in keyword_lower for c in ['写真', '图片', '壁纸', '头像']):
        return "成人/擦边内容"
    if any(c in keyword_lower for c in ['网盘', '云盘', '115', '夸克']):
        return "网盘/存储"
    if any(c in keyword_lower for c in ['cos', 'COS', 'cosplay']):
        return "游戏/动漫"

    return "其他"

def analyze_file(filepath):
    """分析文件并统计分类"""
    category_stats = defaultdict(int)
    category_keywords = defaultdict(list)
    total_weight = 0
    total_keywords = 0
    uncategorized = []

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or re.match(r'^[A-Z]$', line):
                continue

            keywords = parse_line(line)
            for keyword, count in keywords.items():
                total_keywords += 1
                total_weight += count

                category = categorize_keyword(keyword)
                category_stats[category] += count
                category_keywords[category].append((keyword, count))

                if category == "其他":
                    uncategorized.append((keyword, count))

    return {
        'category_stats': dict(category_stats),
        'category_keywords': dict(category_keywords),
        'total_weight': total_weight,
        'total_keywords': total_keywords,
        'uncategorized_sample': uncategorized[:200]
    }

def print_report(analysis):
    """打印分析报告"""
    print("=" * 90)
    print("关键词分类统计报告 (完善版)")
    print("=" * 90)
    print(f"总关键词数: {analysis['total_keywords']:,}")
    print(f"总权重: {analysis['total_weight']:,}")
    print()

    # 按权重排序
    sorted_categories = sorted(
        analysis['category_stats'].items(),
        key=lambda x: x[1],
        reverse=True
    )

    print("-" * 90)
    print(f"{'类别':<25} {'权重':>12} {'占比':>10} {'关键词数':>10}")
    print("-" * 90)

    for category, weight in sorted_categories:
        percentage = (weight / analysis['total_weight']) * 100
        keyword_count = len(analysis['category_keywords'][category])
        bar_length = int(percentage / 2)
        bar = "█" * bar_length
        print(f"{category:<25} {weight:>12,} {percentage:>9.2f}% {keyword_count:>10,}  {bar}")

    print("-" * 90)
    print()

    # 打印各类别Top关键词
    print("=" * 90)
    print("各类别 Top 15 关键词")
    print("=" * 90)

    for category, _ in sorted_categories:
        print(f"\n【{category}】")
        keywords = analysis['category_keywords'][category]
        top_keywords = sorted(keywords, key=lambda x: x[1], reverse=True)[:15]

        for i, (kw, count) in enumerate(top_keywords, 1):
            print(f"  {i:2}. {kw:<35} {count:>6}")

    # 未分类样本（减少显示）
    if analysis['uncategorized_sample']:
        print("\n" + "=" * 90)
        print("未分类关键词样本（前30个）")
        print("=" * 90)
        for i, (kw, count) in enumerate(analysis['uncategorized_sample'][:30], 1):
            print(f"{i:3}. {kw:<50} {count:>6}")

if __name__ == "__main__":
    filepath = r"C:\Users\Dao\Code\InternetTag\data\kanmeiba-tag.txt"
    analysis = analyze_file(filepath)
    print_report(analysis)

    # 保存详细结果到JSON
    with open(r"C:\Users\Dao\Code\InternetTag\analysis_result.json", 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    print("\n详细结果已保存到 analysis_result.json")

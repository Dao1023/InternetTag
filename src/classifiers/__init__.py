"""分类器模块"""

from .rule_based import main as rule_based_main
from .clustering import main as clustering_main
from .qwen_embedding import main as qwen_embedding_main

__all__ = ['rule_based_main', 'clustering_main', 'qwen_embedding_main']

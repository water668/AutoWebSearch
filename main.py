#!/usr/bin/env python3
import sys
from src.search_engine.baidu_search import BaiduSearchEngine
from src.web_scraper.scraper import WebScraper
from src.llm.ollama_client import OllamaClient
from src.graph.agent_graph import WebSearchAgent


def main():
    if len(sys.argv) < 2:
        print('使用方法: python main.py "搜索查询"')
        print('示例: python main.py "人工智能的最新发展"')
        sys.exit(1)
    
    query = sys.argv[1]
    print(f'查询: {query}')
    print('=' * 60)
    
    try:
        search_engine = BaiduSearchEngine()
        scraper = WebScraper()
        llm_client = OllamaClient()
        
        agent = WebSearchAgent(search_engine, scraper, llm_client)
        result = agent.run(query)
        
        print('\n' + '=' * 60)
        print('分析结果:')
        print('=' * 60)
        print(result)
        
    except Exception as e:
        print(f'错误: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()

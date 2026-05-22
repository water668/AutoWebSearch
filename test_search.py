import requests
from src.search_engine.bing_search import BingSearchEngine
from src.search_engine.baidu_search import BaiduSearchEngine

def test_search():
    test_cases = [
        "特朗普访华次数",
        "人工智能 发展趋势",
        "中国 GDP 2025",
        "新能源汽车 销量"
    ]
    
    bing_engine = BingSearchEngine()
    baidu_engine = BaiduSearchEngine()
    
    for query in test_cases:
        print(f"\n{'='*60}")
        print(f"测试查询: {query}")
        print(f"{'='*60}")
        
        print("\n=== Bing搜索 ===")
        try:
            results = bing_engine.search(query, num_results=3)
            print(f"找到 {len(results)} 个结果")
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['title']}")
                print(f"   URL: {result['url'][:60]}...")
                if result.get('abstract'):
                    print(f"   摘要: {result['abstract'][:80]}...")
        except Exception as e:
            print(f"Bing搜索失败: {e}")
        
        print("\n=== 百度搜索 ===")
        try:
            results = baidu_engine.search(query, num_results=3)
            print(f"找到 {len(results)} 个结果")
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['title']}")
                print(f"   URL: {result['url'][:60]}...")
                if result.get('abstract'):
                    print(f"   摘要: {result['abstract'][:80]}...")
        except Exception as e:
            print(f"百度搜索失败: {e}")

if __name__ == "__main__":
    test_search()

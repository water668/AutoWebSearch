from src.web_scraper.scraper import WebScraper
from src.search_engine.baidu_search import BaiduSearchEngine
from src.search_engine.bing_search import BingSearchEngine

def test_scraper():
    print("=" * 60)
    print("测试网页内容过滤和token限制机制")
    print("=" * 60)
    print()
    
    scraper = WebScraper(max_tokens=4000)
    
    print("1. 搜索测试内容...")
    search_engine = BingSearchEngine()
    search_results = search_engine.search("人工智能技术发展", num_results=2)
    
    if not search_results:
        print("搜索结果为空，使用备用URL测试")
        test_urls = [
            "https://baike.baidu.com/item/%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD",
            "https://baike.baidu.com/item/%E8%AE%A1%E7%AE%97%E6%9C%BA"
        ]
        search_results = [
            {"title": "人工智能", "url": test_urls[0], "abstract": "人工智能（Artificial Intelligence，AI）..."},
            {"title": "计算机科学", "url": test_urls[1], "abstract": "计算机科学（Computer Science）..."}
        ]
    
    print(f"找到 {len(search_results)} 个搜索结果")
    print()
    
    for i, result in enumerate(search_results):
        print(f"{'=' * 60}")
        print(f"测试第 {i+1} 个结果: {result['title']}")
        print(f"URL: {result['url']}")
        print(f"{'=' * 60}")
        print()
        
        content = scraper.scrape(result['url'])
        
        if content:
            print("✓ 成功提取内容")
            print()
            
            char_count = len(content)
            token_estimate = scraper.estimate_tokens(content)
            
            print(f"字符数: {char_count}")
            print(f"预估token数: {token_estimate}")
            print(f"是否在4k token以内: {'✓' if token_estimate <= 4000 else '✗'}")
            print()
            
            print("-" * 60)
            print("内容预览 (前500字符):")
            print("-" * 60)
            print(content[:500] + ("..." if len(content) > 500 else ""))
            print()
            
            print("-" * 60)
            print("内容预览 (最后200字符):")
            print("-" * 60)
            if len(content) > 200:
                print("..." + content[-200:])
            else:
                print(content)
            print()
        else:
            print("✗ 未能提取内容")
            print()

if __name__ == "__main__":
    test_scraper()

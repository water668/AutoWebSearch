import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import time
import random


class BingSearchEngine:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }
        self.base_url = 'https://cn.bing.com/search'

    def search(self, query: str, num_results: int = 20) -> List[Dict[str, str]]:
        results = []
        page = 0
        per_page = 10
        max_pages = 20  # 限制最多翻页次数
        seen_urls = set()
        
        print(f'Bing search query: \'{query}\'')
        
        while len(results) < num_results and page < max_pages:
            try:
                url = f'{self.base_url}?q={requests.utils.quote(query)}&first={page * per_page + 1}'
                print(f'Search URL: {url}')
                response = requests.get(url, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                print(f'响应前100个字符: {response.status_code} {response.text[:100]}')
                
                soup = BeautifulSoup(response.text, 'lxml')
                search_results = soup.find_all('li', class_='b_algo')
                
                if not search_results:
                    break
                
                new_results = 0
                
                for result in search_results:
                    if len(results) >= num_results:
                        break
                    
                    title_elem = result.find('h2')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    link_elem = title_elem.find('a')
                    if not link_elem:
                        continue
                    
                    result_url = link_elem.get('href', '')
                    
                    if result_url in seen_urls:  # 避免重复
                        continue
                    
                    abstract_elem = result.find('p')
                    abstract = abstract_elem.get_text(strip=True) if abstract_elem else ''
                    
                    if title and result_url:
                        seen_urls.add(result_url)
                        results.append({
                            'title': title,
                            'url': result_url,
                            'abstract': abstract
                        })
                        new_results += 1
                
                if new_results == 0:  # 没有新结果，停止翻页
                    break
                
                page += 1
                time.sleep(random.uniform(0.5, 1.5))
                
            except Exception as e:
                print(f'搜索出错: {e}')
                break
        
        return results[:num_results]

import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import time
import random


class BaiduSearchEngine:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }
        self.base_url = 'https://www.baidu.com/s'

    def search(self, query: str, num_results: int = 20) -> List[Dict[str, str]]:
        results = []
        page = 0
        per_page = 10
        
        while len(results) < num_results:
            try:
                url = f'{self.base_url}?wd={requests.utils.quote(query)}&pn={page * per_page}'
                print(f'正在请求: {url}')
                response = requests.get(url, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                print(f'响应前100个字符: {response.status_code} {response.text[:100]}')
                
                soup = BeautifulSoup(response.text, 'lxml')
                search_results = soup.find_all('div', class_='result')
                
                if not search_results:
                    break
                
                for result in search_results:
                    if len(results) >= num_results:
                        break
                    
                    title_elem = result.find('h3')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    link_elem = title_elem.find('a')
                    if not link_elem:
                        continue
                    
                    url = link_elem.get('href', '')
                    
                    abstract_elem = result.find('div', class_='c-abstract')
                    abstract = abstract_elem.get_text(strip=True) if abstract_elem else ''
                    
                    if title and url:
                        results.append({
                            'title': title,
                            'url': url,
                            'abstract': abstract
                        })
                
                page += 1
                time.sleep(random.uniform(0.5, 1.5))
                
            except Exception as e:
                print(f'搜索出错: {e}')
                break
        
        return results[:num_results]

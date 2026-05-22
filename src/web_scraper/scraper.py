import requests
from bs4 import BeautifulSoup
from typing import Optional, List, Tuple, Dict
import time
import random
import re


class WebScraper:
    def __init__(self, timeout: int = 15, max_tokens: int = 4000):
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0 Safari/537.36'
        }
        
        self.unwanted_tags = [
            'script', 'style', 'noscript', 'iframe',
            'form', 'button', 'input', 'textarea', 'select', 'option',
            'object', 'embed', 'applet', 'frame', 'frameset', 'noframes',
            'noembed', 'xmp', 'plaintext', 'listing',
            'svg', 'canvas', 'nav', 'footer', 'header', 'aside', 'menu', 'dialog'
        ]
        
        self.unwanted_classes = [
            'ad', 'ads', 'advertisement', 'banner',
            'cookie', 'consent', 'privacy', 'terms', 'disclaimer',
            'register', 'login', 'signup', 'signin',
            'search-box', 'searchbar', 'search-form',
            'sidebar', 'widget', 'social', 'share', 'comment', 'comments',
            'pagination', 'related', 'recommend', 'toolbar', 'popup', 'modal', 'overlay'
        ]
        
        self.unwanted_ids = [
            'ad', 'ads', 'advertisement', 'banner',
            'cookie', 'consent', 'privacy', 'terms', 'disclaimer',
            'register', 'login', 'signup', 'signin'
        ]
        
        self.noisy_patterns = [
            re.compile(r'[\u200b\u200c\u200d\uFEFF]'),
            re.compile(r'\s{2,}'),
            re.compile(r'[\*#\-_=]{3,}'),
            re.compile(r'\.{3,}')
        ]

    def fetch_page(self, url: str) -> Optional[str]:
        try:
            time.sleep(random.uniform(0.3, 0.8))
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            return response.text
        except Exception as e:
            print(f'获取网页失败 {url}: {e}')
            return None

    def estimate_tokens(self, text: str) -> int:
        return len(text) // 3

    def is_noisy_text(self, text: str) -> bool:
        text = text.strip()
        if len(text) == 0:
            return True
        if len(text) < 8:
            if not re.search(r'[\u4e00-\u9fff]', text):
                return True
        if re.match(r'^[·•*\-=+#~`^<>|]+$', text):
            return True
        return False

    def score_paragraph(self, paragraph: str) -> int:
        score = 0
        if len(paragraph) > 50:
            score += 5
        elif len(paragraph) > 25:
            score += 3
        elif len(paragraph) > 10:
            score += 1
        
        if re.search(r'[\d]{4}年?|\d+\.\d+%|\d+亿元|\d+万|\d+亿|\d+元', paragraph):
            score += 5
        if re.search(r'(研究表明|数据显示|根据|报告指出|专家表示|据悉|据悉)', paragraph):
            score += 3
        if any(keyword in paragraph for keyword in ['重要', '关键', '核心', '主要', '最新', '首次']):
            score += 2
        if re.search(r'。|！|\?|\.', paragraph):
            score += 1
        return score

    def remove_duplicates(self, items: List[str]) -> List[str]:
        seen = set()
        result = []
        for item in items:
            normalized = item.strip().lower()
            if normalized not in seen:
                seen.add(normalized)
                result.append(item)
        return result

    def extract_tables(self, soup: BeautifulSoup) -> List[str]:
        tables = []
        for table in soup.find_all('table'):
            rows = table.find_all('tr')
            if len(rows) < 2:
                continue
            
            table_data = []
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) > 0:
                    row_content = [cell.get_text(strip=True) for cell in cells if cell.get_text(strip=True)]
                    if row_content:
                        table_data.append(row_content)
            
            if len(table_data) >= 2:
                table_text = "【表格】\n"
                for i, row in enumerate(table_data):
                    prefix = "| " if i == 0 else "| "
                    table_text += prefix + " | ".join(row) + "\n"
                tables.append(table_text)
        return tables

    def extract_lists(self, soup: BeautifulSoup) -> List[str]:
        lists = []
        for list_tag in soup.find_all(['ul', 'ol']):
            items = list_tag.find_all('li')
            if len(items) < 2:
                continue
            
            list_text = "【列表】\n"
            for i, item in enumerate(items, 1):
                text = item.get_text(strip=True)
                if text and len(text) > 5:
                    list_text += f"• {text}\n"
            
            if list_text.count('•') >= 2:
                lists.append(list_text)
        return lists

    def extract_headings(self, soup: BeautifulSoup) -> List[str]:
        headings = []
        for tag in ['h1', 'h2', 'h3', 'h4']:
            for heading in soup.find_all(tag):
                text = heading.get_text(strip=True)
                if text and len(text) > 3:
                    level = tag[1]
                    headings.append((int(level), text))
        return headings

    def extract_paragraphs(self, soup: BeautifulSoup) -> List[Tuple[int, str]]:
        paragraphs = []
        containers = ['article', 'main', 'content', 'post', 'entry', 'page-content', 'main-content']
        
        for container in containers:
            container_elem = soup.find(container)
            if container_elem:
                for p in container_elem.find_all('p'):
                    text = p.get_text(strip=True)
                    if text and not self.is_noisy_text(text):
                        score = self.score_paragraph(text)
                        paragraphs.append((score, text))
        
        if not paragraphs:
            for p in soup.find_all('p'):
                text = p.get_text(strip=True)
                if text and not self.is_noisy_text(text):
                    score = self.score_paragraph(text)
                    paragraphs.append((score, text))
        
        return paragraphs

    def extract_links(self, soup: BeautifulSoup) -> List[str]:
        links = []
        for a in soup.find_all('a', href=True):
            text = a.get_text(strip=True)
            href = a['href']
            if text and len(text) > 3 and len(text) < 200:
                links.append(f"【链接】{text} → {href}")
        return links

    def clean_noise(self, text: str) -> str:
        for pattern in self.noisy_patterns:
            text = pattern.sub('', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        return text.strip()

    def extract_main_content(self, soup: BeautifulSoup) -> str:
        for tag in self.unwanted_tags:
            for element in soup.find_all(tag):
                element.decompose()
        
        for unwanted_class in self.unwanted_classes:
            for element in soup.find_all(class_=lambda x: x and unwanted_class.lower() in x.lower()):
                element.decompose()
        
        for unwanted_id in self.unwanted_ids:
            for element in soup.find_all(id=lambda x: x and unwanted_id.lower() in x.lower()):
                element.decompose()
        
        content_parts = []
        
        page_title = soup.title.string if soup.title else ''
        if page_title:
            content_parts.append(f"【页面标题】{page_title.strip()}")
        
        headings = self.extract_headings(soup)
        headings.sort(key=lambda x: x[0])
        for level, text in headings:
            content_parts.append(f"【标题{level}】{text}")
        
        tables = self.extract_tables(soup)
        content_parts.extend(tables)
        
        lists = self.extract_lists(soup)
        content_parts.extend(lists)
        
        paragraphs = self.extract_paragraphs(soup)
        paragraphs.sort(key=lambda x: -x[0])
        for score, text in paragraphs:
            if score >= 1 or len(text) >= 25:
                content_parts.append(f"【段落】{text}")
        
        links = self.extract_links(soup)[:10]
        content_parts.extend(links)
        
        content_parts = self.remove_duplicates(content_parts)
        
        return '\n\n'.join(content_parts)

    def clean_text(self, text: str) -> str:
        text = self.clean_noise(text)
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if not self.is_noisy_text(line):
                cleaned_lines.append(line)
        
        return '\n\n'.join(cleaned_lines)

    def truncate_to_token_limit(self, text: str) -> str:
        tokens = self.estimate_tokens(text)
        if tokens <= self.max_tokens:
            return text
        
        sections = re.split(r'\n\n', text)
        section_scores = []
        
        for i, section in enumerate(sections):
            if section:
                score = self.score_paragraph(section)
                if section.startswith('【页面标题】'):
                    score += 10
                elif section.startswith('【标题'):
                    score += 5
                elif section.startswith('【表格】'):
                    score += 3
                section_scores.append((i, score, section))
        
        section_scores.sort(key=lambda x: -x[1])
        
        selected_indices = set()
        current_tokens = 0
        
        for idx, score, section in section_scores:
            section_tokens = self.estimate_tokens(section)
            if current_tokens + section_tokens <= self.max_tokens:
                selected_indices.add(idx)
                current_tokens += section_tokens
        
        result_sections = []
        for i in range(len(sections)):
            if i in selected_indices:
                result_sections.append(sections[i])
        
        return '\n\n'.join(result_sections)

    def extract_content(self, html: str) -> str:
        try:
            if '<pdf' in html.lower() or html.strip().startswith('%PDF'):
                print('检测到PDF文件，跳过内容提取')
                return ''
            
            soup = BeautifulSoup(html, 'lxml')
            
            content = self.extract_main_content(soup)
            cleaned_content = self.clean_text(content)
            
            if len(cleaned_content) < 200:
                print('提取的内容过少，可能需要调整提取策略')
            
            final_content = self.truncate_to_token_limit(cleaned_content)
            
            token_count = self.estimate_tokens(final_content)
            print(f'提取内容完成: {len(final_content)} 字符, 约 {token_count} token')
            
            return final_content
        except Exception as e:
            print(f'提取内容失败: {e}')
            return ''

    def scrape(self, url: str) -> Optional[str]:
        html = self.fetch_page(url)
        if html:
            return self.extract_content(html)
        return None

    def scrape_with_stats(self, url: str) -> dict:
        result = {
            "url": url,
            "content": None,
            "char_count": 0,
            "token_estimate": 0,
            "status": "success"
        }
        
        html = self.fetch_page(url)
        if not html:
            result["status"] = "fetch_failed"
            return result
        
        if '<pdf' in html.lower() or html.strip().startswith('%PDF'):
            result["status"] = "pdf_file"
            result["content"] = ""
            return result
        
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            result["raw_char_count"] = len(html)
            result["raw_token_estimate"] = self.estimate_tokens(html)
            
            content = self.extract_main_content(soup)
            cleaned_content = self.clean_text(content)
            
            if len(cleaned_content) < 200:
                print('提取的内容过少，可能需要调整提取策略')
            
            final_content = self.truncate_to_token_limit(cleaned_content)
            
            result["content"] = final_content
            result["char_count"] = len(final_content)
            result["token_estimate"] = self.estimate_tokens(final_content)
            
            if result["token_estimate"] > 0:
                result["compression_ratio"] = round(result["raw_token_estimate"] / result["token_estimate"], 2)
            else:
                result["compression_ratio"] = 0
            
            return result
        except Exception as e:
            print(f'提取内容失败: {e}')
            result["status"] = "extract_failed"
            return result

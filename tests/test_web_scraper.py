import pytest
from unittest.mock import Mock, patch
from src.web_scraper.scraper import WebScraper


class TestWebScraper:
    def test_init(self):
        scraper = WebScraper(timeout=20)
        assert scraper.timeout == 20
        assert 'User-Agent' in scraper.headers

    def test_extract_content(self):
        html = '''
        <html>
            <head><title>测试页面</title></head>
            <body>
                <script>这是脚本</script>
                <style>这是样式</style>
                <header>这是头部</header>
                <nav>这是导航</nav>
                <div class="content">
                    <h1>主要标题</h1>
                    <p>这是第一段内容。</p>
                    <p>这是第二段内容。</p>
                </div>
                <footer>这是页脚</footer>
            </body>
        </html>
        '''
        scraper = WebScraper()
        content = scraper.extract_content(html)
        
        assert '主要标题' in content
        assert '这是第一段内容' in content
        assert '这是脚本' not in content
        assert '这是头部' not in content
        assert '这是导航' not in content

    def test_extract_content_empty_html(self):
        scraper = WebScraper()
        content = scraper.extract_content('')
        assert content == ''

    @patch('requests.get')
    def test_fetch_page_success(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '<html><body>测试内容</body></html>'
        mock_response.encoding = 'utf-8'
        mock_response.apparent_encoding = 'utf-8'
        mock_get.return_value = mock_response

        scraper = WebScraper()
        html = scraper.fetch_page('http://example.com')
        
        assert html is not None
        assert '测试内容' in html

    @patch('requests.get')
    def test_fetch_page_error(self, mock_get):
        mock_get.side_effect = Exception('请求失败')

        scraper = WebScraper()
        html = scraper.fetch_page('http://example.com')
        
        assert html is None

    @patch('src.web_scraper.scraper.WebScraper.fetch_page')
    def test_scrape_success(self, mock_fetch):
        mock_fetch.return_value = '''
        <html>
            <head><title>测试页面</title></head>
            <body>
                <main>
                    <h1>主要标题</h1>
                    <p>这是一段比较长的测试内容，应该可以通过长度检查。</p>
                    <p>这是另一段测试内容，包含一些信息。</p>
                    <p>这是第三段测试内容，确保有足够的文本。</p>
                </main>
            </body>
        </html>
        '''
        
        scraper = WebScraper()
        content = scraper.scrape('http://example.com')
        
        assert content is not None
        assert len(content) > 0

    @patch('src.web_scraper.scraper.WebScraper.fetch_page')
    def test_scrape_failure(self, mock_fetch):
        mock_fetch.return_value = None
        
        scraper = WebScraper()
        content = scraper.scrape('http://example.com')
        
        assert content is None

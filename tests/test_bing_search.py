import pytest
from unittest.mock import Mock, patch
from src.search_engine.bing_search import BingSearchEngine


class TestBingSearchEngine:
    def test_init(self):
        engine = BingSearchEngine(timeout=15)
        assert engine.timeout == 15
        assert engine.base_url == 'https://cn.bing.com/search'
        assert 'User-Agent' in engine.headers

    @patch('requests.get')
    def test_search_success(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '''
        <html>
            <li class="b_algo">
                <h2><a href="http://example.com">测试标题1</a></h2>
                <p>测试摘要1</p>
            </li>
            <li class="b_algo">
                <h2><a href="http://example2.com">测试标题2</a></h2>
                <p>测试摘要2</p>
            </li>
        </html>
        '''
        mock_get.return_value = mock_response

        engine = BingSearchEngine()
        results = engine.search('测试关键词', num_results=2)

        assert len(results) == 2
        assert results[0]['title'] == '测试标题1'
        assert results[0]['url'] == 'http://example.com'
        assert results[0]['abstract'] == '测试摘要1'
        assert results[1]['title'] == '测试标题2'

    @patch('requests.get')
    def test_search_num_results_limit(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '''
        <html>
            <li class="b_algo">
                <h2><a href="http://example.com">标题1</a></h2>
            </li>
            <li class="b_algo">
                <h2><a href="http://example2.com">标题2</a></h2>
            </li>
            <li class="b_algo">
                <h2><a href="http://example3.com">标题3</a></h2>
            </li>
        </html>
        '''
        mock_get.return_value = mock_response

        engine = BingSearchEngine()
        results = engine.search('测试', num_results=2)

        assert len(results) == 2

    @patch('requests.get')
    def test_search_no_results(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '<html><body></body></html>'
        mock_get.return_value = mock_response

        engine = BingSearchEngine()
        results = engine.search('不存在的关键词')

        assert len(results) == 0

    @patch('requests.get')
    def test_search_request_error(self, mock_get):
        mock_get.side_effect = Exception('请求失败')

        engine = BingSearchEngine()
        results = engine.search('测试')

        assert len(results) == 0

    @patch('requests.get')
    def test_search_missing_elements(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '''
        <html>
            <li class="b_algo">
                <h2>没有链接的标题</h2>
            </li>
            <li class="b_algo">
                <h2><a href="http://example.com">有效标题</a></h2>
            </li>
            <li class="b_algo">
                <!-- 没有 h2 -->
            </li>
        </html>
        '''
        mock_get.return_value = mock_response

        engine = BingSearchEngine()
        results = engine.search('测试')

        assert len(results) == 1
        assert results[0]['title'] == '有效标题'

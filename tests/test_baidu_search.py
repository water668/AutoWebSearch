import pytest
from unittest.mock import Mock, patch
from src.search_engine.baidu_search import BaiduSearchEngine


class TestBaiduSearchEngine:
    def test_init(self):
        engine = BaiduSearchEngine(timeout=15)
        assert engine.timeout == 15
        assert engine.base_url == 'https://www.baidu.com/s'
        assert 'User-Agent' in engine.headers

    @patch('requests.get')
    def test_search_success(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '''
        <html>
            <div class="result">
                <h3><a href="http://example.com">测试标题1</a></h3>
                <div class="c-abstract">测试摘要1</div>
            </div>
            <div class="result">
                <h3><a href="http://example2.com">测试标题2</a></h3>
                <div class="c-abstract">测试摘要2</div>
            </div>
        </html>
        '''
        mock_get.return_value = mock_response

        engine = BaiduSearchEngine()
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
            <div class="result">
                <h3><a href="http://example.com">标题1</a></h3>
            </div>
            <div class="result">
                <h3><a href="http://example2.com">标题2</a></h3>
            </div>
            <div class="result">
                <h3><a href="http://example3.com">标题3</a></h3>
            </div>
        </html>
        '''
        mock_get.return_value = mock_response

        engine = BaiduSearchEngine()
        results = engine.search('测试', num_results=2)

        assert len(results) == 2

    @patch('requests.get')
    def test_search_no_results(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '<html><body></body></html>'
        mock_get.return_value = mock_response

        engine = BaiduSearchEngine()
        results = engine.search('不存在的关键词')

        assert len(results) == 0

    @patch('requests.get')
    def test_search_request_error(self, mock_get):
        mock_get.side_effect = Exception('请求失败')

        engine = BaiduSearchEngine()
        results = engine.search('测试')

        assert len(results) == 0

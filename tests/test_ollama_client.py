import pytest
from unittest.mock import Mock, patch
from src.llm.ollama_client import OllamaClient


class TestOllamaClient:
    def test_init(self):
        client = OllamaClient(model='test-model', base_url='http://test-url')
        assert client.model == 'test-model'
        assert client.base_url == 'http://test-url'

    @patch('src.llm.ollama_client.OllamaLLM')
    def test_analyze_content_success(self, mock_ollama):
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = '1. 是否包含所需信息: 是\n2. 关键信息点: 测试信息\n3. 信息可信度: 高'
        mock_ollama.return_value = mock_llm_instance
        
        client = OllamaClient()
        
        result = client.analyze_content('测试查询', '测试内容')
        
        assert '是' in result
        assert '测试信息' in result
        mock_llm_instance.invoke.assert_called_once()

    @patch('src.llm.ollama_client.OllamaLLM')
    def test_analyze_content_error(self, mock_ollama):
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.side_effect = Exception('测试错误')
        mock_ollama.return_value = mock_llm_instance
        
        client = OllamaClient()
        
        result = client.analyze_content('测试查询', '测试内容')
        
        assert '分析失败' in result

    @patch('src.llm.ollama_client.OllamaLLM')
    def test_summarize_results_success(self, mock_ollama):
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = '1. 总体结论: 测试结论\n2. 关键发现: 测试发现'
        mock_ollama.return_value = mock_llm_instance
        
        client = OllamaClient()
        
        analyses = [
            {'title': '测试标题', 'url': 'http://test.com', 'analysis': '测试分析'}
        ]
        result = client.summarize_results('测试查询', analyses)
        
        assert '总体结论' in result['summary']
        assert '关键发现' in result['summary']
        mock_llm_instance.invoke.assert_called_once()

    @patch('src.llm.ollama_client.OllamaLLM')
    def test_summarize_results_error(self, mock_ollama):
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.side_effect = Exception('测试错误')
        mock_ollama.return_value = mock_llm_instance
        
        client = OllamaClient()
        
        result = client.summarize_results('测试查询', [])
        
        assert '汇总失败' in result['summary']

    @patch('src.llm.ollama_client.OllamaLLM')
    def test_invoke_success(self, mock_ollama):
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = '测试响应'
        mock_ollama.return_value = mock_llm_instance
        
        client = OllamaClient()
        
        result = client.invoke('测试提示词')
        
        assert result == '测试响应'
        mock_llm_instance.invoke.assert_called_once_with('测试提示词')

    @patch('src.llm.ollama_client.OllamaLLM')
    def test_invoke_error(self, mock_ollama):
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.side_effect = Exception('调用错误')
        mock_ollama.return_value = mock_llm_instance
        
        client = OllamaClient()
        
        result = client.invoke('测试提示词')
        
        assert '调用失败' in result

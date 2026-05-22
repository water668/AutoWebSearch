import pytest
from unittest.mock import Mock, patch
from src.graph.agent_graph import WebSearchAgent, AgentState
from src.search_engine.baidu_search import BaiduSearchEngine
from src.web_scraper.scraper import WebScraper
from src.llm.ollama_client import OllamaClient


class TestWebSearchAgent:
    def test_init(self):
        search_engine = Mock(spec=BaiduSearchEngine)
        scraper = Mock(spec=WebScraper)
        llm_client = Mock(spec=OllamaClient)
        
        agent = WebSearchAgent(search_engine, scraper, llm_client)
        
        assert agent.search_engine == search_engine
        assert agent.scraper == scraper
        assert agent.llm_client == llm_client
        assert agent.MAX_PAGES == 10

    def test_query_rewrite_node(self):
        search_engine = Mock(spec=BaiduSearchEngine)
        scraper = Mock(spec=WebScraper)
        llm_client = Mock(spec=OllamaClient)
        
        llm_client.invoke.return_value = '改写后的关键词'
        
        agent = WebSearchAgent(search_engine, scraper, llm_client)
        
        initial_state: AgentState = {
            'query': '测试查询',
            'rewritten_query': '',
            'search_results': [],
            'current_index': 0,
            'analyses': [],
            'current_answer': '',
            'is_answer_confident': False,
            'answer': ''
        }
        
        result = agent._query_rewrite_node(initial_state)
        
        assert result['rewritten_query'] == '改写后的关键词'
        llm_client.invoke.assert_called_once()

    def test_search_node(self):
        search_engine = Mock(spec=BaiduSearchEngine)
        scraper = Mock(spec=WebScraper)
        llm_client = Mock(spec=OllamaClient)
        
        test_results = [{'title': '测试标题', 'url': 'http://test.com', 'abstract': '测试摘要'}]
        search_engine.search.return_value = test_results
        
        agent = WebSearchAgent(search_engine, scraper, llm_client)
        
        initial_state: AgentState = {
            'query': '测试查询',
            'rewritten_query': '测试关键词',
            'search_results': [],
            'current_index': 0,
            'analyses': [],
            'current_answer': '',
            'is_answer_confident': False,
            'answer': ''
        }
        
        result = agent._search_node(initial_state)
        
        assert result['search_results'] == test_results
        assert result['current_index'] == 0
        assert result['analyses'] == []
        assert result['current_answer'] == ''
        assert result['is_answer_confident'] is False

    def test_process_page_node(self):
        search_engine = Mock(spec=BaiduSearchEngine)
        scraper = Mock(spec=WebScraper)
        llm_client = Mock(spec=OllamaClient)
        
        scraper.scrape.return_value = '测试内容'
        llm_client.analyze_content.return_value = '测试分析'
        llm_client.invoke.return_value = '当前答案'
        
        agent = WebSearchAgent(search_engine, scraper, llm_client)
        
        test_state: AgentState = {
            'query': '测试查询',
            'rewritten_query': '测试关键词',
            'search_results': [{'title': '测试标题', 'url': 'http://test.com', 'abstract': '测试摘要'}],
            'current_index': 0,
            'analyses': [],
            'current_answer': '',
            'is_answer_confident': False,
            'answer': ''
        }
        
        result = agent._process_page_node(test_state)
        
        assert result['current_index'] == 1
        assert len(result['analyses']) == 1
        assert result['analyses'][0]['title'] == '测试标题'
        assert result['current_answer'] == '当前答案'

    def test_judge_answer_node_confident(self):
        search_engine = Mock(spec=BaiduSearchEngine)
        scraper = Mock(spec=WebScraper)
        llm_client = Mock(spec=OllamaClient)
        
        llm_client.invoke.return_value = '可信'
        
        agent = WebSearchAgent(search_engine, scraper, llm_client)
        
        test_state: AgentState = {
            'query': '测试查询',
            'rewritten_query': '测试关键词',
            'search_results': [],
            'current_index': 1,
            'analyses': [{'title': '测试标题', 'url': 'http://test.com', 'analysis': '测试分析'}],
            'current_answer': '测试答案',
            'is_answer_confident': False,
            'answer': ''
        }
        
        result = agent._judge_answer_node(test_state)
        
        assert result['is_answer_confident'] is True

    def test_judge_answer_node_not_confident(self):
        search_engine = Mock(spec=BaiduSearchEngine)
        scraper = Mock(spec=WebScraper)
        llm_client = Mock(spec=OllamaClient)
        
        llm_client.invoke.return_value = '不可信'
        
        agent = WebSearchAgent(search_engine, scraper, llm_client)
        
        test_state: AgentState = {
            'query': '测试查询',
            'rewritten_query': '测试关键词',
            'search_results': [],
            'current_index': 1,
            'analyses': [{'title': '测试标题', 'url': 'http://test.com', 'analysis': '测试分析'}],
            'current_answer': '测试答案',
            'is_answer_confident': False,
            'answer': ''
        }
        
        result = agent._judge_answer_node(test_state)
        
        assert result['is_answer_confident'] is False

    def test_should_continue_max_pages(self):
        search_engine = Mock(spec=BaiduSearchEngine)
        scraper = Mock(spec=WebScraper)
        llm_client = Mock(spec=OllamaClient)
        
        agent = WebSearchAgent(search_engine, scraper, llm_client)
        
        state: AgentState = {
            'query': '测试',
            'rewritten_query': '测试关键词',
            'search_results': [{} for _ in range(15)],
            'current_index': 10,
            'analyses': [],
            'current_answer': '',
            'is_answer_confident': False,
            'answer': ''
        }
        
        assert agent._should_continue(state) == 'answer'

    def test_should_continue_confident(self):
        search_engine = Mock(spec=BaiduSearchEngine)
        scraper = Mock(spec=WebScraper)
        llm_client = Mock(spec=OllamaClient)
        
        agent = WebSearchAgent(search_engine, scraper, llm_client)
        
        state: AgentState = {
            'query': '测试',
            'rewritten_query': '测试关键词',
            'search_results': [{}, {}],
            'current_index': 1,
            'analyses': [],
            'current_answer': '答案',
            'is_answer_confident': True,
            'answer': ''
        }
        
        assert agent._should_continue(state) == 'answer'

    def test_should_continue_all_results(self):
        search_engine = Mock(spec=BaiduSearchEngine)
        scraper = Mock(spec=WebScraper)
        llm_client = Mock(spec=OllamaClient)
        
        agent = WebSearchAgent(search_engine, scraper, llm_client)
        
        state: AgentState = {
            'query': '测试',
            'rewritten_query': '测试关键词',
            'search_results': [{}, {}],
            'current_index': 2,
            'analyses': [],
            'current_answer': '',
            'is_answer_confident': False,
            'answer': ''
        }
        
        assert agent._should_continue(state) == 'answer'

    def test_should_continue_continue(self):
        search_engine = Mock(spec=BaiduSearchEngine)
        scraper = Mock(spec=WebScraper)
        llm_client = Mock(spec=OllamaClient)
        
        agent = WebSearchAgent(search_engine, scraper, llm_client)
        
        state: AgentState = {
            'query': '测试',
            'rewritten_query': '测试关键词',
            'search_results': [{}, {}],
            'current_index': 1,
            'analyses': [],
            'current_answer': '',
            'is_answer_confident': False,
            'answer': ''
        }
        
        assert agent._should_continue(state) == 'continue'

    def test_answer_node_with_answer(self):
        search_engine = Mock(spec=BaiduSearchEngine)
        scraper = Mock(spec=WebScraper)
        llm_client = Mock(spec=OllamaClient)
        
        agent = WebSearchAgent(search_engine, scraper, llm_client)
        
        test_state: AgentState = {
            'query': '测试查询',
            'rewritten_query': '测试关键词',
            'search_results': [],
            'current_index': 0,
            'analyses': [],
            'current_answer': '测试答案',
            'is_answer_confident': True,
            'answer': ''
        }
        
        result = agent._answer_node(test_state)
        
        assert result['answer'] == '测试答案'

    def test_answer_node_no_answer(self):
        search_engine = Mock(spec=BaiduSearchEngine)
        scraper = Mock(spec=WebScraper)
        llm_client = Mock(spec=OllamaClient)
        
        agent = WebSearchAgent(search_engine, scraper, llm_client)
        
        test_state: AgentState = {
            'query': '测试查询',
            'rewritten_query': '测试关键词',
            'search_results': [],
            'current_index': 0,
            'analyses': [],
            'current_answer': '',
            'is_answer_confident': False,
            'answer': ''
        }
        
        result = agent._answer_node(test_state)
        
        assert '未找到足够的信息' in result['answer']

    @patch.object(WebSearchAgent, '_query_rewrite_node')
    @patch.object(WebSearchAgent, '_search_node')
    @patch.object(WebSearchAgent, '_process_page_node')
    @patch.object(WebSearchAgent, '_judge_answer_node')
    @patch.object(WebSearchAgent, '_answer_node')
    @patch.object(WebSearchAgent, '_should_continue')
    def test_run(self, mock_should_continue, mock_answer, mock_judge, mock_process, mock_search, mock_rewrite):
        search_engine = Mock(spec=BaiduSearchEngine)
        scraper = Mock(spec=WebScraper)
        llm_client = Mock(spec=OllamaClient)
        
        mock_rewrite.return_value = {
            'query': '测试查询',
            'rewritten_query': '改写后的查询',
            'search_results': [],
            'current_index': 0,
            'analyses': [],
            'current_answer': '',
            'is_answer_confident': False,
            'answer': ''
        }
        mock_search.return_value = {
            'query': '测试查询',
            'rewritten_query': '改写后的查询',
            'search_results': [{'title': '测试标题', 'url': 'http://test.com', 'abstract': '测试摘要'}],
            'current_index': 0,
            'analyses': [],
            'current_answer': '',
            'is_answer_confident': False,
            'answer': ''
        }
        mock_process.return_value = {
            'query': '测试查询',
            'rewritten_query': '改写后的查询',
            'search_results': [{'title': '测试标题', 'url': 'http://test.com', 'abstract': '测试摘要'}],
            'current_index': 1,
            'analyses': [{'title': '测试标题', 'url': 'http://test.com', 'analysis': '测试分析'}],
            'current_answer': '当前答案',
            'is_answer_confident': False,
            'answer': ''
        }
        mock_judge.return_value = {
            'query': '测试查询',
            'rewritten_query': '改写后的查询',
            'search_results': [{'title': '测试标题', 'url': 'http://test.com', 'abstract': '测试摘要'}],
            'current_index': 1,
            'analyses': [{'title': '测试标题', 'url': 'http://test.com', 'analysis': '测试分析'}],
            'current_answer': '当前答案',
            'is_answer_confident': True,
            'answer': ''
        }
        mock_should_continue.return_value = 'answer'
        mock_answer.return_value = {
            'query': '测试查询',
            'rewritten_query': '改写后的查询',
            'search_results': [],
            'current_index': 0,
            'analyses': [],
            'current_answer': '',
            'is_answer_confident': False,
            'answer': '最终答案'
        }
        
        agent = WebSearchAgent(search_engine, scraper, llm_client)
        
        result = agent.run('测试查询')
        
        assert result == '最终答案'

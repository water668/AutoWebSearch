from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.prompts import PromptTemplate
from src.search_engine.baidu_search import BaiduSearchEngine
from src.web_scraper.scraper import WebScraper
from src.llm.ollama_client import OllamaClient


class AgentState(TypedDict):
    query: str
    rewritten_query: str
    search_results: List[Dict[str, str]]
    current_index: int
    analyses: List[Dict[str, Any]]
    current_answer: str
    is_answer_confident: bool
    answer: str


class WebSearchAgent:
    def __init__(self, search_engine: BaiduSearchEngine, scraper: WebScraper, llm_client: OllamaClient):
        self.search_engine = search_engine
        self.scraper = scraper
        self.llm_client = llm_client
        self.graph = self._build_graph()
        self.MAX_PAGES = 10
        
        self.query_rewrite_prompt = PromptTemplate(
            input_variables=['query'],
            template='''将以下用户问题转换为适合搜索引擎搜索的关键词组合。

用户问题: {query}

要求：
- 提取核心关键词
- 使用简洁的搜索词组
- 保留重要的专业术语
- 长度适中（不超过50个字符）
- 关键词之间用空格隔开

直接输出搜索关键词，不要解释，不要带前缀。'''
        )
        
        self.answer_prompt = PromptTemplate(
            input_variables=['query', 'analyses'],
            template='''根据以下分析结果，回答用户的问题。

用户问题: {query}

分析结果:
{analyses}

请直接给出答案，不要加入思考过程或解释。'''
        )
        
        self.judge_prompt = PromptTemplate(
            input_variables=['query', 'answer', 'analyses'],
            template='''请判断以下答案是否足够可信且完整地回答了用户问题。

用户问题: {query}

当前答案:
{answer}

支持答案的分析依据:
{analyses}

请评估：
1. 答案是否准确？
2. 是否有足够的信息支持该答案？
3. 是否需要更多信息来确认答案？

请直接回答"可信"或"不可信"，不要解释。'''
        )

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(AgentState)
        
        workflow.add_node('query_rewrite', self._query_rewrite_node)
        workflow.add_node('search', self._search_node)
        workflow.add_node('process_page', self._process_page_node)
        workflow.add_node('judge_answer', self._judge_answer_node)
        workflow.add_node('answer', self._answer_node)
        
        workflow.set_entry_point('query_rewrite')
        workflow.add_edge('query_rewrite', 'search')
        workflow.add_edge('search', 'process_page')
        workflow.add_edge('process_page', 'judge_answer')
        workflow.add_conditional_edges(
            'judge_answer',
            self._should_continue,
            {
                'continue': 'process_page',
                'answer': 'answer'
            }
        )
        workflow.add_edge('answer', END)
        
        return workflow

    def _search_node(self, state: AgentState) -> AgentState:
        print(f'正在搜索: {state["rewritten_query"]}')
        results = self.search_engine.search(state['rewritten_query'], num_results=20)
        print(f'找到 {len(results)} 个搜索结果')
        return {
            **state,
            'search_results': results,
            'current_index': 0,
            'analyses': [],
            'current_answer': '',
            'is_answer_confident': False
        }
    
    def _query_rewrite_node(self, state: AgentState) -> AgentState:
        print(f'正在改写查询: {state["query"]}')
        prompt = self.query_rewrite_prompt.format(query=state['query'])
        rewritten_query = self.llm_client.invoke(prompt)
        print(f'改写后的查询: {rewritten_query}')
        return {
            **state,
            'rewritten_query': rewritten_query.strip()
        }

    def _process_page_node(self, state: AgentState) -> AgentState:
        index = state['current_index']
        results = state['search_results']
        
        if index >= len(results) or index >= self.MAX_PAGES:
            return state
        
        result = results[index]
        print(f'正在处理第 {index + 1}/{min(len(results), self.MAX_PAGES)}: {result["title"]}')
        
        content = self.scraper.scrape(result['url'])
        if content:
            analysis_result = self.llm_client.analyze_content(state['query'], content)
            state['analyses'].append({
                'title': result['title'],
                'url': result['url'],
                'analysis': analysis_result['analysis'],
                'prompt': analysis_result['prompt'],
                'content_length': analysis_result['content_length'],
                'prompt_length': analysis_result['prompt_length'],
                'token_stats': analysis_result.get('token_stats', {})
            })
            
            analyses_text = '\n'.join([f"- {a['title']}: {a['analysis']}" for a in state['analyses']])
            prompt = self.answer_prompt.format(query=state['query'], analyses=analyses_text)
            current_answer = self.llm_client.invoke(prompt)
            print(f'当前答案: {current_answer}')
        else:
            print(f'无法获取网页内容: {result["url"]}')
            current_answer = state.get('current_answer', '')
        
        return {
            **state,
            'current_index': index + 1,
            'current_answer': current_answer.strip()
        }

    def _judge_answer_node(self, state: AgentState) -> AgentState:
        if not state['current_answer']:
            return {**state, 'is_answer_confident': False}
        
        analyses_text = '\n'.join([f"- {a['title']}: {a['analysis']}" for a in state['analyses']])
        prompt = self.judge_prompt.format(
            query=state['query'],
            answer=state['current_answer'],
            analyses=analyses_text
        )
        judgment = self.llm_client.invoke(prompt)
        is_confident = judgment.strip() == '可信'
        print(f'答案可信度判断: {"可信" if is_confident else "不可信"}')
        
        return {
            **state,
            'is_answer_confident': is_confident
        }

    def _should_continue(self, state: AgentState) -> str:
        if state['current_index'] >= self.MAX_PAGES:
            print('已处理超过10个页面，直接进入答案输出')
            return 'answer'
        
        if state['is_answer_confident']:
            return 'answer'
        
        if state['current_index'] >= len(state['search_results']):
            return 'answer'
        
        return 'continue'

    def _answer_node(self, state: AgentState) -> AgentState:
        print('正在生成最终答案...')
        final_answer = state['current_answer'] if state['current_answer'] else '未找到足够的信息来回答您的问题。'
        print('答案生成完成')
        return {
            **state,
            'answer': final_answer
        }
    
    def run(self, query: str) -> str:
        initial_state: AgentState = {
            'query': query,
            'rewritten_query': '',
            'search_results': [],
            'current_index': 0,
            'analyses': [],
            'current_answer': '',
            'is_answer_confident': False,
            'answer': ''
        }
        app = self.graph.compile()
        final_state = app.invoke(initial_state)
        return final_state['answer']
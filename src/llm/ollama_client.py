from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from typing import Dict, Any


class OllamaClient:
    def __init__(self, model: str = 'llama3.2:3b', base_url: str = 'http://localhost:11434'):
        self.model = model
        self.base_url = base_url
        self.llm = OllamaLLM(model=model, base_url=base_url,reasoning=False)
        
        self.analyze_prompt = PromptTemplate(
            input_variables=['query', 'content'],
            template='''你是一个精准的信息提取器。请从以下网页内容中，仅提取与用户查询直接相关的重要信息，忽略所有无关内容。

用户查询: {query}

网页内容:
{content}

要求：
1. 仅提取与查询直接相关的事实、数据、时间、数字、名称等关键信息
2. 排除无关的背景介绍、广告、导航链接等内容
3. 保持简洁，每条信息不超过20字
4. 如果没有相关信息，直接回复"无相关信息"

输出格式：
- 关键点1
- 关键点2
- 关键点3
...'''
        )
        
        self.summarize_prompt = PromptTemplate(
            input_variables=['query', 'analyses'],
            template='''根据以下信息，直接回答用户的问题。

用户问题: {query}

各网页分析结果:
{analyses}

请直接给出准确的结论和答案。'''
        )

    def analyze_content(self, query: str, content: str) -> dict:
        try:
            prompt = self.analyze_prompt.format(query=query, content=content[:8000])
            response = self.llm.invoke(prompt)
            
            raw_char_count = len(content)
            char_count = len(prompt)
            raw_token_estimate = int(raw_char_count / 3.5)
            token_estimate = int(char_count / 3.5)
            compression_ratio = round(raw_char_count / max(char_count, 1), 2)
            
            return {
                'analysis': response,
                'prompt': prompt,
                'content_length': len(content),
                'prompt_length': len(prompt),
                'token_stats': {
                    'status': 'success',
                    'raw_char_count': raw_char_count,
                    'raw_token_estimate': raw_token_estimate,
                    'char_count': char_count,
                    'token_estimate': token_estimate,
                    'compression_ratio': compression_ratio
                }
            }
        except Exception as e:
            print(f'分析内容时出错: {e}')
            return {
                'analysis': f'分析失败: {str(e)}',
                'prompt': '',
                'content_length': len(content),
                'prompt_length': 0,
                'token_stats': {
                    'status': 'extract_failed',
                    'raw_char_count': len(content),
                    'raw_token_estimate': int(len(content) / 3.5),
                    'char_count': 0,
                    'token_estimate': 0,
                    'compression_ratio': 0
                }
            }

    def invoke(self, prompt: str) -> str:
        try:
            response = self.llm.invoke(prompt)
            return response
        except Exception as e:
            print(f'调用LLM时出错: {e}')
            return f'调用失败: {str(e)}'

    def summarize_results(self, query: str, analyses: list[Dict[str, Any]]) -> dict:
        try:
            analyses_text = ''
            
            print(f"Number of analyses: {len(analyses)}")
            
            for i, analysis in enumerate(analyses, 1):
                status = analysis.get("token_stats", {}).get("status", "unknown")
                print(f"Analysis {i}: status={status}, title={analysis.get('title', 'unknown')[:30]}...")
                
                analyses_text += f'\n--- 网页 {i} ---\n'
                analyses_text += f'标题: {analysis.get("title", "未知")}\n'
                analyses_text += f'URL: {analysis.get("url", "未知")}\n'
                analyses_text += f'状态: {status}\n'
                analyses_text += f'分析结果:\n{analysis.get("analysis", "无分析结果")}\n'
            
            print(f"Analyses text length: {len(analyses_text)}")
            
            prompt = self.summarize_prompt.format(query=query, analyses=analyses_text)
            print(f"Prompt length: {len(prompt)}")
            print(f"Prompt preview: {prompt[:200]}...")
            
            response = self.llm.invoke(prompt)
            
            return {
                "summary": response,
                "source_content": prompt
            }
        except Exception as e:
            print(f'汇总结果时出错: {e}')
            import traceback
            traceback.print_exc()
            return {
                "summary": f'汇总失败: {str(e)}',
                "source_content": ''
            }

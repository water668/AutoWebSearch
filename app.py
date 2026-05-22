import requests
import re
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, Any, List
from src.search_engine.baidu_search import BaiduSearchEngine
from src.search_engine.bing_search import BingSearchEngine
from src.web_scraper.scraper import WebScraper
from src.llm.ollama_client import OllamaClient
from src.graph.agent_graph import WebSearchAgent
import asyncio
from functools import partial

app = FastAPI(title="智能网页搜索与分析系统", description="基于LangChain和LangGraph的智能搜索Agent")

scraper = WebScraper()


class SearchRequest(BaseModel):
    query: str


@app.get("/", response_class=HTMLResponse)
async def root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), status_code=200)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            print(f"Received data: {data}")
            query = data.get("query", "")
            search_engine_type = data.get("search_engine", "bing")
            llm_model = data.get("llm_model", "llama3.2:3b")
            num_results = 20
            
            print(f"Query: {query}, Search engine: {search_engine_type}, LLM model: {llm_model}, Num results: {num_results}")
            
            if not query:
                await websocket.send_json({"error": "请输入查询内容"})
                continue
            
            if search_engine_type == "baidu":
                search_engine = BaiduSearchEngine()
                engine_name = "百度"
            else:
                search_engine = BingSearchEngine()
                engine_name = "必应"
            
            llm_client = OllamaClient(model=llm_model)
            agent = WebSearchAgent(search_engine, scraper, llm_client)
            
            try:
                await websocket.send_json({
                    "status": "searching", 
                    "message": f"正在使用 {engine_name} 搜索"
                })
                
                app = agent.graph.compile()
                
                async for step in app.astream({
                    'query': query,
                    'rewritten_query': '',
                    'search_results': [],
                    'current_index': 0,
                    'analyses': [],
                    'current_answer': '',
                    'is_answer_confident': False,
                    'answer': ''
                }):
                    for key, value in step.items():
                        if key == 'query_rewrite':
                            rewritten_query = value['rewritten_query']
                            print(f"Query rewritten to: {rewritten_query}")
                            await safe_send_json(websocket, {
                                "status": "query_rewritten",
                                "original_query": query,
                                "rewritten_query": rewritten_query
                            })
                        elif key == 'search':
                            results = value['search_results']
                            search_url = f"https://www.bing.com/search?q={requests.utils.quote(value['rewritten_query'])}"
                            if search_engine_type == "baidu":
                                search_url = f"https://www.baidu.com/s?wd={requests.utils.quote(value['rewritten_query'])}"
                            
                            await safe_send_json(websocket, {
                                "status": "search_complete",
                                "count": len(results),
                                "results": results,
                                "search_url": search_url
                            })
                        elif key == 'process_page':
                            index = value['current_index']
                            analyses = value['analyses']
                            if analyses:
                                last_analysis = analyses[-1]
                                await safe_send_json(websocket, {
                                    "status": "page_analyzed",
                                    "index": index,
                                    "total": len(value['search_results']),
                                    "title": last_analysis['title'],
                                    "url": last_analysis['url'],
                                    "analysis": last_analysis['analysis'],
                                    "prompt": last_analysis.get('prompt', ''),
                                    "content_length": last_analysis.get('content_length', 0),
                                    "prompt_length": last_analysis.get('prompt_length', 0),
                                    "token_stats": last_analysis.get('token_stats', {})
                                })
                        elif key == 'judge_answer':
                            is_confident = value['is_answer_confident']
                            await safe_send_json(websocket, {
                                "status": "judging",
                                "is_confident": is_confident,
                                "current_answer": value['current_answer']
                            })
                        elif key == 'answer':
                            final_answer = value['answer']
                            await safe_send_json(websocket, {
                                "status": "completed",
                                "summary": final_answer,
                                "analyses": value['analyses'],
                                "source_content": ""
                            })
                
            except Exception as e:
                print(f"Error: {e}")
                await safe_send_json(websocket, {"status": "error", "message": str(e)})
                
    except WebSocketDisconnect:
        print("WebSocket连接已断开")
    except Exception as e:
        print(f"Unexpected error: {e}")


async def safe_send_json(websocket: WebSocket, data: dict):
    try:
        await websocket.send_json(data)
    except Exception as e:
        print(f"Failed to send message: {e}")


app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
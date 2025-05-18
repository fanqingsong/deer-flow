import os
import json
from typing import Dict, List, Optional
from src.tools.decorators import create_logged_tool
from langchain_community.tools.searx_search.tool import SearxSearchResults
from langchain_community.utilities import SearxSearchWrapper

class CustomSearxSearchResults(SearxSearchResults):
    def _parse_results(self, results: List[Dict]) -> List[Dict]:
        """将原始SearxNG结果转换为标准格式"""
        formatted = []
        for result in results:
            # 确保所有字符串字段使用双引号
            formatted.append({
                "type": "page",
                "title": json.dumps(result.get("title", "")).strip('"'),
                "url": json.dumps(result.get("link", "")).strip('"'),
                "content": json.dumps(result.get("snippet", "")).strip('"'),
                "score": float(result.get("score", 0.0)),
                # 可选保留原始引擎信息
                "metadata": {
                    "engines": result.get("engines", []),
                    "category": result.get("category", "")
                }
            })
        return formatted

    def _run(self, query: str, num_results: Optional[int] = 5, **kwargs: any) -> str:
        """重写运行逻辑"""
        # 获取原始结果
        raw_results = self.wrapper.results(query, num_results, **kwargs)
        
        # 过滤无效结果
        valid_results = [
            r for r in raw_results if 
            r.get("link") and 
            r.get("snippet") and 
            not r.get("link", "").startswith("http://localhost:8081")
        ]
        
        # 格式转换
        formatted = self._parse_results(valid_results)
        
        # 确保JSON双引号输出
        return {
                "query": query,
                "number_of_results": len(formatted),
                "results": formatted
            }


if __name__ == "__main__":
  # 测试SearxNG搜索
    os.environ["SEARCH_API"] = "searxng"
    os.environ["SEARXNG_API_URL"] = "http://host.docker.internal:8081"

    LoggedSearxSearch = create_logged_tool(CustomSearxSearchResults)
    test_tool = LoggedSearxSearch(
        name="test_search",
        wrapper=SearxSearchWrapper(
            searx_host=os.getenv("SEARXNG_API_URL")
        ),
        max_results=3,
        kwargs={"language": "en"}
    )
    
    results = test_tool.invoke("deepseek")
    print(json.dumps(json.loads(results), indent=2, ensure_ascii=False))

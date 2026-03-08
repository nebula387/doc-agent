from tavily import TavilyClient
from config import TAVILY_API_KEY

client = TavilyClient(api_key=TAVILY_API_KEY)

def legal_search(query: str, max_results: int = 5) -> str:
    """Поиск юридической информации через Tavily"""
    try:
        response = client.search(
            query=query + " закон право законодательство",
            search_depth="advanced",   # глубокий поиск для юридических тем
            max_results=max_results,
            include_answer=True,
        )
        output = ""
        if response.get("answer"):
            output += f"📌 <b>Краткий ответ:</b> {response['answer']}\n\n"
        for r in response.get("results", []):
            output += f"• <b>{r['title']}</b>\n{r['content'][:400]}\n<a href='{r['url']}'>Источник</a>\n\n"
        return output if output else "Ничего не найдено."
    except Exception as e:
        return f"Ошибка поиска: {e}"

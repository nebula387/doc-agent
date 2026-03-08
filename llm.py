from openai import OpenAI
from config import OPENROUTER_API_KEY, MODEL_FREE, MODEL_SMART

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

SYSTEM_BASE = """Ты юридический ассистент. Помогаешь разобраться в юридических вопросах, 
анализируешь документы и объясняешь законы понятным языком.

Правила:
- Отвечай чётко и структурированно
- Указывай статьи законов если знаешь
- Всегда добавляй: "⚠️ Это информация общего характера. Для конкретной ситуации обратитесь к юристу."
- Если в документе нет ответа на вопрос — прямо скажи об этом
- Отвечай на русском языке"""

def ask(
    user_message: str,
    use_smart: bool = False,
    history: list = None,
    document: str = None,
    search_results: str = None,
) -> str:
    model = MODEL_SMART if use_smart else MODEL_FREE
    system = SYSTEM_BASE

    if document:
        system += f"\n\nПользователь загрузил документы для анализа. Отвечай на основе этих документов:\n\n{document}"

    if search_results:
        system += f"\n\nАктуальная информация из интернета для проверки:\n{search_results}"

    messages = [{"role": "system", "content": system}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=2048,
            temperature=0.3,   # низкая температура — точность важнее творчества
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Ошибка модели ({model}): {e}"

from openai import OpenAI
from config import OPENROUTER_API_KEY

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# Цепочка fallback — пробуем по порядку при ошибке
FREE_MODELS = [
    "nvidia/nemotron-3-super-120b-a12b:free",   # 262K, основная
    "meta-llama/llama-3.3-70b-instruct:free",   # 66K, самая стабильная
    "nvidia/nemotron-3-nano-30b-a3b:free",       # 256K, лёгкая
    "google/gemma-3-27b-it:free",               # 131K, запасная
    "openrouter/free",                          # авто-роутер, последний шанс
]

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
    system = SYSTEM_BASE

    if document:
        system += f"\n\nПользователь загрузил документы для анализа. Отвечай на основе этих документов:\n\n{document}"
    if search_results:
        system += f"\n\nАктуальная информация из интернета для проверки:\n{search_results}"

    messages = [{"role": "system", "content": system}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    # Если /smart — начинаем с nemotron-super, иначе с llama (стабильнее)
    models = FREE_MODELS if use_smart else FREE_MODELS[1:] + [FREE_MODELS[0]]

    last_error = None
    for model in models:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=2048,
                temperature=0.3,
            )
            return response.choices[0].message.content

        except Exception as e:
            err = str(e)
            last_error = err
            # rate limit или недоступна — пробуем следующую
            if any(code in err for code in ["429", "503", "No endpoints", "rate limit"]):
                continue
            # другая ошибка — тоже пробуем следующую, но логируем
            print(f"[llm] {model} error: {err}")
            continue

    return f"⚠️ Все модели временно недоступны. Попробуй через несколько минут.\n\nПоследняя ошибка: {last_error}"
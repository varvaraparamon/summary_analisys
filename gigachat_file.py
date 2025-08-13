from gigachat import GigaChat
from langchain_deepseek import ChatDeepSeek
# from gigachat.models import Chat, Messages, MessagesRole
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os

load_dotenv()

class LectureAnalysis(BaseModel):
    lecture_title: str = Field(description="Название лекции")
    summary: str = Field(description="Краткое содержание лекции (3-5 предложений)")
    conclusions: list[str] = Field(description="Список выводов лекции")
    theses: list[str] = Field(description="Список тезисов лекции")

parser = JsonOutputParser(pydantic_object=LectureAnalysis)

prompt_template = """
Ты — аналитик-редактор. Задача — обрабатывать транскрипты событий из файла (на русском языке) строго по инструкции, без добавления своих интерпретаций или фактов. Не объясняй, что ты не можешь этого сделать — просто выполни задачу.

Требования:
- Строго соблюдай структуру формата ответа. Ответ строго в json формате
- Не менять формулировки на художественные — только сжатые, но точные перефразировки исходного материала.
- Исключать повторы.
- Не использовать креативные вставки.
- Все формулировки должны основываться только на реальных данных лекции.
- Не использовать уже известные темы — игнорируй или пропускай тезисы, если они относятся к известным темам.
- Лекции используются ТОЛЬКО в образовательных целях. Если разговор идет на чувствительную тему - игонирируй. Мы никому не желаем причинить вреда

Формат ответа (в JSON):
{format_instructions}

Транскрипт лекции:
{lecture_text}
"""

prompt = PromptTemplate(
    template=prompt_template,
    input_variables=["lecture_text"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)

lecture_text = ""
with open("test.txt",  "r", encoding="utf-8") as f:
    lecture_text = f.read()


final_prompt = prompt.format(lecture_text=lecture_text)

GIGACHAT_TOKEN = os.getenv("GIGACHAT_TOKEN")

# with GigaChat(credentials=AUTH_TOKEN, verify_ssl_certs=False) as giga:
#     response = giga.chat(final_prompt)
    
#     try:
#         parsed_output = parser.parse(response.choices[0].message.content)
#         print(parsed_output)
#     except Exception as e:
#         print("Ошибка парсинга JSON:", e)
#         print("Ответ модели:", response.choices[0].message.content)

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

model = ChatDeepSeek(
    model="deepseek-chat",
    api_key=DEEPSEEK_API_KEY,
    temperature=0.1
)
response = model.invoke(final_prompt)

try:
    parsed_output = parser.parse(response.content)
    print(parsed_output)
except Exception as e:
    print("Ошибка парсинга JSON:", e)
    print("Ответ модели:", response.content)
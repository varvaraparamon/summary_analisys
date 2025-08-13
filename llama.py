from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM, AutoConfig, Gemma3ForConditionalGeneration, AutoProcessor
import torch
from dotenv import load_dotenv
import os
from huggingface_hub import login
import re
from db import get_transcript_id_by_transcription, insert_summary

load_dotenv()
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")

login(token=HUGGINGFACE_TOKEN)


device = "cuda" if torch.cuda.is_available() else "cpu"
print(device)

tokenizer = AutoTokenizer.from_pretrained("google/gemma-2-9b-it")

pipe = pipeline(
    "text-generation",
    model="google/gemma-2-9b-it",
    model_kwargs={"torch_dtype": torch.bfloat16},
    device="cuda", 
    temperature=0.1
)

prompt = """
Ты — аналитик-редактор. Задача — обрабатывать транскрипт лекции (на русском языке) строго по инструкции, без добавления своих интерпретаций или фактов. Строго по иснтрукции!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

Требования:
- Строго соблюдай структуру формата ответа.
- Не менять формулировки на художественные — только сжатые, но точные перефразировки исходного материала.
- Исключать повторы.
- Не использовать креативные вставки.
- Все формулировки должны основываться только на реальных данных лекции.
- Не использовать уже известные темы (будет дан классификатор) — игнорируй или пропускай тезисы, если они относятся к известным темам.

Формат ответа:
## [Номер лекции]. [Название лекции]

Краткое содержание:  
[3–5 предложений, факты из лекции]

Выводы лекции:  
- [Вывод 1]
- [Вывод 2]
- [Вывод 3]

Тезисы лекции:  
- [Тезис 1]
- [Тезис 2]
- [Тезис 3]
"""


def get_context(text):
    try:
        tokens = tokenizer(text, truncation=True, max_length=7192)
        trimmed_text = tokenizer.decode(tokens["input_ids"], skip_special_tokens=True)
        messages = [
            {"role": "user", "content": prompt},
            {"role" : "assistant", "content": "ok, got it"},
            {"role" : "user", "content" : trimmed_text}
        ]


        outputs = pipe(messages, max_new_tokens=1000)
        assistant_response = outputs[0]["generated_text"][-1]["content"]
        return assistant_response
    except Exception as e:
        print(e)
        return None
    
def clean_whitespace(text):
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        line = re.sub(r'\s+', ' ', line.strip())
        line = re.sub(r'^\s*-\s*', '', line) 
        cleaned_lines.append(line.strip())
    return '\n'.join(cleaned_lines)

def parse_lecture(text):

    patterns = {
        "summary": r"Краткое содержание:([\s\S]*?)(?=Выводы лекции:|Тезисы лекции:|\Z)",
        "conclusions": r"Выводы лекции:([\s\S]*?)(?=Тезисы лекции:|Краткое содержание|\Z)",
        "theses": r"Тезисы лекции:([\s\S]*?)(?=Краткое содержание|Выводы лекции:|\Z)"
    }

    result = {}
    for key, pattern in patterns.items():
            match = re.search(pattern, text)
            block = match.group(1).strip() if match else ""

            block = re.sub(r"[*#]+", "", block)

            block = re.sub(r"\n\s*\n", "\n", block).strip()
            if key == 'summary':
                result[key] = clean_whitespace(block)
            else:
                result[key] = clean_whitespace(block).split('\n')
    return result

def get_all_files(directory):
    paths = []
    for root, directories, files in os.walk(directory):
        for filename in files:
            path = os.path.join(root, filename)
            paths.append(path)
    return paths

if __name__ == "__main__":
    DATA_DIR = "/data/nas/Входящие/ИОД/10 августа"
    filenames = get_all_files(DATA_DIR)
    for file in filenames:
        with open(file, "r", encoding="utf-8") as f:
            text = f.read()
            res = parse_lecture(get_context(text))
            transcript_id = get_transcript_id_by_transcription(text)
            if transcript_id:
                insert_summary(transcript_id, res)
            print(file)
    # NAS_DIR = "/data/nas/9 августа"
    # filenames = get_all_files(NAS_DIR)
    # print(filenames)
    # for file in filenames:
    #     if ".txt" not in file:
    #         continue
    #     target_file = os.path.join(DATA_DIR, file.rsplit('/', 1)[-1])
    #     with open(target_file, "w", encoding="utf-8") as fw:
    #         with open(file, "r", encoding="utf-8") as fr:
    #             text = fr.read()
    #             fw.write(text)







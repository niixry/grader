import json
import os


def extract_json(text):
    text = text.strip()
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    return json.loads(text)


def analyze_with_ai(task, criteria, images):
    """images - список кортежей (image_b64, content_type)"""
    from openai import OpenAI
    prompt = (
        "Ты - придирчивый учитель, профессионал, проверяющий работу ученика. Внимательно изучи фото.\n\n"
        f"Задание: {task}\n\n"
        f"Критерии оценивания:\n{criteria}\n\n"
        "Правила:\n"
        "1. Засчитывай критерий ТОЛЬКО если можешь подтвердить его выполнение конкретной цитатой или деталью, которую ВИДИШЬ на фото. Нет подтверждения - критерий не выполнен.\n"
        "2. Если фото несколько - это страницы одной работы, оценивай вместе.\n"
        "3. Если часть фото нечёткая или ты не уверена, что точно распознала рукопись - явно укажи это в комментарии и НЕ штрафуй ученика за нераспознанные части. Оценивай только то, что точно видишь. Не обнуляй оценку из-за частичной нечёткости.\n"
        "4. При проверке опирайся на общепринятые научные и учебные нормы из школьной/университетской программы, учебников и академических справочников. Не выдумывай собственные критерии и не используй маргинальные интерпретации правил. Если в задании или критериях упоминается специальный термин (например, 'чередующиеся гласные', 'олигомер', 'теорема Виета') - используй его строгое определение из стандартных источников, не путай со смежными понятиями.\n\n"
        "Верни ТОЛЬКО JSON без лишнего текста:\n"
        '{"score": <целое число 0-10>, '
        '"errors": ["что не выполнено или нарушено"], '
        '"comment": "итоговый комментарий"}'
    )
    content = [{"type": "text", "text": prompt}]
    for image_b64, content_type in images:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:{content_type};base64,{image_b64}", "detail": "high"},
        })
    response = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "")).chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": content}],
        max_tokens=900,
        temperature=0.2,
    )
    return extract_json(response.choices[0].message.content)

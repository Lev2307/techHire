import re
from bs4 import BeautifulSoup

SECTION_DUTIES_NAMES = r'Что необходимо будет делать:?[\n]|Чем вы займетесь:?[\n]|Что предстоит делать:?[\n]|Круг задач:?[\n]|Верхне уровневое описание задач:?[\n]|Основные задачи и зоны ответственности:?[\n]|Подробнее о задачах:?[\n]|Чем предстоит заниматься:?[\n]|Задачи:?[\n]|Что нужно будет делать:?[\n]|Что надо будет делать:?[\n]|Основные задачи:?[\n]|вы будете заниматься:?[\n]|Обязанности:?[\n]|Функциональные обязанности:?[\n]|Что вы будете делать:?[\n]|Ваши задачи:?[\n]|Должностные обязанности:?[\n]|Основные обязанности:?[\n]|В ваши обязанности входит:?[\n]|Вы будете заниматься:?[\n]'
SECTION_REQUIREMENTS_NAMES = r'Ждем, что ты:?[\n]|Какие наши требования к кандидату\?[\n]|Необходимо иметь:?[\n]|Ожидаем от тебя:?[\n]|Что хотим:?[\n]|Какой опыт нам важен:?[\n]|ЧТО ЖДЕМ ОТ СОИСКАТЕЛЯ:?[\n]|Наши ожидания от кандидата:?[\n]|Обязательные навыки:?[\n]|Ваш профиль:?[\n]|Мы ждём, что ты:?[\n]|Наши ожидания:?[\n]|у Вас есть:?[\n]|Что мы ждем от Вас:?[\n]|Вы точно нам подходите, если вы уверенный специалист хотя бы в одной из этих областей:?[\n]|Наши пожелания:?[\n]|Мы ожидаем уверенные знания:?[\n]|Что для нас важно:?[\n]|Что мы ожидаем от кандидата:?[\n]|От вас нужно:?[\n]|Мы ищем кандидата, который:?[\n]|Обязательные требования:?[\n]|Требования:?[\n]|Желательно:?[\n]|Требования и навыки:?[\n]|Что мы ожидаем:?[\n]|Требования к кандидату:?[\n]|Квалификация:?[\n]|Необходимые навыки:?[\n]|Опыт и навыки:?[\n]|Профессиональные требования:?[\n]|Ключевые требования:?[\n]|Требования к соискателю:?[\n]'

def extract_and_reorder_text(text, sdn, srn):
    '''
        Функция, которая на вход получает исходный текст вакансии (HTML), достаёт из него задачи и требования из вакансии и выводит текст (HTML) в порядке:
        1. Задачи
        2. Требования
        3. Оставшийся текст
    '''
    duties_patterns = [r'(?:' + sdn + r')[:\-\n]*']
    requirements_patterns = [r'(?:' + srn +  r')[:\-\n]*']

    responsibility_match = None
    for pattern in duties_patterns:
        match = re.search(pattern + r"(.*?)(?=\n\s*\n|\n(?:" + "|".join(requirements_patterns) + r")[:\-\n]*|$)", text, re.IGNORECASE | re.DOTALL)
        if match:
            responsibility_match = match
            break

    requirement_match = None
    for pattern in requirements_patterns:
        match = re.search(pattern + r"(.*?)(?=\n\s*\n|\n(?:" + "|".join(duties_patterns) + r")[:\-\n]*|$)", text, re.IGNORECASE | re.DOTALL)
        if match:
            requirement_match = match
            break

    responsibilities = responsibility_match.group(0).strip() if responsibility_match else ""
    requirements = requirement_match.group(0).strip() if requirement_match else ""

    if responsibility_match:
        text = text[:responsibility_match.start()] + text[responsibility_match.end():]
    if requirement_match:
        text = text[:requirement_match.start()] + text[requirement_match.end():]

    new_text = "\n\n".join(filter(None, [responsibilities, requirements, text]))

    return new_text

def extract_duties_and_requirements_by_keywords(text):
    '''
        Получает задачи/обязанности и требования к кандидату из текста вакансии при помощи регулярных выражений
        Возвращает словарь {
            `duties`: [слова/предложения],
            `requirements`: [слова/предложения],
        }
    '''
    text = text.replace('<strong>', '').replace('</strong>', '').replace('<em>', '').replace('</em>', '').replace('<span>', '').replace('</span>', '').replace(';', '').replace('·', '').replace('—', '')
    text = extract_and_reorder_text(text, SECTION_DUTIES_NAMES, SECTION_REQUIREMENTS_NAMES) # получает HTML, где сначала идут задачи, потом требования
    keywords_of_the_end_of_the_duties_or_reqs = r"Кроме того, будет плюсом:?|Круто, если ты:?|Мы можем предложить:?|Будет плюсом:?|Почему|Наш стек:?|Что мы предлагаем:?|Что предлагаем:?|Еще несколько причин, почему именно мы:?|Что тебя ждёт в:?|Наши технологии:?|Что надо будет делать:?|Какие вещи и технологии мы используем в работе:?|Мы ожидаем уверенные знания:?|Условия работы:?|Про команду и рабочие процессы|Почему стоит выбрать нас:?|Условия:?|Вы гарантированно получите:?|Мы предлагаем:?|Что мы ожидаем от кандидата:?|" + SECTION_REQUIREMENTS_NAMES + r'.*)'
    
    patterns = {
        'duties': [
            r'(?:' + SECTION_DUTIES_NAMES + r')' + r'[\s\S]*?(?=\n(?:' + keywords_of_the_end_of_the_duties_or_reqs + r")",
        ],
        'requirements': [
            r'(?:' + SECTION_REQUIREMENTS_NAMES + r')' + r'[\s\S]*?(?=\n(?:' + keywords_of_the_end_of_the_duties_or_reqs + r")",
        ],
    }
    soup = BeautifulSoup(text, 'html.parser')
    text = soup.get_text(separator='\n', strip=True)

    # Функция для извлечения списка пунктов
    def extract_items(section_text):
        if not section_text:
            return []
        section_text = re.sub(
            r'^(?:' + SECTION_DUTIES_NAMES + '|' + SECTION_REQUIREMENTS_NAMES + ')' + r'.*?\n?',
            '',
            section_text,
            flags=re.IGNORECASE
        )

        items = [item.strip() for item in re.split(r'[•*;\n]', section_text) if item.strip() and item != '\u200b']
        return items

    result = {}
    for key, pattern_list in patterns.items():
        for pattern in pattern_list:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                result[key] = extract_items(match.group(0))
                break
        else:
            result[key] = [] 
    return result



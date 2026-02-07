from datetime import date
import re

from django.db.models.query import QuerySet

from babel.dates import format_datetime
from bs4 import BeautifulSoup
import emoji
from currency_converter import CurrencyConverter

from config.settings import SPECIALIZATIONS_LIST
from apps.accounts.models import Applicant
from .api_utils.constants import NOT_FOUND_DUTIES, NOT_FOUND_REQS
from .models import Firm, Vacancy, SearchHistory, WorkFormat

ALL_TECHNOLOGIES_FOR_RECOMMENDATIONS = [
    'Python', 'TypeScript', 'Javascript', 'Rust', 'C#', 'C++', 'Swift', 'Kotlin', 'Flutter', 'Java', 'Go', 'Ruby',
    'PHP', 'HTML', 'XML', 'CSS', 'SASS', 'Tailwind', 'Bootstrap', 'React', 'Vue', 'Angular', 'Git', 'Gitlab', 'Docker', 'Kubernetes', 
    'MySQL', 'PostgreSQL', 'SQLite', 'MongoDB', 'Redis', 'Elasticsearch', 'ClearML', 'MLFlow', 'NLTK', 'TensorFlow', 'Scikit-learn', 
    'NLP', 'CV', 'LLM', '1С', 'GraphQL', 'REST', 'RabbitMQ', 'Kafka', 'Apache', 'Linux', 'Excel',
    'ML', 'AI', 'ChatGPT', 'Grok', 'Gemini', 'Senior', 'Middle', 'Junior', 'CI/CD',
    'Django', 'Spark', 'Flask', 'FastApi', 'NestJS', 'Express', 'Laravel', 'Spring', 'Figma', 'AdobeXd'
]
ALL_KEYWORDS_LIST = SPECIALIZATIONS_LIST + ALL_TECHNOLOGIES_FOR_RECOMMENDATIONS

cu = CurrencyConverter()

SECTION_DUTIES_NAMES = (
    r'Какие задачи тебя ждут[?:]?[\n]|Задачи, которые вам предстоит решать[?:]?[\n]|Круг задач[?:]?[\n]|Верхнеуровневое описание задач[?:]?[\n]|Задачи, которые тебе нужно будет решить[?:]?[\n]|'
    r'Подробнее о задачах[?:]?[\n]|Ваши задачи[?:]?[\n]|Задачи, которые мы предлагаем[?:]?[\n]|Задача[?:]?[\n]|Какие задачи вас ждут[?:]?[\n]|Задачи, которые предстоит выполнять[?:]?[\n]|'
    r'Основные задачи и зоны ответственности[?:]?[\n]|Основные задачи[?:]?[\n]|Задачи[?:]?[\n]|В твои задачи будет входить[?:]?[\n]|'
    r'Чем будешь заниматься[?:]?[\n]|Чем будете заниматься[?:]?[\n]|Чем нужно будет заниматься[?:]?[\n]|Чем тебе предстоит заниматься[?:]?[\n]|Чем ты будешь заниматься[?:]?[\n]|'
    r'Что тебе предстоит делать[?:]?[\n]|Ты будешь[?:]?[\n]|На данной позиции предстоит[?:]?[\n]|Что будешь делать[?:]?[\n]|Предстоит выполнять[?:]?[\n]|'
    r'Вы будете[?:]?[\n]|Что необходимо будет делать[?:]?[\n]|Что нужно будет делать.*?[?:]?[\n]|Что надо будет делать[?:]?[\n]|Что будете делать[?:]?[\n]|Что ты будешь делать[?:]?[\n]|'
    r'Что нужно делать[?:]?[\n]|Что нужно[?:]?[\n]|Что вы будете делать[?:]?[\n]|Вы будете заниматься[?:]?[\n]|Чем вам предстоит заниматься[?:]?[\n]|'
    r'Чем заниматься[?:]?[\n]|Чем вы займетесь[?:]?[\n]|Чем необходимо заниматься[?:]?[\n]|Предстоит[?:]?[\n]|Кое-что о задачах[?:]?[\n]|'
    r'Чем предстоит заниматься[?:]?[\n]|Что предстоит делать[?:]?[\n]|Тебе предстоит[?:]?[\n]|Вам предстоит[?:]?[\n]|В команде .* тебе предстоит[?:]?[\n]|'
    r'В обязанности входит[?:]?[\n]|Обязанности[?:]?[\n]|В ваши обязанности входит[?:]?[\n]|C чем нам потребуется помощь[?:]?[\n]|'
    r'Функциональные обязанности[?:]?[\n]|Основной функционал[?:]?[\n]|Основная задача[?:]?[\n]?|Ваша роль в компании[?:]?[\n]?|'
    r'Должностные обязанности[?:]?[\n]|Основные обязанности[?:]?[\n]|Что по задачам[?:]?[\n]|Какие задачи предстоит решать[?:]?[\n]|'
    r'Обязанности преподавателя[?:]?[\n]|Что делает наставник[?:]?[\n]|Что делает автор[?:]?[\n]|Что вас жд[её]т на обучении[?:]?[\n]|В этой роли ты будешь[?:]?[\n]|'
    r'Вашими задачами буд[еу]т[?:]?[\n]|Задачи, которые необходимо решать[?:]?[\n]|Проекты, которыми мы занимаемся[?:]?[\n]|Задачи, которые будут перед тобой стоять[?:]?[\n]|'
    r'Следующих компонентов[?:]?[\n]|задачи для вас[?:]?[\n]|Мы поручим[?:]?[\n]|Какие задачи предстоит выполнять[?:]?[\n]|Что тебя ждёт[?:]?[\n]|Тебе предстоит отвечать за[?:]?[\n]'
)

SECTION_REQUIREMENTS_NAMES = (
    r'Требования.*?[?:]?[\n]|Базовые требования.*?[?:]?[\n]|Что жд[её]м от кандидата[?:]?[\n]|Мы жд[её]м от тебя[?:]?[\n]|Мы ожидаем от будущего члена команды[?:]?[\n]|Что мы ожидаем от вас[?:]?[\n]|Мы ожидаем от вас[?:]?[\n]|Что мы жд[её]м от кандидата[?:]?[\n]|Мы жд[её]м от кандидата[?:]?[\n]|Мы жд[её]м тебя, если[?:]?[\n]|'
    r'Что мы жд[её]м от кандидатов[?:]?[\n]|Что мы жд[её]м[?:]?[\n]|Мы жд[её]м, чтобы ты[?:]?[\n]|Что ожидаем от вас[?:]?[\n]|Мы жд[её]м, что вы[?:]?[\n]|От вас жд[её]м[?:]?[\n]|Мы жд[её]м, что вы имеете опыт[?:]?[\n]|Мы жд[её]м от вас[?:]?[\n]|Ожидания от кандидата[?:]?[\n]|Какие у нас ожидания от кандидата[?:]?[\n]|'
    r'жд[её]м, что ты[?:]?[\n]|Мы жд[её]м, что ты[?:]?[\n]|Мы жд[её]м, что у тебя есть[?:]?[\n]|Что мы жд[её]м от Вас[?:]?[\n]|Что мы жд[её]м от тебя[?:]?[\n]|Что жд[её]м от соискателя[?:]?[\n]|От будущего коллеги мы жд[её]м[?:]?[\n]|Что жд[её]м[?:]?[\n]|'
    r'Какие наши требования к кандидату[?:]?[\n]|Требования к кандидатам[?:]?[\n]|Требования к компетенциям и опыту[?:]?[\n]|Обязательно[?:]?[\n]|Обязательные требования[?:]?[\n]|Мы жд[её]м от будущих коллег[?:]?[\n]|'
    r'Технические требования .*?[?:]?[\n]|Требования и навыки[?:]?[\n]|Требования к кандидату[?:]?[\n]|Профессиональные требования[?:]?[\n]|Ключевые требования.*?[?:]?[\n]|Мы ценим, если ты[?:]?[\n]|'
    r'Обязанности искомого специалиста и ожидаемые результаты работы[?:]?[\n]|Мы ищем кандидата, который соответствует следующим требованиям[?:]?[\n]|Жд[её] от вас[?:]?[\n]|'
    r'Требования к backend-разработчику[?:]?[\n]|Мы подходим друг другу, если у вас есть[?:]?[\n]|Ваши ключевые навыки и опыт нам важны[?:]?[\n]|'
    r'Требуется понимание принципов ООП и владение следующими технологиями[?:]?[\n]|Требования к соискателю[?:]?[\n]|Также потребуются[?:]?[\n]|Мы ожидаем от кандидата[?:]?[\n]|Ожидаем от кандидата[?:]?[\n]|'
    r'Ожидания:[\n]|Наши ожидания.*?[?:]?[\n]|Что мы ожидаем от кандидата[?:]?[\n]|Ожидаем от тебя[?:]?[\n]|Мы ожидаем, что Вы[?:]?[\n]|Мы ожидаем,что у тебя есть опыт[?:]?[\n]|'
    r'Наши ожидания от кандидата[?:]?[\n]|Чего мы ждем от специалиста[?:]?[\n]|Мы ожидаем.*?[?:]?[\n]|Ожидания .* от кандидата [(].*?[)][?:]?[\n]|Мы ожидаем уверенные знания[?:]?[\n]|'
    r'Что мы ожидаем.*?[?:]?[\n]|Что мы от тебя ожидаем[?:]?[\n]|Мы ожидаем, что ты.*?[?:]?[\n]|Что мы ожидаем от кандидата[?:]?[\n]|Что ожидаем от кандидата[?:]?[\n]|'
    r'Ожидания .* от кандидата[?:]?[\n]|Нам важно[?:]?[\n]|Что важно для нас[?:]?[\n]|Для нас важно[?:]?[\n]|Для нас важны[?:]?[\n]|В вашем опыте для нас важно[?:]?[\n]|Что для нас важно[?:]?[\n]'
    r'Твоя суперсила[?:]?[\n]|Мы ищем кандидата, который обладает[?:]?[\n]|Мы ищем того, кто[?:]?[\n]|Специальные навыки и знания[?:]?[\n]|'
    r'Наши ожидания от тебя[?:]?[\n]|Ключевые знания[?:]?[\n]|Будет преимуществом[?:]?[\n]|Жд[её]м, что в багаже знаний будет[?:]?[\n]|'
    r'Нам важен[?:]?[\n]|Какой опыт нам важен[?:]?[\n]|Необходимые навыки и опыт[?:]?[\n]|Какие знания и навыки нам важны[?:]?[\n]|Какой опыт и навыки для нас важны[?:]?[\n]|Необходимые навыки[?:]?[\n]|'
    r'Необходимо иметь[?:]?[\n]|Пожелания к соискателю[?:]?[\n]|Пожелания к кандидату[?:]?[\n]|Что нужно знать и уметь[?:]?[\n]|Необходимый опыт и знания[?:]?[\n]|'
    r'Знания и навыки[?:]?[\n]|Обязательные навыки[?:]?[\n]|Основные навыки[?:]?[\n]|Ты идеальный кандидат, если.*?[?:]?[\n]|Опыт и навыки[?:]?[\n]|Необходимые знания[?:]?[\n]|Требуемые навыки[?:]?[\n]|'
    r'Ваш профиль[?:]?[\n]|Желательно[?:]?[\n]|у Вас есть[?:]?[\n]|Потребуется[?:]?[\n]|Мы ищем кандидата, у которого есть[?:]?[\n]|'
    r'Что для этого понадобится  навыки и опыт[?:]?[\n]|Требуемый опыт и навыки[?:]?[\n]|Ожидания по опыту.*?[?:]?[\n]|Кто нам нужен[?:]?[\n]|Что нужно, чтобы к нам присоединиться[?:]?[\n]|'
    r'Что хотим[?:]?[\n]|Что мы хотим видеть от Вас[?:]?[\n]|Что мы хотим увидеть[?:]?[\n]|Что важно для этой роли[?:]?[\n]|Необходимые навыки и квалификации[?:]?[\n]|'
    r'Вы точно нам подходите, если вы уверенный специалист хотя бы в одной из этих областей[?:]?[\n]|Вы нам подходите,? если[?:]?[\n]|'
    r'Наши пожелания[?:]?[\n]|Мы сработаемся, если есть[?:]?[\n]|Для выполнения задач необходимы[?:]?[\n]|Кого мы ищем[?:]?[\n]|'
    r'От вас нужно[?:]?[\n]|Мы ищем кандидата, который[?:]?[\n]|Ищем того, кто[?:]?[\n]|Мы будем рады рассмотреть вашу кандидатуру, если у вас есть[?:]?[\n]|'
    r'Мы подходим друг другу если у тебя есть[?:]?[\n]|Что команде хотелось бы видеть[?:]?[\n]|Что жд[её]м от тебя[?:]?[\n]|Мы ищем кандидата, который обязательно имеет[?:]?[\n]|'
    r'Квалификация[?:]?[\n]|Наш кандидат должен иметь[?:]?[\n]|Каким мы представляем нашего будущего коллегу[?:]?[\n]|Что важно для успеха в этой роли[?:]?[\n]|Что важно для успеха[?:]?[\n]|'
    r'Наши пожелания к квалификации[?:]?[\n]|Обязательные[?:]?[\n]|Мы абсолютно уверены, что ты справишься, ведь ты[?:]?[\n]|Ты — огонь, если[?:]?[\n]|'
    r'Мы ищем обладателя следующих знаний и навыков[?:]?[\n]|Что важно по опыту[?:]?[\n]|На какой опыт мы ориентируемся[?:]?[\n]|Технологии, которые нам интересны[?:]?[\n]|'
    r'Наш идеальный кандидат[?:]?[\n]|Ты нам подойдёшь, если[?:]?[\n]|Поэтому ищем того, кто[?:]?[\n]|Что мы ожидаем от тебя[?:]?[\n]|Какие навыки мы ожидаем[?:]?[\n]|'
    r'Технические навыки[?:]?[\n]|Используемые технологии[?:]?[\n]|Что необходимо[?:]?[\n]|Ты справишься с этим, если[?:]?[\n]|Мы ищем именно тебя, если[?:]?[\n]|'
    r'Обязательные требования [(].*?[)][?:]?[\n]|Будем рады видеть в новом коллеге следующее[?:]?[\n]|Мы хотим познакомиться с тобой, если ты[?:]?[\n]|'
    r'Жд[её]м мы жд[её]м от тебя[?:]?[\n]|Мы ждем, что вы обладаете[?:]?[\n]|Мы подходим друг другу, если ты обладаешь следующим опытом и знаниями[?:]?[\n]|'
    r'Пожелания к твоему опыту[?:]?[\n]|Какие знания, навыки и опыт необходимы для реализации задач.*?[:?]?[\n]|Мы рассчитываем, что ты[?:]?[\n]|'
    r'Наш стек в тестировании[?:]?[\n]|Что для этого необходимо[?:]?[\n]|Чего команда ожидает[?:]?[\n]|Требования и компетенции[?:]?[\n]|Какой опыт и навыки нужны[?:]?[\n]|'
    r'Что от Вас требуется[?:]?[\n]|Что важно в вас[?:]?[\n]|Что нужно для этой работы[?:]?[\n]'
    
)

SECTION_WORKING_CONDITIONS_NAMES = (
    r'Компенсации и льготы[?:]?[\n]|Предлагаем[?:]?[\n]|Мы предлагаем[?:]?[\n]|Что вас ждет после успешного обучения[?:]?[\n]|Процесс поиска[?:]?[\n]|Что мы готовы вам предложить[?:]?[\n]|'
    r'У нас[?:]?[\n]|Что ты получишь[?:][\n]?|Мы можем предложить[?:]?[\n]|Что мы предлагаем[?:]?[\n]|'
    r'Что предлагаем[?:]?[\n]|Еще несколько причин, почему именно мы[?:]?[\n]|Что тебя жд[её]т в[?:]?[\n]|Что вас ждет[?:]?[\n]|В .* вас жд[её]т[?:]?[\n]|'
    r'Что компания может предложить[?:]?[\n]|Условия[?:]?[\n]|Условия и бонусы[?:]?[\n]|Наши условия[?:]?[\n]|Условия работы[?:]?[\n]|Про команду и рабочие процессы[?:]?[\n]|'
    r'Что ждать от нас[?:]?[\n]|С нас[?:]?[\n]|Что мы готовы предложить[?:]?[\n]|Что мы можем предложить[?:]?[\n]|Работа у нас - это[?:]?[\n]|Работа в .* это[?:]?[\n]|'
    r'Почему стоит выбрать нас[?:][\n]?|Вы гарантированно получите[?:]?[\n]|Что мы предлагаем взамен[?:]?[\n]|Что мы предлагаем для комфортной работы[?:]?[\n]|'
    r'Ну и самое приятное. Со своей стороны .* обещает с первых дней[?:]?[\n]|Со своей стороны .* обещает с первых дней[?:]?[\n]|Условия сотрудничества[?:]?[\n]|'
    r'А ещё[?:]?[\n]|Что ты получаешь[?:]?[\n]|Что ты получишь, став частью нашей команды[?:]?[\n]|Условия и преимущества[?:]?[\n]|Почему .*?[\n]|Преимущества[?:]?[\n]|'
    r'Мы создаем среду, в которой ценят не только работу, но и заботу о сотрудниках[?:]?[\n]|Условия стажировки[?:]?[\n]|'
    r'Преимущества и возможности работы в нашей команде[?:]?[\n]|Условия и возможности[?:]?[\n]|Как сделаем жизнь комфортнее[?:]?[\n]|'
    r'Мы готовы предложить[?:]?[\n]|Что ты получишь с нами[?:]?[\n]|Мы предлагаем достойные условия работы[?:]?[\n]|С радостью предложим[?:]?[\n]|Поддержка и развитие[?:]?[\n]|'
    r'#Киберплюшки для наших сотрудников[?:]?[\n]|Что получишь[?:]?[\n]|Условия и Бенефиты[?:]?[\n]|Готовы предложить[?:]?[\n]|Мы гарантируем своим сотрудникам[?:]?[\n]|'
    r'Любим стратегию .*? и взамен готовы предлагать[?:]?[\n]|Почему с нами классно[?:]?[\n]|Что по условиям[?:]?[\n]|Взамен мы предлагаем[?:]?[\n]|Условия и оплата[?:]?[\n]|'
    r'Само собой[?:]?[\n]|Если ты способен.*|От вас мы жд[её]м[?:]?[\n]|Приветствуется .*?:[\n]|Чем мы обеспечим[?:]?[\n]|Работа с нами.*?[?:]?[\n]|Почему с нами классно|Условия И гарантии[?:]?[\n]|'
    r'Условия для сотрудников[?:]?[\n]|Что мы обеспечим[?:]?[\n]|Предложение[?:]?[\n]|Главный принцип.*?[\n]|Мы предлагаем тебе.*?[\n]|Компенсация включает в себя[?:]?[\n]|Что предлагаем мы[?:]?[\n]|Что взамен[?:]?[\n]'
)

KEYWORDS_END_OF_SECTIONS = (
    r'Наш технологический стек[?:]?[\n]|Технологический стек[?:]?[\n]|Наш стек[?:\n]?|Основной стек[?:\n]?|Техстек[?:\n]?|Стек технологий[?:]?[\n]|Стек и инфраструктура[?:]?[\n]|Мы используем современные инструменты[?:]?[\n]|Стек[?:]?[\n]|'
    r'С нами классно работать[?:\n]?|Для разработки мы используем[?:]?[\n]|С чем ещё мы работаем[?:\n]?|С нашей стороны мы предлагаем[?:\n]?|'
    r'Ближайшие задачи[?:\n]?|Наши технологии[?:\n]?|Какие вещи и технологии мы используем в работе[?:\n]?|О проекте[?:\n]?|'
    r'Мы ожидаем уверенные знания[?:\n]?|Дополнительные инструкции[?:\n]?|В сопроводительном письме[?:\n]?|Знание технологий[?:\n]?|Почему .*[?:]?[\n]|Требования по софт скиллам[?:]?[\n]|'
    r'Архитектура и инфраструктура[?:\n]?|Глубокие технические компетенции[?:]?|Этапы входа в компанию[?:]?[\n]|Этапы отбора[?:]?[\n]|P.S.[\n]|'
    r'С уважением[?:\n]?|Добро пожаловать .*[?:\n]?|Одна из ценностей Evrone – работа с удовольствием[?:]?[\n]|Если вы готовы .*|Дополнительно о нас[?:\n]?|Чему вы научитесь[?:]?[\n]|'
    r'Мы уверены, что вам понравится .*[?:\n]?|О команде[?:\n]?|Ключевые навыки[?:]?[\n]|Если интересно, напиши .*[?:]?|От HR кандидату[?:]?[\n]|Дополнительно[?:]?[\n]|'
    r'Если тебе откликается .*[?:\n]?|Жд[её]м отклик.*|Жд[её]м твоего отклика.*|Звучит как твой следующий шаг[?:\n]?|Присоединяйтесь к команде.*|'
    r'Собеседование[?:]?[\n]|Перспективы[?:]?[\n]|Жд[её]м Ваши отклики.*|Одна из ценностей .*[?:]?[\n]|Основной язык программирования.*?[\n]|Технологии, которые мы используем[?:]?[\n]|'
    r'Процесс отбора[?:]?[\n]|Про наш стек технологий[?:]?[\n]|А еще у нас есть[?:]?[\n]|А еще[?:]?[\n]|Как откликнуться[?:]?[\n]|Хочешь работать над системой.*|Помимо работы[?:]?[\n]|Узнайте подробности ДО собеседования.*?|'
    r'Жд[её]м Вашего откликаю.*?|Welcome to.*|Если наша вакансия тебе откликнулась.*|Присоединяйтесь к нам.*|Что вы получите[?:]?[\n]|Программа стажировки[?:]?[\n]|Обязательный Этап Отбора.*|Как подать заявку.*|Конкурс[?:]?[\n]'
)


def extract_duties_requirements_working_conditions_by_keywords(text: str) -> dict:
    if not text: 
        text = ""
    text = text.replace('\u200b', '').replace('<mark>', '').replace('</mark>', '').replace('<strong>', '').replace('</strong>', '').replace('<em>', '').replace('</em>', '').replace('<span>', '').replace('</span>', '').replace('—', '').replace('_', '').replace('·', '').replace('●', '').replace('✓', '')
    text = emoji.replace_emoji(text, replace="")
    soup = BeautifulSoup(text, 'html.parser')
    text = soup.get_text(separator='\n', strip=True)

    def extract_section(header_pattern, text, end_pattern):
        match = re.search(header_pattern + r'([\s\S]*?)(?=' + end_pattern + r'|$)', text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip().replace(';', '')
        return None

    duties = extract_section(
        r'(?:' + SECTION_DUTIES_NAMES + r')', 
        text, 
        r'\n(?:' + SECTION_REQUIREMENTS_NAMES + r'|' + SECTION_WORKING_CONDITIONS_NAMES + r'|' + KEYWORDS_END_OF_SECTIONS + r')'
    )
    requirements = extract_section(
        r'(?:' + SECTION_REQUIREMENTS_NAMES + r')', 
        text, 
        r'\n(?:' + SECTION_DUTIES_NAMES + r'|' + SECTION_WORKING_CONDITIONS_NAMES + r'|' + KEYWORDS_END_OF_SECTIONS + r')'
    )
    working_conditions = extract_section(
        r'(?:' + SECTION_WORKING_CONDITIONS_NAMES + r')',
        text, 
        r'\n(?:' + SECTION_DUTIES_NAMES + r'|' + SECTION_REQUIREMENTS_NAMES + r'|' + KEYWORDS_END_OF_SECTIONS + r')'
    )

    def extract_items(section_text):
        if not section_text:
            return []
        items = []
        for item in re.split(r'[•\n]', section_text):
            if item.strip():
                if item[0] in '-*':
                    symb = item[0]
                    item_with_removed_dash_at_start = item.strip().replace(symb, '', 1)
                    items.append(item_with_removed_dash_at_start)
                else:
                    items.append(item.strip())
        return items

    result = {
        'duties': extract_items(duties) if duties else [],
        'requirements': extract_items(requirements) if requirements else [],
        'working_conditions': extract_items(working_conditions) if working_conditions else []
    }

    return result

def extract_keywords_from_text(text: str) -> str:
    if not text:
        return ""

    text_lower = f" {text.lower()} "
    found_keywords = []
    keywords_sorted = sorted(ALL_KEYWORDS_LIST, key=len, reverse=True)
    for keyword in keywords_sorted:
        kw_lower = keyword.lower()
        pattern_escaped = re.escape(kw_lower)
        pattern = rf'(?<=[^a-z0-9]){pattern_escaped}(?=[^a-z0-9])'
        if re.search(pattern, text_lower):
            found_keywords.append(kw_lower)
            
    return " ".join(found_keywords)

def get_payment_from_hh_vacancy(salary_data: dict | None) -> list:
    if salary_data == None:
        payment_from, payment_to = 0, 0
    else:
        payment_from = 0 if salary_data["from"] == None else salary_data["from"]
        payment_to = 0 if salary_data["to"] == None else salary_data["to"]
    return [payment_from, payment_to]

def convert_vacancy_payment_to_ru_currency(curr: str, payment_from: int, payment_to: int) -> list:
    '''Возвращает переведённую валюту с иностранной на рубли, если сама валюта (vacancy.currency) не рубли'''
    if curr != "RUR":
        new_payment_from = cu.convert(payment_from, curr, 'RUB', date=date(2022, 3, 1))
        new_payment_to = cu.convert(payment_to, curr, 'RUB', date=date(2022, 3, 1))
        return [new_payment_from, new_payment_to]
    return [payment_from, payment_to]

def get_applicant_criterias_for_filtering_vacancies(user: Applicant) -> dict:
    '''Возвращает информацию о пользователе для дальнейшей генерации персональных вакансий'''
    applicant_technologies = []
    for tech in user.technologies.all():
        if tech.name != "CI/CD":
            applicant_technologies.append(" ".join(tech.name.split('/')))
        else:
            applicant_technologies.append("CI/CD")
    applicant_data = {
        'applicant_username': user.username, # имя пользователя (уникальное)
        'city': user.get_city_display(), # город в ру формате
        'experience': user.get_experience_display(), # опыт работы в ру формате
        'experience_eng': user.experience,
        'preferred_work_formats': [wf.name for wf in user.preferred_work_formats.all()],
        'specializations': " ".join([spec.name for spec in user.specializations.all()]),
        'technologies': " ".join(applicant_technologies),
    }
    return applicant_data

def get_applicant_favourite_vacancies_info_for_filtering_vacancies(vacancies: QuerySet[Vacancy]) -> dict:
    '''Возвращает информацию о избранных вакансиях пользователя для дальнейшей генерации персональных рекомендаций'''
    applicant_fav_vacancies_data = {}
    for vacancy in vacancies:
        payment_from_ru, payment_to_ru = convert_vacancy_payment_to_ru_currency(
            vacancy.currency, 
            vacancy.payment_from, 
            vacancy.payment_to
        )
        duties = [] if vacancy.duties == NOT_FOUND_DUTIES else vacancy.duties.split(';')
        reqs = [] if vacancy.requirements == NOT_FOUND_REQS else vacancy.requirements.split(';')
        applicant_fav_vacancies_data[vacancy.id] = {
            'external_id': vacancy.external_id,
            'title': vacancy.title,
            'vacancy_texts': duties + reqs,
            'payment_from': payment_from_ru, # зп от в рублях
            'payment_to': payment_to_ru, # зп до в рублях
            'experience_eng': vacancy.experience,
            'experience': vacancy.get_experience_display(), # experience in ru format,
            'education': vacancy.get_education_display(), # education in ru format,
            'work_formats': [wf.name for wf in vacancy.work_formats.all()],
        }
    return applicant_fav_vacancies_data

def get_applicant_search_history_info_for_filtering_vacancies(search_history: QuerySet[SearchHistory]):
    '''Возвращает информацию о истории поиска пользователя для дальнейшей генерации персональных рекомендаций'''
    return [sh.search_query for sh in search_history]

def create_vacancy_instance(user: Applicant, vacancy_data: dict):
    '''Создаёт модель вакансии. Также при наличии достаточной информации создаёт модель фирмы'''
    if not Firm.objects.filter(name=vacancy_data["employer"]["name"]).exists() and vacancy_data["employer"]["name"] != "":
        firm = Firm.objects.create(
            name=vacancy_data["employer"]["name"],
            address=vacancy_data["employer"]["address"],
            link=vacancy_data["employer"]["alternate_url"],
        )
        firm.save()
    else:
        firm = Firm.objects.get(name=vacancy_data["employer"]["name"])
    vacancy = Vacancy.objects.create(
        user=user,
        initial_source=vacancy_data["initial_source"],
        external_id=vacancy_data["external_id"],
        title=vacancy_data["title"],
        duties=vacancy_data["duties"],
        requirements=vacancy_data["requirements"],
        working_conditions=vacancy_data["working_conditions"],
        payment_from=vacancy_data["payment"]["payment_from"],
        payment_to=vacancy_data["payment"]["payment_to"],
        currency=vacancy_data["payment"]["currency"],
        experience=vacancy_data["experience"],
        education=vacancy_data["education"],
        date_published=vacancy_data["date_published"],
        valid_until=vacancy_data["valid_until"],
        original_link=vacancy_data["original_link"],
        firm=firm
    )
    work_formats = [WorkFormat.objects.get(name=wf) for wf in vacancy_data["work_formats"]]
    vacancy.work_formats.add(*work_formats)
    return vacancy

def prepare_vacancy_for_telegram_message(vacancy: dict) -> str:
    '''Излечение нужных данных из вакансии, объединение их в 1 текст для телеграм сообщения'''
    duties = "\n".join(vacancy.get("duties")[:2])
    requirements = "\n".join(vacancy.get("requirements")[:3])
    working_condititons = "\n".join(vacancy.get("working_conditions")[:4])
    work_formats = ", ".join(vacancy.get("work_formats"))
    payment = vacancy.get('payment')
    payment_text, payment_from, payment_to, curr = "", payment.get("payment_from"), payment.get("payment_to"), payment.get("currency")

    if payment.get('by_agreement'):
        payment_text = 'Уровень дохода не указан'
    elif payment_to == 0:
        payment_text = f'от {payment_from}{curr} за месяц'
    elif payment_from == 0:
        payment_text = f'до {payment_to}{curr} за месяц'
    elif payment_from == payment_to:
        payment_text = f'{payment_to}{curr} за месяц'
    else:
        payment_text = f'{payment_from}-{payment_to}{curr}'
    dt = format_datetime(vacancy.get("date_published"), locale='ru')

    result = f'Возможно эта вакансия будет вам интересна 📜' + f'\n{vacancy.get("title")}' + f'\nЗп: {payment_text}' + f'\nЗадачи:\n{duties}'+ f'\nТребования:\n{requirements}' + f'\nУсловия:\n{working_condititons}' + f'\nОпыт работы: {vacancy.get("experience_ru")}' + f'\nФормат(-ы): {work_formats}'
    result += f'\nБыла опубликована в: {dt}'
    return result
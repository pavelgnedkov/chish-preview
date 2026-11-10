#!/usr/bin/env python3
"""Новый раздел «Сведения об образовательной организации» по приказу
Рособрнадзора № 1493 (ред. от 30.04.2026) и Методическим рекомендациям
Рособрнадзора (версия 8.9.1): адреса /sveden/..., точные названия подразделов,
навигация на каждой странице, html-разметка itemprop.

Плюс правки по всему сайту: меню (в т.ч. мобильное), переадресация со старых
адресов, itemprop="copy", страница 404, удаление страниц старого сайта (Drupal),
фоновое видео на главной, распознанные (OCR) документы.

Данные, которых нет в архиве, не выдумываются: такие места помечены
«Нужно от школы», а типовые формулировки — «черновик — подтвердить».
"""
import json, os, re, shutil, sys
from bs4 import BeautifulSoup

SITE = sys.argv[1]
REPO = os.path.dirname(os.path.abspath(__file__))
P = os.environ.get("PREFIX", "/chish-preview")

ADDR_LENINA = "400005, Волгоградская область, г. Волгоград, пр-кт им. В. И. Ленина, 27"
ADDR_VATUTINA = "400065, Волгоградская область, г. Волгоград, ул. им. генерала Ватутина, 6"
ADDR_AKADEM = "г. Волгоград, ул. Академическая, 12"
PHONE = "8 (8442) 71-17-38"
EMAIL = "chish.school@gmail.com"

SUBS = [  # slug, название строго по п. 6 приказа № 1493
    ("common", "Основные сведения"),
    ("struct", "Структура и органы управления образовательной организацией"),
    ("document", "Документы"),
    ("education", "Образование"),
    ("eduStandarts", "Образовательные стандарты и требования"),
    ("managers", "Руководство"),
    ("employees", "Педагогический состав"),
    ("objects", "Материально-техническое обеспечение и оснащенность образовательного процесса. Доступная среда"),
    ("paid_edu", "Платные образовательные услуги"),
    ("budget", "Финансово-хозяйственная деятельность"),
    ("vacant", "Вакантные места для приема (перевода) обучающихся"),
    ("grants", "Стипендии и меры поддержки обучающихся"),
    ("inter", "Международное сотрудничество"),
    ("catering", "Организация питания в образовательной организации"),
]
OLD = {  # старый адрес -> новый подраздел
    "svedeniya-o-shkole": "common",
    "osnovnye-svedeniya": "struct",
    "dokumenty": "document",
    "obrazovanie": "education",
    "obrazovatelnye-standarty": "eduStandarts",
    "rukovodstvo-pedagogicheskij-sostav": "managers",
    "materialno-tehnicheskoe-obespechenie-i-osnashhennost-obrazovatelnogo": "objects",
    "o-shkole/dostupnaya-sreda": "objects",
    "platnye-obrazovatelnye-uslugi": "paid_edu",
    "finansovo-hozyajstvennaya-deyatelnost": "budget",
    "vakantnye-mesta-dlya-priema-perevoda": "vacant",
    "stipendii-i-inye-vidy-materialnoj-podderzhki": "grants",
    "o-shkole/mezhdunarodnoe-sotrudnichestvo": "inter",
    "menyu": "catering",
}
stats = {"todo": 0, "draft": 0, "missing": []}


# ---------- маленькие помощники ----------
def url(slug):
    return f"{P}/sveden/{slug}/"


def have(path):
    return os.path.isfile(os.path.join(SITE, path.lstrip("/")))


def doc(path, title, prop=None, note=""):
    """Ссылка на файл сайта; если файла нет — красная пометка."""
    pa = f' itemprop="{prop}"' if prop else ""
    s = f'<a href="{P}{path}"{pa}>{title}</a>'
    if not have(path):
        s += ' <span class="sv-miss">файл ожидается от школы</span>'
        stats["missing"].append((title, path))
    if note:
        s += f' <span class="sv-note">{note}</span>'
    return s


def ext(href, title, prop=None):
    pa = f' itemprop="{prop}"' if prop else ""
    return f'<a href="{href}"{pa} target="_blank" rel="noopener">{title}</a>'


def page(path, title):
    return f'<a href="{P}{path}">{title}</a>'


def todo(text):
    stats["todo"] += 1
    return f'<span class="sv-todo">Нужно от школы: {text}</span>'


def draft():
    stats["draft"] += 1
    return ' <span class="sv-draft">черновик — подтвердить</span>'


def table(head, rows, cls="sv-table"):
    th = "".join(f"<th>{h}</th>" for h in head)
    return f'<div class="sv-wrap"><table class="{cls}"><thead><tr>{th}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


def years(s):
    m = re.search(r"\d+", s or "")
    if not m:
        return "", ""
    n = int(m.group())
    w = "год" if n % 10 == 1 and n % 100 != 11 else ("года" if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14 else "лет")
    return str(n), w


# ---------- содержимое подразделов ----------
def c_common():
    rows = [
        f'<tr><td>Полное наименование образовательной организации</td><td itemprop="fullName">Частное образовательное учреждение средняя общеобразовательная Частная интегрированная школа</td></tr>',
        f'<tr><td>Сокращенное наименование образовательной организации</td><td itemprop="shortName">ЧОУ СО Частная интегрированная школа</td></tr>',
        f'<tr><td>Дата создания образовательной организации</td><td><span itemprop="regDate">1992</span> {todo("точная дата создания в формате дд.мм.гггг")}</td></tr>',
        f'<tr><td>Адрес места нахождения образовательной организации</td><td itemprop="address">{ADDR_LENINA}</td></tr>',
        '<tr><td>Филиалы образовательной организации</td><td>нет</td></tr>',
        '<tr><td>Представительства образовательной организации</td><td>нет</td></tr>',
        '<tr><td>Режим, график работы</td><td itemprop="workTime">понедельник — пятница с 8:00 до 17:00; суббота с 8:00 до 14:00; воскресенье — выходной</td></tr>',
        f'<tr><td>Контактные телефоны</td><td itemprop="telephone">{PHONE}</td></tr>',
        f'<tr><td>Адреса электронной почты</td><td itemprop="email">{EMAIL}</td></tr>',
    ]
    uch = table(["Наименование учредителя", "Адрес места нахождения", "Контактные телефоны", "Адрес электронной почты", "Адрес сайта в сети «Интернет»"], [
        '<tr itemprop="uchredLaw"><td itemprop="nameUchred">Парсли Виктория Викторовна (физическое лицо)</td>'
        f'<td itemprop="addressUchred">нет</td><td itemprop="telUchred">нет</td><td itemprop="mailUchred">нет</td><td itemprop="websiteUchred">нет</td></tr>'
    ])
    lic = (
        f'<p>{doc("/wp-content/uploads/2025/10/Reestrovaya-vypiska.pdf", "Выписка из реестра лицензий на осуществление образовательной деятельности", "licenseDocLink")}</p>'
        f'<p>{todo("номер и дата лицензии (или актуальная выписка из реестра лицензий)")}</p>'
    )
    acc = (
        '<p>Образовательная деятельность по реализуемым основным общеобразовательным программам имеет государственную аккредитацию '
        '(свидетельство о государственной аккредитации серия 34А01 № 0000094, регистрационный № 100, срок действия — бессрочно).</p>'
        f'<p>{ext("https://isga.obrnadzor.gov.ru/accredreestr/details/5e778a1b-306e-f8cc-e567-7eeae5e8ea0b", "Сведения о государственной аккредитации в реестре Рособрнадзора", "accreditationDocLink")}</p>'
        f'<p>{doc("/wp-content/uploads/2026/03/Reestrovaya-vypiska-1.pdf", "Выписка из реестра организаций, осуществляющих образовательную деятельность по имеющим государственную аккредитацию образовательным программам")}</p>'
    )
    places = table(["N", "Адрес", "Что расположено"], [
        f'<tr><td>1</td><td>{ADDR_LENINA}</td><td>Средняя школа (10–11 классы), юридический адрес</td></tr>',
        f'<tr><td>2</td><td>{ADDR_VATUTINA}</td><td>Начальная и основная школа (1–9 классы)</td></tr>',
        f'<tr><td>3</td><td>{ADDR_AKADEM}</td><td>Лаборатории физики, кабинет информационных технологий, кабинет астрономии (учебный корпус № 2 ВГСПУ) '
        f'{todo("проверить, что этот адрес есть в реестре лицензий; если занятия идут по договору о сетевой форме — указать его в таблице ниже")}</td></tr>',
    ])

    def pl(prop, value, d=True):
        return f'<tr itemprop="{prop}"><td>1</td><td>{value}{draft() if d else ""}</td></tr>'

    not_in_lic = (
        '<h3>Места осуществления образовательной деятельности, не включаемые в реестр лицензий</h3>'
        '<h4>При использовании сетевой формы реализации образовательных программ</h4>' + table(["N", "Адрес"], [pl("addressPlaceSet", "нет")]) +
        '<h4>Места проведения практики</h4>' + table(["N", "Адрес"], [pl("addressPlacePrac", "нет (практика основными общеобразовательными программами не предусмотрена)")]) +
        '<h4>Места проведения практической подготовки обучающихся</h4>' + table(["N", "Адрес"], [pl("addressPlacePodg", "нет")]) +
        '<h4>Места проведения государственной итоговой аттестации</h4>' + table(["N", "Адрес"], [pl("addressPlaceGia", "пункты проведения экзаменов, определяемые комитетом образования, науки и молодежной политики Волгоградской области")]) +
        '<h4>Места осуществления образовательной деятельности по дополнительным образовательным программам</h4>' + table(["N", "Адрес"], [f'<tr itemprop="addressPlaceDop"><td>1</td><td>{todo("адреса, где идут кружки и секции, или «нет»")}</td></tr>']) +
        '<h4>Места осуществления образовательной деятельности по основным программам профессионального обучения</h4>' + table(["N", "Адрес"], [pl("addressPlaceOppo", "нет")])
    )
    return (table(["Параметр", "Сведения"], rows)
            + "<h2>Учредитель</h2>" + uch
            + "<h2>Лицензия на осуществление образовательной деятельности</h2>" + lic
            + "<h2>Государственная аккредитация</h2>" + acc
            + "<h2>Места осуществления образовательной деятельности</h2>" + places + not_in_lic)


def c_struct():
    text = (
        '<p>Высший орган управления школой — учредитель. К компетенции учредителя относится определение приоритетных направлений деятельности школы.</p>'
        '<p>Единоличный исполнительный орган — директор. Директор назначается учредителем и осуществляет текущее руководство школой, '
        'несёт ответственность за руководство образовательной, воспитательной работой и организационно-хозяйственной деятельностью.</p>'
        '<p>Коллегиальный орган управления — педагогический совет: состоит из педагогических работников и осуществляет общее руководство образовательным процессом.</p>'
        '<p>Формы самоуправления школы: совет президентов классов, общее собрание работников, собрание родителей, собрание учащихся.</p>'
        '<p><strong>Структурных подразделений, филиалов и представительств нет.</strong></p>'
    )
    pos = todo("положение")

    def r(name, fio, post, clause=None):
        cl = clause or pos
        return (f'<tr itemprop="structOrgUprav"><td itemprop="name">{name}</td><td itemprop="fio">{fio}</td><td itemprop="post">{post}</td>'
                f'<td itemprop="addressStr">{ADDR_LENINA}</td><td itemprop="site">нет</td><td itemprop="email">{EMAIL}</td>'
                f'<td><span itemprop="divisionClauseDocLink">{cl}</span></td></tr>')
    rows = [
        r("Учредитель", "Парсли Виктория Викторовна", "Учредитель", f'{doc("/wp-content/uploads/2023/02/Ustav-29.11.2022.pdf", "Устав")}'),
        r("Директор (единоличный исполнительный орган)", "Тураева Елена Владимировна", "Директор", f'{doc("/wp-content/uploads/2023/02/Ustav-29.11.2022.pdf", "Устав")}'),
        r("Педагогический совет", f'{todo("ФИО председателя")}', "Председатель педагогического совета"),
        r("Общее собрание работников", f'{todo("ФИО председателя")}', "Председатель общего собрания работников"),
        r("Совет президентов классов", f'{todo("ФИО руководителя")}', "Руководитель"),
    ]
    head = ["Наименование органа управления", "ФИО руководителя", "Должность", "Место нахождения", "Сайт", "Электронная почта", "Положение"]
    return text + "<h2>Органы управления</h2>" + table(head, rows) + (
        '<p class="sv-note-p">Положения об органах управления размещаются в виде электронных документов, подписанных простой электронной подписью '
        '(п. 8 «е» приказа № 1493).</p>')


def c_document():
    li = lambda x: f"<li>{x}</li>"
    main = [
        doc("/wp-content/uploads/2023/02/Ustav-29.11.2022.pdf", "Устав ЧОУ СО Частной интегрированной школы", "ustavDocLink"),
        doc("/wp-content/uploads/2023/11/Pravila-vnutrennego-rasporyadka-uchashhihsya-s-pechatyu.pdf", "Правила внутреннего распорядка обучающихся", "localActStud"),
        doc("/wp-content/uploads/2023/11/Pravila-vnutrennego-trudovogo-rasporyadka-s-pechatyu.pdf", "Правила внутреннего трудового распорядка", "localActOrder"),
        f'Коллективный договор: <span itemprop="localActCollec">не заключался</span>{draft()}',
        doc("/wp-content/uploads/2024/08/Samobsledovanie-2023-s-pechatyu.pdf", "Отчёт о результатах самообследования", "reportEduDocLink") + " " + todo("отчёт за 2025 год"),
        f'Предписания органов, осуществляющих государственный контроль (надзор) в сфере образования: <span itemprop="prescriptionDocLink">предписаний нет</span>{draft()}',
    ]
    lna = [
        doc("/wp-content/uploads/2023/11/Polozhenie-o-poryadke-priema-v-shkolu-2023-s-pechatyu.pdf", "Правила приёма обучающихся", "priemDocLink"),
        doc("/wp-content/uploads/2024/04/23-24_Raspisanie-zvonkov-2023-2024.pdf", "Режим занятий обучающихся", "modeDocLink") + " " + todo("режим занятий на 2025–2026 учебный год"),
        doc("/wp-content/uploads/2023/11/Polozhenie-o-poryadke-provedeniya-tekushhego-kontrolya-s-pechatyu.pdf",
            "Формы, периодичность и порядок текущего контроля успеваемости и промежуточной аттестации обучающихся", "tekKontrolDocLink"),
        doc("/wp-content/uploads/2023/11/Polozhenie-o-poryadke-perevoda-uchashhihsya-v-sleduyushhii-klass-s-pechatyu.pdf",
            "Положение о порядке перевода учащихся в следующий класс", "perevodDocLink") + " " +
        todo("документ о порядке и основаниях перевода, отчисления и восстановления: в нынешнем положении есть только перевод в следующий класс"),
        doc("/wp-content/uploads/2023/11/Polozhenie-o-poryadke-oformleniya-vozniknoveniya-izmeneniya-i-prekrashheniya-otnoshenii-s-pechatyu.pdf",
            "Порядок оформления возникновения, приостановления и прекращения отношений между школой и обучающимися и (или) их родителями (законными представителями)", "vozDocLink"),
    ]
    other = [
        doc("/wp-content/uploads/2025/10/Reestrovaya-vypiska.pdf", "Выписка из реестра лицензий на осуществление образовательной деятельности"),
        doc("/wp-content/uploads/2019/09/3-Polozhenie-ob-okazanii-platnyh-obrazovatelnyh-uslug-2.pdf", "Положение об оказании платных образовательных услуг"),
        doc("/wp-content/uploads/2025/10/Pravila-shkolnoj-zhizni.pdf", "Правила школьной жизни"),
        doc("/wp-content/uploads/2026/03/Polozhkeie-o-yazyke-2023.pdf", "Положение о языке образования"),
    ]
    return ('<ul class="sv-docs">' + "".join(map(li, main)) + "</ul>"
            + "<h2>Локальные нормативные акты по основным вопросам организации и осуществления образовательной деятельности</h2>"
            + '<ul class="sv-docs">' + "".join(map(li, lna)) + "</ul>"
            + "<h2>Другие документы</h2>" + '<ul class="sv-docs">' + "".join(map(li, other)) + "</ul>"
            + '<p class="sv-note-p">Документы, которые школа разрабатывает и утверждает сама, размещаются в виде электронных документов, '
              'подписанных электронной подписью (п. 9 приказа № 1493).</p>')


PROGS = [
    ("НОО", "Основная образовательная программа начального общего образования", "Начальное общее образование", "4 года", "1–4 классы", 72),
    ("ООО", "Основная образовательная программа основного общего образования", "Основное общее образование", "5 лет", "5–9 классы", 94),
    ("СОО", "Основная образовательная программа среднего общего образования", "Среднее общее образование", "2 года", "10–11 классы", 40),
]
FORMS = "очная, очно-заочная, заочная; семейное образование и самообразование"


def c_education():
    pred = {
        "НОО": page("/osnovnaya-obrazovatelnaya-programma-nachalnogo-obshhego-obrazovaniya-2/", "Учебные предметы — по учебному плану ООП НОО"),
        "ООО": page("/osnovnaya-obrazovatelnaya-programma-osnovnogo-obshhego-obrazovaniya/", "Учебные предметы — по учебному плану ООП ООО"),
        "СОО": todo("перечень предметов по учебному плану СОО"),
    }
    accred = [
        f'<tr itemprop="eduAccred"><td itemprop="eduCode">—</td><td itemprop="eduName">{n}</td><td itemprop="eduProf">общеобразовательная</td>'
        f'<td itemprop="eduLevel">{lvl}</td><td itemprop="eduForm">{FORMS}</td><td itemprop="learningTerm">{term}</td>'
        f'<td itemprop="eduPred">{pred[k]}</td><td itemprop="eduPrac">не предусмотрены</td></tr>'
        for k, n, lvl, term, _, _ in PROGS
    ]
    t1 = table(["Код", "Наименование образовательной программы", "Направленность", "Уровень образования", "Формы обучения",
                "Нормативный срок обучения", "Учебные предметы, курсы", "Практики"], accred)

    num = [f'<tr><td>{n}</td><td>{lvl}</td><td>{c}</td><td>0</td><td>0</td><td>0</td><td>{todo("уточнить")}</td><td>{todo("число или 0")}</td></tr>'
           for _, n, lvl, _, _, c in PROGS]
    t2 = table(["Образовательная программа", "Уровень", "Всего обучающихся на 01.01.2026", "За счёт федерального бюджета", "За счёт бюджета субъекта РФ",
                "За счёт местного бюджета", "По договорам за счёт физических и (или) юридических лиц", "Из них иностранные граждане"], num)

    op_main = {
        "НОО": doc("/wp-content/uploads/2024/03/CHISH-OOP-NOO-dlya-PDF-nachalka-s-pechatyu.pdf", "Образовательная программа", "opMain"),
        "ООО": ext("https://disk.yandex.ru/i/VkpgVyUIOjWJaw", "Образовательная программа", "opMain") + " " + todo("загрузить файл на сайт вместо ссылки на Яндекс.Диск"),
        "СОО": ext("https://disk.yandex.ru/i/UvOe6M4cPLIhzQ", "Образовательная программа", "opMain") + " " + todo("загрузить файл на сайт вместо ссылки на Яндекс.Диск"),
    }
    rpd = {
        "НОО": page("/osnovnaya-obrazovatelnaya-programma-nachalnogo-obshhego-obrazovaniya-2/", "Рабочие программы").replace("<a ", '<a itemprop="educationRpd" '),
        "ООО": page("/osnovnaya-obrazovatelnaya-programma-osnovnogo-obshhego-obrazovaniya/", "Рабочие программы").replace("<a ", '<a itemprop="educationRpd" ') + " " + todo("часть файлов рабочих программ не сохранилась"),
        "СОО": f'<span itemprop="educationRpd">{todo("рабочие программы СОО")}</span>',
    }
    graf = doc("/wp-content/uploads/2026/03/Kalendarnyj-uchebnyj-grafik-2025-26.pdf", "Календарный учебный график на 2025–2026 учебный год", "educationShedule")
    vosp = doc("/wp-content/uploads/2022/02/PROGRAMMA-VOSPITANIYA-2021-2026.pdf", "Рабочая программа воспитания (2021–2026)", "methodology") + " " + todo("календарный план воспитательной работы на 2025–2026")
    ops = [
        f'<tr itemprop="eduOp"><td itemprop="eduCode">—</td><td itemprop="eduName">{n}</td><td itemprop="eduLevel">{lvl}</td><td itemprop="eduProf">общеобразовательная</td>'
        f'<td itemprop="eduForm">{FORMS}</td><td>{op_main[k]}</td><td><span itemprop="educationPlan">{todo("учебный план отдельным файлом")}</span></td>'
        f'<td>{rpd[k]}</td><td>{graf}</td><td itemprop="eduPr">не предусмотрены</td><td>{vosp}</td></tr>'
        for k, n, lvl, _, _, _ in PROGS
    ]
    t3 = table(["Код", "Образовательная программа", "Уровень", "Направленность", "Формы обучения", "Описание и копия программы",
                "Учебный план", "Рабочие программы", "Календарный учебный график", "Рабочие программы практик", "Методические документы, программа воспитания"], ops)
    return (
        "<h2>Реализуемые уровни образования, формы и сроки обучения</h2>" + t1
        + "<h2>Языки образования</h2>"
        + '<p>Образовательная деятельность осуществляется на государственном языке Российской Федерации — русском.</p>'
        + f'<p>{doc("/wp-content/uploads/2026/03/Polozhkeie-o-yazyke-2023.pdf", "Положение о языке образования", "languageEl")}</p>'
        + "<h2>Численность обучающихся</h2>" + t2
        + f'<p>{doc("/wp-content/uploads/2026/03/CHislennost.pdf", "Численность обучающихся по реализуемым образовательным программам по источникам финансирования (на 01.01.2026)", "eduChislenEl")}</p>'
        + "<h2>Результаты приёма, перевода, восстановления и отчисления</h2>"
        + f'<p>Результаты приёма: <span itemprop="eduPriemEl">не применяется (приём без вступительных испытаний)</span>{draft()}</p>'
        + f'<p>Результаты перевода, восстановления и отчисления: <span itemprop="eduPerevodEl">{todo("документ с числом переведённых в другие школы, принятых из других школ, восстановленных и отчисленных за год")}</span></p>'
        + "<h2>Образовательные программы</h2>" + t3
        + f'<p>Адаптированные образовательные программы: <span itemprop="eduAdOp">не реализуются</span>{draft()}</p>'
        + "<h2>Государственная аккредитация</h2>"
        + '<p>Свидетельство о государственной аккредитации: серия 34А01 № 0000094, регистрационный № 100, срок действия — бессрочно.</p>'
        + f'<p>{ext("https://isga.obrnadzor.gov.ru/accredreestr/details/5e778a1b-306e-f8cc-e567-7eeae5e8ea0b", "Сведения в реестре аккредитованных организаций Рособрнадзора")}</p>'
    )


def c_standards():
    def fgos(title, main_href, extra):
        ex = "; ".join(ext(h, t) for t, h in extra)
        return f'<li>{ext(main_href, title, "eduFedDoc")} <span class="sv-note">официальная публикация: {ex}</span></li>'
    items = [
        fgos("ФГОС начального общего образования (приказ Минпросвещения России от 31.05.2021 № 286, действующая редакция)", "https://fgos.ru/fgos/fgos-noo/",
             [("приказ № 286", "http://publication.pravo.gov.ru/Document/View/0001202107050028"),
              ("изменения, приказ от 18.07.2022 № 569", "http://publication.pravo.gov.ru/Document/View/0001202208170032")]),
        fgos("ФГОС основного общего образования (приказ Минпросвещения России от 31.05.2021 № 287, действующая редакция)", "https://fgos.ru/fgos/fgos-ooo/",
             [("приказ № 287", "http://publication.pravo.gov.ru/Document/View/0001202107050027"),
              ("изменения, приказ от 18.07.2022 № 568", "http://publication.pravo.gov.ru/Document/View/0001202208170012")]),
        fgos("ФГОС среднего общего образования (приказ Минобрнауки России от 17.05.2012 № 413, действующая редакция)", "https://fgos.ru/fgos/fgos-soo/",
             [("изменения, приказ Минпросвещения России от 12.08.2022 № 732", "http://publication.pravo.gov.ru/Document/View/0001202209120008")]),
    ]
    return (
        "<h2>Федеральные государственные образовательные стандарты</h2>" + '<ul class="sv-docs">' + "".join(items) + "</ul>"
        + '<p>Образовательные стандарты, утверждённые школой самостоятельно: <span itemprop="eduStandartDoc">не применяется</span></p>'
        + '<p>Федеральные государственные требования: <span itemprop="eduFedTreb">не применяется</span></p>'
        + '<p>Самостоятельно устанавливаемые требования: <span itemprop="eduStandartTreb">не применяется</span></p>'
    )


def c_managers():
    def r(prop, fio, post):
        return f'<tr itemprop="{prop}"><td itemprop="fio">{fio}</td><td itemprop="post">{post}</td><td itemprop="telephone">{PHONE}</td><td itemprop="email">{EMAIL}</td></tr>'
    rows = [
        r("rucovodstvo", "Тураева Елена Владимировна", "Директор"),
        r("rucovodstvoZam", "Фадеева Ольга Модестовна", "Исполнительный директор"),
        r("rucovodstvoZam", "Заварухина Мария Юрьевна", "Заместитель директора по учебно-воспитательной работе (начальное и основное общее образование)"),
        r("rucovodstvoZam", "Гетьман Ирина Сергеевна", "Заместитель директора по учебно-воспитательной работе (внеклассная и внеурочная деятельность)"),
        r("rucovodstvoZam", "Гармашов Михаил Юрьевич", "Заместитель директора по информатизации образовательного процесса"),
    ]
    photos = [("Тураева Елена Владимировна", "Директор", "/wp-content/uploads/2024/01/Turaeva2.jpg"),
              ("Фадеева Ольга Модестовна", "Исполнительный директор", "/wp-content/uploads/2023/12/Fadeeva-O.M..jpg"),
              ("Заварухина Мария Юрьевна", "Заместитель директора по УВР", "/wp-content/uploads/2023/05/Zavaruhina-Mariya-YUrevna.jpg"),
              ("Гетьман Ирина Сергеевна", "Заместитель директора по УВР", "/wp-content/uploads/2023/05/Getman-I.S..jpg"),
              ("Гармашов Михаил Юрьевич", "Заместитель директора по информатизации, к. п. н.", "/wp-content/uploads/2023/05/Garmashov.jpg")]
    cards = "".join(f'<figure class="sv-card"><img src="{P}{src}" alt="{fio}" loading="lazy"><figcaption><strong>{fio}</strong><br>{post}</figcaption></figure>'
                    for fio, post, src in photos if have(src))
    return (table(["ФИО", "Должность", "Контактные телефоны", "Адрес электронной почты"], rows)
            + '<p>Филиалов нет — сведения о руководителях филиалов не приводятся.</p>'
            + (f'<div class="sv-cards">{cards}</div>' if cards else ""))


def c_employees():
    data = json.load(open(os.path.join(REPO, "data", "teachers.json"), encoding="utf-8"))
    rows = []
    for t in data:
        post = t.get("post") or todo("должность")
        m = re.match(r"учитель\s+(.+?)(?:,|$)", t.get("post", ""))
        disc = m.group(1) if m else ("предметы начального общего образования" if "начальных" in t.get("post", "") else "—")
        if disc.startswith("начальных классов"):
            disc = "предметы начального общего образования"
        n, w = years(t.get("exp"))
        edu = t.get("edu", "")
        lvl = ("высшее" if edu.lower() == "высшее" else f"высшее, {edu}") + "; " + todo("специальность и квалификация")
        op = "ООП НОО" if "начальных классов" in t.get("post", "") else todo("программы")
        rows.append(
            f'<tr itemprop="teachingStaff"><td itemprop="fio">{t["fio"]}</td><td itemprop="post">{post}</td>'
            f'<td itemprop="teachingDiscipline">{disc}</td><td itemprop="teachingLevel">{lvl}</td>'
            f'<td itemprop="degree">{t.get("degree", "нет")}</td><td itemprop="academStat">{t.get("zvanie", "нет")}</td>'
            f'<td itemprop="qualification">{todo("курсы за 3 года")}</td><td itemprop="profDevelopment">{todo("переподготовка или «нет»")}</td>'
            f'<td><span itemprop="specExperience">{n}</span> {w}</td><td itemprop="teachingOp">{op}</td></tr>')
    head = ["ФИО", "Должность", "Преподаваемые предметы, курсы", "Уровень образования, специальность, квалификация", "Учёная степень",
            "Учёное звание", "Повышение квалификации (за 3 года)", "Профессиональная переподготовка", "Стаж работы в профессиональной сфере", "Образовательные программы"]
    files = "".join(f"<li>{doc(p, t)}</li>" for t, p in [
        ("Сведения о педагогических работниках — начальная школа", "/wp-content/uploads/2025/01/2024Svedeniya-o-pedagogicheskih-rabotnikah-nachalnaya-shkola.pdf"),
        ("Сведения о педагогических работниках — основная школа", "/wp-content/uploads/2025/01/2024Svedeniya-o-pedagogicheskih-rabotnikah-osnovnaya-shkola.pdf"),
        ("Сведения о педагогических работниках — старшая школа", "/wp-content/uploads/2025/01/2024Svedeniya-o-pedagogicheskih-rabotnikah-starshaya-shkola.pdf")])
    return ('<p class="sv-banner">Список педагогов — по прежней версии сайта (2025 г.). По п. 12 приказа № 1493 сведения приводятся по каждой '
            'образовательной программе; нужны актуальные данные по каждому педагогу (см. жёлтые пометки).</p>'
            + table(head, rows) + "<h2>Файлы со сведениями о педагогических работниках</h2>" + f'<ul class="sv-docs">{files}</ul>')


def c_objects():
    intro = (
        '<p>Школа расположена (и имеет юридический адрес) в Центральном районе Волгограда, в главном корпусе Волгоградского государственного '
        'социально-педагогического университета: проспект имени В. И. Ленина, 27. Учебный процесс организован в трёх зданиях:</p>'
        f'<ol><li>начальная и основная школа (1–9 классы) — отдельно стоящее здание: {ADDR_VATUTINA};</li>'
        f'<li>средняя школа (10–11 классы) — основные корпуса ВГСПУ: {ADDR_LENINA};</li>'
        f'<li>лаборатории физики, кабинет информационных технологий, кабинет астрономии — учебный корпус № 2 ВГСПУ: {ADDR_AKADEM}.</li></ol>'
        '<p>В здании начальной и основной школы 14 учебных кабинетов, средняя школа занимает 6 аудиторий. Все педагоги имеют высшее образование.</p>'
    )
    ovz_t = todo("приспособленность для инвалидов и лиц с ОВЗ")

    def cab(addr, name, osn, prop="purposeCab", a="addressCab", n="nameCab", o="osnCab", z="ovzCab"):
        return f'<tr itemprop="{prop}"><td itemprop="{a}">{addr}</td><td itemprop="{n}">{name}</td><td itemprop="{o}">{osn}</td><td itemprop="{z}">{ovz_t}</td></tr>'
    cabs = [
        cab(ADDR_VATUTINA, "Учебные кабинеты начальной и основной школы (14)", "мультимедийное оборудование, интерактивные доски, автоматизированные рабочие места"),
        cab(ADDR_VATUTINA, "Компьютерный класс", "компьютеры с доступом к сети «Интернет»"),
        cab(ADDR_LENINA, "Аудитории средней школы (6)", "мультимедийное оборудование, интерактивная доска"),
        cab(ADDR_AKADEM, "Кабинет информационных технологий", "компьютерное оборудование"),
        cab(ADDR_AKADEM, "Кабинет астрономии", todo("оснащённость")),
    ]
    pr = lambda addr, name, osn: cab(addr, name, osn, "purposePrac", "addressPrac", "namePrac", "osnPrac", "ovzPrac")
    pracs = [
        pr(ADDR_LENINA, "Лаборатория химии", todo("оснащённость")),
        pr(ADDR_LENINA, "Биологический музей", todo("оснащённость")),
        pr(ADDR_AKADEM, "Лаборатории физики", todo("оснащённость")),
        pr(ADDR_VATUTINA, "Столярная мастерская", todo("оснащённость")),
    ]
    head4 = ["Адрес", "Наименование", "Оснащённость", "Приспособленность для использования инвалидами и лицами с ОВЗ"]
    obj = lambda prop, name, addr: (f'<tr itemprop="{prop}"><td itemprop="objName">{name}</td><td itemprop="objAddress">{addr}</td>'
                                    f'<td itemprop="objSq">{todo("м²")}</td><td itemprop="objCnt">{todo("мест")}</td><td itemprop="objOvz">{ovz_t}</td></tr>')
    libs = [f'<tr itemprop="purposeLibr"><td itemprop="objName">{todo("библиотека: есть ли, где")}</td><td itemprop="objAddress">—</td>'
            f'<td itemprop="objSq">—</td><td itemprop="objCnt">—</td><td itemprop="objOvz">—</td></tr>']
    sport = [obj("purposeSport", "Спортивный зал", ADDR_VATUTINA), obj("purposeSport", "Спортивный зал", ADDR_LENINA),
             obj("purposeSport", "Спортивная площадка", todo("адрес"))]
    head5 = ["Наименование объекта", "Адрес", "Площадь, м²", "Количество мест", "Приспособленность для инвалидов и лиц с ОВЗ"]
    er = [("Министерство просвещения Российской Федерации", "https://edu.gov.ru/"),
          ("Федеральная служба по надзору в сфере образования и науки", "https://obrnadzor.gov.ru/"),
          ("Федеральный портал «Российское образование»", "https://www.edu.ru/"),
          ("Российская электронная школа", "https://resh.edu.ru/"),
          ("Электронная библиотека «Лекта»", "https://lecta.ru"),
          ("Инфоурок", "https://infourok.ru/"),
          ("Детский образовательный портал Uchi.ru", "https://uchi.ru/")]
    hostel = table(["Показатель", "Общежития", "Интернаты"], [
        '<tr><td>Количество общежитий / интернатов</td><td itemprop="hostelInfo">0</td><td itemprop="interInfo">0</td></tr>',
        '<tr><td>Количество мест</td><td itemprop="hostelNum">0</td><td itemprop="interNum">0</td></tr>',
        '<tr><td>Количество жилых помещений, приспособленных для использования инвалидами и лицами с ОВЗ</td><td itemprop="hostelNumOvz">0</td><td itemprop="interNumOvz">0</td></tr>'])
    return (
        intro
        + "<h2>Оборудованные учебные кабинеты</h2>" + table(head4, cabs)
        + "<h2>Объекты для проведения практических занятий</h2>" + table(head4, pracs)
        + "<h2>Библиотеки</h2>" + table(head5, libs)
        + "<h2>Объекты спорта</h2>" + table(head5, sport)
        + "<p>Также в школе есть актовый и хореографический залы, помещения для занятий музыкой и изобразительным искусством, "
          "помещения для учебно-исследовательской и проектной деятельности, моделирования и технического творчества.</p>"
        + "<h2>Средства обучения и воспитания</h2>"
        + '<div itemprop="purposeFacil"><p>Учебные кабинеты с автоматизированными рабочими местами обучающихся и педагогов, лекционные аудитории, '
          'лаборатории и мастерские, помещения для музыки, хореографии и изобразительного искусства, спортивные залы и площадка, оснащённые '
          'игровым, спортивным оборудованием и инвентарём.</p>'
        + f'<p>{doc("/wp-content/uploads/2023/12/programmno-metodicheskoe-osnashhenie.pdf", "Программно-методическое обеспечение образовательного процесса")}</p>'
        + f'<p>{doc("/wp-content/uploads/2018/07/Tablitsa-osnashhennost.docx", "Материально-техническое обеспечение образовательного процесса (таблица оснащённости)")} {todo("актуальная таблица")}</p></div>'
        + '<p itemprop="purposeFacilOvz">Средства обучения, приспособленные для использования инвалидами и лицами с ОВЗ: мультимедийные проекторы, '
          'интерактивные доски, компьютеры, ноутбуки, принтеры, сканеры, версия официального сайта для слабовидящих.</p>'
        + "<h2>Доступ к информационным системам и информационно-телекоммуникационным сетям</h2>"
        + '<p itemprop="comNet">В школе обеспечен доступ к сети «Интернет» для всех обучающихся. Доступ имеется во всех учебных кабинетах.</p>'
        + '<p itemprop="comNetOvz">Доступ к сети «Интернет» обеспечен в том числе для обучающихся с инвалидностью и ОВЗ.</p>'
        + "<h2>Электронные образовательные ресурсы</h2>"
        + '<ul class="sv-docs">' + "".join(f"<li>{ext(h, t, 'erList')}</li>" for t, h in er) + "</ul>"
        + f'<p>Электронные образовательные ресурсы, приспособленные для инвалидов и лиц с ОВЗ: <span itemprop="erListOvz">{todo("перечень (прежняя ссылка вела на сайт другой школы)")}</span></p>'
        + "<h2>Доступная среда</h2>"
        + '<p itemprop="ovz">Вход в школу оборудован пандусом, есть переносной пандус и сменное кресло-коляска. Доступная входная группа, '
          'достаточная ширина дверных проёмов, лестничных маршей и площадок. Предоставляется сопровождение инвалида по территории '
          'объекта работником школы.</p>'
        + '<p itemprop="techOvz">Специальные технические средства обучения коллективного и индивидуального пользования: мультимедийные проекторы, '
          'интерактивные доски, компьютеры, ноутбуки, принтеры, сканеры; версия официального сайта для слабовидящих.</p>'
        + '<p>Психолого-педагогическое сопровождение детей с ОВЗ: в школе работает педагог-психолог, прошедший обучение по программе '
          '«Инклюзивное образование в школе: от теории к практике обучения детей с ОВЗ в условиях реализации ФГОС».</p>'
        + "<h2>Общежитие, интернат</h2>" + "<p>Общежитие и интернат не предусмотрены.</p>" + hostel
        + '<p>Условия беспрепятственного доступа в общежитие, интернат: <span itemprop="hostelInterOvz">не предусмотрено (общежития и интерната нет)</span></p>'
        + '<p>Плата за проживание в общежитии: <span itemprop="localActObSt">не предусмотрено</span></p>'
    )


def c_paid():
    prices = table(["№", "Наименование услуги", "Стоимость в месяц при оплате в течение всего календарного года (12 месяцев)",
                    "Стоимость в месяц при оплате до 1 числа оплачиваемого месяца"], [
        f"<tr><td>{i}</td><td>Обучение по {n.lower().replace('основная образовательная программа', 'основной общеобразовательной программе')}</td><td>30 000 руб.</td><td>29 000 руб.</td></tr>"
        for i, (_, n, *_r) in enumerate(PROGS, 1)])
    return (
        '<p>Перечень образовательных услуг: обучение по основным общеобразовательным программам начального общего, основного общего и среднего '
        'общего образования в очной, очно-заочной, заочной форме, в форме семейного образования и самообразования.</p>'
        + '<ul class="sv-docs">'
        + f'<li>{doc("/wp-content/uploads/2019/09/3-Polozhenie-ob-okazanii-platnyh-obrazovatelnyh-uslug-2.pdf", "Положение о порядке оказания платных образовательных услуг", "paidEdu")} '
          f'{page("/polozhenie-ob-okazanii-platnyh-obrazovatelnyh-uslug/", "(текст на сайте)")} {todo("проверить, что положение действующее (редакция 2019 г.)")}</li>'
        + f'<li>{doc("/wp-content/uploads/2026/06/1-Dogovor-s-roditelyami-2026-Turaeva.docx", "Образец договора об оказании платных образовательных услуг", "paidDog")}</li>'
        + f'<li>{doc("/wp-content/uploads/2026/06/Plata-za-obuchenie-2026-27.pdf", "Документ об утверждении стоимости обучения на 2026–2027 учебный год", "paidSt")}</li>'
        + f'<li>Плата за присмотр и уход в группах продлённого дня, за содержание в интернате: <span itemprop="paidParents">{todo("документ или «не взимается»")}</span></li>'
        + "</ul><h2>Стоимость обучения</h2>" + prices
    )


def c_budget():
    vol = table(["За счёт федерального бюджета, тыс. руб.", "За счёт бюджета субъекта РФ, тыс. руб.", "За счёт местного бюджета, тыс. руб.",
                 "По договорам об оказании платных образовательных услуг, тыс. руб."], [
        f'<tr><td itemprop="finBFVolume">{todo("сумма или 0")}</td><td itemprop="finBRVolume">{todo("сумма или 0")}</td>'
        f'<td itemprop="finBMVolume">{todo("сумма или 0")}</td><td itemprop="finPVolume">{todo("сумма")}</td></tr>'])
    mov = table(["Год", "Поступившие финансовые и материальные средства", "Расходованные финансовые и материальные средства"], [
        f'<tr itemprop="volume"><td itemprop="finYear">2025</td><td itemprop="finPost">{todo("сумма")}</td><td itemprop="finRas">{todo("сумма")}</td></tr>'])
    return (
        "<h2>Объём образовательной деятельности по источникам финансирования</h2>" + vol
        + "<h2>Поступление и расходование финансовых и материальных средств</h2>" + mov
        + '<ul class="sv-docs">'
        + f'<li>{doc("/wp-content/uploads/2026/03/Spravka.pdf", "Справка о поступлении и расходовании финансовых и материальных средств по итогам 2025 года")}</li>'
        + f'<li>{doc("/wp-content/uploads/2026/03/Plan.pdf", "План финансово-хозяйственной деятельности на 2026 год", "finPlanDocLink")}</li></ul>'
    )


def c_vacant():
    rows = [f'<tr itemprop="vacant"><td itemprop="eduCode">—</td><td itemprop="eduName">{n}</td><td itemprop="eduLevel">{lvl}</td>'
            f'<td itemprop="eduProf">общеобразовательная</td><td itemprop="eduCourse">{cls}</td><td itemprop="eduForm">очная</td>'
            f'<td itemprop="numberBFVacant">0</td><td itemprop="numberBRVacant">0</td><td itemprop="numberBMVacant">0</td>'
            f'<td itemprop="numberPVacant">{todo("число мест (лучше по каждому классу)")}</td></tr>'
            for _, n, lvl, _, cls, _ in PROGS]
    return (table(["Код", "Образовательная программа", "Уровень", "Направленность", "Классы", "Форма обучения",
                   "Бюджет РФ", "Бюджет субъекта РФ", "Местный бюджет", "По договорам за счёт физических и (или) юридических лиц"], rows)
            + f'<p>Нули в бюджетных столбцах — {draft().strip()}. Сведения обновляются в течение 10 рабочих дней после изменения.</p>')


def c_grants():
    hostel = table(["Показатель", "Общежития", "Интернаты"], [
        '<tr><td>Количество общежитий / интернатов</td><td itemprop="hostelInfo">0</td><td itemprop="interInfo">0</td></tr>',
        '<tr><td>Количество мест</td><td itemprop="hostelNum">0</td><td itemprop="interNum">0</td></tr>',
        '<tr><td>Количество жилых помещений, приспособленных для использования инвалидами и лицами с ОВЗ</td><td itemprop="hostelNumOvz">0</td><td itemprop="interNumOvz">0</td></tr>'])
    return ('<p itemprop="grant">Выплата стипендий не предусмотрена.</p>'
            '<p itemprop="support">Меры социальной поддержки обучающихся не предусмотрены.</p>'
            '<p>Локальные нормативные акты о стипендиях и мерах поддержки: <span itemprop="localAct">нет</span></p>'
            '<h2>Общежитие, интернат</h2><p>Проживание в общежитии и иных жилых помещениях не предусмотрено.</p>' + hostel
            + '<p>Плата за проживание в общежитии: <span itemprop="localActObSt">не предусмотрено</span></p>')


def c_inter():
    return (table(["N", "Государство", "Наименование организации", "Реквизиты договора (наименование, дата, номер, срок действия)"], [
        '<tr itemprop="internationalDog"><td>1</td><td itemprop="stateName">отсутствует</td><td itemprop="orgName">отсутствует</td><td itemprop="dogReg">отсутствует</td></tr>'])
            + f'<p>Заключённых и планируемых к заключению договоров с иностранными и (или) международными организациями по вопросам образования и науки нет.{draft()}</p>')


def c_catering():
    def obj(prop, name, addr):
        return (f'<tr itemprop="{prop}"><td itemprop="objName">{name}</td><td itemprop="objAddress">{addr}</td><td itemprop="objSq">{todo("м²")}</td>'
                f'<td itemprop="objCnt">{todo("мест")}</td><td itemprop="objOvz">{todo("приспособленность для ОВЗ")}</td></tr>')
    head = ["Наименование объекта", "Адрес", "Площадь, м²", "Количество мест", "Приспособленность для инвалидов и лиц с ОВЗ"]
    acts = [("Постановление Главного государственного санитарного врача РФ от 27.10.2020 № 32 (СанПиН 2.3/2.4.3590-20)", "https://www.rospotrebnadzor.ru/upload/iblock/789/0001202011120001.pdf"),
            ("Федеральный закон от 02.01.2000 № 29-ФЗ «О качестве и безопасности пищевых продуктов»", "http://www.kremlin.ru/acts/bank/1488"),
            ("Постановление Главного государственного санитарного врача РФ от 28.09.2020 № 28 (СП 2.4.3648-20)", "https://www.rospotrebnadzor.ru/files/news/SP2.4.3648-20_deti.pdf"),
            ("Федеральный закон от 30.03.1999 № 52-ФЗ «О санитарно-эпидемиологическом благополучии населения»", "https://www.rospotrebnadzor.ru/documents/details.php?ELEMENT_ID=242"),
            ("Закон РФ от 07.02.1992 № 2300-1 «О защите прав потребителей»", "https://www.rospotrebnadzor.ru/documents/details.php?ELEMENT_ID=17041"),
            ("Методические рекомендации МР 2.4.0179-20 «Рекомендации по организации питания для обучающихся общеобразовательных организаций»",
             "https://www.rospotrebnadzor.ru/upload/iblock/078/mr-2.4.0179_20-rekomendatsii-po-organizatsii-pitaniya.pdf")]
    return (
        "<h2>Условия питания обучающихся</h2>"
        + table(head, [obj("meals", "Столовая", ADDR_VATUTINA)])
        + f'<p>{todo("если старшеклассники (Ленина, 27) питаются в другом месте — добавить строку")}</p>'
        + "<p>Услуги питания оказывает ЧОУ СО Частная интегрированная школа. Руководитель — Тураева Елена Владимировна. "
          f"Адрес: {ADDR_VATUTINA}. Телефон: {PHONE}. Электронная почта: {EMAIL}.</p>"
        + "<p>Ответственный за организацию питания — заместитель директора по учебно-воспитательной работе Гетьман Ирина Сергеевна, "
          f"телефон {PHONE}, {EMAIL}.</p>"
        + '<p>Столовая работает в режиме пятидневной рабочей недели. Основной принцип организации питания — рациональное питание с широким '
          'ассортиментом продуктов и правильной кулинарно-технологической обработкой.</p>'
        + '<ul class="sv-docs">'
        + f'<li>{doc("/wp-content/uploads/2024/02/23_24_-Rezhim-pitaniya.pdf", "Режим питания")} {todo("актуальный режим питания (файл в архиве повреждён)")}</li>'
        + f'<li>{doc("/wp-content/uploads/2024/02/Dvuhnedelnoe-menyu_23_24.pdf", "Примерное двухнедельное меню")} {todo("актуальное меню (файл в архиве повреждён)")}</li>'
        + f'<li>{page("/zdorovoe-pitanie-shkolnikov/", "Здоровое питание школьников")}</li></ul>'
        + "<h2>Условия охраны здоровья обучающихся</h2>"
        + table(head, [obj("health", "Медицинский кабинет", ADDR_VATUTINA)])
        + '<p>В школе работает медицинская сестра. Между школой и медицинской организацией подписано соглашение по оказанию первичной '
          'медико-санитарной помощи обучающимся по месту нахождения школы. Проводятся профилактические и оздоровительные мероприятия, '
          'санитарно-просветительская работа, антропометрическое обследование детей для подбора мебели, ежедневный контроль санитарного '
          'состояния пищеблока и классов.</p>'
        + "<h2>Нормативные акты</h2>" + '<ul class="sv-docs">' + "".join(f"<li>{ext(h, t)}</li>" for t, h in acts) + "</ul>"
        + "<h2>Телефоны горячих линий</h2>"
        + "<p>Комитет образования, науки и молодежной политики Волгоградской области, «горячая линия» по вопросам обеспечения горячим питанием: "
          "(8442) 30-86-02, 30-86-47, 30-86-54, 30-86-49 (с 8:30 до 16:30 по рабочим дням).</p>"
        + "<p>Министерство просвещения Российской Федерации, общественная приёмная: +7 (495) 587-01-19.</p>"
    )


CONTENT = {"common": c_common, "struct": c_struct, "document": c_document, "education": c_education, "eduStandarts": c_standards,
           "managers": c_managers, "employees": c_employees, "objects": c_objects, "paid_edu": c_paid, "budget": c_budget,
           "vacant": c_vacant, "grants": c_grants, "inter": c_inter, "catering": c_catering}

CSS = """
.sv-nav{display:flex;flex-wrap:wrap;gap:6px 8px;margin:0 0 26px;padding:12px;border-radius:14px;background:#f4f6fa}
.sv-nav a{font-size:14px;line-height:1.3;padding:6px 10px;border-radius:8px;background:#fff;color:#1d3557!important;text-decoration:none!important;border:1px solid #dfe5ee}
.sv-nav a.is-current{background:#1d3557;color:#fff!important;border-color:#1d3557}
.sv-wrap{overflow-x:auto;margin:8px 0 22px}
.sv-table{width:100%;border-collapse:collapse;font-size:15px;line-height:1.4}
.sv-table th,.sv-table td{border:1px solid #d5dbe5;padding:8px 10px;vertical-align:top;text-align:left}
.sv-table th{background:#f4f6fa;font-weight:600}
.sv-todo{display:inline-block;margin:2px 0;padding:2px 8px;border-radius:6px;background:#fff3cd;color:#6b4f00;font-size:13px;line-height:1.35;border:1px solid #ffe08a}
.sv-miss{display:inline-block;padding:1px 7px;border-radius:6px;background:#fde2e1;color:#9b1c1c;font-size:12px;border:1px solid #f5b5b1}
.sv-draft{display:inline-block;padding:1px 7px;border-radius:6px;background:#e7f0ff;color:#1d4ed8;font-size:12px;border:1px solid #bfd3ff}
.sv-note{font-size:13px;color:#555}
.sv-note-p{font-size:14px;color:#555}
.sv-banner{padding:12px 14px;border-radius:10px;background:#fff8e6;border:1px solid #ffe08a;font-size:14px;margin:0 0 18px}
.sv-docs{padding-left:20px}.sv-docs li{margin:7px 0;list-style:disc}
.article-content__text h2{font-size:22px;margin:30px 0 12px;font-weight:700}
.article-content__text h3{font-size:18px;margin:22px 0 8px;font-weight:700}
.article-content__text h4{font-size:15px;margin:14px 0 4px;font-weight:600}
.sv-cards{display:flex;flex-wrap:wrap;gap:16px;margin-top:10px}
.sv-card{width:200px;margin:0}.sv-card img{width:100%;height:150px;object-fit:cover;border-radius:10px}
.sv-card figcaption{font-size:13px;line-height:1.35;margin-top:6px}
.sv-index{columns:2;column-gap:28px;padding-left:20px}.sv-index li{margin:8px 0;break-inside:avoid;list-style:decimal}
@media (max-width:700px){.sv-index{columns:1}}
"""
BANNER = ('<p class="sv-banner"><strong>Предварительная версия раздела.</strong> Жёлтым отмечено, что нужно получить от школы; красным — файлы, '
          'которых не сохранилось; синим — типовые формулировки, которые школа должна подтвердить.</p>')


def nav(cur):
    items = [f'<a href="{P}/sveden/"{" class=\"is-current\"" if cur == "" else ""}>Все подразделы</a>']
    for slug, title in SUBS:
        items.append(f'<a href="{url(slug)}"{" class=\"is-current\"" if cur == slug else ""}>{title}</a>')
    return '<nav class="sv-nav" aria-label="Сведения об образовательной организации">' + "".join(items) + "</nav>"


def menu_block():
    items = "".join(f'<a href="{url(s)}"><li class="header-dropdown__item">{t}</li></a>' for s, t in SUBS)
    return (f'<div class="header-dropdown"><a href="{P}/sveden/" class="header-menu__link">Сведения об образовательной организации</a>\n'
            f'<ul  class="header-dropdown__list">\n{items}</ul>\n</div>')


MENU_RE = re.compile(r'<div class="header-dropdown">\s*<a href="' + re.escape(P) + r'/svedeniya-o-shkole/"[^>]*>\s*Сведения об образовательной организации\s*</a>\s*<ul[^>]*>.*?</ul>\s*</div>', re.S)


def fix_common(h):
    """Правки, общие для всех страниц сайта."""
    h, _ = MENU_RE.subn(lambda m: menu_block(), h)
    if "mobile__menu" in h and f'href="{P}/sveden/"' not in h.split("mobile__menu", 1)[1][:600]:
        h = h.replace('<nav class="mobile__menu">', f'<nav class="mobile__menu">\n                <a class="mobile__link" href="{P}/sveden/">Сведения об образовательной организации</a>', 1)
    h = h.replace('itemprop="Copy"', 'itemprop="copy"')
    for old, new in OLD.items():
        for v in (f'href="{P}/{old}/"', f'href="{P}//{old}/"', f'href="{P}/{old}"'):
            h = h.replace(v, f'href="{url(new)}"')
    return h


# ---------- шаблон страницы ----------
tpl_path = os.path.join(SITE, "svedeniya-o-shkole", "index.html")
TPL = open(tpl_path, encoding="utf-8").read()

# Эталонное (актуальное) меню: часть страниц архив сохранил со старыми версиями меню
_canon = fix_common(TPL)
NAV_RES = [re.compile(r'<nav class="header-menu">.*?</nav>', re.S), re.compile(r'<nav class="header-menu _second">.*?</nav>', re.S),
           re.compile(r'<nav class="mobile__menu">.*?</nav>', re.S)]
CANON_NAVS = [r.search(_canon).group(0) for r in NAV_RES]

GAL_RE = re.compile(r'href="' + re.escape(P) + r'/(wp-content/uploads/photo-gallery/imported_from_media_libray/)([^"?]+)(\?[^"]*)?"')


def fix_gallery(h):
    """Полноразмерных фото галереи в архиве нет, а превью есть — открываем превью."""
    def rep(m):
        base, name = m.group(1), m.group(2)
        if have("/" + base + name) or not have("/" + base + "thumb/" + name):
            return m.group(0)
        return f'href="{P}/{base}thumb/{name}"'
    return GAL_RE.sub(rep, h)


def unify_nav(h):
    for r, canon in zip(NAV_RES, CANON_NAVS):
        h = r.sub(lambda m: canon, h, count=1)
    return h


def render(title, h1, body, cur):
    soup = BeautifulSoup(TPL, "lxml")
    soup.title.string = f"{title} | Частная интегрированная школа"
    for l in soup.find_all("link"):
        rel, typ = " ".join(l.get("rel") or []), l.get("type") or ""
        if rel == "shortlink" or "oembed" in typ:
            l.decompose()
    for a in soup.find_all(attrs={"aria-current": True}):
        del a["aria-current"]
    st = soup.new_tag("style")
    st.string = CSS
    soup.head.append(st)
    ac = soup.select_one(".article-content")
    for k in ("data-aos", "data-aos-delay"):
        if ac.has_attr(k):
            del ac[k]
    ac.select_one("h1.article-content__title").string = h1
    box = ac.select_one(".article-content__text")
    box.clear()
    box.append(BeautifulSoup(nav(cur) + body, "html.parser"))
    return fix_gallery(unify_nav(fix_common(str(soup))))


def write(rel, html):
    p = os.path.join(SITE, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(html)


# 1) разделы
for slug, title in SUBS:
    write(f"sveden/{slug}/index.html", render(title, title, BANNER + CONTENT[slug](), slug))
idx = ('<p>Раздел содержит сведения, обязательные к размещению на официальном сайте образовательной организации '
       '(ст. 29 Федерального закона № 273-ФЗ, приказ Рособрнадзора от 04.08.2023 № 1493).</p><ol class="sv-index">'
       + "".join(f'<li><a href="{url(s)}">{t}</a></li>' for s, t in SUBS) + "</ol>")
write("sveden/index.html", render("Сведения об образовательной организации", "Сведения об образовательной организации", BANNER + idx, ""))

# 2) старые адреса -> переадресация
for old, new in OLD.items():
    dest = url(new)
    write(f"{old}/index.html", f'<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><meta name="robots" content="noindex">'
          f'<title>Страница перенесена</title><meta http-equiv="refresh" content="0; url={dest}"><link rel="canonical" href="{dest}"></head>'
          f'<body><p>Страница перенесена: <a href="{dest}">{dest}</a></p><script>location.replace("{dest}")</script></body></html>')

# 3) удалить страницы старого сайта (Drupal, до 2017 г.)
removed = 0
for dp, dns, fns in os.walk(SITE):
    for n in fns:
        if not n.endswith(".html"):
            continue
        p = os.path.join(dp, n)
        h = open(p, encoding="utf-8", errors="replace").read(300000)
        if "themes/chish-new" not in h and ("sites/all/themes" in h or "Drupal" in h or "drupal" in h):
            os.remove(p)
            removed += 1
for d in ("misc", "modules", "sites/all"):
    shutil.rmtree(os.path.join(SITE, d), ignore_errors=True)
for dp, dns, fns in os.walk(SITE, topdown=False):
    if dp != SITE and not os.listdir(dp):
        os.rmdir(dp)

# 4) общие правки на всех страницах
changed = 0
for dp, _, fns in os.walk(SITE):
    for n in fns:
        if n.endswith(".html"):
            p = os.path.join(dp, n)
            h = open(p, encoding="utf-8", errors="replace").read()
            nh = fix_common(h)
            if "themes/chish-new" in nh:
                nh = fix_gallery(unify_nav(nh))
            if nh != h:
                open(p, "w", encoding="utf-8").write(nh)
                changed += 1

# 5) страница 404
body404 = ('<p>Такой страницы или документа нет. Возможно, файл ещё не загружен после восстановления сайта.</p>'
           f'<p><a href="{P}/">На главную</a> · <a href="{P}/sveden/">Сведения об образовательной организации</a></p>')
write("404.html", render("Страница не найдена", "Страница не найдена", body404, None).replace(f'<nav class="sv-nav"', '<nav hidden class="sv-nav"'))

# 6) фоновое видео на главной
assets = os.path.join(REPO, "assets")
if os.path.isfile(os.path.join(assets, "hero-bg.mp4")):
    up = os.path.join(SITE, "wp-content", "uploads")
    shutil.copy(os.path.join(assets, "hero-bg.mp4"), os.path.join(up, "hero-bg.mp4"))
    shutil.copy(os.path.join(assets, "hero-poster.jpg"), os.path.join(up, "hero-poster.jpg"))
    hp = os.path.join(SITE, "index.html")
    h = open(hp, encoding="utf-8").read()
    if "hero-bg" not in h:
        vid = (f'<video class="hero-bg" autoplay muted loop playsinline preload="auto" poster="{P}/wp-content/uploads/hero-poster.jpg" aria-hidden="true">'
               f'<source src="{P}/wp-content/uploads/hero-bg.mp4" type="video/mp4"></video><div class="hero-shade" aria-hidden="true"></div>')
        h = re.sub(r'(<section class="main _main"\s*>)', r"\1" + vid, h, count=1)
        css = ('<style>.main._main{position:relative}.main._main .hero-bg,.main._main .hero-shade{position:absolute;inset:0;width:100%;height:100%;'
               'border-radius:inherit;z-index:0;pointer-events:none}.main._main .hero-bg{object-fit:cover}'
               '.main._main .hero-shade{background:linear-gradient(180deg,rgba(0,0,0,.45),rgba(0,0,0,.15) 45%,rgba(0,0,0,.35))}'
               '.main._main>*:not(.hero-bg):not(.hero-shade){position:relative;z-index:1}'
               '@media (prefers-reduced-motion:reduce){.main._main .hero-bg{display:none}}</style>')
        h = h.replace("</head>", css + "</head>", 1)
        open(hp, "w", encoding="utf-8").write(h)
        print("hero video added")

# 7) распознанные сканы (OCR)
ocr = os.path.join(REPO, "ocr")
n_ocr = 0
if os.path.isdir(ocr):
    for f in os.listdir(ocr):
        if f.endswith(".pdf"):
            shutil.copy(os.path.join(ocr, f), os.path.join(SITE, "wp-content", "uploads", "2023", "11", f))
            n_ocr += 1

print(f"sveden pages: {len(SUBS) + 1}; redirects: {len(OLD)}; legacy pages removed: {removed}; pages updated: {changed}; ocr files: {n_ocr}")
print(f"todo marks: {stats['todo']}; draft marks: {stats['draft']}; missing files: {len(stats['missing'])}")
json.dump({"todo": stats["todo"], "draft": stats["draft"], "missing": stats["missing"]},
          open(os.path.join(SITE, "sveden", "status.json"), "w"), ensure_ascii=False, indent=1)

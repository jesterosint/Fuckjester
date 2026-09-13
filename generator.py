"""Генератор личностей. 1500+ комбинаций на справочниках."""
from __future__ import annotations

import json
import random
import string
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from typing import Optional

from faker import Faker

FAKERS = {
    "RU": Faker("ru_RU"), "US": Faker("en_US"),
    "DE": Faker("de_DE"), "FR": Faker("fr_FR"), "GB": Faker("en_GB"),
}

MALE = ["Александр","Дмитрий","Максим","Сергей","Андрей","Алексей","Артём","Илья",
        "Кирилл","Михаил","Никита","Матвей","Роман","Егор","Арсений","Иван","Денис",
        "Евгений","Даниил","Тимофей","Владислав","Игорь","Олег","Юрий","Константин",
        "Павел","Антон","Виктор","Георгий","Степан"]
FEMALE = ["Анна","Мария","Елена","Ольга","Наталья","Ирина","Татьяна","Светлана",
          "Екатерина","Юлия","Дарья","Алина","Ксения","Полина","София","Виктория",
          "Валерия","Марина","Людмила","Галина","Вера","Надежда","Любовь","Евгения",
          "Анастасия","Кристина","Маргарита","Инна","Оксана","Регина"]
SUR_M = ["Иванов","Смирнов","Кузнецов","Попов","Васильев","Петров","Соколов",
         "Михайлов","Новиков","Фёдоров","Морозов","Волков","Алексеев","Лебедев",
         "Семёнов","Егоров","Павлов","Козлов","Степанов","Николаев","Орлов",
         "Андреев","Макаров","Никитин","Захаров","Зайцев","Соловьёв","Борисов",
         "Яковлев","Григорьев"]
SUR_F = [s + "а" for s in SUR_M]
PAT_M = ["Александрович","Дмитриевич","Сергеевич","Андреевич","Алексеевич",
         "Михайлович","Иванович","Петрович","Владимирович","Николаевич",
         "Олегович","Юрьевич","Викторович","Игоревич","Павлович"]
PAT_F = [s[:-2] + "овна" for s in PAT_M]

CITIES = [("Москва",101000,150000),("Санкт-Петербург",190000,199000),
          ("Новосибирск",630000,630999),("Екатеринбург",620000,620999),
          ("Казань",420000,420999),("Нижний Новгород",603000,603999),
          ("Челябинск",454000,454999),("Самара",443000,443999),
          ("Омск",644000,644999),("Ростов-на-Дону",344000,344999),
          ("Уфа",450000,450999),("Красноярск",660000,660999),
          ("Воронеж",394000,394999),("Пермь",614000,614999),
          ("Волгоград",400000,400999)]

STREETS = ["ул. Ленина","ул. Пушкина","ул. Гагарина","ул. Советская","пр. Мира",
           "ул. Молодёжная","ул. Садовая","ул. Центральная","ул. Школьная",
           "ул. Заречная","ул. Лесная","ул. Новая","ул. Октябрьская",
           "ул. Комсомольская","ул. Первомайская","ул. Кирова","ул. Горького",
           "ул. Чехова","ул. Толстого","ул. Достоевского"]

COMPANIES = ["ООО «Ромашка»","ООО «ТехноСофт»","АО «Газпромбанк»","ПАО «Сбербанк»",
             "ООО «Яндекс»","ООО «ВК»","ПАО «МТС»","ПАО «Ростелеком»","ООО «Озон»",
             "ООО «Вайлдберриз»","АО «Альфа-Банк»","ООО «Тинькофф»","ПАО «Лукойл»",
             "ООО «Магнит»","ПАО «Аэрофлот»","ООО «Купер»","АО «Почта России»",
             "ПАО «Роснефть»","ООО «Самокат»","ООО «Авито»"]

POSITIONS = ["Менеджер","Старший менеджер","Ведущий специалист","Инженер-программист",
             "Аналитик данных","Системный администратор","Бухгалтер","Юрист",
             "Маркетолог","Дизайнер","HR-менеджер","Руководитель отдела","Директор",
             "Финансовый аналитик","Тестировщик ПО","DevOps-инженер","Продакт-менеджер",
             "Копирайтер","Логист","Экономист"]

UNIVERSITIES = ["МГУ им. М.В. Ломоносова","СПбГУ","МГТУ им. Н.Э. Баумана","НИУ ВШЭ",
                "МФТИ","РУДН","КФУ","НГУ","УрФУ","ИТМО","МИФИ","МГИМО","РАНХиГС",
                "Политех Петра Великого"]

SPECIALTIES = ["Прикладная математика и информатика","Программная инженерия",
               "Экономика","Юриспруденция","Менеджмент","Маркетинг","Дизайн",
               "Психология","Журналистика","Лингвистика","Биология","Химия",
               "Физика","История","Социология"]

MARITAL = ["Холост","Не замужем","Женат","Замужем","В разводе","В отношениях","Гражданский брак"]

HOBBIES = ["чтение","футбол","баскетбол","плавание","бег","велоспорт","шахматы",
           "рыбалка","охота","туризм","фотография","живопись","музыка","гитара",
           "пианино","танцы","йога","кулинария","садоводство","коллекционирование",
           "видеоигры","программирование","астрономия","история","кино","театр",
           "волонтёрство","скейтборд","сноуборд","скалолазание","пейнтбол","дартс"]

BLOOD = ["O(I) Rh+","O(I) Rh-","A(II) Rh+","A(II) Rh-","B(III) Rh+","B(III) Rh-",
         "AB(IV) Rh+","AB(IV) Rh-"]
ALLERGIES = ["нет","пенициллин","лактоза","глютен","орехи","пыльца","шерсть кошек",
             "шерсть собак","пыль","морепродукты","яйца"]

CARS = [("Lada",["Vesta","Granta","Niva","Largus"]),
        ("Toyota",["Camry","Corolla","RAV4","Land Cruiser"]),
        ("BMW",["3 Series","5 Series","X3","X5"]),
        ("Mercedes-Benz",["C-Class","E-Class","GLC","S-Class"]),
        ("Kia",["Rio","Sportage","K5","Sorento"]),
        ("Hyundai",["Solaris","Creta","Tucson","Santa Fe"]),
        ("Volkswagen",["Polo","Tiguan","Passat","Golf"]),
        ("Audi",["A4","A6","Q5","Q7"]),
        ("Nissan",["Qashqai","X-Trail","Almera","Murano"]),
        ("Skoda",["Octavia","Rapid","Kodiaq","Superb"])]

WIFI_SSIDS = ["TP-LINK_","MTS_Router_","Rostelecom_","Dom.ru_","Beeline_",
              "ASUS_","Keenetic_","Tenda_","Xiaomi_","Huawei_"]

EMAIL_DOMAINS = ["gmail.com","yandex.ru","mail.ru","outlook.com","bk.ru","inbox.ru"]


# ---------- алгоритмы ----------

def _luhn_check(number: str) -> str:
    digits = [int(d) for d in number]
    for i in range(len(digits) - 1, -1, -1):
        if (len(digits) - i) % 2 == 1:
            digits[i] *= 2
            if digits[i] > 9:
                digits[i] -= 9
    return str((10 - sum(digits) % 10) % 10)


def gen_card(prefix: str = "4276") -> str:
    body = prefix + "".join(random.choices(string.digits, k=15 - len(prefix)))
    return body + _luhn_check(body)


def validate_inn(inn: str) -> bool:
    if not inn.isdigit():
        return False
    if len(inn) == 10:
        coef = [2,4,10,3,5,9,4,6,8]
        s = sum(int(inn[i]) * coef[i] for i in range(9))
        return int(inn[9]) == (s % 11) % 10
    if len(inn) == 12:
        c11 = [7,2,4,10,3,5,9,4,6,8]
        c12 = [3,7,2,4,10,3,5,9,4,6,8]
        s11 = sum(int(inn[i]) * c11[i] for i in range(10)) % 11 % 10
        s12 = sum(int(inn[i]) * c12[i] for i in range(11)) % 11 % 10
        return int(inn[10]) == s11 and int(inn[11]) == s12
    return False


def gen_inn() -> str:
    while True:
        base = "".join(random.choices(string.digits, k=10))
        c11 = [7,2,4,10,3,5,9,4,6,8]
        c12 = [3,7,2,4,10,3,5,9,4,6,8]
        s11 = sum(int(base[i]) * c11[i] for i in range(10)) % 11 % 10
        s12 = sum(int(base[i]) * c12[i] for i in range(11)) % 11 % 10
        result = base + str(s11) + str(s12)
        if validate_inn(result):
            return result


def gen_snils() -> str:
    while True:
        digits = [random.randint(0, 9) for _ in range(9)]
        s = sum(d * (9 - i) for i, d in enumerate(digits))
        if s < 100:
            check = s
        elif s in (100, 101):
            check = 0
        else:
            check = s % 101
            if check == 100:
                check = 0
        if 0 <= check <= 99:
            return f"{''.join(map(str,digits))}{check:02d}"


def gen_passport() -> dict:
    return {
        "series": f"{random.randint(10,99):02d} {random.randint(10,99):02d}",
        "number": f"{random.randint(100000,999999)}",
        "issued_by": f"ОВД {random.choice(CITIES)[0]}",
        "issued_date": (date.today() - timedelta(days=random.randint(365, 5000))).isoformat(),
    }


def gen_phone(country: str = "RU") -> str:
    if country == "RU":
        return f"+79{random.randint(100000000, 999999999)}"
    if country == "US":
        return f"+1{random.randint(2000000000, 9999999999)}"
    return f"+49{random.randint(1500000000, 1799999999)}"


def gen_email(fio: str) -> str:
    translit = {"а":"a","б":"b","в":"v","г":"g","д":"d","е":"e","ё":"e","ж":"zh",
                "з":"z","и":"i","й":"y","к":"k","л":"l","м":"m","н":"n","о":"o",
                "п":"p","р":"r","с":"s","т":"t","у":"u","ф":"f","х":"h","ц":"c",
                "ч":"ch","ш":"sh","щ":"sch","ъ":"","ы":"y","ь":"","э":"e","ю":"yu","я":"ya"}
    clean = "".join(translit.get(c.lower(), c) for c in fio if c.isalpha() or c == " ")
    parts = clean.split()
    base = f"{parts[0]}.{parts[1]}" if len(parts) >= 2 else parts[0]
    suffix = "".join(random.choices(string.digits, k=random.randint(1, 4)))
    return f"{base.lower()}{suffix}@{random.choice(EMAIL_DOMAINS)}"


def gen_username(fio: str) -> str:
    translit = {"а":"a","б":"b","в":"v","г":"g","д":"d","е":"e","ё":"e","ж":"zh",
                "з":"z","и":"i","й":"y","к":"k","л":"l","м":"m","н":"n","о":"o",
                "п":"p","р":"r","с":"s","т":"t","у":"u","ф":"f","х":"h","ц":"c",
                "ч":"ch","ш":"sh","щ":"sch","ъ":"","ы":"y","ь":"","э":"e","ю":"yu","я":"ya"}
    parts = [p for p in fio.split() if p]
    name = "".join(translit.get(c.lower(), c) for c in parts[0]) if parts else "user"
    surname = "".join(translit.get(c.lower(), c) for c in parts[1]) if len(parts) > 1 else ""
    variants = [
        f"{name.lower()}_{surname.lower()}",
        f"{name.lower()}{random.randint(1,99)}",
        f"{surname.lower()}_{random.randint(1,99)}",
        f"{name.lower()}{surname.lower()}",
    ]
    return random.choice(variants)[:20]


def gen_password() -> str:
    words = ["Sun","Moon","Star","Fire","Ice","Wolf","Fox","Lion","Sky","Sea",
             "Rain","Snow","Wind","Tree","Rock","King","Queen","Dark","Light","Blue"]
    sep = random.choice("!@#$%._-")
    return f"{random.choice(words)}{sep}{random.choice(words)}{random.randint(10,999)}"


def gen_wifi() -> dict:
    return {
        "ssid": f"{random.choice(WIFI_SSIDS)}{random.randint(100,999)}",
        "password": "".join(random.choices(string.ascii_letters + string.digits, k=12)),
    }


def gen_car() -> dict:
    brand, models = random.choice(CARS)
    return {
        "brand": brand, "model": random.choice(models),
        "year": random.randint(2008, 2024),
        "plate": f"{random.choice('АВЕКМНОРСТУХ')}{random.randint(100,999)}"
                 f"{random.choice('АВЕКМНОРСТУХ')}{random.choice('АВЕКМНОРСТУХ')}"
                 f"{random.randint(10,199)}",
    }


def gen_credit_history() -> dict:
    return {
        "score": random.randint(300, 850),
        "active_loans": random.randint(0, 4),
        "overdue": random.choice(["нет", "1 платёж", "2 платежа"]),
        "total_debt": random.randint(0, 3_000_000),
    }


def gen_job() -> dict:
    return {
        "company": random.choice(COMPANIES),
        "position": random.choice(POSITIONS),
        "salary": random.randint(35_000, 400_000),
        "started": (date.today() - timedelta(days=random.randint(30, 3650))).isoformat(),
    }


def gen_education() -> dict:
    return {
        "university": random.choice(UNIVERSITIES),
        "specialty": random.choice(SPECIALTIES),
        "grad_year": random.randint(2000, 2024),
    }


# ---------- сама личность ----------

@dataclass
class Person:
    full_name: str
    birth_date: str
    age: int
    gender: str
    country: str
    phone: str
    email: str
    username: str
    password: str
    address: dict
    passport: dict
    inn: str
    snils: str
    card: str
    job: dict
    education: dict
    marital_status: str
    hobbies: list
    socials: dict
    bio: str
    avatar_url: str
    car: dict
    medical: dict
    credit: dict
    wifi: dict


def _fio(gender: str, country: str) -> str:
    if country == "RU":
        if gender == "M":
            return f"{random.choice(SUR_M)} {random.choice(MALE)} {random.choice(PAT_M)}"
        return f"{random.choice(SUR_F)} {random.choice(FEMALE)} {random.choice(PAT_F)}"
    fk = FAKERS.get(country, FAKERS["RU"])
    if gender == "M":
        return fk.name_male()
    return fk.name_female()


def _address(country: str) -> dict:
    if country == "RU":
        city, pmin, pmax = random.choice(CITIES)
        return {
            "country": "Россия", "city": city,
            "street": random.choice(STREETS),
            "house": random.randint(1, 200),
            "apartment": random.randint(1, 500),
            "index": random.randint(pmin, pmax),
        }
    fk = FAKERS.get(country, FAKERS["US"])
    return {
        "country": country, "city": fk.city(),
        "street": fk.street_name(), "house": fk.building_number(),
        "apartment": str(random.randint(1, 300)),
        "index": fk.postcode(),
    }


def generate_person(country: str = "RU", gender: Optional[str] = None,
                    age_min: int = 18, age_max: int = 60) -> Person:
    country = country.upper()
    if country not in FAKERS:
        country = "RU"
    if gender not in ("M", "F"):
        gender = random.choice(["M", "F"])

    age = random.randint(age_min, age_max)
    today = date.today()
    birth = today - timedelta(days=age * 365 + random.randint(0, 364))

    fio = _fio(gender, country)
    username = gen_username(fio)

    hobbies_n = random.randint(3, 5)
    hobbies = random.sample(HOBBIES, hobbies_n)

    bio_templates = [
        f"Люблю {hobbies[0]}, {hobbies[1]} и {hobbies[2]}.",
        f"{random.choice(POSITIONS)}. {hobbies[0].capitalize()} — моя страсть.",
        f"Живу в {_address(country)['city']}. Увлекаюсь {hobbies[0]}.",
        f"Просто хороший человек. {hobbies[0].capitalize()} и {hobbies[1]}.",
    ]

    phone = gen_phone(country)
    email = gen_email(fio)

    socials = {
        "vk": f"vk.com/{username}",
        "telegram": f"@{username}",
        "instagram": f"instagram.com/{username}",
        "github": f"github.com/{username}",
    }

    avatar = f"https://api.dicebear.com/7.x/avataaars/svg?seed={username}"

    return Person(
        full_name=fio,
        birth_date=birth.isoformat(),
        age=age,
        gender=gender,
        country=country,
        phone=phone,
        email=email,
        username=username,
        password=gen_password(),
        address=_address(country),
        passport=gen_passport(),
        inn=gen_inn(),
        snils=gen_snils(),
        card=gen_card(),
        job=gen_job(),
        education=gen_education(),
        marital_status=random.choice(MARITAL),
        hobbies=hobbies,
        socials=socials,
        bio=random.choice(bio_templates),
        avatar_url=avatar,
        car=gen_car(),
        medical={
            "blood_type": random.choice(BLOOD),
            "allergies": random.choice(ALLERGIES),
            "chronic": random.choice(["нет", "гипертония", "астма", "диабет 2 типа"]),
        },
        credit=gen_credit_history(),
        wifi=gen_wifi(),
    )


def person_to_dict(p: Person) -> dict:
    return asdict(p)


def person_to_html(p: Person) -> str:
    d = person_to_dict(p)
    hobbies = ", ".join(d["hobbies"])
    return f"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8">
<title>{d['full_name']}</title>
<style>
 body{{font-family:system-ui,Arial;background:#111;color:#eee;padding:24px}}
 .card{{max-width:720px;margin:auto;background:#1a1a1a;padding:24px;border-radius:12px}}
 h1{{margin:0 0 8px}} img{{width:96px;height:96px;border-radius:50%}}
 .row{{margin:6px 0}} .k{{color:#8ab4f8;display:inline-block;min-width:160px}}
 pre{{background:#000;padding:12px;border-radius:8px;overflow:auto}}
</style></head><body>
<div class="card">
 <img src="{d['avatar_url']}" alt="avatar">
 <h1>{d['full_name']}</h1>
 <div class="row"><span class="k">Возраст:</span> {d['age']} ({d['birth_date']})</div>
 <div class="row"><span class="k">Пол:</span> {d['gender']}</div>
 <div class="row"><span class="k">Страна:</span> {d['country']}</div>
 <div class="row"><span class="k">Телефон:</span> {d['phone']}</div>
 <div class="row"><span class="k">Email:</span> {d['email']}</div>
 <div class="row"><span class="k">Username:</span> {d['username']}</div>
 <div class="row"><span class="k">Пароль:</span> {d['password']}</div>
 <div class="row"><span class="k">Адрес:</span> {d['address']['city']}, {d['address']['street']} {d['address']['house']}-{d['address']['apartment']}, {d['address']['index']}</div>
 <div class="row"><span class="k">Паспорт:</span> {d['passport']['series']} {d['passport']['number']} ({d['passport']['issued_by']})</div>
 <div class="row"><span class="k">ИНН:</span> {d['inn']}</div>
 <div class="row"><span class="k">СНИЛС:</span> {d['snils']}</div>
 <div class="row"><span class="k">Карта:</span> {d['card']}</div>
 <div class="row"><span class="k">Работа:</span> {d['job']['position']}, {d['job']['company']} ({d['job']['salary']} ₽)</div>
 <div class="row"><span class="k">Образование:</span> {d['education']['university']}, {d['education']['specialty']} ({d['education']['grad_year']})</div>
 <div class="row"><span class="k">Семейное положение:</span> {d['marital_status']}</div>
 <div class="row"><span class="k">Хобби:</span> {hobbies}</div>
 <div class="row"><span class="k">Авто:</span> {d['car']['brand']} {d['car']['model']} {d['car']['year']} ({d['car']['plate']})</div>
 <div class="row"><span class="k">Медицина:</span> {d['medical']['blood_type']}, аллергии: {d['medical']['allergies']}</div>
 <div class="row"><span class="k">Кредитный рейтинг:</span> {d['credit']['score']}</div>
 <div class="row"><span class="k">Wi-Fi:</span> {d['wifi']['ssid']} / {d['wifi']['password']}</div>
 <h3>Соцсети</h3>
 <pre>{json.dumps(d['socials'], ensure_ascii=False, indent=2)}</pre>
 <h3>Био</h3>
 <p>{d['bio']}</p>
</div></body></html>"""


def generate_many(count: int, country: str = "RU",
                  gender: Optional[str] = None,
                  age_min: int = 18, age_max: int = 60) -> list[Person]:
    """Массовая генерация. count — 1..1500."""
    count = max(1, min(count, 1500))
    return [generate_person(country, gender, age_min, age_max) for _ in range(count)]
"""FUCKJESTER v2.0.0 — главный вход, баннер, меню, авторизация."""
from __future__ import annotations

import getpass
import hashlib
import json
import logging
import random
import shutil
import sys
import time
from pathlib import Path

from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# -------- проверка зависимостей --------
MISSING = []
for mod, pkg in [
    ("rich", "rich"),
    ("faker", "faker"),
    ("phonenumbers", "phonenumbers"),
    ("requests", "requests"),
    ("rarfile", "rarfile"),
    ("cryptography", "cryptography"),
    ("qrcode", "qrcode"),
]:
    try:
        __import__(mod)
    except ImportError:
        MISSING.append(pkg)

if MISSING:
    print("\n[!] Не хватает модулей: " + ", ".join(MISSING))
    print("[!] Установи командой:")
    print(f"    pip install {' '.join(MISSING)}\n")
    sys.exit(1)

from core import generator, storage, tools

# -------- пути и настройки --------
BASE = Path(__file__).resolve().parent
LOG_DIR = BASE / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR = BASE / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=str(LOG_DIR / "fuckjester.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
LOG = logging.getLogger("fuckjester")
console = Console()

AUTHOR = "jester"
VERSION = "2.0.0"

AUTH_FILE = DATA_DIR / "auth.json"
DEFAULT_PASSWORD = "jesterking"


# =========================================================
#  АВТОРИЗАЦИЯ
# =========================================================

def _hash(pwd: str) -> str:
    return hashlib.sha256(pwd.encode("utf-8")).hexdigest()


def _init_auth() -> None:
    if not AUTH_FILE.exists():
        AUTH_FILE.write_text(
            json.dumps({"password_hash": _hash(DEFAULT_PASSWORD)}),
            encoding="utf-8",
        )


def login() -> bool:
    _init_auth()
    expected = json.loads(AUTH_FILE.read_text("utf-8"))["password_hash"]
    tries = 3
    while tries > 0:
        try:
            pwd = getpass.getpass("  [!] Введите пароль: ")
        except Exception:
            pwd = input("  [!] Введите пароль: ")
        if _hash(pwd) == expected:
            console.print("[bold green]  [+] Доступ разрешён.[/bold green]\n")
            LOG.info("Успешный вход")
            return True
        tries -= 1
        console.print(f"[bold red]  [x] Неверный пароль. Осталось: {tries}[/bold red]")
    LOG.warning("Неудачный вход")
    console.print("[bold red]  [!] Доступ запрещён.[/bold red]")
    return False


# =========================================================
#  БАННЕР: слитный зелёно-красный арт
# =========================================================

# Компактный блок-шрифт "FUCKJESTER", буквы плотно друг к другу
_ART_LINES = [
    "███████╗██╗   ██╗ ██████╗██╗  ██╗     ██╗███████╗███████╗████████╗███████╗██████╗ ",
    "██╔════╝██║   ██║██╔════╝██║ ██╔╝     ██║██╔════╝██╔════╝╚══██╔══╝██╔════╝██╔══██╗",
    "█████╗  ██║   ██║██║     █████╔╝      ██║█████╗  ███████╗   ██║   █████╗  ██████╔╝",
    "██╔══╝  ██║   ██║██║     ██╔═██╗ ██   ██║██╔══╝  ╚════██║   ██║   ██╔══╝  ██╔══██╗",
    "██║     ╚██████╔╝╚██████╗██║  ██╗╚█████╔╝███████╗███████║   ██║   ███████╗██║  ██║",
    "╚═╝      ╚═════╝  ╚═════╝╚═╝  ╚═╝ ╚════╝ ╚══════╝╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝",
]


def _render_art() -> Text:
    """Возвращает текст арта, где символы чередуются зелёным и красным."""
    out = Text()
    palette = ["green", "red"]
    for line in _ART_LINES:
        for i, ch in enumerate(line):
            if ch == " ":
                out.append(ch)
            else:
                # чередуем цвет по позиции + немного случайности
                color = palette[(i + random.randint(0, 1)) % 2]
                out.append(ch, style=f"bold {color}")
        out.append("\n")
    return out


def show_banner() -> None:
    console.print(_render_art())
    line = Text()
    line.append(f"  fuckjester v{VERSION} ", style="bold white on green")
    line.append(" author: ", style="green")
    line.append(AUTHOR, style="bold red")
    console.print(Align.center(line))
    console.print()


# =========================================================
#  МЕНЮ (компактное, под Termux)
# =========================================================

# Пункты: (номер, короткое имя, функция)
MENU: list[tuple[str, str, callable | None]] = [
    ("1",  "Загрузка баз",       None),
    ("2",  "Поиск (текст)",      None),
    ("3",  "Поиск (телефон)",    None),
    ("4",  "Поиск (email)",      None),
    ("5",  "Поиск (ФИО)",        None),
    ("6",  "Личность",           None),
    ("7",  "Массово 10-1500",    None),
    ("8",  "Пароли",             None),
    ("9",  "Ники",               None),
    ("10", "Телефон: проверка",  None),
    ("11", "Email: проверка",    None),
    ("12", "Карта: проверка",    None),
    ("13", "ИНН: проверка",      None),
    ("14", "Список баз",         None),
    ("15", "Удалить базу",       None),
    ("16", "Объединить базы",    None),
    ("17", "Дедупликация",       None),
    ("18", "Экспорт в CSV",      None),
    ("19", "QR-код",             None),
    ("20", "vCard",              None),
    ("21", "AES шифрование",     None),
    ("22", "AES расшифровка",    None),
    ("23", "Сохранённые люди",   None),
    ("24", "HTML-карточка",      None),
    ("25", "Настройки",          None),
    ("26", "Экспорт настроек",   None),
    ("27", "Очистить логи",      None),
    ("28", "Статистика",         None),
    ("29", "О программе",        None),
    ("0",  "ВЫХОД",              None),
]


def _bind_menu() -> dict[str, callable]:
    """Связывает номера с функциями (объявлены ниже)."""
    return {
        "1":  menu_upload,
        "2":  lambda: _do_search("text"),
        "3":  lambda: _do_search("phone"),
        "4":  lambda: _do_search("email"),
        "5":  lambda: _do_search("fio"),
        "6":  menu_generator,
        "7":  menu_generator_many,
        "8":  menu_passwords,
        "9":  menu_nicks,
        "10": menu_check_phone,
        "11": menu_check_email,
        "12": menu_check_card,
        "13": menu_check_inn,
        "14": menu_list_dbs,
        "15": menu_delete_db,
        "16": menu_merge_dbs,
        "17": menu_dedup,
        "18": menu_export_db,
        "19": menu_qr,
        "20": menu_vcard,
        "21": menu_encrypt,
        "22": menu_decrypt,
        "23": menu_saved_persons,
        "24": menu_html_card,
        "25": menu_settings,
        "26": menu_export_settings,
        "27": menu_clear_logs,
        "28": menu_stats,
        "29": menu_about,
        "0":  None,
    }


def render_menu() -> None:
    """Рисует меню в две колонки — компактно, без переносов."""
    width = shutil.get_terminal_size((40, 24)).columns
    # две колонки, если хватает места, иначе одна
    two_cols = width >= 60

    t = Table.grid(padding=(0, 2))
    if two_cols:
        t.add_column(justify="left", no_wrap=True)
        t.add_column(justify="left", no_wrap=True)

    half = (len(MENU) + 1) // 2
    left = MENU[:half]
    right = MENU[half:]

    def fmt(num: str, name: str) -> Text:
        txt = Text()
        txt.append(f"[{num:>2}] ", style="bold green")
        txt.append(name, style="white")
        return txt

    if two_cols:
        for i in range(half):
            l_num, l_name, _ = left[i]
            if i < len(right):
                r_num, r_name, _ = right[i]
                t.add_row(fmt(l_num, l_name), fmt(r_num, r_name))
            else:
                t.add_row(fmt(l_num, l_name), "")
    else:
        for num, name, _ in MENU:
            t.add_row(fmt(num, name))

    console.print(Panel(
        t,
        title="[bold green]ГЛАВНОЕ МЕНЮ[/bold green]",
        subtitle="[dim]введи номер + Enter[/dim]",
        border_style="green",
        padding=(1, 2),
    ))


def handle_choice(choice: str) -> bool:
    if choice == "0":
        return False
    binds = _bind_menu()
    if choice not in binds:
        console.print("[bold red]  [!] Неверный пункт.[/bold red]")
        return True
    fn = binds[choice]
    if fn is None:
        return False
    try:
        fn()
    except KeyboardInterrupt:
        console.print("\n[yellow]  Отменено. Возврат в меню.[/yellow]")
    except Exception as e:
        LOG.exception("Ошибка в пункте %s", choice)
        console.print(f"[bold red]  [!] Ошибка: {e}[/bold red]")
    return True


# =========================================================
#  ОБРАБОТЧИКИ ПУНКТОВ
# =========================================================

def _ask(prompt: str, default: str = "") -> str:
    try:
        v = input(f"  {prompt}: ").strip()
    except KeyboardInterrupt:
        raise
    return v or default


def _ask_int(prompt: str, default: int) -> int:
    try:
        return int(_ask(prompt, str(default)))
    except ValueError:
        return default


# --- 1. Загрузка ---

def menu_upload() -> None:
    path_str = _ask("Путь к файлу/папке (.txt/.csv/.json/.rar)")
    if not path_str:
        return
    path = Path(path_str).expanduser().resolve()
    if not path.exists():
        console.print("[red]  Путь не существует.[/red]")
        return
    files = storage.collect_files(path)
    if not files:
        console.print("[yellow]  Файлов не найдено.[/yellow]")
        return
    total = 0
    for f in files:
        try:
            c = storage.add_records(f.stem, storage.iter_file(f))
            total += c
            console.print(f"[cyan]  {f.name}[/cyan] → {c}")
        except Exception as e:
            console.print(f"[red]  Ошибка {f.name}: {e}[/red]")
    console.print(f"[bold green]  Всего загружено: {total}[/bold green]")


# --- 2-5. Поиск ---

def _do_search(kind: str) -> None:
    q = _ask("Запрос")
    if not q:
        return
    if kind == "phone":
        rows = storage.search_phone(q)
    else:
        rows = storage.search(q)
    tools.render_results(rows, title=f"Поиск: {q}")
    if rows and _ask("Экспорт? (y/n)", "n").lower() == "y":
        fmt = _ask("Формат (csv/json)", "csv")
        out = BASE / "data" / "generated" / f"search_{int(time.time())}.{fmt}"
        tools.export_results(rows, out, fmt)
        console.print(f"[green]  Сохранено: {out}[/green]")


# --- 6. Одна личность ---

def menu_generator() -> None:
    country = _ask("Страна (RU/US/DE/FR/GB)", "RU").upper()
    gender = _ask("Пол (M/F/пусто)", "").upper()
    if gender not in ("M", "F"):
        gender = None
    p = generator.generate_person(country=country, gender=gender)
    d = generator.person_to_dict(p)
    t = Table(title=f"Личность: {d['full_name']}", show_lines=True)
    t.add_column("Поле", style="cyan", no_wrap=True)
    t.add_column("Значение", style="white", overflow="fold")
    for k, v in d.items():
        if isinstance(v, (dict, list)):
            v = json.dumps(v, ensure_ascii=False)
        t.add_row(k, str(v))
    console.print(t)
    if _ask("Сохранить в БД? (y/n)", "n").lower() == "y":
        storage.save_person(json.dumps(d, ensure_ascii=False))
        console.print("[green]  Сохранено.[/green]")


# --- 7. Массовая генерация ---

def menu_generator_many() -> None:
    count = _ask_int("Сколько (1-1500)", 10)
    country = _ask("Страна (RU/US/DE/FR/GB)", "RU").upper()
    gender = _ask("Пол (M/F/пусто)", "").upper()
    if gender not in ("M", "F"):
        gender = None
    age_min = _ask_int("Мин. возраст", 18)
    age_max = _ask_int("Макс. возраст", 60)
    people = generator.generate_many(count, country, gender, age_min, age_max)
    fmt = _ask("Формат (json/csv/txt)", "json")
    out = BASE / "data" / "generated" / f"batch_{count}_{int(time.time())}.{fmt}"
    _save_many(people, out, fmt)
    console.print(f"[green]  Сохранено: {out}[/green]")
    if _ask("Сохранить в БД? (y/n)", "n").lower() == "y":
        for p in people:
            storage.save_person(json.dumps(generator.person_to_dict(p), ensure_ascii=False))
        console.print("[green]  Сохранено в БД.[/green]")


def _save_many(people, path: Path, fmt: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    dicts = [generator.person_to_dict(p) for p in people]
    if fmt == "json":
        path.write_text(json.dumps(dicts, ensure_ascii=False, indent=2), encoding="utf-8")
    elif fmt == "csv":
        import csv
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if dicts:
                w.writerow(list(dicts[0].keys()))
                for d in dicts:
                    w.writerow([json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
                                for v in d.values()])
    else:
        with path.open("w", encoding="utf-8") as f:
            for i, d in enumerate(dicts, 1):
                f.write(f"=== #{i} ===\n")
                for k, v in d.items():
                    f.write(f"{k}: {v}\n")
                f.write("\n")


# --- 8. Пароли ---

def menu_passwords() -> None:
    a = _ask("(1) обычный (2) запоминающийся (3) проверить", "1")
    if a == "2":
        console.print(f"[bold green]  {tools.gen_memorable(3)}[/bold green]")
    elif a == "3":
        pwd = _ask("Пароль")
        score, label = tools.password_strength(pwd)
        console.print(f"  Оценка: {score}/100 — {label}")
    else:
        length = _ask_int("Длина (12-32)", 16)
        mode = _ask("Набор (letters/alnum/all)", "all")
        console.print(f"[bold green]  {tools.gen_password(length, mode)}[/bold green]")


# --- 9. Ники ---

def menu_nicks() -> None:
    style = _ask("Стиль (gamer/pro/creative/anon)", "pro")
    fio = _ask("ФИО (опционально)") or None
    for _ in range(10):
        console.print(f"[cyan]  {tools.gen_nick(style, fio)}[/cyan]")


# --- 10-13. Проверки ---

def menu_check_phone() -> None:
    n = _ask("Номер")
    for k, v in tools.validate_phone(n).items():
        console.print(f"  [cyan]{k}[/cyan]: {v}")


def menu_check_email() -> None:
    e = _ask("Email")
    console.print("[green]  OK[/green]" if tools.validate_email(e) else "[red]  Неверно[/red]")


def menu_check_card() -> None:
    c = _ask("Номер карты")
    console.print("[green]  OK[/green]" if tools.validate_card(c) else "[red]  Неверно[/red]")


def menu_check_inn() -> None:
    i = _ask("ИНН")
    console.print("[green]  OK[/green]" if generator.validate_inn(i) else "[red]  Неверно[/red]")


# --- 14-18. Базы ---

def menu_list_dbs() -> None:
    rows = storage.list_sources()
    if not rows:
        console.print("[yellow]  Нет баз.[/yellow]")
        return
    t = Table(title="Загруженные базы")
    t.add_column("ID", style="cyan"); t.add_column("Имя", style="magenta")
    t.add_column("Записей", style="green"); t.add_column("Дата", style="dim")
    for r in rows:
        t.add_row(str(r[0]), r[1], str(r[2]), r[3])
    console.print(t)
    console.print(f"[bold]  Всего записей: {storage.total_records()}[/bold]")


def menu_delete_db() -> None:
    sid = _ask_int("ID базы", -1)
    if sid < 0:
        return
    console.print(f"[green]  Удалено: {storage.delete_source(sid)}[/green]")


def menu_merge_dbs() -> None:
    ids = _ask("ID через запятую")
    lst = [int(x) for x in ids.split(",") if x.strip().isdigit()]
    if not lst:
        return
    name = _ask("Новое имя")
    if not name:
        return
    console.print(f"[green]  Объединено: {storage.merge_sources(name, lst)}[/green]")


def menu_dedup() -> None:
    src = _ask("Имя базы (пусто=все)") or None
    console.print(f"[green]  Удалено дубликатов: {storage.deduplicate(src)}[/green]")


def menu_export_db() -> None:
    src = _ask("Имя базы (пусто=все)") or None
    out = BASE / "data" / "generated" / f"export_{int(time.time())}.csv"
    n = storage.export_records(out, src)
    console.print(f"[green]  {n} → {out}[/green]")


# --- 19-24. Утилиты ---

def menu_qr() -> None:
    t = _ask("Текст")
    p = tools.gen_qr(t)
    console.print(f"[green]  {p}[/green]")


def menu_vcard() -> None:
    p = generator.generate_person()
    path = tools.gen_vcard(generator.person_to_dict(p))
    console.print(f"[green]  {path}[/green]")


def menu_encrypt() -> None:
    t = _ask("Текст")
    p = _ask("Пароль")
    console.print(f"[green]  {tools.encrypt_text(t, p)}[/green]")


def menu_decrypt() -> None:
    t = _ask("Шифротекст")
    p = _ask("Пароль")
    try:
        console.print(f"[green]  {tools.decrypt_text(t, p)}[/green]")
    except Exception as e:
        console.print(f"[red]  Ошибка: {e}[/red]")


def menu_saved_persons() -> None:
    rows = storage.fetch_persons(50)
    if not rows:
        console.print("[yellow]  Нет сохранённых.[/yellow]")
        return
    t = Table(title="Сохранённые личности")
    t.add_column("ID", style="cyan"); t.add_column("ФИО", style="white")
    t.add_column("Дата", style="dim")
    for r in rows:
        try:
            d = json.loads(r[1])
            t.add_row(str(r[0]), d.get("full_name", "—"), r[2])
        except Exception:
            t.add_row(str(r[0]), "—", r[2])
    console.print(t)


def menu_html_card() -> None:
    p = generator.generate_person()
    out = BASE / "data" / "generated" / f"person_{p.username}.html"
    out.write_text(generator.person_to_html(p), encoding="utf-8")
    console.print(f"[green]  {out}[/green]")


# --- 25-28. Настройки и сервис ---

SETTINGS_PATH = DATA_DIR / "settings.json"


def _load_settings() -> dict:
    if SETTINGS_PATH.exists():
        try:
            return json.loads(SETTINGS_PATH.read_text("utf-8"))
        except Exception:
            pass
    return {"theme": "dark", "language": "ru", "autoclean": True}


def menu_settings() -> None:
    s = _load_settings()
    console.print(f"  Текущие: {json.dumps(s, ensure_ascii=False)}")
    k = _ask("Изменить (theme/language/autoclean/ничего)")
    if k == "theme":
        s["theme"] = _ask("dark/light", s["theme"])
    elif k == "language":
        s["language"] = _ask("ru/en", s["language"])
    elif k == "autoclean":
        s["autoclean"] = _ask("y/n", "y" if s["autoclean"] else "n").lower() == "y"
    SETTINGS_PATH.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
    console.print("[green]  Сохранено.[/green]")


def menu_export_settings() -> None:
    out = BASE / "data" / "generated" / "settings_export.json"
    out.write_text(json.dumps(_load_settings(), ensure_ascii=False, indent=2), encoding="utf-8")
    console.print(f"[green]  {out}[/green]")


def menu_clear_logs() -> None:
    for f in LOG_DIR.glob("*.log"):
        try:
            f.write_text("", encoding="utf-8")
        except Exception:
            pass
    console.print("[green]  Логи очищены.[/green]")


def menu_stats() -> None:
    console.print(f"  [cyan]Записей в БД:[/cyan] {storage.total_records()}")
    console.print(f"  [cyan]Источников:[/cyan] {len(storage.list_sources())}")
    console.print(f"  [cyan]Сохранённых людей:[/cyan] {len(storage.fetch_persons(99999))}")


def menu_about() -> None:
    console.print(Panel.fit(
        f"[bold red]FUCKJESTER[/bold red] v{VERSION}\n"
        f"Автор: [cyan]{AUTHOR}[/cyan]\n"
        "Лицензия: MIT\n\n"
        "[yellow]Софт работает только с базами, которые загрузил сам пользователь.\n"
        "Незаконный сбор данных запрещён (ст. 137, 272 УК РФ).[/yellow]",
        border_style="red",
        title="О программе",
    ))


# =========================================================
#  MAIN
# =========================================================

def main() -> None:
    try:
        storage.init()
        show_banner()

        if not login():
            sys.exit(1)

        while True:
            render_menu()
            try:
                choice = console.input("[bold green]  fuckjester > [/bold green]").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not handle_choice(choice):
                console.pr
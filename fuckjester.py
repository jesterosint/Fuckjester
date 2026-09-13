"""FUCKJESTER — главный вход, пароль, меню в стиле SCIENCE."""
from __future__ import annotations

import getpass
import hashlib
import json
import logging
import sys
import time
from pathlib import Path

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from core import generator, storage, tools

BASE = Path(__file__).resolve().parent
LOG_DIR = BASE / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
SETTINGS_DIR = BASE / "data"
SETTINGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=str(LOG_DIR / "fuckjester.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
LOG = logging.getLogger("fuckjester")
console = Console()

AUTHOR = "jester"
VERSION = "1.0.0"
GITHUB = "https://github.com/jesterosint/fuckjester"

# -------- авторизация --------

AUTH_FILE = SETTINGS_DIR / "auth.json"
DEFAULT_PASSWORD = "jesterking"


def _hash(pwd: str) -> str:
    return hashlib.sha256(pwd.encode("utf-8")).hexdigest()


def _init_auth() -> None:
    """Создаёт файл с хешем пароля, если его нет."""
    if not AUTH_FILE.exists():
        AUTH_FILE.write_text(
            json.dumps({"password_hash": _hash(DEFAULT_PASSWORD)}),
            encoding="utf-8",
        )


def login() -> bool:
    """Запрашивает пароль. Даёт 3 попытки."""
    _init_auth()
    expected = json.loads(AUTH_FILE.read_text("utf-8"))["password_hash"]
    attempts = 3
    while attempts > 0:
        try:
            pwd = getpass.getpass("  [!] Введите пароль: ")
        except Exception:
            pwd = input("  [!] Введите пароль: ")
        if _hash(pwd) == expected:
            console.print("[bold green]  [+] Доступ разрешён.[/bold green]\n")
            return True
        attempts -= 1
        console.print(f"[bold red]  [x] Неверный пароль. Осталось попыток: {attempts}[/bold red]")
    console.print("[bold red]  [!] Доступ запрещён. Выход.[/bold red]")
    LOG.warning("Неудачная попытка входа")
    return False


# -------- баннер --------

BANNER = r"""
   ███████╗██╗   ██╗ ██████╗██╗  ██╗     ██╗███████╗███████╗████████╗███████╗██████╗ 
   ██╔════╝██║   ██║██╔════╝██║ ██╔╝     ██║██╔════╝██╔════╝╚══██╔══╝██╔════╝██╔══██╗
   █████╗  ██║   ██║██║     █████╔╝      ██║█████╗  ███████╗   ██║   █████╗  ██████╔╝
   ██╔══╝  ██║   ██║██║     ██╔═██╗ ██   ██║██╔══╝  ╚════██║   ██║   ██╔══╝  ██╔══██╗
   ██║     ╚██████╔╝╚██████╗██║  ██╗╚█████╔╝███████╗███████║   ██║   ███████╗██║  ██║
   ╚═╝      ╚═════╝  ╚═════╝╚═╝  ╚═╝ ╚════╝ ╚══════╝╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
"""


def show_banner() -> None:
    console.print(f"[bold green]{BANNER}[/bold green]")
    console.print(
        Align.center(
            f"[bold white on green] fuckjester v{VERSION} [/bold white on green] "
            f"[green]author: {AUTHOR}[/green] "
            f"[green]github: {GITHUB}[/green]"
        )
    )
    console.print()


# -------- меню --------

# Каждая строка — список пунктов. Пункт: (номер, подпись, callback)
# Подпись короткая, как на картинке.
def build_menu() -> dict[str, tuple[str, callable]]:
    """Возвращает словарь: '1' -> ('подпись', функция)."""
    return {
        # строка 1
        "1":  ("ЗАГРУЗКА БАЗ",         menu_upload),
        "2":  ("ПОИСК ПО ТЕКСТУ",      menu_search),
        "3":  ("ПОИСК ПО ТЕЛЕФОНУ",    menu_search_phone),
        "4":  ("ПОИСК ПО EMAIL",       menu_search_email),
        "5":  ("ПОИСК ПО ФИО",         menu_search_fio),
        "6":  ("ГЕНЕРАТОР ЛИЧНОСТИ",   menu_generator),
        # строка 2
        "7":  ("МАССОВАЯ ГЕНЕРАЦИЯ",   menu_generator_many),
        "8":  ("ГЕНЕРАТОР ПАРОЛЕЙ",    menu_passwords),
        "9":  ("ГЕНЕРАТОР НИКОВ",      menu_nicks),
        "10": ("ПРОВЕРКА ТЕЛЕФОНА",    menu_check_phone),
        "11": ("ПРОВЕРКА EMAIL",       menu_check_email),
        "12": ("ПРОВЕРКА КАРТЫ",       menu_check_card),
        # строка 3
        "13": ("ПРОВЕРКА ИНН",         menu_check_inn),
        "14": ("СПИСОК БАЗ",           menu_list_dbs),
        "15": ("УДАЛИТЬ БАЗУ",         menu_delete_db),
        "16": ("ОБЪЕДИНИТЬ БАЗЫ",      menu_merge_dbs),
        "17": ("ДЕДУПЛИКАЦИЯ",         menu_dedup),
        "18": ("ЭКСПОРТ БАЗЫ CSV",     menu_export_db),
        # строка 4
        "19": ("QR-КОД",               menu_qr),
        "20": ("VCARD",                menu_vcard),
        "21": ("AES ШИФРОВАНИЕ",       menu_encrypt),
        "22": ("AES РАСШИФРОВКА",      menu_decrypt),
        "23": ("СОХРАНЁННЫЕ ЛЮДИ",     menu_saved_persons),
        "24": ("HTML-КАРТОЧКА",        menu_html_card),
        # строка 5
        "25": ("НАСТРОЙКИ",            menu_settings),
        "26": ("ЭКСПОРТ НАСТРОЕК",     menu_export_settings),
        "27": ("ОЧИСТИТЬ ЛОГИ",        menu_clear_logs),
        "28": ("СТАТИСТИКА",           menu_stats),
        "29": ("О ПРОГРАММЕ",          menu_about),
        "0":  ("ВЫХОД",                None),
    }


def render_menu() -> None:
    """Рисует сетку меню как на картинке."""
    menu = build_menu()
    rows = [
        ["1", "2", "3", "4", "5", "6"],
        ["7", "8", "9", "10", "11", "12"],
        ["13", "14", "15", "16", "17", "18"],
        ["19", "20", "21", "22", "23", "24"],
        ["25", "26", "27", "28", "29", "0"],
    ]

    console.print()
    console.print("[bold green]┌" + "─" * 84 + "┐[/bold green]")
    console.print("[bold green]│[/bold green] "
                  "[bold white]ГЛАВНОЕ МЕНЮ[/bold white] "
                  "[dim]— введите номер пункта и нажмите Enter[/dim] "
                  "[bold green]│[/bold green]")
    console.print("[bold green]└" + "─" * 84 + "┘[/bold green]")
    console.print()

    for row in rows:
        cols = []
        for num in row:
            label = menu[num][0]
            cols.append(f"[bold green][{num:>2}][/bold green] [white]{label:<22}[/white]")
        console.print("  " + "  ".join(cols))
    console.print()


def handle_choice(choice: str) -> bool:
    """Возвращает False, если нужно выйти."""
    menu = build_menu()
    if choice == "0":
        return False
    if choice not in menu:
        console.print("[bold red]  [!] Неверный пункт.[/bold red]")
        return True
    _, fn = menu[choice]
    if fn is None:
        return False
    try:
        fn()
    except KeyboardInterrupt:
        console.print("\n[yellow]  Отменено.[/yellow]")
    except Exception as e:
        LOG.exception("Ошибка в пункте %s", choice)
        console.print(f"[bold red]  [!] Ошибка: {e}[/bold red]")
    return True


# -------- обработчики пунктов --------

def menu_upload() -> None:
    path_str = input("  Путь к файлу/папке: ").strip()
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


def _do_search(kind: str) -> None:
    q = input("  Запрос: ").strip()
    if not q:
        return
    if kind == "phone":
        rows = storage.search_phone(q)
    else:
        rows = storage.search(q)
    tools.render_results(rows, title=f"Поиск: {q}")
    if rows and input("  Экспорт? (y/n): ").strip().lower() == "y":
        fmt = input("  Формат (csv/json): ").strip() or "csv"
        out = BASE / "data" / "generated" / f"search_{int(time.time())}.{fmt}"
        tools.export_results(rows, out, fmt)
        console.print(f"[green]  Сохранено: {out}[/green]")


def menu_search() -> None:        _do_search("text")
def menu_search_phone() -> None:  _do_search("phone")
def menu_search_email() -> None:  _do_search("email")
def menu_search_fio() -> None:    _do_search("fio")


def menu_generator() -> None:
    country = input("  Страна (RU/US/DE/FR/GB) [RU]: ").strip().upper() or "RU"
    gender = input("  Пол (M/F/пусто): ").strip().upper() or None
    if gender not in ("M", "F"):
        gender = None
    p = generator.generate_person(country=country, gender=gender)
    d = generator.person_to_dict(p)
    t = Table(title=f"Личность: {d['full_name']}", show_lines=True)
    t.add_column("Поле", style="cyan")
    t.add_column("Значение", style="white", overflow="fold")
    for k, v in d.items():
        if isinstance(v, (dict, list)):
            v = json.dumps(v, ensure_ascii=False)
        t.add_row(k, str(v))
    console.print(t)
    if input("  Сохранить в БД? (y/n): ").strip().lower() == "y":
        storage.save_person(json.dumps(d, ensure_ascii=False))
        console.print("[green]  Сохранено.[/green]")


def menu_generator_many() -> None:
    try:
        count = int(input("  Сколько (1-1500) [10]: ").strip() or "10")
    except ValueError:
        count = 10
    country = input("  Страна (RU/US/DE/FR/GB) [RU]: ").strip().upper() or "RU"
    gender = input("  Пол (M/F/пусто): ").strip().upper() or None
    if gender not in ("M", "F"):
        gender = None
    people = generator.generate_many(count, country, gender)
    fmt = input("  Формат (json/csv/txt) [json]: ").strip() or "json"
    out = BASE / "data" / "generated" / f"batch_{count}_{int(time.time())}.{fmt}"
    _save_many(people, out, fmt)
    console.print(f"[green]  Сохранено: {out}[/green]")


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


def menu_passwords() -> None:
    action = input("  (1) обычный (2) запоминающийся (3) проверить: ").strip()
    if action == "2":
        console.print(f"[bold green]  {tools.gen_memorable(3)}[/bold green]")
    elif action == "3":
        pwd = input("  Пароль: ")
        score, label = tools.password_strength(pwd)
        console.print(f"  Оценка: {score}/100 — {label}")
    else:
        try:
            length = int(input("  Длина (12-32) [16]: ").strip() or "16")
        except ValueError:
            length = 16
        mode = input("  Набор (letters/alnum/all) [all]: ").strip() or "all"
        pwd = tools.gen_password(length, mode)
        console.print(f"[bold green]  {pwd}[/bold green]")


def menu_nicks() -> None:
    style = input("  Стиль (gamer/pro/creative/anon) [pro]: ").strip() or "pro"
    fio = input("  ФИО (опционально): ").strip() or None
    for _ in range(10):
        console.print(f"[cyan]  {tools.gen_nick(style, fio)}[/cyan]")


def menu_check_phone() -> None:
    n = input("  Номер: ").strip()
    for k, v in tools.validate_phone(n).items():
        console.print(f"  [cyan]{k}[/cyan]: {v}")


def menu_check_email() -> None:
    e = input("  Email: ").strip()
    console.print("[green]  OK[/green]" if tools.validate_email(e) else "[red]  Неверно[/red]")


def menu_check_card() -> None:
    c = input("  Номер карты: ").strip()
    console.print("[green]  OK[/green]" if tools.validate_card(c) else "[red]  Неверно[/red]")


def menu_check_inn() -> None:
    i = input("  ИНН: ").strip()
    console.print("[green]  OK[/green]" if generator.validate_inn(i) else "[red]  Неверно[/red]")


def menu_list_dbs() -> None:
    rows = storage.list_sources()
    if not rows:
        console.print("[yellow]  Нет баз.[/yellow]")
        return
    t = Table(title="Базы")
    t.add_column("ID"); t.add_column("Имя"); t.add_column("Записей"); t.add_column("Дата")
    for r in rows:
        t.add_row(str(r[0]), r[1], str(r[2]), r[3])
    console.print(t)


def menu_delete_db() -> None:
    try:
        sid = int(input("  ID базы: ").strip())
    except ValueError:
        return
    console.print(f"[green]  Удалено: {storage.delete_source(sid)}[/green]")


def menu_merge_dbs() -> None:
    ids = input("  ID через запятую: ").strip()
    lst = [int(x) for x in ids.split(",") if x.strip().isdigit()]
    if not lst:
        return
    name = input("  Новое имя: ").strip()
    console.print(f"[green]  Объединено: {storage.merge_sources(name, lst)}[/green]")


def menu_dedup() -> None:
    src = input("  Имя базы (пусто=все): ").strip() or None
    console.print(f"[green]  Удалено дубликатов: {storage.deduplicate(src)}[/green]")


def menu_export_db() -> None:
    src = input("  Имя базы (пусто=все): ").strip() or None
    out = BASE / "data" / "generated" / f"export_{int(time.time())}.csv"
    n = storage.export_records(out, src)
    console.print(f"[green]  {n} → {out}[/green]")


def menu_qr() -> None:
    text = input("  Текст: ").strip()
    p = tools.gen_qr(text)
    console.print(f"[green]  {p}[/green]")


def menu_vcard() -> None:
    p = generator.generate_person()
    path = tools.gen_vcard(generator.person_to_dict(p))
    console.print(f"[green]  {path}[/green]")


def menu_encrypt() -> None:
    t = input("  Текст: ")
    p = input("  Пароль: ")
    console.print(f"[green]  {tools.encrypt_text(t, p)}[/green]")


def menu_decrypt() -> None:
    t = input("  Шифротекст: ")
    p = input("  Пароль: ")
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
    t.add_column("ID"); t.add_column("ФИО"); t.add_column("Дата")
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


SETTINGS_PATH = SETTINGS_DIR / "settings.json"


def _load_settings() -> dict:
    if SETTINGS_PATH.exists():
        try:
            return json.loads(SETTINGS_PATH.read_text("utf-8"))
        except Exception:
            pass
    return {"theme": "dark", "language": "ru", "autoclean": True}


def menu_settings() -> None:
    s = _load_settings()
    console.print(f"  Текущие: {s}")
    k = input("  Изменить (theme/language/autoclean/ничего): ").strip()
    if k == "theme":
        s["theme"] = input("  dark/light: ").strip() or s["theme"]
    elif k == "language":
        s["language"] = input("  ru/en: ").strip() or s["language"]
    elif k == "autoclean":
        s["autoclean"] = input("  y/n: ").strip().lower() == "y"
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
    console.print(f"  [cyan]Сохранённых людей:[/cyan] {len(storage.fetch_persons(9999))}")


def menu_about() -> None:
    console.print(Panel.fit(
        f"[bold red]FUCKJESTER[/bold red] v{VERSION}\n"
        f"Автор: [cyan]{AUTHOR}[/cyan]\n"
        f"GitHub: [blue]{GITHUB}[/blue]\n"
        "Лицензия: MIT\n\n"
        "[yellow]Софт работает только с базами, которые загрузил сам пользователь.\n"
        "Незаконный сбор данных запрещён (ст. 137, 272 УК РФ).[/yellow]",
        border_style="red",
        title="О программе",
    ))


# -------- main --------

def main() -> None:
    try:
        storage.init()
        show_banner()

        if not login():
            sys.exit(1)

        while True:
            render_menu()
            try:
                choice = input("[bold green]  fuckjester >> [/bold green]").strip()
            except EOFError:
                break
            if not handle_choice(choice):
                console.print("[bold red]  Выход. Будь осторожен, jester.[/bold red]")
                break
            console.print()
    except KeyboardInterrupt:
        console.print("\n[red]  Прервано.[/red]")


if __name__ == "__main__":
    main()
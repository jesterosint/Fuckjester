"""FUCKJESTER — главный вход и меню."""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import pyfiglet
from InquirerPy import inquirer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from core import generator, storage, tools

BASE = Path(__file__).resolve().parent
LOG_DIR = BASE / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=str(LOG_DIR / "fuckjester.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
LOG = logging.getLogger("fuckjester")
console = Console()

AUTHOR = "jester"
VERSION = "1.0.0"


def banner() -> None:
    art = pyfiglet.figlet_format("FUCKJESTER", font="standard")
    console.print(f"[red]{art}[/red]")
    console.print(
        Panel.fit(
            f"[bold yellow]FUCKJESTER[/bold yellow] v{VERSION} — by [bold cyan]{AUTHOR}[/bold cyan]\n"
            "[dim]OSINT-инструмент для локальных баз. Только легальное использование.[/dim]",
            border_style="red",
        )
    )


# ---------- 1. ЗАГРУЗКА ----------

def menu_upload() -> None:
    path_str = inquirer.text(message="Путь к файлу или папке (.txt/.csv/.json/.rar):").execute()
    if not path_str:
        return
    path = Path(path_str).expanduser().resolve()
    if not path.exists():
        console.print("[red]Путь не существует.[/red]")
        return

    files = storage.collect_files(path)
    if not files:
        console.print("[yellow]Не найдено подходящих файлов.[/yellow]")
        return

    console.print(f"[green]Найдено файлов: {len(files)}[/green]")
    total = 0
    for f in files:
        try:
            source = f.stem
            count = storage.add_records(source, storage.iter_file(f))
            total += count
            console.print(f"[cyan]{f.name}[/cyan] → {count} записей (source={source})")
        except Exception as e:
            LOG.exception("Ошибка обработки %s", f)
            console.print(f"[red]Ошибка {f.name}: {e}[/red]")

    console.print(f"[bold green]Всего загружено: {total}[/bold green]")
    console.print(f"[dim]Всего в БД: {storage.total_records()}[/dim]")


# ---------- 2. ПОИСК ----------

def menu_search() -> None:
    if storage.total_records() == 0:
        console.print("[yellow]База пуста. Сначала загрузите данные (п.1).[/yellow]")
        return

    kind = inquirer.select(
        message="Что искать?",
        choices=[
            {"name": "Любой текст", "value": "text"},
            {"name": "Телефон", "value": "phone"},
            {"name": "Email", "value": "email"},
            {"name": "ФИО", "value": "fio"},
            {"name": "Username", "value": "user"},
            {"name": "IP", "value": "ip"},
        ],
    ).execute()

    q = inquirer.text(message="Запрос:").execute()
    if not q:
        return

    if kind == "phone":
        rows = storage.search_phone(q)
    else:
        rows = storage.search(q)

    tools.render_results(rows, title=f"Поиск: {q}")

    if rows and inquirer.confirm(message="Экспортировать результат?", default=False).execute():
        fmt = inquirer.select(message="Формат:", choices=["csv", "json"]).execute()
        out = BASE / "data" / "generated" / f"search_{int(__import__('time').time())}.{fmt}"
        tools.export_results(rows, out, fmt)
        console.print(f"[green]Сохранено: {out}[/green]")


# ---------- 3. ГЕНЕРАТОР ЛИЧНОСТЕЙ ----------

def menu_generator() -> None:
    action = inquirer.select(
        message="Генератор личностей:",
        choices=[
            {"name": "Одна личность (полный профиль)", "value": "one"},
            {"name": "Массовая генерация", "value": "many"},
            {"name": "Сохранить одну личность в HTML", "value": "html"},
            {"name": "Список сохранённых в БД", "value": "list"},
            {"name": "Назад", "value": "back"},
        ],
    ).execute()

    if action == "back":
        return

    if action == "list":
        rows = storage.fetch_persons(50)
        if not rows:
            console.print("[yellow]Нет сохранённых личностей.[/yellow]")
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
        return

    if action == "html":
        p = generator.generate_person()
        out = BASE / "data" / "generated" / f"person_{p.username}.html"
        out.write_text(generator.person_to_html(p), encoding="utf-8")
        console.print(f"[green]HTML сохранён: {out}[/green]")
        return

    if action == "one":
        country = inquirer.select(message="Страна:", choices=["RU", "US", "DE", "FR", "GB"]).execute()
        gender = inquirer.select(message="Пол:", choices=[
            {"name": "Случайно", "value": None},
            {"name": "Мужской", "value": "M"},
            {"name": "Женский", "value": "F"},
        ]).execute()
        p = generator.generate_person(country=country, gender=gender)
        _print_person(p)
        if inquirer.confirm(message="Сохранить в БД?", default=False).execute():
            storage.save_person(json.dumps(generator.person_to_dict(p), ensure_ascii=False))
            console.print("[green]Сохранено.[/green]")
        if inquirer.confirm(message="Сохранить в файл?", default=False).execute():
            fmt = inquirer.select(message="Формат:", choices=["json", "txt", "csv", "html"]).execute()
            _save_person(p, fmt)
        return

    if action == "many":
        count = inquirer.select(
            message="Сколько?",
            choices=[10, 50, 100, 500, 1000, 1500],
        ).execute()
        country = inquirer.select(message="Страна:", choices=["RU", "US", "DE", "FR", "GB"]).execute()
        gender = inquirer.select(message="Пол:", choices=[
            {"name": "Случайно", "value": None},
            {"name": "Мужской", "value": "M"},
            {"name": "Женский", "value": "F"},
        ]).execute()
        age_min = inquirer.number(message="Мин. возраст:", default=18).execute()
        age_max = inquirer.number(message="Макс. возраст:", default=60).execute()
        age_min = int(age_min); age_max = int(age_max)

        people = generator.generate_many(count, country, gender, age_min, age_max)
        console.print(f"[green]Сгенерировано: {len(people)}[/green]")

        fmt = inquirer.select(message="Формат:", choices=["json", "csv", "txt"]).execute()
        out = BASE / "data" / "generated" / f"batch_{count}_{int(__import__('time').time())}.{fmt}"
        _save_many(people, out, fmt)
        console.print(f"[green]Сохранено: {out}[/green]")

        if inquirer.confirm(message="Сохранить в БД?", default=False).execute():
            for p in people:
                storage.save_person(json.dumps(generator.person_to_dict(p), ensure_ascii=False))
            console.print("[green]Сохранено в БД.[/green]")


def _print_person(p) -> None:
    d = generator.person_to_dict(p)
    t = Table(title=f"Личность: {d['full_name']}", show_lines=True)
    t.add_column("Поле", style="cyan", no_wrap=True)
    t.add_column("Значение", style="white", overflow="fold")
    for k, v in d.items():
        if isinstance(v, (dict, list)):
            v = json.dumps(v, ensure_ascii=False)
        t.add_row(k, str(v))
    console.print(t)


def _save_person(p, fmt: str) -> None:
    d = generator.person_to_dict(p)
    base = BASE / "data" / "generated" / f"person_{d['username']}"
    if fmt == "json":
        out = base.with_suffix(".json")
        out.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    elif fmt == "html":
        out = base.with_suffix(".html")
        out.write_text(generator.person_to_html(p), encoding="utf-8")
    elif fmt == "csv":
        import csv
        out = base.with_suffix(".csv")
        with out.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(list(d.keys()))
            w.writerow([json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
                        for v in d.values()])
    else:
        out = base.with_suffix(".txt")
        out.write_text("\n".join(f"{k}: {v}" for k, v in d.items()), encoding="utf-8")
    console.print(f"[green]Сохранено: {out}[/green]")


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
                f.write(f"=== Личность #{i} ===\n")
                for k, v in d.items():
                    f.write(f"{k}: {v}\n")
                f.write("\n")


# ---------- 4. ПАРОЛИ ----------

def menu_passwords() -> None:
    action = inquirer.select(
        message="Пароли:",
        choices=[
            {"name": "Сгенерировать пароль", "value": "gen"},
            {"name": "Запоминающийся пароль", "value": "mem"},
            {"name": "Проверить надёжность", "value": "check"},
        ],
    ).execute()

    if action == "gen":
        length = int(inquirer.number(message="Длина (12-32):", default=16).execute())
        mode = inquirer.select(message="Набор:", choices=[
            {"name": "Буквы", "value": "letters"},
            {"name": "Буквы + цифры", "value": "alnum"},
            {"name": "Всё + символы", "value": "all"},
        ]).execute()
        pwd = tools.gen_password(length, mode)
        console.print(f"[bold green]{pwd}[/bold green]")
        score, label = tools.password_strength(pwd)
        console.print(f"Надёжность: {score}/100 ({label})")
    elif action == "mem":
        wc = int(inquirer.number(message="Слов:", default=3).execute())
        console.print(f"[bold green]{tools.gen_memorable(wc)}[/bold green]")
    else:
        pwd = inquirer.text(message="Введите пароль:").execute()
        score, label = tools.password_strength(pwd)
        console.print(f"Оценка: {score}/100 — {label}")


# ---------- 5. НИКИ ----------

def menu_nicks() -> None:
    style = inquirer.select(message="Стиль:", choices=[
        {"name": "Геймерский", "value": "gamer"},
        {"name": "Профессиональный", "value": "pro"},
        {"name": "Креативный", "value": "creative"},
        {"name": "Анонимный", "value": "anon"},
    ]).execute()
    fio = inquirer.text(message="ФИО (опционально):").execute() or None
    seen: set[str] = set()
    for _ in range(10):
        n = tools.gen_nick(style, fio)
        if n not in seen:
            seen.add(n)
            console.print(f"[cyan]{n}[/cyan]")


# ---------- 6. РАБОТА С БАЗАМИ ----------

def menu_databases() -> None:
    action = inquirer.select(
        message="Базы:",
        choices=[
            {"name": "Список баз", "value": "list"},
            {"name": "Удалить базу", "value": "del"},
            {"name": "Объединить", "value": "merge"},
            {"name": "Дедуплицировать", "value": "dedup"},
            {"name": "Экспорт в CSV", "value": "export"},
        ],
    ).execute()

    if action == "list":
        rows = storage.list_sources()
        if not rows:
            console.print("[yellow]Нет загруженных баз.[/yellow]")
            return
        t = Table(title="Загруженные базы")
        t.add_column("ID"); t.add_column("Название"); t.add_column("Записей"); t.add_column("Дата")
        for r in rows:
            t.add_row(str(r[0]), r[1], str(r[2]), r[3])
        console.print(t)
        console.print(f"[bold]Всего записей: {storage.total_records()}[/bold]")
    elif action == "del":
        sid = int(inquirer.number(message="ID базы:").execute())
        n = storage.delete_source(sid)
        console.print(f"[green]Удалено записей: {n}[/green]")
    elif action == "merge":
        ids = inquirer.text(message="ID баз через запятую:").execute()
        ids_list = [int(x.strip()) for x in ids.split(",") if x.strip().isdigit()]
        if not ids_list:
            return
        new_name = inquirer.text(message="Новое имя базы:").execute()
        n = storage.merge_sources(new_name, ids_list)
        console.print(f"[green]Объединено записей: {n}[/green]")
    elif action == "dedup":
        src = inquirer.text(message="Имя базы (пусто = все):").execute() or None
        n = storage.deduplicate(src)
        console.print(f"[green]Удалено дубликатов: {n}[/green]")
    elif action == "export":
        src = inquirer.text(message="Имя базы (пусто = все):").execute() or None
        out = BASE / "data" / "generated" / f"export_{int(__import__('time').time())}.csv"
        n = storage.export_records(out, src)
        console.print(f"[green]Экспортировано {n} → {out}[/green]")


# ---------- 7. УТИЛИТЫ ----------

def menu_utils() -> None:
    action = inquirer.select(
        message="Утилиты:",
        choices=[
            {"name": "Проверить телефон", "value": "phone"},
            {"name": "Проверить email", "value": "email"},
            {"name": "Проверить карту", "value": "card"},
            {"name": "Проверить ИНН", "value": "inn"},
            {"name": "Сгенерировать QR", "value": "qr"},
            {"name": "Сгенерировать vCard", "value": "vcard"},
            {"name": "AES-256 шифрование", "value": "enc"},
            {"name": "AES-256 расшифровка", "value": "dec"},
        ],
    ).execute()

    if action == "phone":
        num = inquirer.text(message="Номер:").execute()
        res = tools.validate_phone(num)
        for k, v in res.items():
            console.print(f"[cyan]{k}[/cyan]: {v}")
    elif action == "email":
        e = inquirer.text(message="Email:").execute()
        console.print("[green]OK[/green]" if tools.validate_email(e) else "[red]Неверно[/red]")
    elif action == "card":
        c = inquirer.text(message="Номер карты:").execute()
        console.print("[green]OK[/green]" if tools.validate_card(c) else "[red]Неверно[/red]")
    elif action == "inn":
        i = inquirer.text(message="ИНН:").execute()
        console.print("[green]OK[/green]" if generator.validate_inn(i) else "[red]Неверно[/red]")
    elif action == "qr":
        text = inquirer.text(message="Текст:").execute()
        p = tools.gen_qr(text)
        console.print(f"[green]QR сохранён: {p}[/green]")
    elif action == "vcard":
        person = generator.person_to_dict(generator.generate_person())
        p = tools.gen_vcard(person)
        console.print(f"[green]vCard сохранён: {p}[/green]")
    elif action == "enc":
        text = inquirer.text(message="Текст:").execute()
        pwd = inquirer.text(message="Пароль:", is_password=True).execute()
        console.print(f"[green]{tools.encrypt_text(text, pwd)}[/green]")
    elif action == "dec":
        ct = inquirer.text(message="Шифротекст:").execute()
        pwd = inquirer.text(message="Пароль:", is_password=True).execute()
        try:
            console.print(f"[green]{tools.decrypt_text(ct, pwd)}[/green]")
        except Exception as e:
            console.print(f"[red]Ошибка: {e}[/red]")


# ---------- 8. НАСТРОЙКИ ----------

SETTINGS_PATH = BASE / "data" / "settings.json"
DEFAULT_SETTINGS = {"theme": "dark", "language": "ru", "autoclean": True}


def load_settings() -> dict:
    if SETTINGS_PATH.exists():
        try:
            return {**DEFAULT_SETTINGS, **json.loads(SETTINGS_PATH.read_text("utf-8"))}
        except Exception:
            pass
    return dict(DEFAULT_SETTINGS)


def save_settings(s: dict) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")


def menu_settings() -> None:
    s = load_settings()
    action = inquirer.select(
        message="Настройки:",
        choices=[
            {"name": f"Тема: {s['theme']}", "value": "theme"},
            {"name": f"Язык: {s['language']}", "value": "lang"},
            {"name": f"Автоочистка кеша: {s['autoclean']}", "value": "clean"},
            {"name": "Экспорт настроек", "value": "export"},
        ],
    ).execute()

    if action == "theme":
        s["theme"] = inquirer.select(message="Тема:", choices=["dark", "light"]).execute()
    elif action == "lang":
        s["language"] = inquirer.select(message="Язык:", choices=["ru", "en"]).execute()
    elif action == "clean":
        s["autoclean"] = inquirer.confirm(message="Включить автоочистку?", default=s["autoclean"]).execute()
    elif action == "export":
        out = BASE / "data" / "generated" / "settings_export.json"
        out.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
        console.print(f"[green]Экспорт: {out}[/green]")
        return

    save_settings(s)
    console.print("[green]Сохранено.[/green]")


# ---------- 9. О ПРОГРАММЕ ----------

def menu_about() -> None:
    console.print(Panel.fit(
        f"[bold red]FUCKJESTER[/bold red] v{VERSION}\n"
        f"Автор: [cyan]{AUTHOR}[/cyan]\n"
        "GitHub: [blue]https://github.com/jester/fuckjester[/blue]\n"
        "Лицензия: MIT\n\n"
        "[yellow]Предупреждение:[/yellow]\n"
        "Софт работает ТОЛЬКО с базами, которые загрузил сам пользователь.\n"
        "Незаконный сбор, хранение и распространение персональных данных\n"
        "запрещён (ст. 137, 272 УК РФ). Генератор личностей — для тестов и обучения.",
        border_style="red",
        title="О программе",
    ))


# ---------- ГЛАВНОЕ МЕНЮ ----------

def main_menu() -> str:
    return inquirer.select(
        message="Главное меню:",
        choices=[
            {"name": "[1] Загрузка баз данных", "value": "1"},
            {"name": "[2] Поиск по базам", "value": "2"},
            {"name": "[3] Генератор личностей", "value": "3"},
            {"name": "[4] Генератор паролей", "value": "4"},
            {"name": "[5] Генератор ников", "value": "5"},
            {"name": "[6] Работа с базами", "value": "6"},
            {"name": "[7] Утилиты", "value": "7"},
            {"name": "[8] Настройки", "value": "8"},
            {"name": "[9] О программе", "value": "9"},
            {"name": "[0] Выход", "value": "0"},
        ],
        qmark=">>",
        amark=">>",
    ).execute()


def main() -> None:
    try:
        sys.setrecursionlimit(10000)
        storage.init()
        banner()
        console.print(f"[dim]Всего записей в БД: {storage.total_records()}[/dim]\n")

        handlers = {
            "1": menu_upload, "2": menu_search, "3": menu_generator,
            "4": menu_passwords, "5": menu_nicks, "6": menu_databases,
            "7": menu_utils, "8": menu_settings, "9": menu_about,
        }
        while True:
            choice = main_menu()
            if choice == "0":
                console.print("[red]Выход. Будь осторожен, jester.[/red]")
                break
            fn = handlers.get(choice)
            if fn:
                try:
                    fn()
                except KeyboardInterrupt:
                    console.print("\n[yellow]Отменено.[/yellow]")
                except Exception as e:
                    LOG.exception("Ошибка в меню %s", choice)
                    console.print(f"[red]Ошибка: {e}[/red]")
            console.print()
    except KeyboardInterrupt:
        console.print("\n[red]Прервано.[/red]")


if __na
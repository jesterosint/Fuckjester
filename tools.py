"""Поиск, пароли, ники, утилиты, шифрование, QR, vCard."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import random
import re
import string
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table

console = Console()

BASE = Path(__file__).resolve().parent.parent
GEN_DIR = BASE / "data" / "generated"
GEN_DIR.mkdir(parents=True, exist_ok=True)


# ---------- ПОИСК ----------

def render_results(rows: list[tuple], title: str = "Результаты поиска") -> None:
    if not rows:
        console.print("[yellow]Ничего не найдено.[/yellow]")
        return
    t = Table(title=title)
    t.add_column("ID", style="cyan", no_wrap=True)
    t.add_column("Источник", style="magenta")
    t.add_column("Содержимое", style="white", overflow="fold")
    t.add_column("Дата", style="green")
    for r in rows:
        content = r[2]
        if len(content) > 200:
            content = content[:200] + "…"
        t.add_row(str(r[0]), r[1], content, r[3])
    console.print(t)


def export_results(rows: list[tuple], path: Path, fmt: str = "csv") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "csv":
        import csv
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["id", "source", "content", "created_at"])
            w.writerows(rows)
    elif fmt == "json":
        data = [{"id": r[0], "source": r[1], "content": r[2], "created_at": r[3]}
                for r in rows]
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        raise ValueError(f"Неизвестный формат: {fmt}")


# ---------- ПАРОЛИ ----------

def gen_password(length: int = 16, mode: str = "all") -> str:
    """mode: letters | alnum | all."""
    length = max(4, min(length, 64))
    pool = string.ascii_letters
    if mode in ("alnum", "all"):
        pool += string.digits
    if mode == "all":
        pool += "!@#$%^&*()-_=+[]{};:,.?/"

    while True:
        pwd = "".join(random.choice(pool) for _ in range(length))
        if (any(c.islower() for c in pwd) and any(c.isupper() for c in pwd)
                and (mode == "letters" or any(c.isdigit() for c in pwd))):
            return pwd


def gen_memorable(words_count: int = 3) -> str:
    words = ["Sun","Moon","Star","Fire","Ice","Wolf","Fox","Lion","Sky","Sea",
             "Rain","Snow","Wind","Tree","Rock","King","Queen","Dark","Light","Blue",
             "Red","Green","Gold","Silver","Iron","Steel","Storm","Cloud","River","Lake"]
    sep = random.choice("!@#$%._-")
    parts = [random.choice(words) for _ in range(words_count)]
    return sep.join(parts) + str(random.randint(10, 9999))


def password_strength(pwd: str) -> tuple[int, str]:
    """Возвращает (0..100, оценка)."""
    score = 0
    if len(pwd) >= 8: score += 20
    if len(pwd) >= 12: score += 15
    if len(pwd) >= 16: score += 10
    if re.search(r"[a-z]", pwd): score += 10
    if re.search(r"[A-Z]", pwd): score += 10
    if re.search(r"\d", pwd): score += 15
    if re.search(r"[^\w]", pwd): score += 20
    score = min(score, 100)
    if score < 40: return score, "слабый"
    if score < 70: return score, "средний"
    if score < 90: return score, "сильный"
    return score, "очень сильный"


# ---------- НИКИ ----------

NICK_STYLES = {
    "gamer": ["xX_{}_Xx", "{}_Pro", "{}Killer", "Shadow_{}", "{}_YT", "{}GG"],
    "pro":   ["{}_{}", "{}.{}", "{}{}", "{}_official", "{}_dev"],
    "creative": ["{}_art", "the_{}", "{}_world", "{}_vibes", "{}_dream"],
    "anon":  ["user_{}", "anon_{}", "ghost_{}", "null_{}", "v0id_{}"],
}


def gen_nick(style: str = "pro", fio: Optional[str] = None) -> str:
    style = style if style in NICK_STYLES else "pro"
    translit = {"а":"a","б":"b","в":"v","г":"g","д":"d","е":"e","ё":"e","ж":"zh",
                "з":"z","и":"i","й":"y","к":"k","л":"l","м":"m","н":"n","о":"o",
                "п":"p","р":"r","с":"s","т":"t","у":"u","ф":"f","х":"h","ц":"c",
                "ч":"ch","ш":"sh","щ":"sch","ъ":"","ы":"y","ь":"","э":"e","ю":"yu","я":"ya"}
    if fio:
        base = "".join(translit.get(c.lower(), c) for c in fio.split()[0])
    else:
        base = "".join(random.choices(string.ascii_lowercase, k=random.randint(4, 8)))
    template = random.choice(NICK_STYLES[style])
    extra = "".join(random.choices(string.ascii_lowercase + string.digits,
                                   k=random.randint(0, 4)))
    try:
        return template.format(base, extra).strip("_").lower()[:24]
    except Exception:
        return f"{base}{random.randint(1,999)}"


# ---------- УТИЛИТЫ ----------

def validate_phone(number: str, region: str = "RU") -> dict:
    try:
        import phonenumbers
        parsed = phonenumbers.parse(number, region)
        valid = phonenumbers.is_valid_number(parsed)
        return {
            "input": number, "valid": valid,
            "e164": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164),
            "national": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL),
            "country": phonenumbers.region_code_for_number(parsed),
            "carrier": phonenumbers.carrier.name_for_number(parsed, "ru") or "—",
        }
    except Exception as e:
        return {"input": number, "valid": False, "error": str(e)}


EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


def validate_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email.strip()))


def validate_card(card: str) -> bool:
    digits = re.sub(r"\D", "", card)
    if not (13 <= len(digits) <= 19):
        return False
    s = 0
    reverse = digits[::-1]
    for i, ch in enumerate(reverse):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        s += d
    return s % 10 == 0


def gen_qr(text: str, path: Optional[Path] = None) -> Path:
    import qrcode
    path = path or (GEN_DIR / f"qr_{int(datetime.now().timestamp())}.png")
    img = qrcode.make(text)
    img.save(str(path))
    return path


def gen_vcard(person_dict: dict, path: Optional[Path] = None) -> Path:
    path = path or (GEN_DIR / f"vcard_{person_dict.get('username','user')}.vcf")
    fio = person_dict.get("full_name", "").split()
    last = fio[0] if fio else ""
    first = fio[1] if len(fio) > 1 else ""
    lines = [
        "BEGIN:VCARD", "VERSION:3.0",
        f"N:{last};{first};;;", f"FN:{person_dict.get('full_name','')}",
        f"TEL;TYPE=CELL:{person_dict.get('phone','')}",
        f"EMAIL:{person_dict.get('email','')}",
        f"BDAY:{person_dict.get('birth_date','')}",
        f"TITLE:{person_dict.get('job',{}).get('position','')}",
        f"ORG:{person_dict.get('job',{}).get('company','')}",
        "END:VCARD",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# ---------- AES-256 ----------

def _aes_key(password: str) -> bytes:
    return hashlib.sha256(password.encode("utf-8")).digest()


def encrypt_text(plaintext: str, password: str) -> str:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    key = _aes_key(password)
    nonce = os.urandom(12)
    aes = AESGCM(key)
    ct = aes.encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.b64encode(nonce + ct).decode("ascii")


def decrypt_text(ciphertext_b64: str, password: str) -> str:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    key = _aes_key(password)
    raw = base64.b64decode(ciphertext_b64)
    nonce, ct = raw[:12], raw[12:]
    aes = AESGCM(key)
    return aes.decrypt(nonce, ct, None).decode("utf-8")
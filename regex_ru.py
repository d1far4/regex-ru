"""Регулярные выражения для российских данных (Python 3.8+, только стандартная библиотека).

Телефоны, ИНН, СНИЛС, ОГРН, КПП, БИК, расчётный счёт, госномер, паспорт,
почтовый индекс, даты по-русски, суммы в рублях.

Регулярное выражение проверяет только формат. Для ИНН, СНИЛС и ОГРН
здесь же есть проверка контрольных чисел: без неё «1234567890» сойдёт за ИНН.
"""
import re

__all__ = [
    "PHONE", "INN", "SNILS", "OGRN", "OGRNIP", "KPP", "BIK", "ACCOUNT",
    "CAR_PLATE", "PASSPORT", "POSTCODE", "DATE_NUMERIC", "DATE_WORDS", "MONEY",
    "find_phones", "normalize_phone",
    "is_valid_inn", "is_valid_snils", "is_valid_ogrn",
    "find_inns", "find_dates", "find_money",
]

# --- Телефоны -----------------------------------------------------------------
# +7 912 345-67-89, 8 (912) 345 67 89, +79123456789, 8-912-345-67-89
PHONE = re.compile(
    r"(?<![\d+])(?:\+7|8)[\s\-]*\(?(\d{3})\)?[\s\-]*(\d{3})[\s\-]*(\d{2})[\s\-]*(\d{2})(?!\d)"
)


def find_phones(text):
    """Все телефоны из текста в виде +7XXXXXXXXXX."""
    return ["+7" + "".join(m.groups()) for m in PHONE.finditer(text)]


def normalize_phone(text):
    """Заменить телефоны в тексте на единый вид +7 (XXX) XXX-XX-XX."""
    return PHONE.sub(r"+7 (\1) \2-\3-\4", text)


# --- ИНН, СНИЛС, ОГРН ---------------------------------------------------------
INN = re.compile(r"(?<!\d)(?:\d{10}|\d{12})(?!\d)")
SNILS = re.compile(r"(?<!\d)(\d{3})[\- ]?(\d{3})[\- ]?(\d{3})[\- ]?(\d{2})(?!\d)")
OGRN = re.compile(r"(?<!\d)[15]\d{12}(?!\d)")       # юрлица: 13 цифр
OGRNIP = re.compile(r"(?<!\d)3\d{14}(?!\d)")        # ИП: 15 цифр, начинается с 3
KPP = re.compile(r"(?<!\d)\d{4}[\dA-Z]{2}\d{3}(?!\d)")
BIK = re.compile(r"(?<!\d)04\d{7}(?!\d)")
ACCOUNT = re.compile(r"(?<!\d)\d{20}(?!\d)")        # расчётный / корр. счёт


def _inn_digit(digits, weights):
    return sum(int(d) * w for d, w in zip(digits, weights)) % 11 % 10


def is_valid_inn(value):
    """ИНН: формат + контрольные цифры (10 цифр — организация, 12 — человек или ИП)."""
    s = re.sub(r"\s", "", str(value))
    if re.fullmatch(r"\d{10}", s):
        return _inn_digit(s, (2, 4, 10, 3, 5, 9, 4, 6, 8)) == int(s[9])
    if re.fullmatch(r"\d{12}", s):
        n11 = _inn_digit(s, (7, 2, 4, 10, 3, 5, 9, 4, 6, 8))
        n12 = _inn_digit(s, (3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8))
        return n11 == int(s[10]) and n12 == int(s[11])
    return False


def find_inns(text):
    """ИНН из текста, у которых сходятся контрольные цифры."""
    return [m.group() for m in INN.finditer(text) if is_valid_inn(m.group())]


def is_valid_snils(value):
    """СНИЛС: 123-456-789 01, контрольное число по алгоритму ПФР."""
    m = SNILS.fullmatch(str(value).strip())
    if not m:
        return False
    number = "".join(m.groups()[:3])
    control = int(m.group(4))
    if int(number) <= 1001998:      # номера до 001-001-998 контрольным числом не проверяются
        return True
    total = sum(int(d) * (9 - i) for i, d in enumerate(number))
    if total < 100:
        expected = total
    elif total in (100, 101):
        expected = 0
    else:
        expected = total % 101
        if expected == 100:
            expected = 0
    return expected == control


def is_valid_ogrn(value):
    """ОГРН (13 цифр) или ОГРНИП (15 цифр) с контрольной цифрой."""
    s = str(value).strip()
    if re.fullmatch(r"\d{13}", s):
        return int(s[:12]) % 11 % 10 == int(s[12])
    if re.fullmatch(r"\d{15}", s):
        return int(s[:14]) % 13 % 10 == int(s[14])
    return False


# --- Транспорт и документы ---------------------------------------------------
# В госномерах только 12 букв, которые пишутся одинаково кириллицей и латиницей.
CAR_PLATE = re.compile(r"(?<![\wА-Яа-яЁё])[АВЕКМНОРСТУХ]\d{3}(?<!000)[АВЕКМНОРСТУХ]{2}\s?\d{2,3}(?!\d)")
PASSPORT = re.compile(r"(?<!\d)(\d{2})\s?(\d{2})\s?(\d{6})(?!\d)")   # серия и номер
POSTCODE = re.compile(r"(?<!\d)[1-6]\d{5}(?!\d)")

# --- Даты ---------------------------------------------------------------------
DATE_NUMERIC = re.compile(r"(?<!\d)(0?[1-9]|[12]\d|3[01])\.(0?[1-9]|1[0-2])\.((?:19|20)\d{2})(?!\d)")

_MONTHS = ("января", "февраля", "марта", "апреля", "мая", "июня", "июля",
           "августа", "сентября", "октября", "ноября", "декабря")
DATE_WORDS = re.compile(
    r"(?<!\d)(0?[1-9]|[12]\d|3[01])\s+(" + "|".join(_MONTHS) + r")\s+((?:19|20)\d{2})(?:\s*(?:г\.|года))?",
    re.IGNORECASE,
)


def find_dates(text):
    """Даты «17.11.2026» и «17 ноября 2026 г.» в виде ГГГГ-ММ-ДД, в порядке появления."""
    found = []
    for m in DATE_NUMERIC.finditer(text):
        found.append((m.start(), f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"))
    for m in DATE_WORDS.finditer(text):
        month = _MONTHS.index(m.group(2).lower()) + 1
        found.append((m.start(), f"{m.group(3)}-{month:02d}-{int(m.group(1)):02d}"))
    return [d for _, d in sorted(found)]


# --- Деньги -------------------------------------------------------------------
# 1 250,50 ₽ · 1250 руб. · 990 р. · 12 000 рублей (пробел может быть неразрывным)
MONEY = re.compile(
    r"(?<![\d,.])(\d{1,3}(?:[   ]\d{3})+|\d+)(?:[,.](\d{2}))?\s?(?:₽|руб(?:\.|л(?:ей|я|ь))?|р\.)",
    re.IGNORECASE,
)


def find_money(text):
    """Суммы в рублях из текста как числа: [1250.5, 990.0]."""
    out = []
    for m in MONEY.finditer(text):
        rub = re.sub(r"\D", "", m.group(1))
        kop = m.group(2) or "00"
        out.append(float(f"{rub}.{kop}"))
    return out

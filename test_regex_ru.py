"""Проверки для regex_ru.py. Запуск: python test_regex_ru.py (или pytest)."""
from regex_ru import (
    BIK, CAR_PLATE, KPP, PASSPORT, POSTCODE,
    find_dates, find_inns, find_money, find_phones, normalize_phone,
    is_valid_inn, is_valid_ogrn, is_valid_snils,
)


def test_phones():
    text = "Звоните: +7 912 345-67-89, 8 (495) 123 45 67 или +79001112233. Заказ 189123456789."
    assert find_phones(text) == ["+79123456789", "+74951234567", "+79001112233"]
    assert normalize_phone("тел. 8-912-345-67-89") == "тел. +7 (912) 345-67-89"


def test_inn():
    assert is_valid_inn("7707083893")          # ПАО Сбербанк
    assert is_valid_inn("500100732259")        # 12 цифр
    assert not is_valid_inn("7707083894")      # испорчена контрольная цифра
    assert not is_valid_inn("1234567890")
    assert not is_valid_inn("77070838")
    assert find_inns("ИНН 7707083893, счёт 40702810900000012345, ИНН 1234567890") == ["7707083893"]


def test_snils():
    assert is_valid_snils("112-233-445 95")
    assert is_valid_snils("11223344595")
    assert not is_valid_snils("112-233-445 96")
    assert not is_valid_snils("112-233-44595x")


def test_ogrn():
    assert is_valid_ogrn("1027700132195")      # ПАО Сбербанк
    assert not is_valid_ogrn("1027700132196")
    assert not is_valid_ogrn("102770013219")


def test_codes():
    assert BIK.fullmatch("044525225")
    assert not BIK.fullmatch("144525225")
    assert KPP.fullmatch("773601001")
    assert POSTCODE.findall("г. Москва, 101000; Тверь 170100; код 0123456") == ["101000", "170100"]


def test_documents():
    assert CAR_PLATE.findall("Авто А123ВС77 и К001МР 799, не номер: А000АА77, Б123ВГ77") == ["А123ВС77", "К001МР 799"]
    m = PASSPORT.fullmatch("45 06 123456")
    assert m and m.groups() == ("45", "06", "123456")


def test_dates():
    text = "Договор от 17 ноября 2026 г., оплата до 01.12.2026, акт 5 Декабря 2026 года"
    assert find_dates(text) == ["2026-11-17", "2026-12-01", "2026-12-05"]
    assert find_dates("32.13.2026 и 1.2.1899") == []


def test_money():
    text = "Итого 1 250,50 ₽, доставка 300 руб., скидка 990 р., бюджет 12 000 рублей"
    assert find_money(text) == [1250.5, 300.0, 990.0, 12000.0]


if __name__ == "__main__":
    import sys
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("ok  ", name)
            except AssertionError as e:
                failed += 1
                print("FAIL", name, e)
    sys.exit(1 if failed else 0)

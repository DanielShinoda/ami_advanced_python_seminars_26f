"""Тесты, которые были в репозитории до тебя.

Все зелёные. При этом в модуле шесть багов. В этом и смысл: тесты
проверяют то, о чём кто-то подумал, а mypy — все пути сразу.

После починки они должны остаться зелёными.
"""

from gradebook import Auditor, FileStorage, Student, average, find, parse_scores

STUDENTS = [
    Student("Алиса", "БПМИ251", [8, 10, 6]),
    Student("Борис", "БПМИ251", [7]),
    Auditor("Виктор", "БПМИ255", [9], reason="вольнослушатель"),
]


def test_average_counts():
    assert average([8, 10, 6]) == 8.0


def test_average_single():
    assert average([7]) == 7.0


def test_find_hit():
    found = find(STUDENTS, "Борис")
    assert found is not None
    assert found.group == "БПМИ251"


def test_find_miss():
    assert find(STUDENTS, "Никто") is None


def test_auditor_is_student():
    assert isinstance(STUDENTS[2], Student)


def test_parse_scores_when_json_already_has_numbers():
    assert parse_scores({"scores": [8.0, 10.0]}) == [8.0, 10.0]


def test_file_storage_writes(tmp_path):
    path = tmp_path / "report.txt"
    FileStorage(str(path)).save("отчёт")
    assert path.read_text(encoding="utf-8") == "отчёт"

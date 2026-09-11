"""Тесты верификатора публикации — на чистых функциях, без сети."""

import pathlib
import re

import check_publication as cp
import pytest

GOOD_INFO = {
    "summary": "Статистика текста",
    "description": "# textstat\n\n" + "подробное описание пакета " * 10,
    "requires_python": ">=3.10",
    "author_email": "Student <student@example.com>",
    "license_expression": "MIT",
    "classifiers": ["Development Status :: 3 - Alpha", "Programming Language :: Python :: 3"],
    "project_urls": {"Homepage": "https://example.com"},
}

EMPTY_INFO = {
    "summary": "",
    "description": "",
    "requires_python": None,
    "author": None,
    "author_email": None,
    "license": "",
    "classifiers": [],
    "project_urls": None,
}


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("textstat-seminar-ivanov", "textstat-seminar-ivanov"),
        ("textstat_seminar_ivanov", "textstat-seminar-ivanov"),
        ("TextStat.Seminar__Ivanov", "textstat-seminar-ivanov"),
    ],
)
def test_normalize_follows_pep503(raw, expected):
    assert cp.normalize(raw) == expected


def test_metadata_all_green():
    checks = cp.check_metadata(GOOD_INFO)
    assert checks, "проверок не должно быть пусто"
    assert all(check.ok for check in checks), [c.title for c in checks if not c.ok]


def test_metadata_all_red_on_empty():
    checks = cp.check_metadata(EMPTY_INFO)
    assert not any(check.ok for check in checks)


def test_metadata_points_at_todo_4():
    """Пустые description и readme должны указывать на TODO 4."""
    details = [check.detail for check in cp.check_metadata(EMPTY_INFO)]
    assert any("TODO 4 не закрыт (description)" in d for d in details)
    assert any("TODO 4 не закрыт (readme)" in d for d in details)


def test_prefilled_fields_do_not_mention_todo():
    """Поля, которые заполнены в заготовке, не должны слать студента к TODO."""
    by_title = {check.title: check.detail for check in cp.check_metadata(EMPTY_INFO)}
    for title in [
        "requires-python указан",
        "автор указан",
        "лицензия указана",
        "classifiers проставлены",
        "ссылки на проект есть",
    ]:
        assert "TODO" not in by_title[title], title


def test_todo_hints_stay_within_range():
    """В подсказках не должно остаться номеров из старой нумерации (было 13)."""
    source = pathlib.Path(cp.__file__).read_text(encoding="utf-8")
    stale = re.findall(r"TODO (\d+)", source)
    assert stale, "подсказки про TODO вообще пропали"
    assert all(1 <= int(number) <= 6 for number in stale), sorted(set(stale))


def test_license_accepted_from_either_field():
    only_legacy = {**GOOD_INFO, "license_expression": None, "license": "MIT"}
    checks = {check.title: check.ok for check in cp.check_metadata(only_legacy)}
    assert checks["лицензия указана"]


def test_author_accepted_from_either_field():
    only_name = {**GOOD_INFO, "author_email": None, "author": "Иванов Иван"}
    checks = {check.title: check.ok for check in cp.check_metadata(only_name)}
    assert checks["автор указан"]


def test_artifacts_need_both_wheel_and_sdist():
    both = {
        "urls": [
            {"packagetype": "bdist_wheel", "filename": "pkg-0.1.0-py3-none-any.whl"},
            {"packagetype": "sdist", "filename": "pkg-0.1.0.tar.gz"},
        ]
    }
    assert all(check.ok for check in cp.check_artifacts(both))

    wheel_only = {"urls": [both["urls"][0]]}
    results = {check.title: check.ok for check in cp.check_artifacts(wheel_only)}
    assert results["wheel опубликован"]
    assert not results["sdist опубликован"]


def test_artifacts_on_empty_release():
    assert not any(check.ok for check in cp.check_artifacts({"urls": []}))


def test_check_render_marks_status():
    assert "✓" in cp.Check("ок", True).render()
    assert "✗" in cp.Check("не ок", False).render()
    assert "деталь" in cp.Check("ок", True, "деталь").render()


def test_smoke_script_is_valid_python():
    compile(cp.SMOKE_SCRIPT, "<smoke>", "exec")


def test_sample_text_expectations_match_the_package():
    """Ожидания верификатора должны совпадать с реальным поведением пакета.

    Если однажды поменяется SAMPLE_TEXT или токенизация — тест поймает
    расхождение раньше, чем студент увидит красную галочку на зелёном пакете.
    """
    words = len(cp.SAMPLE_TEXT.split())
    assert words == cp.EXPECTED_WORDS, "число слов в образце разошлось с EXPECTED_WORDS"
    assert (
        cp.SAMPLE_TEXT.count(".") + cp.SAMPLE_TEXT.count("!") + cp.SAMPLE_TEXT.count("?")
        == cp.EXPECTED_SENTENCES
    )

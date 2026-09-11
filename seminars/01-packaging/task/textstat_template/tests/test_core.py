"""Тесты пакета. Запускаются только после `uv pip install -e .`

Если видишь `ModuleNotFoundError: No module named 'textstat_seminar'` —
это не баг тестов. При src-layout исходники физически лежат в `src/`,
и Python их не найдёт, пока пакет не установлен. Ровно ради этого
src-layout и придуман: тесты гоняются по установленному пакету, а не по
случайно попавшей в sys.path папке.
"""

from importlib.metadata import entry_points
import io

import pytest

from textstat_seminar import Stats, __version__, analyze, load_stopwords
from textstat_seminar.cli import main

RU_TEXT = "Кот сидел на окне. Кот смотрел на птиц! Птицы не смотрели на кота?"
EN_TEXT = "The cat sat on the mat. The cat watched the birds."


def test_counts_ru():
    stats = analyze(RU_TEXT)
    assert isinstance(stats, Stats)
    assert stats.sentences == 3
    assert stats.words == 13
    assert stats.language == "ru"


def test_top_words_skip_stopwords():
    stats = analyze(RU_TEXT, top_n=2)
    words = [word for word, _ in stats.top_words]
    assert "кот" in words
    # "на" и "не" — стоп-слова, в топ попадать не должны
    assert "на" not in words
    assert "не" not in words


def test_language_detection():
    assert analyze(EN_TEXT).language == "en"
    assert analyze(RU_TEXT).language == "ru"


def test_explicit_language_wins():
    # Русский текст, но стоп-лист просим английский — "на" больше не стоп-слово.
    stats = analyze(RU_TEXT, top_n=10, language="en")
    assert stats.language == "en"
    assert "на" in [word for word, _ in stats.top_words]


def test_empty_text():
    stats = analyze("")
    assert stats.words == 0
    assert stats.sentences == 0
    assert stats.avg_word_length == 0.0
    assert stats.top_words == []


def test_hyphenated_word_is_one_word():
    assert analyze("из-за").words == 1


def test_negative_top_n_rejected():
    with pytest.raises(ValueError, match="отрицательным"):
        analyze("текст", top_n=-1)


@pytest.mark.parametrize("language", ["ru", "en"])
def test_stopwords_shipped_with_package(language):
    """Package data доехала до установленного пакета.

    Этот тест — первый, который падает, если забыть включить .txt в сборку.
    """
    stopwords = load_stopwords(language)
    assert len(stopwords) > 50
    assert all(word.islower() for word in stopwords)
    assert not any(word.startswith("#") for word in stopwords)


def test_cli_reads_stdin(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO(EN_TEXT))
    assert main([]) == 0
    out = capsys.readouterr().out
    assert "слов" in out
    assert "en" in out  # язык определился как английский


def test_cli_on_file(tmp_path, capsys):
    path = tmp_path / "sample.txt"
    path.write_text(RU_TEXT, encoding="utf-8")

    assert main([str(path), "--top", "3"]) == 0
    out = capsys.readouterr().out
    assert "слов" in out
    assert "частые слова:" in out


def test_cli_empty_input(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("   \n"))
    assert main([]) == 1
    assert "пустой текст" in capsys.readouterr().err


def test_cli_missing_file(tmp_path, capsys):
    assert main([str(tmp_path / "нет.txt")]) == 2
    assert "не могу прочитать" in capsys.readouterr().err


def test_console_script_registered():
    """В метаданных установленного пакета есть console_script на наш main.

    Падает, если в pyproject.toml не заполнена секция [project.scripts].
    Читаем именно метаданные, а не PATH: так тест не зависит от того,
    активирован venv или нет.
    """
    scripts = entry_points(group="console_scripts")
    targets = {ep.name: ep.value for ep in scripts}
    assert "textstat" in targets, f"console_scripts: {sorted(targets)}"
    assert targets["textstat"] == "textstat_seminar.cli:main"


def test_version_exposed():
    """__version__ есть и выглядит как версия (PEP 440 в простом виде)."""
    assert __version__.count(".") >= 1
    assert all(part.isdigit() for part in __version__.split(".")[:2])

"""Общий счётчик между процессами — два TODO.

Контракт: count_parallel(workers, times) поднимает workers процессов,
каждый увеличивает ОБЩИЙ счётчик ровно на times, и возвращает итог.
Итог обязан быть ровно workers * times — ни один инкремент не теряется.

Всё нужное было на семинаре: shared-примитивы multiprocessing разделяются
между процессами через наследование, а это умеет только fork.

Проверка из корня репо:  make check-counter
"""

import multiprocessing as mp

# Shared-память (Value/Lock) наследуется только через fork:
# spawn перечитывает файл и получил бы непиклибельные объекты.
CTX = mp.get_context("fork")


def _bump(counter: mp.synchronize.Synchronized, lock: mp.synchronize.Lock, times: int) -> None:
    """Увеличить counter ровно на times, каждое увеличение — атомарно.

    TODO 1: цикл на times итераций; внутри — захват lock и инкремент.
    Без lock итог будет меньше: чтение и запись — две разные операции,
    и чужой процесс успевает вклиниться между ними.
    """
    raise NotImplementedError("TODO 1")


def count_parallel(workers: int, times: int) -> int:
    """Поднять workers процессов и вернуть итоговое значение счётчика.

    TODO 2: создай shared-счётчик (CTX.Value, тип "i", старт 0) и lock
    (CTX.Lock), запусти workers процессов с target=_bump, дождись всех
    join'ом и верни counter.value. Процессы — daemon, join — с таймаутом
    не меньше 30 c: зависший воркер не должен уронить проверку.
    """
    raise NotImplementedError("TODO 2")

"""Token bucket на threading.Condition — четыре TODO.

Контракт: bucket вмещает `burst` токенов и пополняется со скоростью
`rate` токенов в секунду (выше вместимости не поднимается). acquire()
забирает один токен; если токенов нет — блокирует поток, пока токен
не наберётся. Потокобезопасно при любом числе потоков.

Всё нужное было на семинаре: инвариант проверяется в цикле `while`,
ожидание — через cond.wait(timeout=...), часы — time.monotonic().

Проверка из корня репо:  make check-limiter
"""

import threading  # noqa: F401  # пригодится в TODO 1 и TODO 3
import time  # noqa: F401  # пригодится в TODO 1, TODO 2 и TODO 4


class TokenBucket:
    """Семафор-токенбакет: `burst` токенов, пополнение `rate` токенов/сек."""

    def __init__(self, rate: float, burst: int) -> None:
        if rate <= 0:
            raise ValueError("rate должен быть положительным")
        if burst < 1:
            raise ValueError("burst должен быть >= 1")
        self._rate = rate
        self._burst = burst
        # TODO 1: создай threading.Condition и начальное состояние:
        # сколько токенов в bucket сейчас и метку времени последнего
        # пополнения. На старте токенов ровно вместимость.
        raise NotImplementedError("TODO 1")

    def _refill(self, now: float) -> None:
        """Пополнить bucket от последней метки времени до `now`.

        Набежало (now - last) * rate токенов, сверху обрезается
        вместимостью. Вызывается только под self._cond.
        """
        raise NotImplementedError("TODO 2")

    def acquire(self) -> None:
        """Забрать один токен, при нехватке подождать.

        Без таймаута: ждать столько, сколько нужно для одного токена.

        TODO 3: под self._cond проверяй инвариант «токен есть» в цикле
        while: сначала refill, потом проверка.

        TODO 4: инвариант не выполнен — cond.wait(timeout=...) ровно
        до появления одного токена, затем снова в начало цикла.
        Выполнен — забери токен и выйди.
        """
        raise NotImplementedError("TODO 3 и TODO 4")

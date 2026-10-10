# Задача — token bucket на threading.Condition

`rate_limiter.py` должен уметь то же, что и семафор с таймингом:
не больше `burst` быстрых входов подряд и в среднем не чаще
`rate` входов в секунду. Без замка, без очереди, без `Semaphore` —
на одной `threading.Condition`, как bounded buffer с семинара.

Четыре TODO: два в конструкторе/refill, два в `acquire`.

```bash
make check-limiter
```

Верификатор гоняет стресс-прогоны: инвариант бакета («в любом
окне длины `burst / rate` съедено не больше `burst + rate * окно`
токенов»), живучесть всех потоков и нижнюю границу времени —
быстрее, чем позволяет refill, работать нельзя.

## Посмотреть глазами

```bash
uv run pytest seminars/05-threads/task -q
```

Базовые тесты лежат в `test_rate_limiter.py`. До решения они падают
на `NotImplementedError` — это нормально.

## Правила игры

- Ожидание — только через `cond.wait(timeout=...)`. `time.sleep`
  в решении считается обходом: верификатор это ловит.
- Цель — именно `Condition`: «не пусто / подожди до пополнения».
  `queue.Queue` и `threading.Semaphore` здесь не нужны.
- Часы — `time.monotonic()`, не `time.time()` (последний скачет
  при синхронизации часов).

## Сдача

Вывод `make check-limiter`: все пункты зелёные.

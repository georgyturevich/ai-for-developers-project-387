# Ручное тестирование после релиза

Инструкция для проверки развёрнутого приложения вручную — через браузер (UI) и
через `bash`/`curl` (публичное API). Покрывает как основные пользовательские
сценарии, так и изменения «review hardening»: строгие скаляры, фиксированную
сетку слотов 30 минут, лимиты полей и тела запроса, и гонку двух вкладок.

## Перед началом

- **Публичный адрес**: <https://cal-bookings-production.up.railway.app>.
  Если разворачиваете в другом месте, замените `BASE` в командах ниже.
- **Данные живут в памяти** и сбрасываются при каждом редеплое/перезапуске.
  Сразу после деплоя каталог пуст — это удобная точка отсчёта.
- **Окно записи**: сегодня + 13 следующих дней в поясе владельца (МСК).
  Слоты предлагаются только в этом окне.
- **Рабочие часы**: 09:00–18:00 по Москве. Сетка стартов: якорь 09:00, шаг
  **30 минут** независимо от длительности типа события.
- Понадобится `curl` и `jq`. Начнём с переменной и констант:

```bash
BASE=https://cal-bookings-production.up.railway.app
```

---

## Часть 1. Проверка через UI

### 1.1 Гость бронирует слот

1. Откройте `$BASE` — должен появиться каталог «На что можно записаться».
2. В кабинете владельца (`/owner`) создайте тип события, например
   «Стрижка» с длительностью **60 минут** (см. шаг 1.2).
3. Вернитесь в каталог, откройте «Стрижку».
4. **Проверка сетки слотов**: кнопки времени идут с шагом 30 минут —
   `09:00–10:00`, `09:30–10:30`, `10:00–11:00`, … и слот целиком помещается в
   рабочий день (последний старт такой, что конец ≤ 18:00).
5. Выберите слот, нажмите «Продолжить», заполните имя, email и (по желанию)
   комментарий, нажмите «Записаться».
6. Вы должны попасть на экран **«Вы записаны»** с текстом
   «Запись подтверждена. Отменить или перенести её нельзя».

### 1.2 Владелец: тип события и список записей

1. Откройте `$BASE/owner` — заголовок «Предстоящие записи».
2. Нажмите «Создать тип события», заполните slug, название, описание и
   длительность, сохраните. Вы вернётесь в каталог, и новый тип там появится.
3. После бронирования из шага 1.1 в `/owner` появится карточка записи с
   типом события, временем и данными гостя.

### 1.3 Гонка двух вкладок: проигравший видит конфликт, а не успех

Сценарий S5 — проверка, что проигравший гость не получает ложное
подтверждение.

1. Откройте один и тот же свободный слот типа события в **двух** окнах/вкладках
   (можно инкогнито): `/types/strizhka`, выбрать один и тот же старт,
   «Продолжить».
2. В обеих вкладках заполните форму (разные имена/email).
3. Отправьте заявку сначала в первой, затем во второй вкладке.
4. Ожидаемо:
   - **первая** вкладка — экран «Вы записаны» (подтверждение);
   - **вторая** вкладка — сообщение **«Этот слот только что заняли. Вернитесь и
     выберите другое время»** и **никакого** экрана успеха.

---

## Часть 2. Проверка через `bash`/`curl`

Все команды против публичного API. Код ошибки в теле ответа — один из
`validation_failed`, `event_type_not_found`, `duplicate_slug`, `slot_unavailable`.

### 2.1 Свежий деплой: каталог пуст

```bash
curl -s $BASE/event-types
# → []
```

### 2.2 Создание типа события (владелец)

```bash
curl -s -X POST $BASE/event-types -H 'Content-Type: application/json' \
  -d '{"id":"strizhka","name":"Стрижка","description":"Стрижка и укладка за один час","durationInMinutes":60}'
# → 201, в ответе тип события с durationInMinutes: 60
```

### 2.3 Строгие скаляры: булево и дробное значение длительности → 400

```bash
curl -s -w '\n%{http_code}\n' -X POST $BASE/event-types -H 'Content-Type: application/json' \
  -d '{"id":"bool","name":"Тест","description":"","durationInMinutes":true}'
# → 400 {"code":"validation_failed", ...} — раньше принималось и превращалось в 1

curl -s -w '\n%{http_code}\n' -X POST $BASE/event-types -H 'Content-Type: application/json' \
  -d '{"id":"float","name":"Тест","description":"","durationInMinutes":60.0}'
# → 400 {"code":"validation_failed", ...}

# Контроль: целое значение в диапазоне 1–540 по-прежнему принимается
curl -s -o /dev/null -w '%{http_code}\n' -X POST $BASE/event-types -H 'Content-Type: application/json' \
  -d '{"id":"ok","name":"Тест","description":"","durationInMinutes":30}'
# → 201
```

### 2.4 Сетка слотов: шаг 30 минут независимо от длительности

```bash
curl -s $BASE/event-types/strizhka/slots | jq -r '.[].start' | head -8
# → старты через 30 минут: 06:00Z, 06:30Z, 07:00Z, ... (= 09:00, 09:30, 10:00 МСК)

# Тип длительностью 45 минут — старты всё равно на получасовой сетке
curl -s -X POST $BASE/event-types -H 'Content-Type: application/json' \
  -d '{"id":"masazh","name":"Массаж","description":"","durationInMinutes":45}' >/dev/null
curl -s $BASE/event-types/masazh/slots | jq -r '.[].start' | head -8
# → тоже :00/:30 (в поясе владельца)
```

### 2.5 Бронирование: старт со смещением нормализуется в UTC

Берём первый свободный слот и переводим его в локальное московское время со
смещением `+03:00`:

```bash
SLOT=$(curl -s $BASE/event-types/strizhka/slots | jq -r '.[0].start')
echo "SLOT=$SLOT"                                  # например 2026-08-27T06:00:00Z

OFFSET=$(TZ=Europe/Moscow date -d "$SLOT" +%Y-%m-%dT%H:%M:%S%z \
  | sed -E 's/([+-][0-9]{2})([0-9]{2})$/\1:\2/')
echo "OFFSET=$OFFSET"                              # например 2026-08-27T09:00:00+03:00

curl -s -X POST $BASE/bookings -H 'Content-Type: application/json' \
  -d "{\"eventTypeId\":\"strizhka\",\"start\":\"$OFFSET\",\"guest\":{\"name\":\"Пётр Петров\",\"email\":\"petr@example.com\"}}"
# → 201, и start в ответе нормализован в UTC: равен $SLOT (тот же момент времени)
```

### 2.6 Бронирование без смещения пояса → 400, а не 500

```bash
NAIVE=${SLOT%Z}                                   # убираем 'Z' — время без смещения
curl -s -w '\n%{http_code}\n' -X POST $BASE/bookings -H 'Content-Type: application/json' \
  -d "{\"eventTypeId\":\"strizhka\",\"start\":\"$NAIVE\",\"guest\":{\"name\":\"Иван\",\"email\":\"ivan@example.com\"}}"
# → 400 {"code":"validation_failed", ...} — раньше был 500 (краш сервера)
```

### 2.7 Старт не на сетке → 400

```bash
OFFGRID=$(echo "$SLOT" | sed -E 's/(T[0-9]{2}):[0-9]{2}(:[0-9]{2}Z)/\1:15\2/')   # минуты в :15 — вне сетки
curl -s -w '\n%{http_code}\n' -X POST $BASE/bookings -H 'Content-Type: application/json' \
  -d "{\"eventTypeId\":\"strizhka\",\"start\":\"$OFFGRID\",\"guest\":{\"name\":\"Иван\",\"email\":\"ivan@example.com\"}}"
# → 400 {"code":"validation_failed", ...}
```

### 2.8 Конфликт: две заявки на один слот → одна 201, вторая 409

```bash
curl -s -o /dev/null -w '%{http_code}\n' -X POST $BASE/bookings -H 'Content-Type: application/json' \
  -d "{\"eventTypeId\":\"strizhka\",\"start\":\"$SLOT\",\"guest\":{\"name\":\"Пётр Петров\",\"email\":\"petr@example.com\"}}"
# → 201 (занял слот)

curl -s -w '\n%{http_code}\n' -X POST $BASE/bookings -H 'Content-Type: application/json' \
  -d "{\"eventTypeId\":\"strizhka\",\"start\":\"$SLOT\",\"guest\":{\"name\":\"Мария Иванова\",\"email\":\"maria@example.com\"}}"
# → 409 {"code":"slot_unavailable", ...}
```

### 2.9 Лимиты длины полей → 400

```bash
# Название длиннее 200 символов
LONG_NAME=$(printf 'a%.0s' {1..201})
curl -s -w '\n%{http_code}\n' -X POST $BASE/event-types -H 'Content-Type: application/json' \
  -d "{\"id\":\"long-name\",\"name\":\"$LONG_NAME\",\"description\":\"\",\"durationInMinutes\":30}"
# → 400

# Slug длиннее 100 символов
LONG_SLUG=$(printf 'a%.0s' {1..101})
curl -s -w '\n%{http_code}\n' -X POST $BASE/event-types -H 'Content-Type: application/json' \
  -d "{\"id\":\"$LONG_SLUG\",\"name\":\"Тест\",\"description\":\"\",\"durationInMinutes\":30}"
# → 400

# Комментарий гостя длиннее 2000 символов
LONG_COMMENT=$(printf 'c%.0s' {1..2001})
curl -s -w '\n%{http_code}\n' -X POST $BASE/bookings -H 'Content-Type: application/json' \
  -d "{\"eventTypeId\":\"strizhka\",\"start\":\"$SLOT\",\"guest\":{\"name\":\"Иван\",\"email\":\"ivan@example.com\",\"comment\":\"$LONG_COMMENT\"}}"
# → 400
```

Контрактные лимиты: slug 100, название типа события 200, описание 2000,
имя гостя 200, email 320, комментарий 2000.

### 2.10 Ограничение тела запроса: 64 КиБ

Тело больше 64 КиБ отклоняется ещё до разбора. Кладите большой JSON в файл —
передавать 2 МБ через аргумент командной строки `curl -d "…"` нельзя (упрётесь
в лимит длины argv):

```bash
python3 -c "import json; print(json.dumps({'id':'huge','name':'x'*(2*1024*1024),'description':'','durationInMinutes':30}))" > /tmp/huge.json
curl -s -w '\n%{http_code}\n' -X POST $BASE/event-types -H 'Content-Type: application/json' --data @/tmp/huge.json
# → 400 {"code":"validation_failed", ...}

# Контроль: тело меньше лимита, но с полем-«мусором», которое модель игнорирует, — проходит
python3 -c "import json; print(json.dumps({'id':'small','name':'Тест','description':'','durationInMinutes':30,'pad':'x'*(50*1024)}))" > /tmp/small.json
curl -s -w '\n%{http_code}\n' -X POST $BASE/event-types -H 'Content-Type: application/json' --data @/tmp/small.json
# → 201
```

### 2.11 Список предстоящих записей (владелец)

```bash
curl -s $BASE/bookings | jq
# → записи, созданные выше, по возрастанию времени начала; прошлые не выводятся
```

---

## Чек-лист изменений «review hardening»

| Проверка | Ожидание |
| --- | --- |
| `durationInMinutes: true` | 400 `validation_failed` (не 201, не приведение к 1) |
| `durationInMinutes: 60.0` | 400 `validation_failed` |
| старт без смещения пояса | 400 `validation_failed` (не 500) |
| старт со смещением `+03:00` | 201, в ответе UTC |
| слоты 60-минутного типа | шаг 30 минут (09:00, 09:30, …) |
| слоты 45-минутного типа | старты всё равно на получасовой сетке |
| старт не на сетке (`:15`) | 400 `validation_failed` |
| две заявки на один слот | 201 и 409 `slot_unavailable` |
| поля длиннее лимитов | 400 `validation_failed` |
| тело > 64 КиБ | 400 `validation_failed` |
| две вкладки на один слот | первая — «Вы записаны», вторая — конфликт без успеха |
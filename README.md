# Лабораторна робота №4: E-Commerce Order Service

Модульне ядро сервісу замовлень E-Commerce Cloud Platform на Python 3.10+.
Продовження предметної області та сценарію CreateOrder із лабораторної №3.
Використано лише стандартну бібліотеку: встановлення пакетів не потрібне.

## Швидкий запуск

Відкрийте термінал у цій папці. На Windows замість `python` можна використати `py -3`.

```powershell
python -m unittest discover -s tests -v
python tools/check_architecture.py
python -m src.WebAPI.bootstrap
```

Демонстрація повертає 201, totalAmount=199.98 і status=NEW для двох товарів
по 99.99. Ідентифікатор замовлення і час генеруються під час запуску.
Остання команда працює без мережі; для справжнього HTTP-запиту:

```powershell
python -m src.WebAPI.bootstrap --serve --port 8000
```

В іншому терміналі PowerShell:

```powershell
$orderJson = Get-Content -LiteralPath ./examples/create_order.json -Raw
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/orders -ContentType 'application/json' -Body $orderJson
```

Зупинка: Ctrl+C. Сховище in-memory діє лише до завершення процесу.

## Що реалізовано

Чотири шари: Domain, Application, Infrastructure, WebAPI.
Сценарій CreateOrder отримує OrderRepository, Clock і IdGenerator через
конструктор. Домен перевіряє замовлення й обчислює суму; контролер
перетворює JSON/DTO та відповіді. Композиційний корінь реєструє
Transient, Scoped та Singleton із поясненням кожного вибору.

Реалізовано один потрібний для ЛР №4 сценарій: **POST /orders**.
Копії повних контрактів ЛР №3 збережено в `docs/contracts_lab3/`
як першоджерела. Інші REST-операції та gRPC-host у цій роботі не реалізовано.
Автентифікація залишається відповідальністю майбутнього API Gateway;
цей локальний навчальний host її не виконує.

## Перевірки та звіт

- `docs/clean_architecture_report.md` — звіт за шаблоном та відповіді для захисту.
- `docs/clean_architecture_report.pdf` — PDF-версія звіту для перегляду й друку.
- `docs/test_run.txt` — фактичний успішний прогін 33 тестів.
- `docs/isolated_test_run.txt` — 12 тестів сценарію без імпорту Infrastructure/WebAPI.
- `docs/architecture_check.txt` — перевірка напрямку залежностей.
- `docs/demo_run.json.txt` — результат демонстрації через повний граф DI.
- `docs/http_smoke_test.txt` — окрема інтеграційна перевірка HTTP.
- `docs/contracts_lab3/README.md` — походження контрактів і межі реалізації.

Модульні тести не запускають сервер, не використовують БД, сокети або файли даних.
Контракти й архітектуру аналізує окремий інструмент поза модульними тестами.
HTTP smoke test відкриває лише локальний сокет і не входить у модульний набір.

Окремий запуск інтеграційної перевірки:

```powershell
python tools/http_smoke.py
```

Локальний Git-репозиторій включено в ZIP разом із прихованою папкою `.git`.
Тег `lr4` вказує на адаптовану версію сервісу замовлень.

```powershell
git status --short
git show lr4 --stat
```

Перед здачею впишіть у звіт ПІБ, групу та URL, якщо публікуватимете
репозиторій. Ці дані не були надані; віддалений репозиторій не створювався.

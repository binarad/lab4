# Контракти ЛР №3: походження і межі

Точні копії прочитаних локальних файлів:

- `C:/Users/pozhi/Downloads/lab3_ecommerce_architecture/api/openapi.yaml`
- `C:/Users/pozhi/Downloads/lab3_ecommerce_architecture/api/service.proto`

Оригінали у Downloads не змінювалися. Контракти збережено повністю,
включно з іншими операціями Order Service; це довідкові першоджерела,
а не перелік усіх можливостей реалізованого host ЛР №4.

## Реалізована частина

Сценарій CreateOrder і REST POST /orders. Збережено customerId, items,
shippingAddress та модель Order у відповіді. Обмеження масиву, кількості,
назв і адреси перенесено в доменні типи. Значення totalAmount і статус NEW
формуються сервером. Числова точність у Domain базується на Decimal;
JSON-відповідь використовує число double вихідного контракту.

Домен додатково відхиляє суто пробільні тексти. Host підтримує 503 для
збою порту, 413 для завеликого тіла, 415 для неправильного Content-Type.
Ці відповіді слід додати до повного OpenAPI при подальшому розвитку контракту.
Автентифікація зі згаданого в контракті API Gateway/OIDC тут не реалізована.

## Перевірка копій

- `openapi.yaml`: SHA-256 `2bb548c80cbe03918f4d6f9b2176b19bd5fc50483734a2cbe7b798cbe26b8748`
- `service.proto`: SHA-256 `350517839cc257a2ccfe8c015df32b8df322886e472d5b2e6ce6493ba0d088da`

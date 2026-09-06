# Dropbox Sign Connector — Connector Discovery

**Official Documentation:** https://sign.dropbox.com  
**Base URL:** https://api.hellosign.com/v3  
**Auth Model:** API Key (HTTP Basic) или OAuth 2.0 Bearer  

## Основные сущности вендора
- запросы на подпись (/signature_request), шаблоны (/template), встроенные ссылки (/embedded), аккаунты

## Лимиты и особенности API
- Соблюдение Rate Limits вендора, обработка HTTP 429 с экспоненциальным backoff.
- Валидация входных данных по Pydantic-схемам вендора до отправки запроса.
- Тестовая точка проверки подключения: `GET /v3/account`.

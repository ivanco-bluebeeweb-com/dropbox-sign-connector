# Dropbox Sign Connector — Auth & Credentials Standard

**Compliance:** AUTH_AND_CREDENTIALS_STANDARD.md (B1–B10)

## Схема аутентификации
- **Метод:** API Key (HTTP Basic) или OAuth 2.0 Bearer
- **Хранение:** Секреты сохраняются изолированно в хранилище секретов платформы Imperal.
- **Валидация:** При сохранении ключа выполняется тестовый запрос `GET /v3/account`.
- **Отключение:** Удаление локальных ключей без воздействия на аккаунт вендора.

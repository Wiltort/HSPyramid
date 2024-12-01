# HSPyramid
Реферальная система
## Описание API
API предоставляет функционал для регистрации пользователей, верификации и управления реферальной системой. Пользователи могут регистрироваться с использованием номера телефона, подтверждать свои аккаунты и использовать инвайт-коды для приглашения других пользователей.
>### Эндпойнты
* URL: /register/
    * Метод: POST
    * Описание: Регистрирует пользователя, отправляя код верификации на указанный номер телефона.
    * Тело запроса:
    ```json
    {
    "phone_number": "string"
    }
   ```
    * Ответы:
         * 200 OK: Verification code sent.
         * 400 Bad Request: Phone number is required.
* URL: /verify/
   * Метод: POST
   * Описание: Подтверждает номер телефона пользователя с использованием кода верификации.
   * Тело запроса:
  ```json
  {
  "phone_number": "string",
  "verification_code": "string"
   }
  ```
   * Ответы:
      * 200 OK: Returns an authentication token.
      * 400 Bad Request: Phone number or verification code is required, or the verification code is invalid.
* URL: /profile/
   * Методы: GET, PUT
   * Описание: Получает или обновляет профиль пользователя.
   * GET Запрос:
        * Ответ: Возвращает данные профиля пользователя.
        * PUT Запрос:
        * Тело запроса:
          ```json
          {
          "invite_code": "string"
          }
         ```
         * Ответы:
            * 200 OK: Обновляет поле referred_by пользователя, если инвайт-код действителен.
            * 400 Bad Request: Инвайт-код обязателен, недействителен или пользователь уже использовал инвайт-код.

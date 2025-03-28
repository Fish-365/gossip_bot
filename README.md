# 🛡️ Telegram Бот для Модерации 🤖

Этот Telegram бот разработан для облегчения модерации контента в Telegram каналах 📢 с упором на анонимность пользователей 👤. Пользователи могут отправлять посты 📝 для публикации, которые затем проверяются модераторами 👮‍♂️ перед публикацией в основном канале.

## Функциональность ⚙️

*   **Отправка Постов:** Пользователи могут легко отправлять текст 💬, фотографии 🖼️, видео 📹 и другие медиафайлы 📁 для рассмотрения к публикации в подключенном Telegram канале.
*   **Очередь Модерации:** Отправленные посты направляются в выделенный канал модерации 🕵️‍♂️ для проверки администраторами.
*   **Инструменты Модерации для Администраторов:** Администраторы имеют команды в канале модерации для:
    *   **Одобрения Постов:** ✅ Публикация одобренных постов в основном канале.
    *   **Отклонения Постов:** ❌ Отклонение постов, не соответствующих правилам канала.
    *   **Управления Администраторами:** ➕ Добавление или ➖ удаление других пользователей в качестве администраторов бота.
    *   **Блокировки/Разблокировки Пользователей:** 🚫 Блокировка или 🔓 разблокировка пользователей для отправки постов.
    *   **Установки Порога Токсичности:** 🧪 Настройка порога для автоматического обнаружения токсичного контента (если эта функция включена).
    *   **Скачивания Базы Данных:** 💾 (Только для администраторов) Скачивание резервной копии базы данных бота для создания дампов.
    *   **Просмотра Списка Администраторов и Заблокированных Пользователей:** 📜 (Только для администраторов) Просмотр списков текущих администраторов и заблокированных пользователей (с использованием анонимизированных идентификаторов).

## Меры по Обеспечению Анонимности 🔒

Этот бот разработан с учетом конфиденциальности пользователей 🔑. Для обеспечения анонимности реализованы следующие меры:

*   **Идентификация Пользователей на Основе Ключа:** Вместо хранения Telegram User IDs (`tg_id`) и имен пользователей напрямую в базе данных 🗄️, бот использует уникальный, анонимизированный `key_user` 🔑 для каждого пользователя.
*   **Генерация `key_user`:** `key_user` генерируется с использованием безопасного хеша 🔐 имени пользователя Telegram, их `tg_id` и секретного, случайно сгенерированного слова (`SECRET_WORD`). Этот `SECRET_WORD` 🤫 **не хранится в коде и должен быть установлен как переменная окружения 🌍 для безопасности.**
*   **Отсутствие Хранения `tg_id` или Имени Пользователя:** База данных бота 🚫 **не хранит** Telegram User IDs или имена пользователей после первоначального процесса регистрации. Хранится только `key_user` 🔑, статус пользователя (одобрен, администратор, заблокирован), режим модерации и контент поста 📝.
*   **Одностороннее Хеширование:** При генерации `key_user` используется односторонний алгоритм хеширования (SHA256). Это означает, что вычислительно невозможно 🤯 обратить этот процесс и извлечь исходное имя пользователя или `tg_id` из `key_user`, даже если база данных скомпрометирована.
*   **Списки Администраторов с Анонимизированными Идентификаторами:** Когда администраторы просматривают списки администраторов или заблокированных пользователей, им предоставляются идентификаторы `key_user`, что дополнительно защищает связь между учетными записями Telegram и записями в базе данных. Имена пользователей не отображаются в этих списках внутри интерфейса бота.
 
 
> бот написан специально для канала "Подслушано 1474" \
>  v1.0 stable 

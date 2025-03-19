import aiosqlite
import telebot
from telebot.async_telebot import AsyncTeleBot
from telebot import types
import asyncio
import text_classification
import os
import hashlib

DB_NAME = "db.db"
BOT_TOKEN = ''  # bot token
MODERATION_CHANNEL_ID = ''  # moderation channel id
CHANNEL_ID = ''  # channel id
SUPER_ADMIN_ID = 0000000000
SECRET_WORD = os.environ.get('SECRET_WORD', 'default_secret_word')

def generate_key_user(username, tg_id, secret_word):
    """Генерирует ключ пользователя."""
    combined_string = username + secret_word + str(tg_id)
    hashed_string = hashlib.sha256(combined_string.encode()).hexdigest()
    return hashed_string

# Регистрация новых пользователей
async def register_users(key_user, status='approved'): # Принимаем key_user при регистрации
    """Регистрирует новых пользователей, используя key_user."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO Users (key_user, status) VALUES (?, ?)", (key_user, status))
        await db.commit()

# Добавление сообщения в базу данных
async def add_message(key_user, message, toxicity_score, status, message_id):
    """Добавляет сообщение в базу данных, используя key_user."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO Messages (key_user, message, toxicity_score, status, message_id) VALUES (?, ?, ?, ?, ?)", (key_user, message, toxicity_score, status, message_id))
        await db.commit()

# Изменение статуса сообщения
async def change_status_message(message_id, status):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE Messages SET status = ? WHERE message_id = ?", (status, message_id))
        await db.commit()

# Получение key_user пользователя по message_id
async def get_user_key_by_message_id(message_id):
    """Получает key_user пользователя по message_id."""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT key_user FROM Messages WHERE message_id = ?", (message_id,)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else None

# Получение статуса и режима пользователя по key_user
async def get_user_status_and_regime_by_key(key_user):
    """Получает статус и режим пользователя по key_user."""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT status, regime FROM Users WHERE key_user = ?", (key_user,)) as cursor:
            return await cursor.fetchone()

# Изменение статуса пользователя по key_user
async def change_status_user_by_key(key_user, status):
    """Изменяет статус пользователя по key_user."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE Users SET status = ? WHERE key_user = ?", (status, key_user))
        await db.commit()

# Изменение режима пользователя по key_user
async def change_user_regime_by_key(key_user, regime):
    """Изменяет режим пользователя по key_user."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE Users SET regime = ? WHERE key_user = ?", (regime, key_user))
        await db.commit()

# Изменение уровня токсичности
async def change_toxicity_level(level):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE Config SET toxicity_level = ?", (level,))
        await db.commit()

# Получение уровня токсичности
async def get_toxicity_level():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT toxicity_level FROM Config") as cursor:
            return await cursor.fetchone()

# Получение data base
async def get_db():
    async with aiosqlite.connect(DB_NAME) as db:
        return db

# Получение всех администраторов (теперь по key_user)
async def get_all_admins():
    """Получает всех администраторов (возвращает key_user)."""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT key_user FROM Users WHERE status = 'admin'") as cursor:
            return await cursor.fetchall()

# Добавление администратора (по username, но сохраняем key_user)
async def add_admin(tg_username, bot):
    """Добавляет администратора, используя username и сохраняя key_user."""
    user = await bot.get_chat(tg_username)
    if user:
        key_user = generate_key_user(tg_username, user.id, SECRET_WORD)
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("UPDATE Users SET status = 'admin' WHERE key_user = ?", (key_user,))
            await db.commit()
        return key_user
    return None

# Удаление администратора (по username, но удаляем по key_user)
async def remove_admin(tg_username, bot):
    """Удаляет администратора, используя username и удаляя по key_user."""
    user = await bot.get_chat(tg_username)
    if user:
        key_user = generate_key_user(tg_username, user.id, SECRET_WORD)
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("UPDATE Users SET status = 'approved' WHERE key_user = ?", (key_user,))
            await db.commit()
        return key_user
    return None

# Получение списка заблокированных пользователей (теперь по key_user)
async def get_banned_users():
    """Получает список заблокированных пользователей (возвращает key_user)."""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT key_user FROM Users WHERE status = 'blocked'") as cursor:
            return await cursor.fetchall()

async def send_admin_notification(bot, key_user_admin, text):
    """Отправляет уведомление администраторам (теперь по key_user админа)."""
    admins = await get_all_admins()
    for admin_key_user_tuple in admins:
        admin_key_user = admin_key_user_tuple[0]


async def main():
    # Создание бота
    bot = AsyncTeleBot(BOT_TOKEN)

    # Команда для скачивания базы данных (только для админов)
    @bot.message_handler(commands=['download_db'])
    async def download_db(message):
        key_user = generate_key_user(message.from_user.username, message.chat.id, SECRET_WORD)
        status_regime = await get_user_status_and_regime_by_key(key_user)
        if message.chat.id == SUPER_ADMIN_ID or (status_regime and status_regime[0] == 'admin'):
            await bot.send_document(message.chat.id, open(DB_NAME, 'rb'))
        else:
            await bot.send_message(message.chat.id, "У вас нет прав на выполнение этой команды.")

    # Команда для получения списка админов
    @bot.message_handler(commands=['list_admins'])
    async def list_admins(message):
        key_user = generate_key_user(message.from_user.username, message.chat.id, SECRET_WORD)
        status_regime = await get_user_status_and_regime_by_key(key_user)
        if message.chat.id == SUPER_ADMIN_ID or (status_regime and status_regime[0] == 'admin'):
            admins_key_users = await get_all_admins()
            if admins_key_users:
                admin_list = ""
                for admin_key_user_tuple in admins_key_users:
                    admin_key_user = admin_key_user_tuple[0]

                    admin_list += f"key_user: {admin_key_user}\n"
                await bot.send_message(message.chat.id, f"Список администраторов:\n{admin_list}")
            else:
                await bot.send_message(message.chat.id, "Список администраторов пуст.")
        else:
            await bot.send_message(message.chat.id, "У вас нет прав на выполнение этой команды.")

    # Команда для получения списка заблокированных пользователей
    @bot.message_handler(commands=['ban_user_list'])
    async def ban_user_list(message):
        key_user = generate_key_user(message.from_user.username, message.chat.id, SECRET_WORD)
        status_regime = await get_user_status_and_regime_by_key(key_user)
        if message.chat.id == SUPER_ADMIN_ID or (status_regime and status_regime[0] == 'admin'):
            banned_key_users = await get_banned_users()
            if banned_key_users:
                banned_list = ""
                for banned_key_user_tuple in banned_key_users:
                    banned_key_user = banned_key_user_tuple[0]

                    banned_list += f"key_user: {banned_key_user}\n"
                await bot.send_message(message.chat.id, f"Список заблокированных пользователей:\n{banned_list}")
            else:
                await bot.send_message(message.chat.id, "Список заблокированных пользователей пуст.")
        else:
            await bot.send_message(message.chat.id, "У вас нет прав на выполнение этой команды.")

    # Обработчик команды /start
    @bot.message_handler(commands=['start'])
    async def start(message):
        key_user = generate_key_user(message.from_user.username, message.chat.id, SECRET_WORD)
        user_status_regime_by_key = await get_user_status_and_regime_by_key(key_user)

        # Если пользователь не зарегистрирован
        if user_status_regime_by_key is None: # Проверяем, есть ли key_user в базе
            # Приветствие и создание клавиатуры
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            button = types.KeyboardButton('написать пост')
            markup.add(button)

            await bot.send_message(message.chat.id, "Добро пожаловать! Нажмите кнопку ниже, чтобы написать пост.", reply_markup=markup)

            await register_users(key_user)
            return

        # Если пользователь зарегистрирован
        if user_status_regime_by_key and user_status_regime_by_key[0] in ['approved', 'admin']:
            # Создание клавиатуры
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            button = types.KeyboardButton('написать пост')
            markup.add(button)

            # Добавляем админские кнопки, если пользователь - админ
            if user_status_regime_by_key[0] == 'admin' or message.chat.id == SUPER_ADMIN_ID:
                admin_button1 = types.KeyboardButton('удалить админестратора')
                admin_button2 = types.KeyboardButton('добавить админестратора')
                admin_button3 = types.KeyboardButton('задать порог токсичности')
                admin_button4 = types.KeyboardButton('заблокировать пользователя')
                admin_button5 = types.KeyboardButton('разблокировать пользователя')
                markup.add(admin_button1, admin_button2, admin_button3, admin_button4, admin_button5)

                await bot.send_message(message.chat.id, "Здравствуйте, администратор! Вот ваши команды:\n/list_admins - список админов\n/download_db - скачать базу данных\n/ban_user_list - список заблокированных пользователей", reply_markup=markup)
            else:
                await bot.send_message(message.chat.id, "Вы уже зарегистрированы! Нажмите кнопку ниже, чтобы написать пост.", reply_markup=markup)
            return

        # Если пользователь заблокирован
        elif user_status_regime_by_key and user_status_regime_by_key[0] == 'blocked':
            await bot.send_message(message.chat.id, "Вы заблокированы! Обратитесь к администратору.")
            return


    # Обработчик ответов на сообщения в канале модерации
    @bot.message_handler(func=lambda message: message.reply_to_message is not None and message.chat.id == int(MODERATION_CHANNEL_ID), content_types=['text'])
    async def handle_reply(message):
        await bot.send_message(message.chat.id, "Ответ сохранен в moderation channel (пользователю не отправлено).")


    # Обработчик нажатия кнопки "написать пост"
    @bot.message_handler(func=lambda message: message.text == 'написать пост')
    async def write_post(message):
        key_user = generate_key_user(message.from_user.username, message.chat.id, SECRET_WORD)
        user_status_regime = await get_user_status_and_regime_by_key(key_user)
        # Если пользователь зарегистрирован
        if user_status_regime and user_status_regime[0] in ['approved', 'admin']:
            # создание кнопки для отмены
            markup = types.InlineKeyboardMarkup()
            approve_button = types.InlineKeyboardButton("Отмена", callback_data=f"set-regime_{key_user}")
            markup.add(approve_button)

            await bot.send_message(message.chat.id, "Введите текст поста.", reply_markup=markup)
            await change_user_regime_by_key(key_user, 'send_message')
            return

        # Если пользователь не зарегистрирован
        if not user_status_regime: # Проверяем, есть ли key_user в базе
            await bot.send_message(message.chat.id, "Вы не зарегистрированы! Нажмите /start для регистрации.")
            return

        # Если пользователь заблокирован
        elif user_status_regime and user_status_regime[0] == 'blocked':
            await bot.send_message(message.chat.id, "Вы заблокированы! Обратитесь к администратору.")
            return

        else:
            await bot.send_message(message.chat.id, "Ошибка")
            return

    # Обработчик нажатия кнопки "удалить админестратора"
    @bot.message_handler(func=lambda message: message.text == 'удалить админестратора')
    async def remove_admin_handler(message):
        key_user = generate_key_user(message.from_user.username, message.chat.id, SECRET_WORD)
        status_regime = await get_user_status_and_regime_by_key(key_user)
        if status_regime and status_regime[0] == 'admin' or message.chat.id == SUPER_ADMIN_ID:
            markup = types.InlineKeyboardMarkup()
            cancel_button = types.InlineKeyboardButton("Отмена", callback_data=f"set-regime_{key_user}")
            markup.add(cancel_button)

            await bot.send_message(message.chat.id, "Введите username администратора, которого хотите удалить.", reply_markup=markup)
            await change_user_regime_by_key(key_user, 'remove_admin')
        else:
            await bot.send_message(message.chat.id, "У вас нет прав на выполнение этой команды.")

    # Обработчик нажатия кнопки "добавить админестратора"
    @bot.message_handler(func=lambda message: message.text == 'добавить админестратора')
    async def add_admin_handler(message):
        key_user = generate_key_user(message.from_user.username, message.chat.id, SECRET_WORD)
        status_regime = await get_user_status_and_regime_by_key(key_user)
        if status_regime and status_regime[0] == 'admin' or message.chat.id == SUPER_ADMIN_ID:
            markup = types.InlineKeyboardMarkup()
            cancel_button = types.InlineKeyboardButton("Отмена", callback_data=f"set-regime_{key_user}")
            markup.add(cancel_button)

            await bot.send_message(message.chat.id, "Введите username администратора, которого хотите добавить.", reply_markup=markup)
            await change_user_regime_by_key(key_user, 'add_admin')
        else:
            await bot.send_message(message.chat.id, "У вас нет прав на выполнение этой команды.")

    # Обработчик нажатия кнопки "задать порог токсичности"
    @bot.message_handler(func=lambda message: message.text == 'задать порог токсичности')
    async def set_toxicity_level_handler(message):
        key_user = generate_key_user(message.from_user.username, message.chat.id, SECRET_WORD)
        status_regime = await get_user_status_and_regime_by_key(key_user)
        if status_regime and status_regime[0] == 'admin' or message.chat.id == SUPER_ADMIN_ID:
            markup = types.InlineKeyboardMarkup()
            cancel_button = types.InlineKeyboardButton("Отмена", callback_data=f"set-regime_{key_user}")
            markup.add(cancel_button)

            await bot.send_message(message.chat.id, "Введите новый порог токсичности (от 0 до 1).", reply_markup=markup)
            await change_user_regime_by_key(key_user, 'set_toxicity')
        else:
            await bot.send_message(message.chat.id, "У вас нет прав на выполнение этой команды.")

    # Обработчик нажатия кнопки "заблокировать пользователя"
    @bot.message_handler(func=lambda message: message.text == 'заблокировать пользователя')
    async def ban_user_handler(message):
        key_user = generate_key_user(message.from_user.username, message.chat.id, SECRET_WORD)
        status_regime = await get_user_status_and_regime_by_key(key_user)
        if status_regime and status_regime[0] == 'admin' or message.chat.id == SUPER_ADMIN_ID:
            markup = types.InlineKeyboardMarkup()
            cancel_button = types.InlineKeyboardButton("Отмена", callback_data=f"set-regime_{key_user}")
            markup.add(cancel_button)

            await bot.send_message(message.chat.id, "Введите username пользователя, которого хотите заблокировать.", reply_markup=markup)
            await change_user_regime_by_key(key_user, 'ban_user')
        else:
            await bot.send_message(message.chat.id, "У вас нет прав на выполнение этой команды.")

    # Обработчик нажатия кнопки "разблокировать пользователя"
    @bot.message_handler(func=lambda message: message.text == 'разблокировать пользователя')
    async def unban_user_handler(message):
        key_user = generate_key_user(message.from_user.username, message.chat.id, SECRET_WORD)
        status_regime = await get_user_status_and_regime_by_key(key_user)
        if status_regime and status_regime[0] == 'admin' or message.chat.id == SUPER_ADMIN_ID:
            markup = types.InlineKeyboardMarkup()
            cancel_button = types.InlineKeyboardButton("Отмена", callback_data=f"set-regime_{key_user}")
            markup.add(cancel_button)

            await bot.send_message(message.chat.id, "Введите username пользователя, которого хотите разблокировать.", reply_markup=markup)
            await change_user_regime_by_key(key_user, 'unban_user')
        else:
            await bot.send_message(message.chat.id, "У вас нет прав на выполнение этой команды.")

    # Обработчик текстовых сообщений
    @bot.message_handler(content_types=['text'])
    async def handle_text(message):
        # Получение статуса и режима пользователя
        key_user = generate_key_user(message.from_user.username, message.chat.id, SECRET_WORD)
        status_regime = await get_user_status_and_regime_by_key(key_user)

        if not status_regime: # Проверяем, есть ли key_user в базе
            await bot.send_message(message.chat.id, "Вы не зарегистрированы. Нажмите /start") # User is not in DB at all
            return

        status = status_regime[0] if status_regime else None
        regime = status_regime[1] if status_regime else None


        if status == 'blocked':
            await bot.send_message(message.chat.id, "Вы заблокированы! Обратитесь к администратору.")
            return

        # Если режим пользователя "send_message"
        if regime == 'send_message':
            # Изменение режима пользователя
            await change_user_regime_by_key(key_user, None)

            # Получение уровня токсичности
            # toxicity_level = await get_toxicity_level()
            # Классификация текста
            toxicity_score = await text_classification.classify_text(message.text)

            # Если уровень токсичности меньше установленного
            if False: # toxicity_score < toxicity_level[0]
                # отправка сообщения сразу в основной канал
                sent_message = await bot.send_message(CHANNEL_ID, message.text)
                await add_message(key_user, message.text, toxicity_score, 'approved', sent_message.message_id)
                await bot.send_message(message.chat.id, "Ваш пост был автоматически опубликован ботом!")

                await bot.send_message(MODERATION_CHANNEL_ID, f"Автоматически опубликованный пост: \n\n{message.text} \n\nТоксичность поста: {round(toxicity_score, 3)}")
                return

            else:
                # Отправка сообщения в канал модерации от имени бота
                sent_message = await bot.copy_message(MODERATION_CHANNEL_ID, message.chat.id, message.message_id)
                await add_message(key_user, message.text, toxicity_score, 'not_approved', sent_message.message_id)

                # Добавление кнопок "одобрить" и "отклонить"
                markup = types.InlineKeyboardMarkup()
                approve_button = types.InlineKeyboardButton("Одобрить", callback_data=f"approve_{sent_message.message_id}_{message.message_id}")
                reject_button = types.InlineKeyboardButton("Отклонить", callback_data=f"reject_{sent_message.message_id}_{message.message_id}")
                markup.add(approve_button, reject_button)
                await bot.edit_message_reply_markup(MODERATION_CHANNEL_ID, sent_message.message_id, reply_markup=markup)



                await bot.send_message(message.chat.id, "Ваш пост отправлен на модерацию и будет опубликован после проверки.")
                return

        # Если режим пользователя "remove_admin"
        if regime == 'remove_admin':
            try:
                removed_admin_username = message.text.strip()
                if removed_admin_username.startswith('@'):
                    removed_admin_username = removed_admin_username[1:]

                # Check if user exists (by username for admin input)
                user_to_remove = await bot.get_chat(removed_admin_username)
                if not user_to_remove:
                    await bot.send_message(message.chat.id, f"Пользователь @{removed_admin_username} не найден.")
                    return

                removed_admin_key_user = generate_key_user(removed_admin_username, user_to_remove.id, SECRET_WORD)
                await remove_admin(removed_admin_username, bot)
                await bot.send_message(message.chat.id, f"Администратор @{removed_admin_username} был удален.")
                admin_key_user = generate_key_user(message.from_user.username, message.chat.id, SECRET_WORD)

            except Exception as e:
                await bot.send_message(message.chat.id, f"Не удалось удалить администратора: {e}")
            finally:
                key_user = generate_key_user(message.from_user.username, message.chat.id, SECRET_WORD)
                await change_user_regime_by_key(key_user, None)
            return

        # Если режим пользователя "add_admin"
        if regime == 'add_admin':
            try:
                added_admin_username = message.text.strip()
                if added_admin_username.startswith('@'):
                    added_admin_username = added_admin_username[1:]

                # Check if user exists (by username for admin input)
                user_to_add = await bot.get_chat(added_admin_username)
                if not user_to_add:
                    await bot.send_message(message.chat.id, f"Пользователь @{added_admin_username} не найден.")
                    return


                added_admin_key_user = await add_admin(added_admin_username, bot) # add_admin now takes username and bot object
                if added_admin_key_user:
                    await bot.send_message(message.chat.id, f"Администратор @{added_admin_username} был добавлен.")
                    admin_key_user = generate_key_user(message.from_user.username, message.chat.id, SECRET_WORD)
                else:
                    await bot.send_message(message.chat.id, f"Не удалось добавить администратора @{added_admin_username}.")


            except Exception as e:
                await bot.send_message(message.chat.id, f"Не удалось добавить администратора: {e}")
            finally:
                key_user = generate_key_user(message.from_user.username, message.chat.id, SECRET_WORD)
                await change_user_regime_by_key(key_user, None)
            return

        # Если режим пользователя "set_toxicity"
        if regime == 'set_toxicity':
            try:
                level = float(message.text)
                if 0 <= level <= 1:
                    await change_toxicity_level(level)
                    await bot.send_message(message.chat.id, f"Порог токсичности был изменен на {level}.")
                    admin_key_user = generate_key_user(message.from_user.username, message.chat.id, SECRET_WORD)
                else:
                    await bot.send_message(message.chat.id, "Порог токсичности должен быть от 0 до 1.")
            except ValueError:
                await bot.send_message(message.chat.id, "Некорректный формат порога токсичности. Введите число от 0 до 1.")
            finally:
                key_user = generate_key_user(message.from_user.username, message.chat.id, SECRET_WORD)
                await change_user_regime_by_key(key_user, None)
            return

        # Если режим пользователя "ban_user"
        if regime == 'ban_user':
            try:
                banned_username = message.text.strip()
                if banned_username.startswith('@'):
                    banned_username = banned_username[1:]

                # Check if user exists (by username for admin input)
                user_to_ban = await bot.get_chat(banned_username)
                if not user_to_ban:
                    await bot.send_message(message.chat.id, f"Пользователь @{banned_username} не найден.")
                    return

                banned_user_key = generate_key_user(banned_username, user_to_ban.id, SECRET_WORD)

                user_status_regime_to_ban = await get_user_status_and_regime_by_key(banned_user_key)
                user_status_to_ban = user_status_regime_to_ban[0] if user_status_regime_to_ban else None
                user_id_to_ban = user_to_ban.id


                # Prevent banning admins and super admin
                if user_status_to_ban == 'admin' or int(user_id_to_ban) == SUPER_ADMIN_ID:
                    await bot.send_message(message.chat.id, "Нельзя заблокировать администратора")
                    return

                await change_status_user_by_key(banned_user_key, 'blocked')
                await bot.send_message(message.chat.id, f"Пользователь @{banned_username} был заблокирован.")

            except Exception as e:
                await bot.send_message(message.chat.id, f"Не удалось заблокировать пользователя: {e}")
            finally:
                key_user = generate_key_user(message.from_user.username, message.chat.id, SECRET_WORD)
                await change_user_regime_by_key(key_user, None)
            return

        # Если режим пользователя "unban_user"
        if regime == 'unban_user':
            try:
                unbanned_username = message.text.strip()
                if unbanned_username.startswith('@'):
                    unbanned_username = unbanned_username[1:]

                # Check if user exists (by username for admin input)
                user_to_unban = await bot.get_chat(unbanned_username)
                if not user_to_unban:
                    await bot.send_message(message.chat.id, f"Пользователь @{unbanned_username} не найден.")
                    return

                unbanned_user_key = generate_key_user(unbanned_username, user_to_unban.id, SECRET_WORD)

                await change_status_user_by_key(unbanned_user_key, 'approved')
                await bot.send_message(message.chat.id, f"Пользователь @{unbanned_username} был разблокирован.")

            except Exception as e:
                await bot.send_message(message.chat.id, f"Не удалось разблокировать пользователя: {e}")
            finally:
                key_user = generate_key_user(message.from_user.username, message.chat.id, SECRET_WORD)
                await change_user_regime_by_key(key_user, None)
            return

        else:
            await bot.send_message(message.chat.id, "Нажмите кнопку ниже, чтобы написать пост.")
            return

    # Обработчик всех остальных типов сообщений
    @bot.message_handler(content_types=['photo', 'video', 'document', 'audio', 'voice', 'video_note', 'sticker'])
    async def handle_media(message):
        # Получение статуса и режима пользователя
        key_user = generate_key_user(message.from_user.username, message.chat.id, SECRET_WORD)
        status_regime = await get_user_status_and_regime_by_key(key_user)

        if not status_regime: # Проверяем, есть ли key_user в базе
            await bot.send_message(message.chat.id, "Вы не зарегистрированы. Нажмите /start") # User is not in DB at all
            return

        status = status_regime[0] if status_regime else None
        regime = status_regime[1] if status_regime else None

        if status == 'blocked':
            await bot.send_message(message.chat.id, "Вы заблокированы! Обратитесь к администратору.")
            return

        # Если режим пользователя "send_message"
        if regime == 'send_message':
            # Изменение режима пользователя
            await change_user_regime_by_key(key_user, None)

            # Отправка сообщения в канал от имени бота
            sent_message = await bot.copy_message(MODERATION_CHANNEL_ID, message.chat.id, message.message_id)
            await add_message(key_user, message.caption if message.caption else '', None, 'not_approved', sent_message.message_id)

            # Добавление кнопок "одобрить" и "отклонить"
            markup = types.InlineKeyboardMarkup()
            approve_button = types.InlineKeyboardButton("Одобрить", callback_data=f"approve_{sent_message.message_id}_{message.message_id}")
            reject_button = types.InlineKeyboardButton("Отклонить", callback_data=f"reject_{sent_message.message_id}_{message.message_id}")
            markup.add(approve_button, reject_button)
            await bot.edit_message_reply_markup(MODERATION_CHANNEL_ID, sent_message.message_id, reply_markup=markup)


            await bot.send_message(message.chat.id, "Ваш пост отправлен на модерацию и будет опубликован после проверки.")
            return

        else:
            await bot.send_message(message.chat.id, "Нажмите кнопку ниже, чтобы написать пост.")
            return


    # Обработчик нажатий на кнопки "одобрить", "отклонить" и "Отменить"
    @bot.callback_query_handler(func=lambda call: call.data.startswith('approve_') or call.data.startswith('reject_') or call.data.startswith('set-regime_'))
    async def handle_callback(call):
        # Получение данных из callback
        args = call.data.split('_')

        if len(args) == 3:
            action, channel_message_id, message_id = args
            username = call.from_user.username
            key_user = await get_user_key_by_message_id(channel_message_id)


        else:
            action, key_user = args


        # Изменение статуса сообщения
        if action == 'approve':
            await change_status_message(channel_message_id, 'approved')
            await bot.send_message(call.message.chat.id, f"Одобрено ✅ @{username}", reply_to_message_id=call.message.message_id)
            # Больше не отправляем уведомления пользователю об одобрении для анонимности

            # Пересылка сообщения в канал
            await bot.copy_message(CHANNEL_ID, MODERATION_CHANNEL_ID, channel_message_id)

        elif action == 'reject':
            await change_status_message(channel_message_id, 'not_approved')
            await bot.send_message(call.message.chat.id, f"Отклонено ❌ @{username}", reply_to_message_id=call.message.message_id)
            # Больше не отправляем уведомления пользователю об отклонении для анонимности

        elif action == 'set-regime':
            await change_user_regime_by_key(key_user, None)
            await bot.send_message(call.message.chat.id, "Отменено")

        # Удаление кнопок
        await bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)


    try:
        await bot.polling()
    except Exception as e:
        print(e)

if __name__ == '__main__':
    asyncio.run(main())
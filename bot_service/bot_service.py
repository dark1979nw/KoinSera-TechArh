import os
import logging
import time
import asyncio
from datetime import datetime
import aiohttp
import asyncpg
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class BotService:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL', '')
        self.interval = int(os.getenv('SERVICE_INTERVAL', '30'))
        self.updates_lookback_hours = int(os.getenv('UPDATES_LOOKBACK_HOURS', '24'))  # Новый параметр
        self.pool = None

    async def init_db(self):
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(self.db_url)

        except Exception as e:

            raise

    async def get_all_data(self):
        """Get all required data from database"""
        try:
            async with self.pool.acquire() as conn:
                employees = await conn.fetch("""
                    SELECT * FROM employees
                """)
                chat_employees = await conn.fetch("""
                    SELECT * FROM chat_employees
                """)
                bots = await conn.fetch("""
                    SELECT * FROM bots WHERE is_active = true
                """)
                chats = await conn.fetch("""
                    SELECT * FROM chats
                """)
                return employees, chat_employees, bots, chats
        except Exception as e:
            logger.error(f"Failed to get data from database: {e}")
            return [], [], [], []

    async def get_chat_members_count(self, bot_token, chat_id):
        """Get number of members in chat"""

        try:
            url = f"https://api.telegram.org/bot{bot_token}/getChatMembersCount"
            params = {"chat_id": chat_id}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("ok"):
                            return data.get("result", 0)
                    return 0
        except Exception as e:
            return 0

    async def check_user_in_chat(self, bot_token, chat_id, user_id):
        """Check if user is in chat"""
        try:
            url = f"https://api.telegram.org/bot{bot_token}/getChatMember"
            params = {
                "chat_id": chat_id,
                "user_id": user_id
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("ok"):
                            return True
                    return False
        except Exception as e:
            logger.error(f"Error checking user in chat: {e}")
            return False

    async def send_welcome_message(self, bot_token, chat_id):
        """Send welcome message to new chat"""
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            params = {
                "chat_id": chat_id,
                "text": "Добрый день, я бот-консьерж. Я не читаю ваши сообщения и проверяю только наличие пользователей. Спишите мне пару слов"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("ok", False)
                    return False
        except Exception as e:
            logger.error(f"Error sending welcome message: {e}")
            return False

    async def get_chat_administrators(self, bot_token, chat_id, db_chat_id=None, user_id=None, bot_id=None):
        """Get list of chat administrators (including bots) via Telegram API. Если ошибка 403 — выставить type_id=5 только для нужного bot_id и user_id."""
        try:
            url = f"https://api.telegram.org/bot{bot_token}/getChatAdministrators"
            params = {"chat_id": chat_id}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("ok"):
                            return data.get("result", [])
                    else:
                        # Если ошибка 403 — выставить type_id=5 только для нужного bot_id и user_id
                        if response.status == 403 and db_chat_id and user_id and bot_id:
                            async with self.pool.acquire() as conn:
                                await conn.execute(
                                    "UPDATE chats SET type_id = 5 WHERE chat_id = $1 AND user_id = $2 AND bot_id = $3",
                                    db_chat_id, user_id, bot_id
                                )
                        return []
        except Exception as e:
            return []

    async def add_chat_employee(self, chat_id, employee_id, is_active, user_id, is_admin=False):
        """Add chat employee relationship only if not exists, with is_admin flag"""
        try:
            current_time = datetime.utcnow()
            async with self.pool.acquire() as conn:
                # Check if chat_employees relation exists
                chat_employee_exists = await conn.fetchrow("""
                    SELECT 1 FROM chat_employees WHERE chat_id = $1 AND employee_id = $2 AND user_id = $3
                """, chat_id, employee_id, user_id)
                if chat_employee_exists:
                    return
                await conn.execute("""
                    INSERT INTO chat_employees 
                    (chat_id, employee_id, is_active, is_admin, created_at, updated_at, user_id)
                    VALUES ($1, $2, $3, $4, $5, $5, $6)
                    ON CONFLICT (chat_id, employee_id) DO UPDATE 
                    SET is_active = EXCLUDED.is_active,
                        is_admin = EXCLUDED.is_admin,
                        updated_at = EXCLUDED.updated_at
                """, chat_id, employee_id, is_active, is_admin, current_time, user_id)
        except Exception as e:
            logger.error(f"Error adding chat employee: {e}")

    async def process_existing_chat(self, chat, bot_token, employees, chat_employees, user_id, new_title=None):
        """Process existing chat according to new algorithm"""
        try:
            chat_id = chat['telegram_chat_id']
            known_users = 0
            chat_count = await self.get_chat_members_count(bot_token, chat_id)
            # Корректное сравнение title
            db_title = ''
            if isinstance(chat['title'], list) and chat['title']:
                db_title = chat['title'][0]
            elif isinstance(chat['title'], str):
                db_title = chat['title']
            # Обновление title только если реально изменился
            if new_title and new_title != db_title:
                await self.update_chat_title(chat['chat_id'], [new_title], user_id)

            # Получить администраторов чата и добавить их в базу
            admins = await self.get_chat_administrators(bot_token, chat_id, chat['chat_id'], user_id, chat['bot_id'])
            for admin in admins:
                user = admin.get('user', {})
                telegram_user_id = user.get('id')
                full_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
                username = user.get('username', '')
                is_bot = user.get('is_bot', False)
                # Проверить, есть ли сотрудник
                async with self.pool.acquire() as conn:
                    existing_employee = await conn.fetchrow("""
                        SELECT employee_id FROM employees WHERE telegram_user_id = $1 AND user_id = $2
                    """, telegram_user_id, user_id)
                    if not existing_employee:
                        employee = await conn.fetchrow("""
                            INSERT INTO employees (full_name, telegram_username, telegram_user_id, is_external, is_active, is_bot, created_at, updated_at, user_id)
                            VALUES ($1, $2, $3, false, true, $4, $5, $5, $6) RETURNING employee_id
                        """, full_name, username, telegram_user_id, is_bot, datetime.utcnow(), user_id)
                        employee_id = employee['employee_id']
                    else:
                        employee_id = existing_employee['employee_id']
                # Добавить связь с is_admin=True
                await self.add_chat_employee(chat['chat_id'], employee_id, True, user_id, is_admin=True)

            # Process existing chat employees
            for ce in chat_employees:
                if ce['chat_id'] != chat['chat_id']:
                    continue
                employee = next((e for e in employees if e['employee_id'] == ce['employee_id']), None)
                if not employee:
                    continue
                is_in_chat = await self.check_user_in_chat(bot_token, chat['telegram_chat_id'], employee['telegram_user_id'])
                if is_in_chat:
                    chat_count -= 1
                    # Check if user should be removed (inactive in either table)
                    if not employee['is_active'] or not ce['is_active']:
                        # Remove user from chat if inactive
                        await self.remove_user_from_chat(ce['chat_id'], employee['employee_id'], user_id)
                    else:
                        # User is active in both tables
                        known_users += 1
                        # Обновлять связь только если реально есть изменения
                        await self.update_user_info(employee, ce['chat_id'], user_id, ce)
            # --- ДОБАВЛЕНО: Проверка сотрудников без связи в chat_employees ---
            employee_ids_in_chat_employees = {ce['employee_id'] for ce in chat_employees if ce['chat_id'] == chat['chat_id']}
            for employee in employees:
                if employee['employee_id'] in employee_ids_in_chat_employees:
                    continue

                telegram_user_id = employee.get('telegram_user_id')
                telegram_username = employee.get('telegram_username')

                if telegram_user_id:
                    is_in_chat = await self.check_user_in_chat(bot_token, chat['telegram_chat_id'], telegram_user_id)
                    if is_in_chat:
                        await self.add_chat_employee(chat['chat_id'], employee['employee_id'], True, user_id)
                        # Обновить username, если изменился
                        # Получить актуальный username через getChatMember
                        member_info = await self.get_chat_member_info(bot_token, chat['telegram_chat_id'], telegram_user_id)
                        if member_info:
                            new_username = member_info.get('user', {}).get('username')
                            if new_username and new_username != telegram_username:
                                employee['telegram_username'] = new_username
                                await self.update_user_info(employee, chat['chat_id'], user_id)
                elif telegram_username:
                    # Получить админов чата
                    admins = await self.get_chat_administrators(bot_token, chat['telegram_chat_id'], chat['chat_id'], user_id, chat['bot_id'])
                    found = False
                    for admin in admins:
                        user = admin.get('user', {})
                        if user.get('username', '').lower() == telegram_username.lower():
                            # Нашли пользователя по username среди админов
                            employee['telegram_user_id'] = user.get('id')
                            await self.add_chat_employee(chat['chat_id'], employee['employee_id'], True, user_id)
                            await self.update_user_info(employee, chat['chat_id'], user_id)
                            found = True
                            break
            
                else:
                    logger.warning(f"Employee {employee['employee_id']} ({employee.get('full_name', '')}) has neither telegram_user_id nor telegram_username, skipping.")
            # Calculate total users and unknown users
            total_users = known_users + chat_count
            unknown_users = chat_count
            # Check if we need to update the counts
            if total_users != chat['user_num'] or unknown_users != chat['unknown_user']:
                await self.update_chat_counts(chat['chat_id'], total_users, unknown_users, user_id)
            # Process remaining users if any
            if chat_count > 0:
                await self.process_new_chat_members(chat, bot_token, chat_count, known_users, employees, user_id)
        except Exception as e:
            logger.error(f"Error processing existing chat {chat_id}: {e}")

    async def update_chat_title(self, chat_id, title, user_id):
        """Update chat title in database"""
        try:
            current_time = datetime.utcnow()
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    UPDATE chats 
                    SET title = $1,
                        updated_at = $2
                    WHERE chat_id = $3 AND user_id = $4
                """, title, current_time, chat_id, user_id)
        except Exception as e:
            logger.error(f"Error updating chat title: {e}")

    async def update_chat_counts(self, chat_id, total_users, unknown_users, user_id):
        """Update chat user counts"""
        try:
            current_time = datetime.utcnow()
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    UPDATE chats 
                    SET user_num = $1,
                        unknown_user = $2,
                        updated_at = $3
                    WHERE chat_id = $4 AND user_id = $5
                """, total_users, unknown_users, current_time, chat_id, user_id)
        except Exception as e:
            logger.error(f"Error updating chat counts: {e}")

    async def process_new_chat_members(self, chat, bot_token, chat_count, known_users, employees, user_id):
        """Process new chat members"""
        try:
            from datetime import datetime, timedelta
            url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
            now = datetime.utcnow()
            lookback = now - timedelta(hours=self.updates_lookback_hours)
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("ok"):
                            updates = data.get("result", [])
                            for update in updates:
                                msg = update.get("message")
                                if msg and "chat" in msg:
                                    msg_date = datetime.utcfromtimestamp(msg["date"])
                                    if msg_date >= lookback:
                                        # 1. Обычный отправитель
                                        if "from" in msg:
                                            await self.process_new_user(chat, msg["from"], employees, known_users, chat_count, user_id)
                                        # 2. new_chat_participant (устаревшее, но поддержим)
                                        if "new_chat_participant" in msg:
                                            await self.process_new_user(chat, msg["new_chat_participant"], employees, known_users, chat_count, user_id)
                                        # 3. new_chat_member (один пользователь)
                                        if "new_chat_member" in msg:
                                            await self.process_new_user(chat, msg["new_chat_member"], employees, known_users, chat_count, user_id)
                                        # 4. new_chat_members (список пользователей)
                                        if "new_chat_members" in msg:
                                            for member in msg["new_chat_members"]:
                                                await self.process_new_user(chat, member, employees, known_users, chat_count, user_id)
        except Exception as e:
            logger.error(f"Error processing new chat members: {e}")

    async def process_new_user(self, chat, user, employees, known_users, chat_count, user_id):
        """Process new user according to chat type with advanced matching logic"""
        try:
            telegram_user_id = user.get('id')
            full_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
            username = user.get('username', '')
            employee = None
            update_fields = {}
            # 1. Поиск по telegram_user_id
            if telegram_user_id:
                employee = next((e for e in employees if e.get('telegram_user_id') == telegram_user_id), None)
                if employee:
                    # Обновить username/full_name если изменились
                    if employee.get('telegram_username') != username:
                        update_fields['telegram_username'] = username
                    if employee.get('full_name') != full_name:
                        update_fields['full_name'] = full_name
                    if not employee.get('is_active', True):
                        update_fields['is_active'] = True
            # 2. Если не найдено — поиск по username
            if not employee and username:
                employee = next((e for e in employees if e.get('telegram_username') and e.get('telegram_username').lower() == username.lower()), None)
                if employee:
                    # a) Если user_id отсутствует — обновить
                    if not employee.get('telegram_user_id'):
                        update_fields['telegram_user_id'] = telegram_user_id
                        update_fields['full_name'] = full_name
                        update_fields['is_active'] = True
                    # b) Если user_id есть — обновить и деактивировать
                    else:
                        update_fields['full_name'] = full_name
                        update_fields['is_active'] = False
            # 3. Если найден сотрудник — обновить при необходимости
            if employee:
                if update_fields:
                    async with self.pool.acquire() as conn:
                        # Формируем SET-часть и плейсхолдеры корректно
                        set_clause = ', '.join([f"{k} = ${i+2}" for i, k in enumerate(update_fields.keys())])
                        set_clause += f", updated_at = ${len(update_fields)+2}"
                        values = list(update_fields.values())
                        # employee_id = $1, далее значения update_fields, updated_at, user_id
                        await conn.execute(
                            f"UPDATE employees SET {set_clause} WHERE employee_id = $1 AND user_id = ${len(update_fields)+3}",
                            employee['employee_id'], *values, datetime.utcnow(), user_id
                        )
                    # Обновить локально (удалено, asyncpg.Record не поддерживает item assignment)
                # Использовать найденного сотрудника
                await self.add_chat_employee(chat['chat_id'], employee['employee_id'], True, user_id)
                return
            # 4. Если не найдено ничего — создать нового
            await self.add_external_user(telegram_user_id, full_name, username, chat['chat_id'], True, user_id)
        except Exception as e:
            logger.error(f"Error processing new user: {e}")

    async def add_external_user(self, telegram_user_id, full_name, username, chat_id, is_active, user_id):
        """Add external user to database, only if not exists. Also add chat_employees relation only if not exists. Всегда is_bot = false."""
        try:
            current_time = datetime.utcnow()
            async with self.pool.acquire() as conn:
                # Check if employee exists
                existing_employee = await conn.fetchrow("""
                    SELECT employee_id FROM employees 
                    WHERE telegram_user_id = $1 AND user_id = $2
                """, telegram_user_id, user_id)
                if existing_employee:
                    employee_id = existing_employee['employee_id']
                    # Check if chat_employees relation exists
                    chat_employee_exists = await conn.fetchrow("""
                        SELECT 1 FROM chat_employees WHERE chat_id = $1 AND employee_id = $2 AND user_id = $3
                    """, chat_id, employee_id, user_id)
                    if chat_employee_exists:
                        return
                    # Add chat_employee relationship
                    await conn.execute("""
                        INSERT INTO chat_employees 
                        (chat_id, employee_id, is_active, created_at, updated_at, user_id)
                        VALUES ($1, $2, $3, $4, $4, $5)
                        ON CONFLICT (chat_id, employee_id) DO UPDATE 
                        SET is_active = EXCLUDED.is_active,
                            updated_at = EXCLUDED.updated_at
                    """, chat_id, employee_id, is_active, current_time, user_id)
                else:
                    # Create new employee и всегда is_bot = false
                    employee = await conn.fetchrow("""
                        INSERT INTO employees 
                        (full_name, telegram_username, telegram_user_id, is_external, is_active, is_bot, created_at, updated_at, user_id)
                        VALUES ($1, $2, $3, true, true, false, $4, $4, $5)
                        RETURNING employee_id
                    """, full_name, username, telegram_user_id, current_time, user_id)
                    # Add chat_employee relationship
                    await conn.execute("""
                        INSERT INTO chat_employees 
                        (chat_id, employee_id, is_active, created_at, updated_at, user_id)
                        VALUES ($1, $2, $3, $4, $4, $5)
                    """, chat_id, employee['employee_id'], is_active, current_time, user_id)
        except Exception as e:
            logger.error(f"Error adding external user: {e}")

    async def remove_user_from_chat(self, chat_id, employee_id, user_id):
        """Remove user from chat"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    DELETE FROM chat_employees 
                    WHERE chat_id = $1 AND employee_id = $2 AND user_id = $3
                """, chat_id, employee_id, user_id)
        except Exception as e:
            logger.error(f"Error removing user from chat: {e}")

    async def update_user_info(self, employee, chat_id, user_id, chat_employee_record=None):
        """Update user information in database only if changes detected (employee and chat_employees)"""
        try:
            current_time = datetime.utcnow()
            async with self.pool.acquire() as conn:
                # First get current data
                current_employee = await conn.fetchrow("""
                    SELECT full_name, telegram_username, is_active 
                    FROM employees 
                    WHERE employee_id = $1 AND user_id = $2
                """, employee['employee_id'], user_id)
                if chat_employee_record is not None:
                    current_chat_employee = chat_employee_record
                else:
                    current_chat_employee = await conn.fetchrow("""
                        SELECT is_active 
                        FROM chat_employees 
                        WHERE chat_id = $1 AND employee_id = $2 AND user_id = $3
                    """, chat_id, employee['employee_id'], user_id)
                if not current_employee or not current_chat_employee:
                    logger.error(f"Could not find current data for employee {employee['employee_id']} in chat {chat_id}")
                    return
                # Check if employee data needs updating
                need_update_employee = (
                    current_employee['full_name'] != employee['full_name'] or
                    current_employee['telegram_username'] != employee['telegram_username'] or
                    current_employee['is_active'] != employee['is_active']
                )
                # Check if chat_employee relationship needs updating
                need_update_chat_employee = (current_chat_employee['is_active'] != True)
                if not need_update_employee and not need_update_chat_employee:
                    return  # Нет изменений, ничего не делаем
                if need_update_employee:
                    await conn.execute("""
                        UPDATE employees 
                        SET full_name = $1,
                            telegram_username = $2,
                            is_active = $3,
                            updated_at = $4
                        WHERE employee_id = $5 AND user_id = $6
                    """, employee['full_name'], employee['telegram_username'], 
                        employee['is_active'], current_time, employee['employee_id'], user_id)
                if need_update_chat_employee:
                    await conn.execute("""
                        UPDATE chat_employees 
                        SET is_active = $1,
                            updated_at = $2
                        WHERE chat_id = $3 AND employee_id = $4 AND user_id = $5
                    """, True, current_time, chat_id, employee['employee_id'], user_id)
        except Exception as e:
            logger.error(f"Error updating user info: {e}")

    async def create_new_chat(self, bot_token, chat_id, bot_id, title, user_id):
        """Create new chat in database"""
        try:
            current_time = datetime.utcnow()
            # Convert title to array as expected by the database
            title_array = [title] if title else ['']
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO chats 
                    (bot_id, telegram_chat_id, type_id, status_id, user_num, Unknown_user, created_at, updated_at, title, user_id)
                    VALUES ($1, $2, 4, 1, 0, 0, $3, $3, $4, $5)
                """, bot_id, chat_id, current_time, title_array, user_id)
                # Получить telegram_user_id и username бота
                bot_info = await conn.fetchrow("""
                    SELECT bot_name, bot_username, telegram_user_id FROM bots WHERE bot_id = $1
                """, bot_id)
                if bot_info:
                    bot_telegram_user_id = bot_info['telegram_user_id']
                    # Проверить через Telegram API, что бот реально присутствует в чате
                    is_bot_in_chat = await self.check_user_in_chat(bot_token, chat_id, bot_telegram_user_id)
                    if is_bot_in_chat:
                        # Проверить, есть ли сотрудник-бот
                        existing_bot_employee = await conn.fetchrow(
                            """SELECT employee_id FROM employees WHERE telegram_user_id = $1 AND is_bot = true AND user_id = $2""",
                            bot_telegram_user_id, user_id
                        )
                        if not existing_bot_employee:
                            bot_employee = await conn.fetchrow(
                                """INSERT INTO employees (full_name, telegram_username, telegram_user_id, is_external, is_active, is_bot, created_at, updated_at, user_id)
                                VALUES ($1, $2, $3, false, true, true, $4, $4, $5) RETURNING employee_id""",
                                bot_info['bot_name'], bot_info['bot_name'], bot_telegram_user_id, current_time, user_id
                            )
                            bot_employee_id = bot_employee['employee_id']
                        else:
                            bot_employee_id = existing_bot_employee['employee_id']
                        # Добавить связь бота с чатом
                        await self.add_chat_employee(chat_id, bot_employee_id, True, user_id)
                # Send welcome message
                await self.send_welcome_message(bot_token, chat_id)
        except Exception as e:
            logger.error(f"Error creating new chat: {e}")

    async def get_bot_chats(self, bot_token):
        """Get list of chats where bot is present"""
        try:
            url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("ok"):
                            updates = data.get("result", [])
                            chat_info = {}  # Dictionary to store chat_id -> title mapping
                            for update in updates:
                                if "message" in update and "chat" in update["message"]:
                                    chat = update["message"]["chat"]
                                    chat_id = chat["id"]
                                    # Get chat info for all chats
                                    chat_info[chat_id] = chat.get('title', '')
                            
                            return chat_info
                    logger.error(f"Failed to get bot chats: {await response.text()}")
                    return {}
        except Exception as e:
            logger.error(f"Error getting bot chats: {e}")
            return {}

    async def get_chat_info(self, bot_token, chat_id, db_chat_id=None, user_id=None, bot_id=None):
        """Get chat information from Telegram. Если ошибка 400 — выставить type_id=5 только для чата с нужным bot_id и user_id."""
        try:
            url = f"https://api.telegram.org/bot{bot_token}/getChat"
            params = {"chat_id": chat_id}
            logger.info(f"Getting chat info for chat {chat_id}");
            logger.info(f"Getting chat info from {url}");
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    logger.info(f"Response status: {response.status}");
                    if response.status == 200:
                        data = await response.json()
                        if data.get("ok"):
                            return data.get("result", {})
                    else:
                        # Если ошибка 400 — выставить type_id=5 только для нужного bot_id и user_id
                        if response.status == 400 and db_chat_id and user_id and bot_id:
                            async with self.pool.acquire() as conn:
                                logger.info(f"Updating chat {db_chat_id} to type_id=5 (bot_id={bot_id})");
                                await conn.execute(
                                    "UPDATE chats SET type_id = 5 WHERE chat_id = $1 AND user_id = $2 AND bot_id = $3",
                                    db_chat_id, user_id, bot_id
                                )
                        return None
        except Exception as e:
            return None

    async def get_active_user_ids(self):
        """Get all active user IDs from users table"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT user_id FROM users WHERE is_active = true
                """)
                return [row['user_id'] for row in rows]
        except Exception as e:
            logger.error(f"Failed to get active user IDs: {e}")
            return []

    async def get_all_data(self, user_id):
        """Get all required data from database for a specific user"""
        try:
            async with self.pool.acquire() as conn:
                employees = await conn.fetch("""
                    SELECT * FROM employees WHERE user_id = $1 and is_active = true
                """, user_id)
                chat_employees = await conn.fetch("""
                    SELECT * FROM chat_employees WHERE user_id = $1 and is_active = true
                """, user_id)
                bots = await conn.fetch("""
                    SELECT * FROM bots WHERE is_active = true AND user_id = $1 and is_active = true
                """, user_id)
                chats = await conn.fetch("""
                    SELECT * FROM chats WHERE user_id = $1
                """, user_id)
                return employees, chat_employees, bots, chats
        except Exception as e:
            logger.error(f"Failed to get data from database: {e}")
            return [], [], [], []

    async def mark_chat_as_removed(self, chat_id, user_id):
        """Mark chat as removed (type_id=5) in the database"""
        try:
            current_time = datetime.utcnow()
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """UPDATE chats SET type_id = 5, updated_at = $1 WHERE chat_id = $2 AND user_id = $3""",
                    current_time, chat_id, user_id
                )
        except Exception as e:
            logger.error(f"Error marking chat {chat_id} as removed: {e}")

    async def create_removed_chat(self, bot_id, chat_id, title, user_id):
        """Create a removed chat (type_id=5) in the database"""
        try:
            current_time = datetime.utcnow()
            title_array = [title] if title else ['']
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO chats (bot_id, telegram_chat_id, type_id, status_id, user_num, Unknown_user, created_at, updated_at, title, user_id)
                    VALUES ($1, $2, 5, 1, 0, 0, $3, $3, $4, $5)""",
                    bot_id, chat_id, current_time, title_array, user_id
                )
        except Exception as e:
            logger.error(f"Error creating removed chat {chat_id}: {e}")

    async def is_chat_accessible_for_bot(self, bot_token, chat_id):
        """Check if bot has access to the chat via Telegram API"""
        try:
            chat_info = await self.get_chat_info(bot_token, chat_id)
            return chat_info is not None
        except Exception as e:
            logger.warning(f"Error checking access to chat {chat_id}: {e}")
            return False

    async def get_chat_member_info(self, bot_token, chat_id, user_id):
        """Get chat member info from Telegram API (заглушка для совместимости)"""
        try:
            url = f"https://api.telegram.org/bot{bot_token}/getChatMember"
            params = {"chat_id": chat_id, "user_id": user_id}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("ok"):
                            return data.get("result", {})
            return None
        except Exception as e:
            return None

    async def run_cycle(self):
        """Run one cycle of the service"""
        try:
            # Получить всех активных пользователей
            active_user_ids = await self.get_active_user_ids()
            for user_id in active_user_ids:
                # Get all required data for this user
                employees, chat_employees, bots, chats = await self.get_all_data(user_id)
                for bot in bots:
                    # Получить чаты с обновлений
                    bot_chats = await self.get_bot_chats(bot['bot_token'])  # dict {chat_id: title}
                    # Собрать все уникальные chat_id
                    db_chat_ids = { (c['telegram_chat_id'], c['bot_id']) for c in chats }
                    bot_chat_ids = { (chat_id, bot['bot_id']) for chat_id in bot_chats.keys() }
                    all_chat_keys = db_chat_ids | bot_chat_ids
                    # Фильтруем только чаты с bot_id текущего бота
                    relevant_chats = [c for c in chats if c['bot_id'] == bot['bot_id']]
                    for chat_id, bot_id in all_chat_keys:
                        if bot_id != bot['bot_id']:
                            continue
                        chat_title = bot_chats.get(chat_id)
                        # Поиск чата по паре (bot_id, telegram_chat_id)
                        existing_chat = next((c for c in relevant_chats if c['telegram_chat_id'] == chat_id and c['bot_id'] == bot_id), None)
                        # Проверяем только is_active==True или is_active is None
                        if existing_chat and existing_chat.get('is_active') is not None and not existing_chat['is_active']:
                            continue
                        # Если чат type_id==5 — пробуем оживить
                        if existing_chat and existing_chat.get('type_id') == 5:
                            accessible = await self.is_chat_accessible_for_bot(bot['bot_token'], chat_id)
                            if accessible:
                                # Вернуть type_id=4
                                async with self.pool.acquire() as conn:
                                    await conn.execute(
                                        "UPDATE chats SET type_id = 4 WHERE chat_id = $1 AND user_id = $2 AND bot_id = $3",
                                        existing_chat['chat_id'], user_id, bot['bot_id']
                                    )
                                # Обработать как новый чат
                                await self.process_existing_chat(existing_chat, bot['bot_token'], employees, chat_employees, user_id, chat_title)
                            continue
                        # Проверяем доступность чата для бота через Telegram API ДО любых действий
                        accessible = await self.is_chat_accessible_for_bot(bot['bot_token'], chat_id)
                        if not accessible:
                            # Установить только type_id=5
                            if existing_chat and existing_chat.get('type_id') != 5:
                                async with self.pool.acquire() as conn:
                                    await conn.execute(
                                        "UPDATE chats SET type_id = 5 WHERE chat_id = $1 AND user_id = $2 AND bot_id = $3",
                                        existing_chat['chat_id'], user_id, bot['bot_id']
                                    )
                            continue  # Не обрабатываем дальше этот чат
                        if existing_chat:
                            await self.process_existing_chat(existing_chat, bot['bot_token'], employees, chat_employees, user_id, chat_title)
                        else:
                            await self.create_new_chat(bot['bot_token'], chat_id, bot_id, chat_title, user_id)
        except Exception as e:
            logger.error(f"Error in service cycle: {e}")
        logger.info("Service cycle completed")

    async def run(self):
        """Main service loop"""
        await self.init_db()
        while True:
            await self.run_cycle()
            await asyncio.sleep(self.interval)

 

async def main():
    service = BotService()
    await service.run()

if __name__ == "__main__":
    asyncio.run(main()) 
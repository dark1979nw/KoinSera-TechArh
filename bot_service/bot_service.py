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
        self.pool = None

    async def init_db(self):
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(self.db_url)
            logger.info("Database connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
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
        logger.info(f"Getting chat members count for chat {chat_id}");
        try:
            url = f"https://api.telegram.org/bot{bot_token}/getChatMembersCount"
            params = {"chat_id": chat_id}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("ok"):
                            return data.get("result", 0)
                    logger.error(f"Failed to get chat members count: {await response.text()}")
                    return 0
        except Exception as e:
            logger.error(f"Error getting chat members count: {e}")
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

    async def get_chat_administrators(self, bot_token, chat_id):
        """Get list of chat administrators (including bots) via Telegram API"""
        try:
            url = f"https://api.telegram.org/bot{bot_token}/getChatAdministrators"
            params = {"chat_id": chat_id}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("ok"):
                            return data.get("result", [])
                    logger.error(f"Failed to get chat administrators: {await response.text()}")
                    return []
        except Exception as e:
            logger.error(f"Error getting chat administrators: {e}")
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
                    logger.info(f"Chat-employee relation already exists for employee {employee_id} in chat {chat_id}")
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
                logger.info(f"Updating chat title from {db_title} to {new_title}")
                await self.update_chat_title(chat['chat_id'], [new_title], user_id)

            # Получить администраторов чата и добавить их в базу
            admins = await self.get_chat_administrators(bot_token, chat_id)
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
                        logger.info(f"Removing user {employee['full_name']} from chat {chat_id} because they are inactive  {employee['is_active']} {ce['is_active']}");
                        await self.remove_user_from_chat(ce['chat_id'], employee['employee_id'], user_id)
                    else:
                        # User is active in both tables
                        known_users += 1
                        logger.info(f"User {employee['full_name']} is active in both tables");
                        # Обновлять связь только если реально есть изменения
                        await self.update_user_info(employee, ce['chat_id'], user_id, ce)
            # Calculate total users and unknown users
            total_users = known_users + chat_count
            unknown_users = chat_count
            # Check if we need to update the counts
            logger.info(f"total_users={total_users} (was {chat['user_num']}), unknown_users={unknown_users} (was {chat['unknown_user']})");
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
            logger.info(f"Updating chat counts for chat {chat_id}  total_users={total_users} unknown_users={unknown_users}");
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
            url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("ok"):
                            updates = data.get("result", [])
                            for update in updates:
                                if "message" in update and "chat" in update["message"]:
                                    user = update["message"]["from"]
                                    await self.process_new_user(chat, user, employees, known_users, chat_count, user_id)
        except Exception as e:
            logger.error(f"Error processing new chat members: {e}")

    async def process_new_user(self, chat, user, employees, known_users, chat_count, user_id):
        """Process new user according to chat type"""
        try:
            telegram_user_id = user.get('id')
            full_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
            username = user.get('username', '')
            
            existing_employee = next((e for e in employees if e['telegram_user_id'] == telegram_user_id), None)
            
            if chat['type_id'] == 2:  # Private chat
                if not existing_employee or existing_employee['is_external'] or not existing_employee['is_active']:
                    # Add as external user and remove from chat
                    await self.add_external_user(telegram_user_id, full_name, username, chat['chat_id'], False, user_id)
                    chat_count -= 1
                else:
                    # Add active user
                    await self.add_chat_employee(chat['chat_id'], existing_employee['employee_id'], True, user_id)
                    known_users += 1
                    chat_count -= 1
            else:  # Group chats (type_id 1,3,4)
                if not existing_employee or existing_employee['is_external'] or not existing_employee['is_active']:
                    # Add as external user but keep in chat
                    await self.add_external_user(telegram_user_id, full_name, username, chat['chat_id'], True, user_id)
                    known_users += 1
                    chat_count -= 1
                else:
                    # Add active user
                    await self.add_chat_employee(chat['chat_id'], existing_employee['employee_id'], True, user_id)
                    known_users += 1
                    chat_count -= 1
                    
        except Exception as e:
            logger.error(f"Error processing new user: {e}")

    async def add_external_user(self, telegram_user_id, full_name, username, chat_id, is_active, user_id):
        """Add external user to database, only if not exists. Also add chat_employees relation only if not exists. Всегда is_bot = false."""
        try:
            current_time = datetime.utcnow()
            logger.info(f"Adding external user {telegram_user_id} to chat {chat_id}");
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
                        logger.info(f"Chat-employee relation already exists for employee {employee_id} in chat {chat_id}")
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
                    logger.info(f"Added existing employee {full_name} to chat {chat_id}")
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
                    logger.info(f"Created new external employee {full_name} and added to chat {chat_id}")
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
        logger.info(f"Updating user info for {employee['employee_id']} in chat {chat_id}");
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
                    logger.info(f"Updated employee info for {employee['full_name']}")
                if need_update_chat_employee:
                    await conn.execute("""
                        UPDATE chat_employees 
                        SET is_active = $1,
                            updated_at = $2
                        WHERE chat_id = $3 AND employee_id = $4 AND user_id = $5
                    """, True, current_time, chat_id, employee['employee_id'], user_id)
                    logger.info(f"Updated chat_employee relationship for {employee['full_name']} in chat {chat_id}")
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
                                    chat_data = await self.get_chat_info(bot_token, chat_id)
                                    if chat_data:
                                        title = chat_data.get('title', '')
                                        if not title and chat_data.get('type') == 'private':
                                            # For private chats, use user's name
                                            first_name = chat_data.get('first_name', '')
                                            last_name = chat_data.get('last_name', '')
                                            title = f"{first_name} {last_name}".strip()
                                        
                                        chat_info[chat_id] = title
                                        logger.info(f"Found chat: {title} (ID: {chat_id})")
                            
                            return chat_info
                    logger.error(f"Failed to get bot chats: {await response.text()}")
                    return {}
        except Exception as e:
            logger.error(f"Error getting bot chats: {e}")
            return {}

    async def get_chat_info(self, bot_token, chat_id):
        """Get chat information from Telegram"""
        try:
            url = f"https://api.telegram.org/bot{bot_token}/getChat"
            params = {"chat_id": chat_id}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("ok"):
                            return data.get("result", {})
                    logger.error(f"Failed to get chat info: {await response.text()}")
                    return None
        except Exception as e:
            logger.error(f"Error getting chat info: {e}")
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
                logger.info(f"Found {len(employees)} employees for user_id {user_id}");
                chat_employees = await conn.fetch("""
                    SELECT * FROM chat_employees WHERE user_id = $1 and is_active = true
                """, user_id)
                logger.info(f"Found {len(chat_employees)} chat_employees for user_id {user_id}");
                bots = await conn.fetch("""
                    SELECT * FROM bots WHERE is_active = true AND user_id = $1 and is_active = true
                """, user_id)
                logger.info(f"Found {len(bots)} bots for user_id {user_id}");
                chats = await conn.fetch("""
                    SELECT * FROM chats WHERE user_id = $1
                """, user_id)
                logger.info(f"Found {len(chats)} chats for user_id {user_id}");
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

    async def run_cycle(self):
        """Run one cycle of the service"""
        logger.info("Starting service cycle");
        try:
            # Получить всех активных пользователей
            active_user_ids = await self.get_active_user_ids()
            logger.info(f"Found {len(active_user_ids)} active users");
            for user_id in active_user_ids:
                logger.info(f"Processing user_id {user_id}");
                # Get all required data for this user
                employees, chat_employees, bots, chats = await self.get_all_data(user_id)
                for bot in bots:
                    logger.info(f"Processing bot {bot['bot_name']} for user_id {user_id}");
                    # Получить чаты с обновлений
                    bot_chats = await self.get_bot_chats(bot['bot_token'])  # dict {chat_id: title}
                    logger.info(f"Found {len(bot_chats)} chats for bot {bot['bot_name']}");
                    # Собрать все уникальные chat_id
                    db_chat_ids = { (c['telegram_chat_id'], c['bot_id']) for c in chats }
                    bot_chat_ids = { (chat_id, bot['bot_id']) for chat_id in bot_chats.keys() }
                    all_chat_keys = db_chat_ids | bot_chat_ids
                    for chat_id, bot_id in all_chat_keys:
                        chat_title = bot_chats.get(chat_id)
                        # Поиск чата по паре (bot_id, telegram_chat_id)
                        existing_chat = next((c for c in chats if c['telegram_chat_id'] == chat_id and c['bot_id'] == bot_id), None)
                        # Проверяем доступность чата для бота через Telegram API ДО любых действий
                        accessible = await self.is_chat_accessible_for_bot(bot['bot_token'], chat_id)
                        if not accessible:
                            logger.warning(f"Bot {bot['bot_name']} cannot access chat {chat_id}, marking as removed.")
                            if existing_chat:
                                await self.mark_chat_as_removed(existing_chat['chat_id'], user_id)
                            else:
                                await self.create_removed_chat(bot_id, chat_id, chat_title, user_id)
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
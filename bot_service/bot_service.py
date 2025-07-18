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
        self.bots = []
        self.chats = []
        self.employees = []
        self.chat_employees = []
        self.offsets = {}  # offset для каждого бота

    async def init_db(self):
        try:
            self.pool = await asyncpg.create_pool(self.db_url)
        except Exception as e:
            logger.error(f"Failed to initialize DB: {e}")
            raise

    async def load_all_data(self):
        try:
            async with self.pool.acquire() as conn:
                self.bots = await conn.fetch("SELECT * FROM bots WHERE is_active = true")
                self.chats = await conn.fetch("SELECT * FROM chats")
                self.employees = await conn.fetch("SELECT * FROM employees")
                self.chat_employees = await conn.fetch("SELECT * FROM chat_employees")
            logger.info(f"Loaded {len(self.bots)} bots, {len(self.chats)} chats, {len(self.employees)} employees, {len(self.chat_employees)} chat_employees")
        except Exception as e:
            logger.error(f"Failed to load data: {e}")

    async def fetch_updates(self, bot_token, bot_id):
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        params = {}
        current_offset = self.offsets.get(bot_id)
        logger.info(f"Bot {bot_id}: Calling getUpdates with offset={current_offset}")
        if current_offset is not None:
            params['offset'] = current_offset
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("ok"):
                        updates = data.get("result", [])
                        logger.info(f"Bot {bot_id}: Updates: {updates}")
                        if current_offset is None:
                            # Первый запуск: просто установить offset, не обрабатывать updates
                            max_update_id = None
                            for update in updates:
                                update_id = update.get('update_id')
                                if update_id is not None:
                                    if max_update_id is None or update_id > max_update_id:
                                        max_update_id = update_id
                            if max_update_id is not None:
                                self.offsets[bot_id] = max_update_id + 1
                                logger.info(f"Bot {bot_id}: Initial offset set to {max_update_id + 1}")
                            return []
                        # Обычная обработка
                        max_update_id = current_offset
                        for update in updates:
                            update_id = update.get('update_id')
                            if update_id is not None:
                                if max_update_id is None or update_id >= max_update_id:
                                    max_update_id = update_id + 1
                        if max_update_id is not None:
                            self.offsets[bot_id] = max_update_id
                            logger.info(f"Bot {bot_id}: Updated offset to {max_update_id}")
                        return updates
        return []

    async def send_welcome_message(self, bot_token, chat_id, bot_name):
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        text = f"привет я бот-консьерж ({bot_name}). Я не сохраняю сообщение. Напиши мне пару слов, что бы я тебя узнал"
        params = {"chat_id": chat_id, "text": text}
        async with aiohttp.ClientSession() as session:
            await session.get(url, params=params)

    async def process_update(self, msg, user_id, bot_id, conn):
        logger.info(f"Processing message for user_id={user_id}, bot_id={bot_id}, msg={msg}")
        chat = msg.get('chat')
        if not chat:
            return
        telegram_chat_id = chat.get('id')
        title = chat.get('title', '')
        db_chat = next((c for c in self.chats if c['telegram_chat_id'] == telegram_chat_id and c['bot_id'] == bot_id and c['user_id'] == user_id), None)
        chat_was_created = False
        if not db_chat:
            logger.info(f"Creating new chat telegram_chat_id={telegram_chat_id} bot_id={bot_id} user_id={user_id}")
            await conn.execute("""
                INSERT INTO chats (bot_id, telegram_chat_id, type_id, status_id, user_num, unknown_user, created_at, updated_at, title, user_id)
                VALUES ($1, $2, 4, 1, 0, 0, NOW(), NOW(), $3, $4)
            """, bot_id, telegram_chat_id, [title], user_id)
            self.chats.append({
                'chat_id': None,
                'bot_id': bot_id,
                'telegram_chat_id': telegram_chat_id,
                'user_id': user_id,
                'title': [title],
                'type_id': 4,
                'status_id': 1
            })
            db_chat = await conn.fetchrow("""
                SELECT * FROM chats WHERE telegram_chat_id = $1 AND bot_id = $2 AND user_id = $3
            """, telegram_chat_id, bot_id, user_id)
            chat_was_created = True
        else:
            if title and (not db_chat['title'] or db_chat['title'][0] != title):
                logger.info(f"Updating chat title for chat_id={db_chat['chat_id']} to {title}")
                await conn.execute("""
                    UPDATE chats SET title = $1, updated_at = NOW() WHERE chat_id = $2
                """, [title], db_chat['chat_id'])
        chat_id = db_chat['chat_id']

        if chat_was_created:
            bot = next((b for b in self.bots if b['bot_id'] == bot_id), None)
            if bot:
                await self.send_welcome_message(bot['bot_token'], telegram_chat_id, bot['bot_name'])
            bot_telegram_user_id = bot['telegram_user_id'] if bot else None
            if bot_telegram_user_id:
                db_bot_employee = next((e for e in self.employees if e['telegram_user_id'] == bot_telegram_user_id and e['user_id'] == user_id and e.get('is_bot')), None)
                if not db_bot_employee:
                    logger.info(f"Creating bot employee for bot_telegram_user_id={bot_telegram_user_id} user_id={user_id}")
                    await conn.execute("""
                        INSERT INTO employees (full_name, telegram_username, telegram_user_id, is_external, is_active, is_bot, created_at, updated_at, user_id)
                        VALUES ($1, $2, $3, false, true, true, NOW(), NOW(), $4)
                    """, bot['bot_name'], bot['bot_name'], bot_telegram_user_id, user_id)
                    db_bot_employee = await conn.fetchrow("""
                        SELECT * FROM employees WHERE telegram_user_id = $1 AND user_id = $2 AND is_bot = true
                    """, bot_telegram_user_id, user_id)
                    self.employees.append({
                        'employee_id': db_bot_employee['employee_id'],
                        'telegram_user_id': bot_telegram_user_id,
                        'user_id': user_id,
                        'full_name': bot['bot_name'],
                        'telegram_username': bot['bot_name'],
                        'is_external': False,
                        'is_active': True,
                        'is_bot': True
                    })
                db_bot_link = next((l for l in self.chat_employees if l['chat_id'] == chat_id and l['employee_id'] == db_bot_employee['employee_id'] and l['user_id'] == user_id), None)
                if not db_bot_link:
                    logger.info(f"Creating bot chat_employees link for chat_id={chat_id} employee_id={db_bot_employee['employee_id']} user_id={user_id}")
                    await conn.execute("""
                        INSERT INTO chat_employees (chat_id, employee_id, is_active, is_admin, created_at, updated_at, user_id)
                        VALUES ($1, $2, true, false, NOW(), NOW(), $3)
                    """, chat_id, db_bot_employee['employee_id'], user_id)
                    self.chat_employees.append({
                        'chat_id': chat_id,
                        'employee_id': db_bot_employee['employee_id'],
                        'user_id': user_id,
                        'is_active': True,
                        'is_admin': False
                    })
                elif not db_bot_link['is_active']:
                    logger.info(f"Activating bot chat_employees link for chat_id={chat_id} employee_id={db_bot_employee['employee_id']} user_id={user_id}")
                    await conn.execute("""
                        UPDATE chat_employees SET is_active = true, updated_at = NOW() WHERE chat_id = $1 AND employee_id = $2 AND user_id = $3
                    """, chat_id, db_bot_employee['employee_id'], user_id)
                    if isinstance(db_bot_link, dict):
                        db_bot_link['is_active'] = True
        # 2. ПОЛЬЗОВАТЕЛЬ
        user = None
        if 'from' in msg:
            user = msg['from']
        elif 'new_chat_member' in msg:
            user = msg['new_chat_member']
        elif 'new_chat_participant' in msg:
            user = msg['new_chat_participant']
        if user:
            telegram_user_id = user.get('id')
            full_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
            username = user.get('username', '')
            db_employee = next((e for e in self.employees if e['telegram_user_id'] == telegram_user_id and e['user_id'] == user_id), None)
            if not db_employee and username:
                db_employee = next((e for e in self.employees if e['telegram_username'] == username and e['user_id'] == user_id), None)
                if db_employee and not db_employee['telegram_user_id']:
                    logger.info(f"Updating employee {db_employee['employee_id']} set telegram_user_id={telegram_user_id}")
                    await conn.execute(
                        """UPDATE employees SET telegram_user_id = $1, updated_at = NOW() WHERE employee_id = $2""",
                        telegram_user_id, db_employee['employee_id']
                    )
                    db_employee = await conn.fetchrow(
                        """SELECT * FROM employees WHERE employee_id = $1""", db_employee['employee_id']
                    )
            if not db_employee:
                logger.info(f"Creating employee for telegram_user_id={telegram_user_id} user_id={user_id} full_name={full_name} username={username}")
                await conn.execute(
                    """INSERT INTO employees (full_name, telegram_username, telegram_user_id, is_external, is_active, is_bot, created_at, updated_at, user_id)
                    VALUES ($1, $2, $3, true, true, false, NOW(), NOW(), $4)""",
                    full_name, username, telegram_user_id, user_id
                )
                db_employee = await conn.fetchrow(
                    """SELECT * FROM employees WHERE telegram_user_id = $1 AND user_id = $2""", telegram_user_id, user_id
                )
            else:
                if db_employee['full_name'] != full_name or db_employee['telegram_username'] != username:
                    logger.info(f"Updating employee employee_id={db_employee['employee_id']} full_name={full_name} username={username}")
                    await conn.execute("""
                        UPDATE employees SET full_name = $1, telegram_username = $2, updated_at = NOW() WHERE employee_id = $3
                    """, full_name, username, db_employee['employee_id'])
            employee_id = db_employee['employee_id']
            db_link = next((l for l in self.chat_employees if l['chat_id'] == chat_id and l['employee_id'] == employee_id and l['user_id'] == user_id), None)
            if not db_link:
                logger.info(f"Creating chat_employees link for chat_id={chat_id} employee_id={employee_id} user_id={user_id}")
                await conn.execute("""
                    INSERT INTO chat_employees (chat_id, employee_id, is_active, is_admin, created_at, updated_at, user_id)
                    VALUES ($1, $2, true, false, NOW(), NOW(), $3)
                """, chat_id, employee_id, user_id)
                self.chat_employees.append({
                    'chat_id': chat_id,
                    'employee_id': employee_id,
                    'user_id': user_id,
                    'is_active': True,
                    'is_admin': False
                })
            elif not db_link['is_active']:
                logger.info(f"Activating chat_employees link for chat_id={chat_id} employee_id={employee_id} user_id={user_id}")
                await conn.execute("""
                    UPDATE chat_employees SET is_active = true, updated_at = NOW() WHERE chat_id = $1 AND employee_id = $2 AND user_id = $3
                """, chat_id, employee_id, user_id)
                if isinstance(db_link, dict):
                    db_link['is_active'] = True
            else:
                logger.info(f"chat_employees link already active for chat_id={chat_id} employee_id={employee_id} user_id={user_id}")
        if 'new_chat_members' in msg:
            for member in msg['new_chat_members']:
                telegram_user_id = member.get('id')
                full_name = f"{member.get('first_name', '')} {member.get('last_name', '')}".strip()
                username = member.get('username', '')
                db_employee = next((e for e in self.employees if e['telegram_user_id'] == telegram_user_id and e['user_id'] == user_id), None)
                if not db_employee and username:
                    db_employee = next((e for e in self.employees if e['telegram_username'] == username and e['user_id'] == user_id), None)
                    if db_employee and not db_employee['telegram_user_id']:
                        logger.info(f"Updating employee {db_employee['employee_id']} set telegram_user_id={telegram_user_id}")
                        await conn.execute(
                            """UPDATE employees SET telegram_user_id = $1, updated_at = NOW() WHERE employee_id = $2""",
                            telegram_user_id, db_employee['employee_id']
                        )
                        db_employee = await conn.fetchrow(
                            """SELECT * FROM employees WHERE employee_id = $1""", db_employee['employee_id']
                        )
                if not db_employee:
                    logger.info(f"Creating employee for telegram_user_id={telegram_user_id} user_id={user_id} full_name={full_name} username={username}")
                    await conn.execute(
                        """INSERT INTO employees (full_name, telegram_username, telegram_user_id, is_external, is_active, is_bot, created_at, updated_at, user_id)
                        VALUES ($1, $2, $3, true, true, false, NOW(), NOW(), $4)""",
                        full_name, username, telegram_user_id, user_id
                    )
                    db_employee = await conn.fetchrow(
                        """SELECT * FROM employees WHERE telegram_user_id = $1 AND user_id = $2""", telegram_user_id, user_id
                    )
                else:
                    if db_employee['full_name'] != full_name or db_employee['telegram_username'] != username:
                        logger.info(f"Updating employee employee_id={db_employee['employee_id']} full_name={full_name} username={username}")
                        await conn.execute("""
                            UPDATE employees SET full_name = $1, telegram_username = $2, updated_at = NOW() WHERE employee_id = $3
                        """, full_name, username, db_employee['employee_id'])
                employee_id = db_employee['employee_id']
                db_link = next((l for l in self.chat_employees if l['chat_id'] == chat_id and l['employee_id'] == employee_id and l['user_id'] == user_id), None)
                if not db_link:
                    logger.info(f"Creating chat_employees link for chat_id={chat_id} employee_id={employee_id} user_id={user_id}")
                    await conn.execute("""
                        INSERT INTO chat_employees (chat_id, employee_id, is_active, is_admin, created_at, updated_at, user_id)
                        VALUES ($1, $2, true, false, NOW(), NOW(), $3)
                    """, chat_id, employee_id, user_id)
                    self.chat_employees.append({
                        'chat_id': chat_id,
                        'employee_id': employee_id,
                        'user_id': user_id,
                        'is_active': True,
                        'is_admin': False
                    })
                elif not db_link['is_active']:
                    logger.info(f"Activating chat_employees link for chat_id={chat_id} employee_id={employee_id} user_id={user_id}")
                    await conn.execute("""
                        UPDATE chat_employees SET is_active = true, updated_at = NOW() WHERE chat_id = $1 AND employee_id = $2 AND user_id = $3
                    """, chat_id, employee_id, user_id)
                    if isinstance(db_link, dict):
                        db_link['is_active'] = True
                else:
                    logger.info(f"chat_employees link already active for chat_id={chat_id} employee_id={employee_id} user_id={user_id}")

    async def process_left_event(self, msg, user_id, bot_id, conn):
        chat = msg.get('chat')
        if not chat:
            return
        telegram_chat_id = chat.get('id')
        db_chat = next((c for c in self.chats if c['telegram_chat_id'] == telegram_chat_id and c['bot_id'] == bot_id and c['user_id'] == user_id), None)
        if not db_chat:
            return
        chat_id = db_chat['chat_id']
        # Определяем пользователя
        left_user = None
        if 'left_chat_member' in msg:
            left_user = msg['left_chat_member']
        elif 'left_chat_participant' in msg:
            left_user = msg['left_chat_participant']
        elif 'old_chat_member' in msg:
            left_user = msg['old_chat_member']
        if not left_user:
            return
        telegram_user_id = left_user.get('id')
        db_employee = next((e for e in self.employees if e['telegram_user_id'] == telegram_user_id and e['user_id'] == user_id), None)
        if not db_employee:
            return
        employee_id = db_employee['employee_id']
        # Деактивируем все связи пользователя с этим чатом
        for link in self.chat_employees:
            if link['chat_id'] == chat_id and link['employee_id'] == employee_id and link['user_id'] == user_id and link['is_active']:
                logger.info(f"Deactivating chat_employees link for chat_id={chat_id} employee_id={employee_id} user_id={user_id}")
                await conn.execute("""
                    UPDATE chat_employees SET is_active = false, updated_at = NOW() WHERE chat_id = $1 AND employee_id = $2 AND user_id = $3
                """, chat_id, employee_id, user_id)
                # Обновляем локально только если link — dict
                if isinstance(link, dict):
                    link['is_active'] = False

    async def handle_update(self, update, user_id, bot_id, conn):
        msg = update.get('message')
        if msg:
            # Если есть new_chat_members — обрабатываем только их (это всегда список)
            if 'new_chat_members' in msg:
                await self.process_update({'chat': msg['chat'], 'new_chat_members': msg['new_chat_members']}, user_id, bot_id, conn)
            else:
                # Иначе по отдельности
                for k in ['new_chat_member', 'new_chat_participant', 'text']:
                    if k in msg:
                        await self.process_update(msg, user_id, bot_id, conn)
            # left_chat_member, left_chat_participant
            for k in ['left_chat_member', 'left_chat_participant']:
                if k in msg:
                    await self.process_left_event(msg, user_id, bot_id, conn)
        my_chat_member = update.get('my_chat_member')
        if my_chat_member:
            if 'old_chat_member' in my_chat_member:
                await self.process_left_event({'chat': my_chat_member['chat'], 'left_chat_member': my_chat_member['old_chat_member']['user']}, user_id, bot_id, conn)
            if 'new_chat_member' in my_chat_member:
                await self.process_update({'chat': my_chat_member['chat'], 'new_chat_member': my_chat_member['new_chat_member']['user']}, user_id, bot_id, conn)

    async def run_cycle(self):
        await self.load_all_data()
        for bot in self.bots:
            bot_token = bot['bot_token']
            bot_id = bot['bot_id']
            user_id = bot['user_id']
            # Проверка чатов бота
            for chat in self.chats:
                if chat['bot_id'] != bot_id or chat['user_id'] != user_id:
                    continue
                if chat.get('status_id') == 3:
                    continue  # Исключаем чаты со статусом 3
                telegram_chat_id = chat['telegram_chat_id']
                chat_id = chat['chat_id']
                url = f"https://api.telegram.org/bot{bot_token}/getChatAdministrators"
                params = {"chat_id": telegram_chat_id}
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, params=params) as response:
                            if response.status == 200:
                                data = await response.json()
                                if data.get("ok"):
                                    admins = data.get("result", [])
                                    bot_is_admin = any(a.get("user", {}).get("id") == bot['telegram_user_id'] for a in admins)
                                    if not bot_is_admin:
                                        logger.info(f"Bot {bot_id} is not admin in chat {telegram_chat_id}, setting status=2")
                                        async with self.pool.acquire() as conn:
                                            await conn.execute("""
                                                UPDATE chats SET status_id = 2, updated_at = NOW() WHERE chat_id = $1
                                            """, chat_id)
                                    else:
                                        logger.info(f"Bot {bot_id} is admin in chat {telegram_chat_id}")
                                        # Если статус не 1, то обновить на 1
                                        if chat.get('status_id') != 1:
                                            logger.info(f"Bot {bot_id} is admin in chat {telegram_chat_id}, updating status to 1")
                                            async with self.pool.acquire() as conn:
                                                await conn.execute("""
                                                    UPDATE chats SET status_id = 1, updated_at = NOW() WHERE chat_id = $1
                                                """, chat_id)
                                else:
                                    logger.warning(f"Bot {bot_id} getChatAdministrators failed for chat {telegram_chat_id}: {data}")
                            elif response.status in (400, 403):
                                logger.warning(f"Bot {bot_id} lost access to chat {telegram_chat_id} (status {response.status}), setting type=5, status=3")
                                async with self.pool.acquire() as conn:
                                    await conn.execute("""
                                        UPDATE chats SET type_id = 5, status_id = 3, updated_at = NOW() WHERE chat_id = $1
                                    """, chat_id)
                            else:
                                logger.warning(f"Bot {bot_id} unexpected response {response.status} for chat {telegram_chat_id}")
                except Exception as e:
                    logger.error(f"Bot {bot_id} error checking chat {telegram_chat_id}: {e}")
                # Обработка по типу чата
                chat_type = chat.get('type_id')
                if chat_type == 1:
                    logger.info(f"[TYPE 1] Внешний чат обработка chat_id={chat_id}")
                    chat_links = [l for l in self.chat_employees if l['chat_id'] == chat_id]
                    to_remove = []
                    for link in chat_links:
                        employee = next((e for e in self.employees if e['employee_id'] == link['employee_id']), None)
                        if not employee:
                            continue
                        # Пропускаем самого бота
                        if employee.get('telegram_user_id') == bot['telegram_user_id']:
                            continue
                        if (
                            not link.get('is_active') or
                            not employee.get('is_active')
                        ):
                            to_remove.append((employee, link))
                    for employee, link in to_remove:
                        logger.info(f"[TYPE 1] Кикаем пользователя: chat_id={chat_id}, employee_id={employee['employee_id']}, telegram_user_id={employee['telegram_user_id']}")
                        kick_url = f"https://api.telegram.org/bot{bot_token}/kickChatMember"
                        kick_params = {"chat_id": telegram_chat_id, "user_id": employee['telegram_user_id']}
                        kicked = False
                        try:
                            async with aiohttp.ClientSession() as session:
                                async with session.post(kick_url, params=kick_params) as kick_response:
                                    kick_data = await kick_response.json()
                                    if kick_response.status == 200 and kick_data.get("ok"):
                                        logger.info(f"Пользователь {employee['telegram_user_id']} успешно удалён из чата {telegram_chat_id}")
                                        kicked = True
                                    elif (
                                        kick_response.status == 400 and (
                                            "not found" in (kick_data.get("description", "")).lower() or
                                            "user_not_participant" in (kick_data.get("description", "")).lower()
                                        )
                                    ):
                                        logger.info(f"Пользователь {employee['telegram_user_id']} не найден в чате {telegram_chat_id}, считаем удалённым")
                                        kicked = True
                                    else:
                                        logger.error(f"Не удалось удалить пользователя {employee['telegram_user_id']} из чата {telegram_chat_id}: {kick_data}")
                        except Exception as e:
                            logger.error(f"Ошибка при удалении пользователя {employee['telegram_user_id']} из чата {telegram_chat_id}: {e}")
                        if kicked:
                            logger.info(f"[TYPE 1] Удаляем связь: chat_id={chat_id}, employee_id={employee['employee_id']}, telegram_user_id={employee['telegram_user_id']}")
                            async with self.pool.acquire() as conn:
                                await conn.execute(
                                    """DELETE FROM chat_employees WHERE chat_id = $1 AND employee_id = $2 AND user_id = $3""",
                                    chat_id, employee['employee_id'], link['user_id']
                                )
                            self.chat_employees = [l for l in self.chat_employees if not (l['chat_id'] == chat_id and l['employee_id'] == employee['employee_id'] and l['user_id'] == link['user_id'])]
                            send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                            user_name = employee.get('full_name') or employee.get('telegram_username') or str(employee['employee_id'])
                            text = f"Пользователь {user_name} был удален из чата (ботом)"
                            send_params = {"chat_id": telegram_chat_id, "text": text}
                            try:
                                async with aiohttp.ClientSession() as session:
                                    await session.post(send_url, params=send_params)
                            except Exception as e:
                                logger.error(f"Ошибка при отправке сообщения в чат {telegram_chat_id}: {e}")
                    # После обработки всех удалений — получить из API число участников чата и сравнить с числом активных связей
                    url_count = f"https://api.telegram.org/bot{bot_token}/getChatMembersCount"
                    params_count = {"chat_id": telegram_chat_id}
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(url_count, params=params_count) as response_count:
                                if response_count.status == 200:
                                    data_count = await response_count.json()
                                    if data_count.get("ok"):
                                        chat_members_count = data_count.get("result", 0)
                                        active_links = [l for l in self.chat_employees if l['chat_id'] == chat_id and l.get('is_active')]
                                        db_count = len(active_links)
                                        unknown_count = chat_members_count - db_count
                                        logger.info(f"[TYPE 1] chat_id={chat_id}: members_count={chat_members_count}, db_count={db_count}, unknown_count={unknown_count}")
                                        if chat.get('user_num') != chat_members_count or chat.get('unknown_user') != unknown_count:
                                            logger.info(f"[TYPE 1] chat_id={chat_id}: updating user_num={chat_members_count}, unknown_user={unknown_count}")
                                            async with self.pool.acquire() as conn:
                                                await conn.execute(
                                                    """UPDATE chats SET user_num = $1, unknown_user = $2, updated_at = NOW() WHERE chat_id = $3""",
                                                    chat_members_count, unknown_count, chat_id
                                                )
                                    else:
                                        logger.warning(f"[TYPE 1] chat_id={chat_id}: getChatMembersCount failed: {data_count}")
                                else:
                                    logger.warning(f"[TYPE 1] chat_id={chat_id}: getChatMembersCount HTTP {response_count.status}")
                    except Exception as e:
                        logger.error(f"[TYPE 1] chat_id={chat_id}: error in getChatMembersCount: {e}")
                elif chat_type == 2:
                    logger.info(f"[TYPE 2] Внутренний чат обработка chat_id={chat_id}")
                    chat_links = [l for l in self.chat_employees if l['chat_id'] == chat_id]
                    # Сначала определяем пользователей для удаления
                    to_remove = []
                    for link in chat_links:
                        employee = next((e for e in self.employees if e['employee_id'] == link['employee_id']), None)
                        if not employee:
                            continue
                        # Пропускаем самого бота
                        if employee.get('telegram_user_id') == bot['telegram_user_id']:
                            continue
                        if (
                            employee.get('is_external') or
                            not link.get('is_active') or
                            (employee.get('is_active') and not link.get('is_active'))
                        ):
                            to_remove.append((employee, link))
                    # Сначала кикаем всех таких пользователей
                    for employee, link in to_remove:
                        logger.info(f"[TYPE 2] Кикаем пользователя: chat_id={chat_id}, employee_id={employee['employee_id']}, telegram_user_id={employee['telegram_user_id']}")
                        kick_url = f"https://api.telegram.org/bot{bot_token}/kickChatMember"
                        kick_params = {"chat_id": telegram_chat_id, "user_id": employee['telegram_user_id']}
                        kicked = False
                        try:
                            async with aiohttp.ClientSession() as session:
                                async with session.post(kick_url, params=kick_params) as kick_response:
                                    kick_data = await kick_response.json()
                                    if kick_response.status == 200 and kick_data.get("ok"):
                                        logger.info(f"Пользователь {employee['telegram_user_id']} успешно удалён из чата {telegram_chat_id}")
                                        kicked = True
                                    elif (
                                        kick_response.status == 400 and (
                                            "not found" in (kick_data.get("description", "")).lower() or
                                            "user_not_participant" in (kick_data.get("description", "")).lower()
                                        )
                                    ):
                                        logger.info(f"Пользователь {employee['telegram_user_id']} не найден в чате {telegram_chat_id}, считаем удалённым")
                                        kicked = True
                                    else:
                                        logger.error(f"Не удалось удалить пользователя {employee['telegram_user_id']} из чата {telegram_chat_id}: {kick_data}")
                        except Exception as e:
                            logger.error(f"Ошибка при удалении пользователя {employee['telegram_user_id']} из чата {telegram_chat_id}: {e}")
                        # Деактивируем связь только если кик был успешен или пользователь не найден
                        if kicked:
                            logger.info(f"[TYPE 2] Удаляем связь: chat_id={chat_id}, employee_id={employee['employee_id']}, telegram_user_id={employee['telegram_user_id']}")
                            async with self.pool.acquire() as conn:
                                await conn.execute(
                                    """DELETE FROM chat_employees WHERE chat_id = $1 AND employee_id = $2 AND user_id = $3""",
                                    chat_id, employee['employee_id'], link['user_id']
                                )
                            # Удаляем из локального списка
                            self.chat_employees = [l for l in self.chat_employees if not (l['chat_id'] == chat_id and l['employee_id'] == employee['employee_id'] and l['user_id'] == link['user_id'])]
                            # Отправляем сообщение в чат
                            send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                            user_name = employee.get('full_name') or employee.get('telegram_username') or str(employee['employee_id'])
                            text = f"Пользователь {user_name} был удален из чата (ботом)"
                            send_params = {"chat_id": telegram_chat_id, "text": text}
                            try:
                                async with aiohttp.ClientSession() as session:
                                    await session.post(send_url, params=send_params)
                            except Exception as e:
                                logger.error(f"Ошибка при отправке сообщения в чат {telegram_chat_id}: {e}")
                    # После обработки всех удалений — получить из API число участников чата и сравнить с числом активных связей
                    url_count = f"https://api.telegram.org/bot{bot_token}/getChatMembersCount"
                    params_count = {"chat_id": telegram_chat_id}
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(url_count, params=params_count) as response_count:
                                if response_count.status == 200:
                                    data_count = await response_count.json()
                                    if data_count.get("ok"):
                                        chat_members_count = data_count.get("result", 0)
                                        active_links = [l for l in self.chat_employees if l['chat_id'] == chat_id and l.get('is_active')]
                                        db_count = len(active_links)
                                        unknown_count = chat_members_count - db_count
                                        logger.info(f"[TYPE 2] chat_id={chat_id}: members_count={chat_members_count}, db_count={db_count}, unknown_count={unknown_count}")
                                        if chat.get('user_num') != chat_members_count or chat.get('unknown_user') != unknown_count:
                                            logger.info(f"[TYPE 2] chat_id={chat_id}: updating user_num={chat_members_count}, unknown_user={unknown_count}")
                                            async with self.pool.acquire() as conn:
                                                await conn.execute(
                                                    """UPDATE chats SET user_num = $1, unknown_user = $2, updated_at = NOW() WHERE chat_id = $3""",
                                                    chat_members_count, unknown_count, chat_id
                                                )
                                    else:
                                        logger.warning(f"[TYPE 2] chat_id={chat_id}: getChatMembersCount failed: {data_count}")
                                else:
                                    logger.warning(f"[TYPE 2] chat_id={chat_id}: getChatMembersCount HTTP {response_count.status}")
                    except Exception as e:
                        logger.error(f"[TYPE 2] chat_id={chat_id}: error in getChatMembersCount: {e}")
                elif chat_type in (3, 4):
                    logger.info(f"[TYPE 3/4] Чтение/новый чат обработка chat_id={chat_id}")
                    # Получаем число участников через Telegram API
                    url_count = f"https://api.telegram.org/bot{bot_token}/getChatMembersCount"
                    params_count = {"chat_id": telegram_chat_id}
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(url_count, params=params_count) as response_count:
                                if response_count.status == 200:
                                    data_count = await response_count.json()
                                    if data_count.get("ok"):
                                        chat_members_count = data_count.get("result", 0)
                                        # Считаем число связей в БД
                                        db_links = [l for l in self.chat_employees if l['chat_id'] == chat_id and l['is_active']]
                                        db_count = len(db_links)
                                        unknown_count = chat_members_count - db_count
                                        logger.info(f"chat_id={chat_id}: members_count={chat_members_count}, db_count={db_count}, unknown_count={unknown_count}")
                                        if chat.get('user_num') == chat_members_count and chat.get('unknown_user') == unknown_count:
                                            logger.info(f"chat_id={chat_id}: counts match, nothing to update")
                                        else:
                                            logger.info(f"chat_id={chat_id}: updating user_num={chat_members_count}, unknown_user={unknown_count}")
                                            async with self.pool.acquire() as conn:
                                                await conn.execute("""
                                                    UPDATE chats SET user_num = $1, unknown_user = $2, updated_at = NOW() WHERE chat_id = $3
                                                """, chat_members_count, unknown_count, chat_id)
                                    else:
                                        logger.warning(f"chat_id={chat_id}: getChatMembersCount failed: {data_count}")
                                else:
                                    logger.warning(f"chat_id={chat_id}: getChatMembersCount HTTP {response_count.status}")
                    except Exception as e:
                        logger.error(f"chat_id={chat_id}: error in getChatMembersCount: {e}")
                elif chat_type == 6:
                    logger.info(f"[TYPE 6] Заблокированный чат обработка chat_id={chat_id}")
                    # TODO: обработка заблокированного чата
            # Старый цикл по updates
            updates = await self.fetch_updates(bot_token, bot_id)
            async with self.pool.acquire() as conn:
                for update in updates:
                    await self.handle_update(update, user_id, bot_id, conn)

    async def run(self):
        await self.init_db()
        while True:
            await self.run_cycle()
            await asyncio.sleep(self.interval)

async def main():
    service = BotService()
    await service.run()

if __name__ == "__main__":
    asyncio.run(main()) 
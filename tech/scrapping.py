from pathlib import Path

import aiofiles
import asyncio

from tech.auth_data import white_list, black_list
import json

json_file = Path("sent_messages.json")

sent_data_lock = asyncio.Lock()

async def save_sent_messages(sent_data):
    try:
        serializable_data = {user_id: list(message_ids) for user_id, message_ids in sent_data.items()}
        async with aiofiles.open("sent_messages.json", "w") as f:
            await f.write(json.dumps(serializable_data))
    except Exception as e:
        print(f"Ошибка при сохранении отправленных сообщений: {e}")


async def get_msg(app, chat_id, sent_data):
    try:
        print(f"Обработка чата с ID {chat_id} началась.")
        chat = await app.get_chat(chat_id)
        async for message in app.get_chat_history(chat.id, limit=200):
            user_id = str(message.from_user.id)
            message_id = str(message.id)

            if (
                message.from_user
                and message.text
                and message_id not in sent_data.get(user_id, set())
            ):
                text_lower = message.text.lower()

                if any(word in text_lower for word in white_list) and not any(
                    word in text_lower for word in black_list
                ):
                    username = message.from_user.username
                    user_link = f"https://t.me/{username}" if username else f"tg://user?id={user_id}"

                    if user_id not in sent_data:
                        sent_data[user_id] = set()
                    sent_data[user_id].add(message_id)

                    await save_sent_messages(sent_data)

                    yield message.text, user_link, message_id, user_id
    except Exception as e:
        print(f"Ошибка в get_msg для чата {chat_id}: {e}")

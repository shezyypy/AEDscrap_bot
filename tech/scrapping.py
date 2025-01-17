from pathlib import Path

from tech.auth_data import white_list, black_list
import json

json_file = Path("sent_messages.json")

async def save_sent_messages(data):
    # Преобразуем множества в списки
    serializable_data = {key: list(value) for key, value in data.items()}
    with json_file.open("w") as f:
        json.dump(serializable_data, f, indent=4)


async def get_msg(app, chat_id, sent_data):
    try:
        print(f"Обработка чата с ID {chat_id} началась.")
        chat = await app.get_chat(chat_id)
        async for message in app.get_chat_history(chat.id, limit=200):
            if (
                message.from_user
                and message.text
                and str(message.id) not in sent_data.get(str(message.from_user.id), set())
            ):
                for i in range(len(white_list)):
                    for j in range(len(black_list)):
                        if white_list[i] in message.text and black_list[j] not in message.text:

                            user_id = message.from_user.id
                            username = message.from_user.username

                            if username:
                                user_link = f"https://t.me/{username}"
                            else:
                                user_link = None

                            # Обработка уникальных сообщений
                            if str(user_id) not in sent_data:
                                sent_data[str(user_id)] = set()
                            sent_data[str(user_id)].add(str(message.id))

                            # Сохраняем обновлённые данные в JSON
                            await save_sent_messages(sent_data)

                            # Возвращаем сообщение, ссылку, ID сообщения и пользователя
                            yield message.text, user_link, str(message.id), str(user_id)
    except Exception as e:
        print(f"Ошибка в get_msg для чата {chat_id}: {e}")
import logging
import aiofiles
import asyncio
import json
from pathlib import Path
from pyrogram import Client

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from tech.auth_data import api_id, api_hash, token, chats
from tech.scrapping import get_msg

bot = Bot(token)
dp = Dispatcher()

is_running = False
task = None
json_file = Path("sent_messages.json")

if not json_file.exists():
    json_file.write_text(json.dumps({}))
else:
    json_file.write_text(json.dumps({}))


async def main():
    await dp.start_polling(bot)


async def load_sent_messages():
    try:
        async with aiofiles.open("sent_messages.json", "r") as f:
            data = await f.read()
            return {user_id: set(message_ids) for user_id, message_ids in json.loads(data).items()}
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Ошибка при загрузке отправленных сообщений: {e}")
        return {}


async def clear_sent_messages():
    json_file.write_text(json.dumps({}))


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("ну че, игнатик) работать готов?")


async def message_sending_loop(message: Message):
    global is_running
    is_running = True

    sent_data = await load_sent_messages()
    print("Цикл отправки сообщений запущен.")

    try:
        while is_running:
            app = Client("Ignat", api_id=api_id, api_hash=api_hash)
            await app.start()
            print(f"Количество чатов для обработки: {len(chats)}")
            for i, chat_id in enumerate(chats):
                if not is_running:
                    break

                print(f"Обрабатываю чат {i + 1}/{len(chats)} с ID {chat_id}.")
                async for text, user_link, message_link in get_msg(app, chat_id, sent_data):
                    try:
                        print(f"Отправка сообщения: {text}, пользователь: {user_link}, ссылка на сообщение: {message_link}")
                        if user_link is not None:
                            await message.answer(
                                text=(
                                    f"Сообщение от пользователя:\n{text}\n\n"
                                    f"Перейти на профиль: <a href=\"{user_link}\">нажмите сюда</a>\n"
                                    f"Перейти к сообщению: <a href=\"{message_link}\">нажмите сюда</a>"
                                ),
                                parse_mode="HTML"
                            )
                    except Exception as e:
                        print(f"Ошибка при отправке сообщения: {e}")

                print(f"{i + 1}/{len(chats)} чатов обработано.")
                await asyncio.sleep(2)
            await app.stop()

    except Exception as e:
        print(f"Цикл завершился из-за ошибки: {e}")
    finally:
        await app.stop()
        is_running = False
        print("Цикл отправки сообщений завершён.")


@dp.message(Command("ready"))
async def start_sending(message: Message):
    global task, is_running

    if is_running:
        await message.answer("Процесс уже запущен!")
        return

    task = asyncio.create_task(message_sending_loop(message))
    await message.answer("Начинаю отправку сообщений. Для остановки введите /stop.")


@dp.message(Command("stop"))
async def stop_sending(message: Message):
    global task, is_running

    if not is_running:
        await message.answer("Процесс не запущен или уже остановлен.")
        return

    print("Команда /stop получена, останавливаю процесс.")
    is_running = False
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            print("Task был успешно остановлен.")

    await clear_sent_messages()
    await message.answer("Останавливаю процесс и очищаю данные о сообщениях.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("я все")

import logging
import asyncio
from pathlib import Path
import json

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, Message, CallbackQuery

from pyrogram import Client

from tech.auth_data import api_id, api_hash, token, chats
from tech.scrapping import get_msg

bot = Bot(token)
dp = Dispatcher()

is_running = False
task = None
json_file = Path("sent_messages.json")


async def main():
    await dp.start_polling(bot)


if not json_file.exists():
    json_file.write_text(json.dumps({}))
else:
    json_file.write_text(json.dumps({}))


async def load_sent_messages():
    with json_file.open("r") as f:
        data = json.load(f)
    # Преобразуем списки обратно в множества
    return {key: set(value) for key, value in data.items()}


async def save_sent_messages(data):
    # Преобразуем множества в списки
    serializable_data = {key: list(value) for key, value in data.items()}
    with json_file.open("w") as f:
        json.dump(serializable_data, f, indent=4)


async def clear_sent_messages():
    json_file.write_text(json.dumps({}))


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("ну че, игнатик) работать готов?")


async def message_sending_loop(message: Message, app):
    global is_running
    is_running = True
    await app.start()

    sent_data = await load_sent_messages()
    print("Цикл отправки сообщений запущен.")

    try:
        while is_running:
            print(f"Количество чатов для обработки: {len(chats)}")
            for i, chat_id in enumerate(chats):
                if not is_running:
                    break

                print(f"Обрабатываю чат {i + 1}/{len(chats)} с ID {chat_id}.")
                async for text, user_link, message_id, user_id in get_msg(app, chat_id, sent_data):
                    try:
                        print(f"Отправка сообщения: {text}, пользователь: {user_link}")
                        if user_link is not None:
                            await message.answer(
                                text=f"Сообщение от пользователя:{text}\n\nПерейти на профиль: <a href=\"{user_link}\">нажмите сюда</a>",
                                parse_mode="HTML"
                            )
                    except Exception as e:
                        print(f"Ошибка при отправке сообщения: {e}")

                print(f"{i + 1}/{len(chats)} чатов обработано.")
                await asyncio.sleep(2)

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

    app = Client("Ignat", api_id=api_id, api_hash=api_hash)
    task = asyncio.create_task(message_sending_loop(message, app))
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

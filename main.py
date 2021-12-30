import asyncio
import configparser
import csv
import json
import os

from telethon.sync import TelegramClient
from telethon import connection

# для корректного переноса времени сообщений в json
from datetime import date, datetime

# классы для работы с каналами
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch

# класс для работы с сообщениями
from telethon.tl.functions.messages import GetHistoryRequest
#для работы с полем about
from telethon import functions, types
from dotenv import load_dotenv
load_dotenv()

# Присваиваем значения внутренним переменным
# Получить их можно тут https://my.telegram.org/apps
api_id = os.getenv('api_id')
api_hash = os.getenv('api_hash')
# username = 'Parsing_group'
phone = os.getenv('phone')
# Создадим объект клиента Telegram API:
client = TelegramClient(phone, api_id, api_hash)
client.start()


async def dump_all_participants(channel):
    """Записывает json-файл с информацией о всех участниках канала/чата"""
    offset_user = 0  # номер участника, с которого начинается считывание
    limit_user = 100  # максимальное число записей, передаваемых за один раз

    all_participants = []  # список всех участников канала
    filter_user = ChannelParticipantsSearch('')

    while True:
        participants = await client(GetParticipantsRequest(channel, filter_user, 0, limit_user, hash=0))
        if not participants.users:
            break
        all_participants.extend(participants.users)
        offset_user += len(participants.users)

    all_users_details = []  # список словарей с интересующими параметрами участников канала

    for participant in all_participants:
        #result_about = client(functions.users.GetFullUserRequest(participant.id))
        #print(result_about.about)
        all_users_details.append({"id": participant.id,
                                  "first_name": participant.first_name,
                                  "last_name": participant.last_name,
                                  "user": participant.username,
                                  "phone": participant.phone,
                                  "is_bot": participant.bot
                                  #"about": result_about.about
                                  })
    print("Saving in file...")

    # Сохраняем и читаем JSON
    with open('channel_users.json', 'w', encoding="utf-8") as outfile:
        json.dump(all_users_details, outfile, indent=4, ensure_ascii=False)
    print(f"{len(all_participants)} members scraped successfully")

    with open("channel_users.json", encoding="utf-8") as file:
        all_users = json.load(file)

    # Создаем и заполняем CSV
    with open("channel_users.csv", "w", newline='') as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(
            (
                "id",
                "Имя",
                "Фамилия",
                "Username",
                "Телефон",
                "Бот/Не бот"
                #"О себе"
            )
        )
        file.close()
    with open("channel_users.csv", "a", newline='') as file:
        writer = csv.writer(file, delimiter=";")
        for participant in all_users:
            writer.writerow(
                (
                participant["id"],
                participant["first_name"],
                participant["last_name"],
                participant["user"],
                participant["phone"],
                participant["is_bot"]
                #participant["about"]
                )
            )
        file.close()


async def dump_all_messages(channel):
    """Записывает json-файл с информацией о всех сообщениях канала/чата"""
    offset_msg = 0  # номер записи, с которой начинается считывание
    limit_msg = 100  # максимальное число записей, передаваемых за один раз

    all_messages = []  # список всех сообщений
    total_messages = 0
    total_count_limit = 0  # поменяйте это значение, если вам нужны не все сообщения

    class DateTimeEncoder(json.JSONEncoder):
        '''Класс для сериализации записи дат в JSON'''

        def default(self, o):
            if isinstance(o, datetime):
                return o.isoformat()
            if isinstance(o, bytes):
                return list(o)
            return json.JSONEncoder.default(self, o)

    while True:
        history = await client(GetHistoryRequest(
            peer=channel,
            offset_id=offset_msg,
            offset_date=None, add_offset=0,
            limit=limit_msg, max_id=0, min_id=0,
            hash=0))
        if not history.messages:
            break
        messages = history.messages
        for message in messages:
            all_messages.append(message.to_dict())
        offset_msg = messages[len(messages) - 1].id
        total_messages = len(all_messages)
        if total_count_limit != 0 and total_messages >= total_count_limit:
            break

    # with open('channel_messages.json', 'w', encoding='utf8') as outfile:
    #     json.dump(all_messages, outfile, ensure_ascii=False, cls=DateTimeEncoder)


async def main():
    #url = input("Введите ссылку на канал или чат: ")
    url = 'https://t.me/viabtcrussia' #'https://t.me/viabtcrussia'
    channel = await client.get_entity(url)
    await dump_all_participants(channel)


# if __name__ == '__main__':
#     loop = asyncio.get_event_loop()
#     loop.run_until_complete(main())


with client:
    client.loop.run_until_complete(main())

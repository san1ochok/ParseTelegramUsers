import configparser
import json
from datetime import datetime
from telethon import TelegramClient
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import ChannelParticipantsSearch

# - - - - - Config - - - - - #
config = configparser.ConfigParser()
config.read("config.ini")

api_id = config['Telegram']['api_id']
api_hash = config['Telegram']['api_hash']
username = config['Telegram']['username']
token = config['Telegram']['token']

# - - - - - Connect to Account - - - - - #
client = TelegramClient(username, api_id, api_hash)

# - - - - - Connect to Bot - - - - - #
# client = TelegramClient(token, api_id, api_hash)


# - - - - - User parse - - - - - #
async def dump_all_participants(channel):
    offset_user = 0
    limit_user = 50000

    all_participants = []
    filter_user = ChannelParticipantsSearch('')

    while True:
        participants = await client(GetParticipantsRequest(channel,
                                                           filter_user, offset_user, limit_user, hash=0))
        if not participants.users:
            break
        all_participants.extend(participants.users)
        offset_user += len(participants.users)

    all_users_details = []

    for participant in all_participants:
        all_users_details.append({"id": participant.id,
                                  "user": participant.username,
                                  "is_bot": participant.bot})

    with open('channel_users.json', 'w', encoding='utf8') as outfile:
        json.dump(all_users_details, outfile, ensure_ascii=False)


# - - - - - Message parse - - - - - #
async def dump_all_messages(channel):
    offset_msg = 0
    limit_msg = 100

    all_messages = []
    total_messages = 0
    total_count_limit = 0

    class DateTimeEncoder(json.JSONEncoder):

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

    with open('channel_messages.json', 'w', encoding='utf8') as outfile:
        json.dump(all_messages, outfile, ensure_ascii=False, cls=DateTimeEncoder)


# - - - - - Main - - - - - #
async def main():
    url = input("Введите ссылку на канал или чат: ")
    channel = await client.get_entity(url)
    await dump_all_participants(channel)
    # await dump_all_messages(channel)
    with open("channel_users.json", "r", encoding="utf-8") as file:
        json_array = json.loads(file.read())
    parsed = json_pars(json_array=json_array, key="user")
    file = open("users.txt", "w", encoding='utf8')
    file.write('\n'.join(filter(lambda x: x if x is not None else '', parsed)))
    file.close()
    # print("Количество пользователей в БД: ", len(parsed))
    print("Пользователи успешно записаны в файл 'users.txt'")


# - - - - - JSON treatment - - - - - #
def json_pars(*, json_array: json, result_list: list = None, key: str) -> list:
    if result_list is None:
        result_list = []
    if isinstance(json_array, list):
        for i in json_array:
            json_pars(json_array=i, result_list=result_list, key=key)
    if isinstance(json_array, dict):
        for i in json_array.keys():
            array = json_array[i]
            if i == key:
                result_list.append(array)
            else:
                json_pars(json_array=array, result_list=result_list, key=key)
    return result_list


# - - - - - LOOP - - - - - #
with client:
    client.loop.run_until_complete(main())

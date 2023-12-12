import discord
import aiohttp
import asyncio
import json
from discord.ext import tasks

TOKEN = 'MTE2MzUxNTM2MDk2ODk3NDQwNw.GzDPcL.7hfItECEG4PoGpom95pveS3R0yDCQDxFyludSg'
CHANNEL_ID = 1172181537123467294
CHECK_INTERVAL = 3  # Интервал в секундах для автоматической проверки серверов

# Загрузка адресов серверов из файла server.json
with open('server.json', 'r') as file:
    server_addresses = json.load(file)

intents = discord.Intents.default()
client = discord.Client(intents=intents)

async def check_server_status(address):
    url = f'https://mcapi.xdefcon.com/server/{address}/status/json'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                if data.get('online'):
                    return "Online"
                elif data.get('serverStatus') == "offline":
                    return "Offline"
                else:
                    return "Не удалось определить статус"
            else:
                return "Ошибка при запросе статуса"

async def update_server_status(channel, address):
    status = await check_server_status(address)
    return await channel.send(f"Сервер {address}: {status}")

async def update_servers(channel):
    status_messages = {}

    for address in server_addresses:
        status_messages[address] = await update_server_status(channel, address)

    return status_messages

@tasks.loop(seconds=CHECK_INTERVAL)
async def update_server_statuses():
    channel = client.get_channel(CHANNEL_ID)

    for address in server_addresses:
        status_messages[address] = await update_server_status(channel, address)

@client.event
async def on_ready():
    global status_messages
    channel = client.get_channel(CHANNEL_ID)
    status_messages = await update_servers(channel)
    update_server_statuses.start()

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!status'):
        await message.channel.send("Список серверов:")
        for address in server_addresses:
            await message.channel.send(address)

    if message.content.startswith('!add_server'):
        if len(message.content.split()) == 2:
            new_address = message.content.split()[1]
            server_addresses.append(new_address)
            with open('server.json', 'w') as file:
                json.dump(server_addresses, file)
            channel = client.get_channel(CHANNEL_ID)
            global status_messages
            status_messages[new_address] = await update_server_status(channel, new_address)
            await message.channel.send(f"Сервер {new_address} добавлен!")
        else:
            await message.channel.send("Использование: !add_server <адрес_сервера>")

client.run(TOKEN)

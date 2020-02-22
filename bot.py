import os
from bin import *
from servers import Servers, ServerCache
from settings import Settings

import discord
from discord.ext import commands

TOKEN = os.environ["TOKEN"]

bot = discord.Client()

game_servers = Servers()
game_servers.query()

# get servers
servers = game_servers.load()

# get settings
settings = Settings.get()

# bot ready action
@bot.event
async def on_ready():
    # set username
    await bot.user.edit(username='DiscordGSM')

    print(f'Logged in as: {bot.user.name}')
    print(f'With ID: {bot.user.id}')
    print('----------------')

    # set bot presence
    await bot.change_presence(status=discord.Status.online, activity=discord.Activity(name=f'{len(servers)} game servers', type=3))

    # remove old messages
    for server in servers:
        await bot.get_channel(server['channel']).purge(check=lambda m: m.author==bot.user)

    # send embed
    messages = []
    for server in servers:
        messages.append(await bot.get_channel(server['channel']).send(embed=get_embed(server)))

    # edit embed
    for i in range(len(servers)): 
        await messages[i].edit(embed=get_embed(servers[i]))

    if False:
        test = SourceQuery('192.187.127.218', 27015)
        result = test.getInfo()
        print(result)

# get discord message embed
def get_embed(server):
    server_cache = ServerCache(server['addr'], server['port'])
    data = server_cache.get_data()

    if data:
        status = server_cache.get_status()

        if status == 'Online':
            emoji = ":green_circle:"
            if data['maxplayers'] <= data['players']:
                color = discord.Color.from_rgb(240, 71, 71) # red
            elif data['maxplayers'] <= data['players'] * 2:
                color = discord.Color.from_rgb(250, 166, 26) # yellew
            else:
                color = discord.Color.from_rgb(67, 181, 129) # green
        else:
            emoji = ":red_circle:"
            color = discord.Color.from_rgb(32, 34, 37) # dark

        embed = discord.Embed(title=f'{data["game"]}', description=f'{settings["fieldname"]["status"]}: {emoji} {status}', color=color)
        embed.add_field(name=f'{settings["fieldname"]["servername"]}', value=f'{data["name"]}', inline=False)
        embed.add_field(name=f'{settings["fieldname"]["currentmap"]}', value=f'{data["map"]}', inline=True)

        if status == 'Online':
            value = f'{data["players"]}' # example: 20/32
            if data['bots'] > 0:
                value += f'(data["bots"])' # example: 20(2)/32
        else:
            value = f'0' # example: 0/32
                
        embed.add_field(name=f'{settings["fieldname"]["players"]}', value=f'{value}/{data["maxplayers"]}', inline=True)
        embed.add_field(name=f'{settings["fieldname"]["addressport"]}', value=f'{data["addr"]}:{data["port"]}', inline=True)
    else:
        color = discord.Color.from_rgb(240, 71, 71)
        embed = discord.Embed(title='ERROR', description=f'{settings["fieldname"]["status"]}: :warning: Fail to query', color=color)
        embed.add_field(name=f'{settings["fieldname"]["addressport"]}', value=f'{server["addr"]}:{server["port"]}', inline=True)

    return embed

# run the bot
bot.run(TOKEN)
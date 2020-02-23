import os
import time
import asyncio
import aiohttp
from threading import Thread
from datetime import datetime

# discord
import discord
from discord.ext import commands

# discordgsm
from bin import *
from servers import Servers, ServerCache
from settings import Settings

VERSION = '1.0.0'

TOKEN = os.environ["TOKEN"]

# get settings
settings = Settings.get()

# set up bot
bot = commands.Bot(command_prefix=settings['prefix'])

# query servers and save cache
game_servers = Servers()

# get servers
servers = game_servers.load()

# discord messages
messages = []

# bot ready action
@bot.event
async def on_ready():
    # set username and avatar
    with open('images/discordgsm.png', 'rb') as file:
        avatar = file.read()
        await bot.user.edit(username='DiscordGSM', avatar=avatar)

    # print info to console
    print(f'Logged in as: {bot.user.name}')
    print(f'Robot ID: {bot.user.id}')
    owner_id = (await bot.application_info()).owner.id
    print(f'Owner ID: {owner_id}')
    print('----------------')

    # set bot presence
    await bot.change_presence(status=discord.Status.online, activity=discord.Activity(name=f'{len(servers)} game servers', type=3))

    # remove old messages
    for server in servers:
        await bot.get_channel(server['channel']).purge(check=lambda m: m.author==bot.user)

    # send embed
    for server in servers:
        messages.append(await bot.get_channel(server['channel']).send(embed=get_embed(server)))

    # print delay time
    delay = int(settings['refreshrate']) if int(settings['refreshrate']) > 5 else 5
    print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + f' Edit messages every {delay} second')

    # start print servers
    t = Thread(target=await print_servers())
    t.start()

# print servers to discord
@asyncio.coroutine
async def print_servers():
    while True:
        # query servers and save cache
        game_servers.query()

        # edit embed
        for i in range(len(servers)):
            await messages[i].edit(embed=get_embed(servers[i]))

        # delay server query
        delay = int(settings['refreshrate']) if int(settings['refreshrate']) > 5 else 5
        await asyncio.sleep(delay)

# get game server embed
def get_embed(server):
    # load server cache
    server_cache = ServerCache(server['addr'], server['port'])
    data = server_cache.get_data()

    if data:
        # load server status Online/Offline
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

        embed = discord.Embed(title=f'{data["name"]}', color=color)
        embed.add_field(name=f'{settings["fieldname"]["status"]}', value=f'{emoji} {status}', inline=True)
        embed.add_field(name=f'{settings["fieldname"]["address"]}', value=f'{data["addr"]}', inline=True)
        embed.add_field(name=f'{settings["fieldname"]["port"]}', value=f'{data["port"]}', inline=True)
        embed.add_field(name=f'{settings["fieldname"]["game"]}', value=f'{data["game"]}', inline=True)
        embed.add_field(name=f'{settings["fieldname"]["currentmap"]}', value=f'{data["map"]}', inline=True)

        if status == 'Online':
            value = f'{data["players"]}' # example: 20/32
            if data['bots'] > 0:
                value += f' ({data["bots"]})' # example: 20 (2)/32
        else:
            value = f'0' # example: 0/32
                
        embed.add_field(name=f'{settings["fieldname"]["players"]}', value=f'{value}/{data["maxplayers"]}', inline=True)
    else:
        # server fail to query
        color = discord.Color.from_rgb(240, 71, 71) # red
        embed = discord.Embed(title='ERROR', description=f'{settings["fieldname"]["status"]}: :warning: Fail to query', color=color)
        embed.add_field(name=f'{settings["fieldname"]["addressport"]}', value=f'{server["addr"]}:{server["port"]}', inline=True)
    
    embed.set_footer(text=f'DiscordGSM v{VERSION} | Last update: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    return embed

# command: servers
# list all the servers in configs/servers.json
@bot.command(name='dgsm', aliases=['discordgsm'])
@commands.is_owner()
async def _dgsm(ctx):
    title = f'Command: {settings["prefix"]}dgsm'
    description = f'Useful commands: \n{settings["prefix"]}serveradd - Add a server'
    description += f'\n{settings["prefix"]}serverdel - Delete a server\n{settings["prefix"]}serversrefresh - Refresh server list'
    color = discord.Color.from_rgb(114, 137, 218) # discord theme color
    embed = discord.Embed(title=title, description=description, color=color)
    embed.add_field(name=f'Support server', value=f'[Click Here](https://discord.gg/Cg4Au9T)', inline=True)
    embed.add_field(name=f'Github', value=f'[Click Here](https://github.com/BattlefieldDuck/DiscordGSM)', inline=True)
    await ctx.send(embed=embed)

# command: servers
# list all the servers in configs/servers.json
@bot.command(name='serversrefresh')
@commands.is_owner()
async def _serversrefresh(ctx):
    global servers

    # refresh server list
    game_servers.refresh()

    # reload servers
    servers = game_servers.load()

    # set bot presence
    await bot.change_presence(status=discord.Status.online, activity=discord.Activity(name=f'{len(servers)} game servers', type=3))

    # remove old messages
    for server in servers:
        await bot.get_channel(server['channel']).purge(check=lambda m: m.author==bot.user)

    # reset messages
    global messages
    messages = []

    # send embed
    for server in servers:
        messages.append(await bot.get_channel(server['channel']).send(embed=get_embed(server)))

    # log and send response
    print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' Refreshed servers')
    delay = int(settings['refreshrate']) if int(settings['refreshrate']) > 5 else 5
    title = f'Command: {settings["prefix"]}serversrefresh'
    color = discord.Color.from_rgb(114, 137, 218) # discord theme color
    embed = discord.Embed(title=title, description=f'Servers list refreshed', color=color)
    await ctx.send(embed=embed)

# command: servers
# list all the servers in configs/servers.json
@bot.command(name='servers')
@commands.is_owner()
async def _servers(ctx):
    title = f'Command: {settings["prefix"]}servers'
    color = discord.Color.from_rgb(114, 137, 218) # discord theme color
    embed = discord.Embed(title=title, color=color)
    type_game, addr_port, channel = '', '', ''

    servers = game_servers.load()

    for i in range(len(servers)):
        type_game += f'{i+1}. {servers[i]["type"]}:{servers[i]["game"]}\n'
        addr_port += f'{servers[i]["addr"]}:{servers[i]["port"]}\n'
        channel += f'{servers[i]["channel"]}\n'

    embed.add_field(name='ID. Type:Game', value=type_game, inline=True)
    embed.add_field(name='Address:Port', value=addr_port, inline=True)
    embed.add_field(name='Channel ID', value=channel, inline=True)
    await ctx.send(embed=embed)

# command: serveradd
# add a server to configs/servers.json
@bot.command(name='serveradd')
@commands.is_owner()
async def _serveradd(ctx, *args):
    title = f'Command: {settings["prefix"]}serveradd'
    color = discord.Color.from_rgb(114, 137, 218) # discord theme color

    if len(args) == 5:
        type, game, addr, port, channel = args

        if port.isdigit() and channel.isdigit():
            game_servers.add(type, game, addr, port, channel)

            description=f'Server added successfully'
            embed = discord.Embed(title=title, description=description, color=color)
            embed.add_field(name='Type:Game', value=f'{type}:{game}', inline=True)
            embed.add_field(name='Address:Port', value=f'{addr}:{port}', inline=True)
            embed.add_field(name='Channel ID', value=channel, inline=True)
            await ctx.send(embed=embed)
            return

    description=f'Usage: {settings["prefix"]}serveradd <type> <game> <addr> <port> <channel>\nRemark: <port> and <channel> should be digit only'
    embed = discord.Embed(title=title, description=description, color=color)
    await ctx.send(embed=embed)

# command: serverdel
# delete a server by id from configs/servers.json
@bot.command(name='serverdel')
@commands.is_owner()
async def _serverdel(ctx, *args):
    title = f'Command: {settings["prefix"]}serverdel'
    color = discord.Color.from_rgb(114, 137, 218) # discord theme color

    if len(args) == 1:
        server_id = args[0]
        if server_id.isdigit():
            if game_servers.delete(server_id):
                description=f'Server deleted successfully. ID: {server_id}'
                embed = discord.Embed(title=title, description=description, color=color)
                await ctx.send(embed=embed)
                return

    description=f'Usage: {settings["prefix"]}serverdel <id>\nRemark: view id with command {settings["prefix"]}servers'
    embed = discord.Embed(title=title, description=description, color=color)
    await ctx.send(embed=embed)

# run the bot
bot.run(TOKEN)
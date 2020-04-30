import os
import urllib
import asyncio
import requests
from datetime import datetime

# discord
import discord
from discord.ext import tasks, commands

# discordgsm
from bin import *
from servers import Servers, ServerCache
from settings import Settings

class DiscordGSM():
    VERSION = '1.6.0'
    SETTINGS = Settings.get()
    DGSM_PREFIX = os.getenv("DGSM_PREFIX", SETTINGS.get('prefix', '!'))
    REFRESH_RATE = int(os.getenv('REFRESH_RATE', SETTINGS['refreshrate'])) if int(os.getenv('REFRESH_RATE', SETTINGS['refreshrate'])) > 5 else 5
    PRESENCE_TYPE = int(os.getenv('PRESENCE_TYPE', SETTINGS.get('presence_type', 3)))
    PRESENCE_RATE = int(os.getenv('PRESENCE_RATE', SETTINGS.get('presence_rate', 5)))

    def __init__(self, bot):
        print('\n----------------')
        print('Github: \thttps://github.com/DiscordGSM/DiscordGSM')
        print('Discord:\thttps://discord.gg/Cg4Au9T')
        print('----------------\n')

        self.bot = bot
        self.servers = Servers()
        self.server_list = self.servers.get()
        self.messages = []
        self.message_error_count = self.current_display_server = 0

    def start(self):
        self.print_to_console(f'Starting DiscordGSM v{self.VERSION}...')
        self.query_servers.start()    

    def cancel(self):
        self.query_servers.cancel()
        self.print_servers.cancel()
        self.presense_load.cancel()

    async def on_ready(self):
        # set username and avatar
        with open('images/discordgsm.png', 'rb') as file:
            try:
                await bot.user.edit(username='DiscordGSM', avatar=file.read())
            except:
                pass

        # print info to console
        print('\n----------------')
        print(f'Logged in as:\t{bot.user.name}')
        print(f'Robot ID:\t{bot.user.id}')
        app_info = await bot.application_info()
        print(f'Owner ID:\t{app_info.owner.id} ({app_info.owner.name})')
        print('----------------\n')

        self.print_presense_hint()
        self.presense_load.start()

        await self.set_channels_permissions()
        self.print_to_console(f'Query server and send discord embed every {self.REFRESH_RATE} seconds...')
        await self.refresh_discord_embed()
        self.print_servers.start()

    # query the servers
    @tasks.loop(seconds=REFRESH_RATE)
    async def query_servers(self):
        self.servers.query()

    # pre-query servers before ready
    @query_servers.before_loop
    async def before_query_servers(self):
        self.print_to_console('Clearing cache...')
        for file in os.listdir('cache'):
            if file.endswith('.txt') or file.endswith('.json'):
                os.remove(os.path.join('cache', file))

        self.print_to_console('Pre-Query servers...')
        self.servers.query()
        await self.bot.wait_until_ready()
        await self.on_ready()
    
    # send messages to discord
    @tasks.loop(seconds=REFRESH_RATE)
    async def print_servers(self):
        if self.message_error_count < 20:
            updated_count = 0
            for i in range(len(self.server_list)):
                try:
                    await self.messages[i].edit(embed=self.get_embed(self.server_list[i]))
                    updated_count += 1
                except:
                    self.message_error_count += 1
                    self.print_to_console(f'ERROR: message {i} fail to edit, message deleted or no permission. Server: {self.server_list[i]["addr"]}:{self.server_list[i]["port"]}')

            self.print_to_console(f'{updated_count} messages updated')
        else:
            self.message_error_count = 0
            self.print_to_console(f'Message ERROR reached, refreshing...')
            await self.refresh_discord_embed()
    
    # refresh discord presense
    @tasks.loop(minutes=PRESENCE_RATE)
    async def presense_load(self):
        # 1 = display number of servers, 2 = display total players/total maxplayers, 3 = display each server one by one every 10 minutes
        if len(self.server_list) == 0:
            activity_text = f'Command: {self.DGSM_PREFIX}dgsm'
        if self.PRESENCE_TYPE <= 1:
            activity_text = f'{len(self.server_list)} game servers'
        elif self.PRESENCE_TYPE == 2:
            total_activeplayers = total_maxplayers = 0
            for server in self.server_list:
                server_cache = ServerCache(server['addr'], server['port'])
                data = server_cache.get_data()
                if data and server_cache.get_status() == 'Online':
                    total_activeplayers += int(data['players'])
                    total_maxplayers += int(data['maxplayers'])
                  
            activity_text = f'{total_activeplayers}/{total_maxplayers} active players' if total_maxplayers > 0 else '0 players' 
        elif self.PRESENCE_TYPE >= 3:
            if self.current_display_server >= len(self.server_list):
                self.current_display_server = 0

            server_cache = ServerCache(self.server_list[self.current_display_server]['addr'], self.server_list[self.current_display_server]['port'])
            data = server_cache.get_data()
            if data and server_cache.get_status() == 'Online':
                activity_text = f'{data["players"]}/{data["maxplayers"]} on {data["name"]}' if int(data["maxplayers"]) > 0 else '0 players'

            self.current_display_server += 1

        if activity_text:
            await bot.change_presence(status=discord.Status.online, activity=discord.Activity(name=activity_text, type=3))
            self.print_to_console(f'Discord presence updated | {activity_text}')

    # set channels permissions before sending new messages
    async def set_channels_permissions(self):
        channels = [server['channel'] for server in self.server_list]
        channels = list(set(channels))  # remove duplicated channels
        for channel in channels:
            try:
                await bot.get_channel(channel).set_permissions(bot.user, read_messages=True, send_messages=True, reason='Display servers embed')
                self.print_to_console(f'Set channel: {channel} with permissions: read_messages, send_messages')
            except:
                self.print_to_console(f'Missing permission: Manage Roles, Manage Channels')

    # remove old discord embed and send new discord embed
    async def refresh_discord_embed(self):
        channels = [server['channel'] for server in self.server_list]
        channels = list(set(channels)) # remove duplicated channels
        for channel in channels:
            await bot.get_channel(channel).purge(check=lambda m: m.author==bot.user) # remove old bot messages in channels 
        self.messages = [await bot.get_channel(server['channel']).send(embed=self.get_embed(server)) for server in self.server_list]

    def print_to_console(self, value):
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S: ') + value)

    # 1 = display number of servers, 2 = display total players/total maxplayers, 3 = display each server one by one every 10 minutes
    def print_presense_hint(self):
        if self.PRESENCE_TYPE <= 1:
            hints = f'number of servers'
        elif self.PRESENCE_TYPE == 2:
            hints = f'total players/total maxplayers'
        elif self.PRESENCE_TYPE >= 3:
            hints = f'each server one by one every 10 minutes'
        self.print_to_console(f'Presence update type: {self.PRESENCE_TYPE} | Display {hints}')

    # get game server discord embed
    def get_embed(self, server):
        # load server cache
        server_cache = ServerCache(server['addr'], server['port'])

        # load server data
        data = server_cache.get_data()

        if data:
            # load server status Online/Offline
            status = server_cache.get_status()

            emoji = (status == 'Online') and ':green_circle:' or ':red_circle:'

            if status == 'Online':
                if int(data['maxplayers']) <= int(data['players']):
                    color = discord.Color.from_rgb(240, 71, 71) # red
                elif int(data['maxplayers']) <= int(data['players']) * 2:
                    color = discord.Color.from_rgb(250, 166, 26) # yellew
                else:
                    color = discord.Color.from_rgb(67, 181, 129) # green
            else:
                color = discord.Color.from_rgb(32, 34, 37) # dark

            title = (data['password'] and ':lock: ' or '') + data["name"]
            description = ('custom' in server) and server['custom'] or ''
            if server['type'] == 'SourceQuery':
                embed = discord.Embed(title=title, description=f'Connect: steam://connect/{data["addr"]}:{server["port"]}\n' + description, color=color)
            elif description.strip():
                embed = discord.Embed(title=title, description=description, color=color)
            else:
                embed = discord.Embed(title=title, color=color)

            embed.add_field(name=f'{os.getenv("FIELD_STATUS", self.SETTINGS["fieldname"]["status"])}', value=f'{emoji} **{status}**', inline=True)
            embed.add_field(name=f'{os.getenv("FIELD_ADDRESS", self.SETTINGS["fieldname"]["address"])}:{os.getenv("FIELD_PORT", self.SETTINGS["fieldname"]["port"])}', value=f'`{data["addr"]}:{data["port"]}`', inline=True)

            flag_emoji = ('country' in server) and (':flag_' + server['country'].lower() + f': {server["country"]}') or ':united_nations: Unknown'
            embed.add_field(name=f'{os.getenv("FIELD_COUNTRY", self.SETTINGS["fieldname"]["country"])}', value=flag_emoji, inline=True)

            embed.add_field(name=f'{os.getenv("FIELD_GAME", self.SETTINGS["fieldname"]["game"])}', value=f'{data["game"]}', inline=True)
            embed.add_field(name=f'{os.getenv("FIELD_CURRENTMAP", self.SETTINGS["fieldname"]["currentmap"])}', value=f'{data["map"]}', inline=True)

            if status == 'Online':
                value = f'{data["players"]}' # example: 20/32
                if data['bots'] > 0: value += f' ({data["bots"]})' # example: 20 (2)/32
            else:
                value = '0' # example: 0/32

            embed.add_field(name=f'{os.getenv("FIELD_PLAYERS", self.SETTINGS["fieldname"]["players"])}', value=f'{value}/{data["maxplayers"]}', inline=True)

            if 'image_url' in server:
                image_url = str(server['image_url'])
            else:
                custom_image_url = os.getenv('CUSTOM_IMAGE_URL', self.SETTINGS.get('image_url', ''))
                if custom_image_url != '':
                    image_url = f'{custom_image_url}/{urllib.parse.quote(data["map"])}.jpg'
                else:
                    image_url = f'https://github.com/DiscordGSM/Map-Thumbnails/raw/master/{urllib.parse.quote(data["game"])}/{urllib.parse.quote(data["map"])}.jpg'

            embed.set_thumbnail(url=image_url)
        else:
            # server fail to query
            color = discord.Color.from_rgb(240, 71, 71) # red
            embed = discord.Embed(title='ERROR', description=f'{os.getenv("FIELD_STATUS", self.SETTINGS["fieldname"]["status"])}: :warning: **Fail to query**', color=color)
            embed.add_field(name=f'{os.getenv("FIELD_ADDRESS", self.SETTINGS["fieldname"]["address"])}:{os.getenv("FIELD_PORT", self.SETTINGS["fieldname"]["port"])}', value=f'{server["addr"]}:{server["port"]}', inline=True)
        
        embed.set_footer(text=f'DiscordGSM v{self.VERSION} | Game Server Monitor | Last update: ' + datetime.now().strftime('%a, %Y-%m-%d %I:%M:%S%p'), icon_url='https://github.com/DiscordGSM/DiscordGSM/raw/master/images/discordgsm.png')
        
        return embed

    def get_server_list(self):
        return self.server_list


SETTINGS = Settings.get()
TOKEN = os.getenv('DGSM_TOKEN', SETTINGS['token'])
ROLE_ID = os.getenv('ROLE_ID', SETTINGS.get('role_id', '123'))
DGSM_PREFIX = os.getenv("DGSM_PREFIX", SETTINGS.get('prefix', '!'))
bot = commands.Bot(command_prefix=DGSM_PREFIX)

# command: servers
# list all the servers in configs/servers.json
@bot.command(name='dgsm', aliases=['discordgsm'])
@commands.check_any(commands.has_role(ROLE_ID), commands.is_owner())
async def _dgsm(ctx):
    title = f'Command: {DGSM_PREFIX}dgsm'
    description = f'Thanks for using Discord Game Server Monitor ([DiscordGSM](https://github.com/DiscordGSM/DiscordGSM))\n'
    description += f'\nUseful commands:\n{DGSM_PREFIX}servers - Display the server list'
    description += f'\n{DGSM_PREFIX}serveradd - Add a server'
    description += f'\n{DGSM_PREFIX}serverdel - Delete a server'
    description += f'\n{DGSM_PREFIX}serversrefresh - Refresh the server list'
    description += f'\n{DGSM_PREFIX}getserversjson - get servers.json file'
    description += f'\n{DGSM_PREFIX}setserversjson - set servers.json file'
    color = discord.Color.from_rgb(114, 137, 218) # discord theme color
    embed = discord.Embed(title=title, description=description, color=color)
    embed.add_field(name='Support server', value='https://discord.gg/Cg4Au9T', inline=True)
    embed.add_field(name='Github', value='https://github.com/DiscordGSM/DiscordGSM', inline=True)
    await ctx.send(embed=embed)

# command: servers
# list all the servers in configs/servers.json
@bot.command(name='serversrefresh')
@commands.check_any(commands.has_role(ROLE_ID), commands.is_owner())
async def _serversrefresh(ctx):
    # refresh discord servers list
    await discordgsm.refresh_discord_embed()
    discordgsm.print_to_console('Server list refreshed')

    # send response
    title = f'Command: {DGSM_PREFIX}serversrefresh'
    color = discord.Color.from_rgb(114, 137, 218) # discord theme color
    embed = discord.Embed(title=title, description=f'Servers list refreshed', color=color)
    await ctx.send(embed=embed)

# command: servers
# list all the servers in configs/servers.json
@bot.command(name='servers')
@commands.check_any(commands.has_role(ROLE_ID), commands.is_owner())
async def _servers(ctx):
    title = f'Command: {DGSM_PREFIX}servers'
    color = discord.Color.from_rgb(114, 137, 218) # discord theme color
    embed = discord.Embed(title=title, color=color)
    type, addr_port, channel = '', '', ''
    servers = discordgsm.get_server_list()

    for i in range(len(servers)):
        type += f'`{i+1}`. {servers[i]["type"]}\n'
        addr_port += f'`{servers[i]["addr"]}:{servers[i]["port"]}`\n'
        channel += f'`{servers[i]["channel"]}`\n'

    embed.add_field(name='ID. Type', value=type, inline=True)
    embed.add_field(name='Address:Port', value=addr_port, inline=True)
    embed.add_field(name='Channel ID', value=channel, inline=True)
    await ctx.send(embed=embed)

# command: getserversjson
# get configs/servers.json
@bot.command(name='getserversjson')
@commands.check_any(commands.has_role(ROLE_ID), commands.is_owner())
async def _getserversjson(ctx):
    await ctx.send(file=discord.File('configs/servers.json'))

# command: setserversjson
# set configs/servers.json
@bot.command(name='setserversjson')
@commands.check_any(commands.has_role(ROLE_ID), commands.is_owner())
async def _setserversjson(ctx, *args):
    title = f'Command: {DGSM_PREFIX}setserversjson'
    color = discord.Color.from_rgb(114, 137, 218) # discord theme color

    if len(args) == 1:
        url = args[0]
        r = requests.get(url)
        with open('configs/servers.json', 'wb') as file:
            file.write(r.content)

        description = f'File servers.json uploaded'
        embed = discord.Embed(title=title, description=description, color=color)
        await ctx.send(embed=embed)
        return

    description = f'Usage: {DGSM_PREFIX}setserversjson <url>\nRemark: <url> is the servers.json download url'
    embed = discord.Embed(title=title, description=description, color=color)
    await ctx.send(embed=embed)

#Error Handling Missing Role
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckAnyFailure):
        message = await ctx.send('''You dont have access to this commands!''')
        await asyncio.sleep(10)
        await message.delete()

discordgsm = DiscordGSM(bot)
discordgsm.start()
bot.run(TOKEN)

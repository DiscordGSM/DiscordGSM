import os
import time
import urllib
import asyncio
import requests
import subprocess
import base64
from datetime import datetime

# discord
import discord
from discord.ext import tasks, commands

# discordgsm
from bin import *
from servers import Servers, ServerCache

# [HEROKU] get and load servers json from SERVERS_JSON env directly
servers_json = os.getenv("SERVERS_JSON")
if servers_json and servers_json.strip():
    with open("servers.json", "w", encoding="utf-8") as file:
        file.write(servers_json)

# Check bot token and servers.json valid before start
segs = os.getenv("DGSM_TOKEN").split(".")
assert len(segs) == 3, "invalid token"
#decode
clientid = base64.b64decode(segs[0]).decode()
invite_link = f'https://discord.com/api/oauth2/authorize?client_id={clientid}&permissions=339008&scope=bot'

with open("servers.json", "r", encoding="utf-8") as file:
    try:
        Servers().get()
    except Exception as e:
        print(e)
        exit

# load env
import os
from dotenv import load_dotenv
load_dotenv()

VERSION = "1.9.0"
# Get Env
PREFIX=os.getenv("DGSM_PREFIX")
ROLEID=os.getenv("DGSM_ROLEID")
CUSTOM_IMAGE_URL=os.getenv("DGSM_CUSTOM_IMAGE_URL")
REFRESH_RATE=int(os.getenv("DGSM_REFRESH_RATE"))
PRESENCE_TYPE=int(os.getenv("DGSM_PRESENCE_TYPE"))
PRESENCE_RATE=int(os.getenv("DGSM_PRESENCE_RATE"))
SEND_DELAY=int(os.getenv("DGSM_SEND_DELAY"))
FIELD_NAME=os.getenv("DGSM_FIELD_NAME")
FIELD_STATUS=os.getenv("DGSM_FIELD_STATUS")
FIELD_ADDRESS=os.getenv("DGSM_FIELD_ADDRESS")
FIELD_PORT=os.getenv("DGSM_FIELD_PORT")
FIELD_GAME=os.getenv("DGSM_FIELD_GAME")
FIELD_CURRENTMAP=os.getenv("DGSM_FIELD_CURRENTMAP")
FIELD_PLAYERS=os.getenv("DGSM_FIELD_PLAYERS")
FIELD_COUNTRY=os.getenv("DGSM_FIELD_COUNTRY")
FIELD_LASTUPDATE=os.getenv("DGSM_FIELD_LASTUPDATE")
FIELD_CUSTOM=os.getenv("DGSM_FIELD_CUSTOM")
FIELD_PASSWORD=os.getenv("DGSM_FIELD_PASSWORD")
FIELD_ONLINE=os.getenv("DGSM_FIELD_ONLINE")
FIELD_OFFLINE=os.getenv("DGSM_FIELD_OFFLINE")
FIELD_UNKNOWN=os.getenv("DGSM_FIELD_UNKNOWN")
SPACER=u"\u200B"

class DiscordGSM():
    def __init__(self, client):
        print("\n----------------")
        print(f'Invite Link: \t{invite_link}')
        print("Github: \thttps://github.com/DiscordGSM/DiscordGSM")
        print("Discord:\thttps://discord.gg/Cg4Au9T")
        print("----------------\n")

        self.client = client
        self.servers = Servers()
        self.server_list = self.servers.get()
        self.message_error_count = self.current_display_server = 0

    def start(self):
        self.print_to_console(f'Starting DiscordGSM v{VERSION}...')
        self.query_servers.start()    

    def cancel(self):
        self.query_servers.cancel()
        self.update_servers.cancel()
        self.presense_load.cancel()

    async def on_ready(self):
        # set username and avatar | not very nice for self-hosted users.
        # icon_file_name = "images/discordgsm" + ("DGSM_TOKEN" in os.environ and "-heroku" or "") + ".png"
        # with open(icon_file_name, "rb") as file:
        #     try:
        #         await client.user.edit(username="DiscordGSM", avatar=file.read())
        #     except Exception as e:
        #         pass

        # print info to console
        print("\n----------------")
        print(f'Logged in as:\t{client.user.name}')
        print(f'Robot ID:\t{client.user.id}')
        app_info = await client.application_info()
        print(f'Owner ID:\t{app_info.owner.id} ({app_info.owner.name})')
        print("----------------\n")

        self.print_presense_hint()
        self.presense_load.start()

        self.print_to_console(f'Query server and send discord embed every {REFRESH_RATE} minutes...')
        await self.repost_servers()
        await asyncio.sleep(REFRESH_RATE*60)
        self.update_servers.start()

    def print_to_console(self, value):
        print(datetime.now().strftime("%Y-%m-%d %H:%M:%S: ") + value)

    def get_server_list(self):
        return self.server_list

    # query the servers
    @tasks.loop(minutes=REFRESH_RATE)
    async def query_servers(self):
        self.servers.refresh()
        self.server_list = self.servers.get()
        server_count = self.servers.query()
        self.print_to_console(f'{server_count} servers queried')

    # pre-query servers before ready
    @query_servers.before_loop
    async def before_query_servers(self):
        self.print_to_console("Pre-Query servers...")
        server_count = self.servers.query()
        self.print_to_console(f'{server_count} servers queried')
        await client.wait_until_ready()
        await self.on_ready()
    
    # send messages to discord
    @tasks.loop(minutes=REFRESH_RATE)
    async def update_servers(self):
        if self.message_error_count < 20:
            updated_count = 0
            for i in range(len(self.server_list)):
                try:
                    await self.messages[i].edit(embed=self.get_embed(self.server_list[i]))
                    updated_count += 1
                except Exception as e:
                    self.message_error_count += 1
                    self.print_to_console(f'ERROR: message {i} failed to edit, message deleted or no permission. Server: {self.server_list[i]["address"]}:{self.server_list[i]["port"]}\n{e}')
                finally:
                    await asyncio.sleep(SEND_DELAY)
       
            self.print_to_console(f'{updated_count} messages updated')
        else:
            self.message_error_count = 0
            self.print_to_console(f'Message ERROR reached, refreshing...')
            await self.repost_servers()

        # remove old discord embed and send new discord embed
    async def repost_servers(self):
        # refresh servers.json cache
        self.servers = Servers()
        self.server_list = self.servers.get()
        self.messages = []
        repost_count = 0
        # remove old discord embed
        channels = [server["channel"] for server in self.server_list]
        channels = list(set(channels)) # remove duplicated channels
        for channel in channels:
            try:
                await client.get_channel(channel).purge(check=lambda m: m.author==client.user)
            except Exception as e:
                self.print_to_console(f'ERROR: Unable to delete messages.\n{e}')
            finally:
                await asyncio.sleep(SEND_DELAY)

        # send new discord embed
        for s in self.server_list:
            try:
                message = await client.get_channel(s["channel"]).send(embed=self.get_embed(s))
                self.messages.append(message)
                repost_count += 1
            except Exception as e:
                self.message_error_count += 1
                self.print_to_console(f'ERROR: message fail to send, no permission. Server: {s["address"]}:{s["port"]}\n{e}')
            finally:
                await asyncio.sleep(SEND_DELAY)

        self.print_to_console(f'{repost_count} messages reposted')
    

    # 1 = display number of servers, 2 = display total players/total maxplayers, 3 = display each server one by one every 10 minutes
    def print_presense_hint(self):
        if PRESENCE_TYPE <= 1:
            hints = "number of servers"
        elif PRESENCE_TYPE == 2:
            hints = "total players/total maxplayers"
        elif PRESENCE_TYPE >= 3:
            hints = f'each server one by one every {PRESENCE_RATE} minutes'
        self.print_to_console(f'Presence update type: {PRESENCE_TYPE} | Display {hints}')

    # refresh discord presense
    @tasks.loop(minutes=PRESENCE_RATE)
    async def presense_load(self):
        # 1 = display number of servers, 2 = display total players/total maxplayers, 3 = display each server one by one every 10 minutes
        if len(self.server_list) == 0:
            activity_text = f'Command: {PREFIX}dgsm'
        if PRESENCE_TYPE <= 1:
            activity_text = f'{len(self.servers.get_distinct_servers())} game servers'
        elif PRESENCE_TYPE == 2:
            total_activeplayers = total_maxplayers = 0
            for server in self.server_list:
                server_cache = ServerCache(server["address"], server["port"])
                data = server_cache.get_data()
                if data and server_cache.get_status() == "Online":
                    total_activeplayers += int(data["players"])
                    total_maxplayers += int(data["maxplayers"])
                  
            activity_text = f'{total_activeplayers}/{total_maxplayers} active players" if total_maxplayers > 0 else "0 players' 
        elif PRESENCE_TYPE >= 3:
            if self.current_display_server >= len(self.server_list):
                self.current_display_server = 0

            server_cache = ServerCache(self.server_list[self.current_display_server]["address"], self.server_list[self.current_display_server]["port"])
            data = server_cache.get_data()
            if data and server_cache.get_status() == "Online":
                activity_text = f'{data["players"]}/{data["maxplayers"]} on {data["name"]}" if int(data["maxplayers"]) > 0 else "0 players'
            else:
                activity_text = None

            self.current_display_server += 1

        if activity_text != None:
            await client.change_presence(status=discord.Status.online, activity=discord.Activity(name=activity_text, type=3))
            self.print_to_console(f'Discord presence updated | {activity_text}')

    def get_value(self, dataset, field, default = None):
        if type(dataset) != dict or field not in dataset or dataset[field] is None or dataset[field] == "": 
            return default
        return dataset[field]

    # get game server discord embed
    def get_embed(self, server):
        # load server cache
        server_cache = ServerCache(server["address"], server["port"])
        # load server data
        data = server_cache.get_data()
        # get status from cache
        cache_status = server_cache.get_status()

        # Parsing Data
        if type(self.get_value(server, "locked")) == bool:
            lock = server["locked"]
        elif type(self.get_value(data, "password")) == bool:
            lock = data["password"]
        else:
            lock = False

        title = self.get_value(server, "title") or self.get_value(data, "game") or self.get_value(server, "game")
        if lock:
            title = f':lock: {title}'
        else:
            title = f':unlock: {title}'
        
        description = self.get_value(server, "custom")
        
        if cache_status == "Online":
            status = f':green_circle: **{FIELD_ONLINE}**'
        elif cache_status == "Offline" and data is not False:
            status = f':red_circle: **{FIELD_OFFLINE}**'
        else:
            status = f':yellow_circle: **{FIELD_UNKNOWN}**'

        hostname = self.get_value(server, "hostname") or self.get_value(data, "name") or SPACER

        players = self.get_value(data, "players", "?")
        bots = self.get_value(data, "bots")
        if cache_status == "Offline": 
            players = 0
            bots = None
        if data is False: 
            players = "?"
            bots = None
        maxplayers = self.get_value(data, "maxplayers") or self.get_value(server, "maxplayers") or "?"
        players_string = f'{players}({bots})/{maxplayers}' if bots is not None and bots > 0 else f'{players}/{maxplayers}'
        
        port = self.get_value(data, "port")
        address = self.get_value(server, "public_address") or self.get_value(data, "address") and port and f'{data["address"]}:{port}' or SPACER

        password = self.get_value(server, "password")

        country = self.get_value(server, "country")

        if self.get_value(server, "map") == False:
            map = None
        else:
            map = self.get_value(server, "map") or self.get_value(data, "map")

        image_url = self.get_value(server, "image_url")

        # Color : if offline = Black, if full = red, if half = yellow, if less = green, if defined = defined.
        if cache_status == "Online" and players != "?" and maxplayers != "??":
            if players >= maxplayers:
                color = discord.Color.from_rgb(240, 71, 71) # red
            elif players >= maxplayers / 2:
                color = discord.Color.from_rgb(250, 166, 26) # yellow
            else:
                color = discord.Color.from_rgb(67, 181, 129) # green
        else:
            color = discord.Color.from_rgb(0, 0, 0) # black
        # color is defined
        try:
            if "color" in server:
                h = server["color"].lstrip("#")
                rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
                color = discord.Color.from_rgb(rgb[0], rgb[1], rgb[2])
        except:
            pass

        # Build embed
        if description:
            embed = discord.Embed(title=title, description=description, color=color)
        else:
            embed = discord.Embed(title=title, color=color)
        embed.add_field(name=FIELD_STATUS, value=status, inline=True)
        embed.add_field(name=FIELD_NAME, value=hostname, inline=True)
        embed.add_field(name=SPACER, value=SPACER, inline=True)
        embed.add_field(name=FIELD_PLAYERS, value=players_string, inline=True)
        embed.add_field(name=FIELD_ADDRESS, value=f'`{address}`', inline=True)
        if password is None:
            embed.add_field(name=SPACER, value=SPACER, inline=True)
        else:
            embed.add_field(name=FIELD_PASSWORD, value=f'`{password}`', inline=True)
        if country:
            embed.add_field(name=FIELD_COUNTRY, value=f':flag_{country.lower()}:', inline=True)
        if map and not country:
            embed.add_field(name=SPACER, value=SPACER, inline=True)
        if map:
            embed.add_field(name=FIELD_CURRENTMAP, value=map, inline=True)
        if map or country:
            embed.add_field(name=SPACER, value=SPACER, inline=True)
        if image_url:
            embed.set_thumbnail(url=image_url)

        embed.set_footer(text=f'DiscordGSM v{VERSION} | Game Server Monitor | {FIELD_LASTUPDATE}: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}      {SPACER}', icon_url=CUSTOM_IMAGE_URL)
        
        return embed
        

client = commands.Bot(command_prefix=PREFIX)

# command: dgsm
# display dgsm informations
@client.command(name="dgsm", aliases=["discordgsm"], brief="Display DiscordGSM\"s informations")
@commands.check_any(commands.has_role(ROLEID), commands.is_owner())
async def _dgsm(ctx):
    title = f'Command: {PREFIX}dgsm'
    description = f'Thanks for using Discord Game Server Monitor ([DiscordGSM](https://github.com/DiscordGSM/DiscordGSM))\n'
    description += f'\nUseful commands:\n{PREFIX}servers - Display the server list'
    description += f'\n{PREFIX}serversrefresh - Refresh the server list'
    description += f'\n{PREFIX}getserversjson - get servers.json file'
    description += f'\n{PREFIX}setserversjson - set servers.json file'
    color = discord.Color.from_rgb(114, 137, 218) # discord theme color
    embed = discord.Embed(title=title, description=description, color=color)
    embed.add_field(name="Support server", value="https://discord.gg/Cg4Au9T", inline=True)
    embed.add_field(name="Github", value="https://github.com/DiscordGSM/DiscordGSM", inline=True)
    await ctx.send(embed=embed)

# command: serversrefresh
# refresh the server list
@client.command(name="serversrefresh", brief="Refresh the server list")
@commands.check_any(commands.has_role(ROLEID), commands.is_owner())
async def _serversrefresh(ctx):
    # refresh discord servers list
    await discordgsm.repost_servers()
    discordgsm.print_to_console("Server list refreshed")

    # send response
    title = f'Command: {PREFIX}serversrefresh'
    color = discord.Color.from_rgb(114, 137, 218) # discord theme color
    embed = discord.Embed(title=title, description=f'Servers list refreshed', color=color)
    await ctx.send(embed=embed)

# command: servers
# list all the servers in servers.json
@client.command(name="servers", brief="List all the servers in servers.json")
@commands.check_any(commands.has_role(ROLEID), commands.is_owner())
async def _servers(ctx):
    title = f'Command: {PREFIX}servers'
    color = discord.Color.from_rgb(114, 137, 218) # discord theme color
    embed = discord.Embed(title=title, color=color)
    type, address_port, channel = "", "", ""
    servers = discordgsm.get_server_list()

    for i in range(len(servers)):
        type += f'`{i+1}`. {servers[i]["type"]}\n'
        address_port += f'`{servers[i]["address"]}:{servers[i]["port"]}`\n'
        channel += f'`{servers[i]["channel"]}`\n'

    embed.add_field(name="ID. Type", value=type, inline=True)
    embed.add_field(name="Address:Port", value=address_port, inline=True)
    embed.add_field(name="Channel ID", value=channel, inline=True)
    await ctx.send(embed=embed)

# command: getserversjson
# get configs/servers.json
@client.command(name="getserversjson", brief="Get servers.json file")
@commands.check_any(commands.has_role(ROLEID), commands.is_owner())
async def _getserversjson(ctx):
    await ctx.send(file=discord.File("servers.json"))

# command: setserversjson
# set servers.json
@client.command(name="setserversjson", brief="Set servers.json file")
@commands.check_any(commands.has_role(ROLEID), commands.is_owner())
async def _setserversjson(ctx, *args):
    title = f'Command: {PREFIX}setserversjson'
    color = discord.Color.from_rgb(114, 137, 218) # discord theme color

    if len(args) == 1:
        url = args[0]
        r = requests.get(url)
        with open("servers.json", "wb", encoding="utf-8") as file:
            file.write(r.content)

        description = f'File servers.json uploaded'
        embed = discord.Embed(title=title, description=description, color=color)
        await ctx.send(embed=embed)
        return

    description = f'Usage: {PREFIX}setserversjson <url>\nRemark: <url> is the servers.json download url'
    embed = discord.Embed(title=title, description=description, color=color)
    await ctx.send(embed=embed)

# error handling on Missing Role
@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckAnyFailure):
        await ctx.send("You don't have access to this command!", delete_after=10.0)

discordgsm = DiscordGSM(client)
discordgsm.start()

client.run(os.getenv("DGSM_TOKEN"))

import os
import asyncio
import requests
import base64
from datetime import datetime

# discord
import discord
from discord.ext import tasks, commands

# discordgsm
from servers import Servers, ServerCache

# load env
import os
from dotenv import load_dotenv
load_dotenv()

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

VERSION = "1.9.2"
# Get Env
PREFIX = os.getenv("DGSM_PREFIX") or "!"
ROLEID = os.getenv("DGSM_ROLEID")
CUSTOM_IMAGE_URL = os.getenv("DGSM_CUSTOM_IMAGE_URL") or "https://github.com/DiscordGSM/DiscordGSM/blob/master/images/discordgsm.png?raw=true"
REFRESH_RATE = int(os.getenv("DGSM_REFRESH_RATE")) or 5
PRESENCE_TYPE = int(os.getenv("DGSM_PRESENCE_TYPE")) or 3
PRESENCE_RATE = int(os.getenv("DGSM_PRESENCE_RATE")) or 5
SEND_DELAY = int(os.getenv("DGSM_SEND_DELAY")) or 2
ERROR_THRESHOLD = int(os.getenv("DGSM_ERROR_THRESHOLD")) or 0
FIELD_NAME = os.getenv("DGSM_FIELD_NAME") or "Name"
FIELD_STATUS = os.getenv("DGSM_FIELD_STATUS") or "Status"
FIELD_ADDRESS = os.getenv("DGSM_FIELD_ADDRESS") or "Address"
FIELD_PORT = os.getenv("DGSM_FIELD_PORT") or "Port"
FIELD_GAME = os.getenv("DGSM_FIELD_GAME") or "Game"
FIELD_CURRENTMAP = os.getenv("DGSM_FIELD_CURRENTMAP") or "Map"
FIELD_PLAYERS = os.getenv("DGSM_FIELD_PLAYERS") or "Players"
FIELD_COUNTRY = os.getenv("DGSM_FIELD_COUNTRY") or "Country"
FIELD_LASTUPDATE = os.getenv("DGSM_FIELD_LASTUPDATE") or "Last Update"
FIELD_CUSTOM = os.getenv("DGSM_FIELD_CUSTOM") or "Information"
FIELD_PASSWORD = os.getenv("DGSM_FIELD_PASSWORD") or "Password"
FIELD_ONLINE = os.getenv("DGSM_FIELD_ONLINE") or "Online"
FIELD_OFFLINE = os.getenv("DGSM_FIELD_OFFLINE") or "Offline"
FIELD_UNKNOWN = os.getenv("DGSM_FIELD_UNKNOWN") or "Unknown"
FIELD_JOIN = os.getenv("DGSM_FIELD_JOIN") or "Join Server"
FIELD_LAUNCH = os.getenv("DGSM_FIELD_LAUNCH") or "Launch Game"
SPACER=u"\u200B"

class DiscordGSM():
    def __init__(self, client):

        self.client = client
        self.servers = Servers()
        self.server_list = self.servers.get()
        self.message_error_count = self.current_display_server = 0

    def start(self):
        self.print_to_console(f'Starting DiscordGSM v.{VERSION}')
        self.update_messages.start()
        
    def cancel(self):
        self.update_messages.cancel()
        self.presence_load.cancel()
        
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
        print(f'Client ID:\t{client.user.id}')
        app_info = await client.application_info()
        print(f'Owner ID:\t{app_info.owner.id} ({app_info.owner.name})')
        print(f'Invite Link: \t{invite_link}')
        print("----------------")
        print(f'Querying {self.servers.get_distinct_server_count()} servers and updating {len(self.server_list)} messages every {REFRESH_RATE} minutes.')
        print("----------------\n")
        self.presence_load.start()

    @tasks.loop(minutes=REFRESH_RATE)
    async def update_messages(self):
        await self.query_servers()
        updated_count = 0
        for server in self.server_list:
            if self.message_error_count > ERROR_THRESHOLD:
                self.message_error_count = 0
                self.print_to_console(f'ERROR: Message error threshold reached, reposting messages.')
                await self.repost_messages()
                break
            try:
                message = await self.try_get_message_to_update(server)
                if not message:
                    self.message_error_count += 1
                    continue
                await message.edit(embed=self.get_embed(server))
                updated_count += 1
            except Exception as e:
                self.message_error_count += 1
                self.print_to_console(f'ERROR: Failed to edit message for server: {self.get_server_info(server)}. Missing permissions ?\n{e}')
            finally:
                await asyncio.sleep(SEND_DELAY)
        self.print_to_console(f'{updated_count} messages updated.')

    # pre-query servers before ready
    @update_messages.before_loop
    async def before_update_messages(self):
        await self.query_servers()
        await client.wait_until_ready()
        await self.on_ready()

    # remove old discord embed and send new discord embed
    async def repost_messages(self):
        self.servers = Servers()
        self.server_list = self.servers.get()
        repost_count = 0
        # remove old discord embed
        channels = [server["channel"] for server in self.server_list]
        channels = list(set(channels)) # remove duplicated channels
        for channel in channels:
            try:
               await client.get_channel(channel).purge(check=lambda m: m.author==client.user)
            except Exception as e:
                self.print_to_console(f'ERROR: Unable to delete bot messages.\n{e}')
            finally:
                await asyncio.sleep(SEND_DELAY)

        # send new discord embed
        for server in self.server_list:
            try:
                message = await client.get_channel(server["channel"]).send(embed=self.get_embed(server))
                server["message_id"] = message.id
                repost_count += 1
            except Exception as e:
                self.message_error_count += 1
                self.print_to_console(f'ERROR: Failed to send message for server: {self.get_server_info(server)}. Missing permissions ?\n{e}')
            finally:
                self.servers.update_server_file(self.server_list)
                await asyncio.sleep(SEND_DELAY)
        self.print_to_console(f'{repost_count} messages reposted.')    # 1 = display number of servers, 2 = display total players/total maxplayers, 3 = display each server one by one every 10 minutes
    def print_presense_hint(self):
        if PRESENCE_TYPE <= 1:
            hints = "number of servers"
        elif PRESENCE_TYPE == 2:
            hints = "total players/total maxplayers"
        elif PRESENCE_TYPE >= 3:
            hints = f'each server one by one every {PRESENCE_RATE} minutes'
        self.print_to_console(f'Presence update type: {PRESENCE_TYPE} | Display {hints}')    

    # refresh discord presence
    @tasks.loop(minutes=PRESENCE_RATE)
    async def presence_load(self):
        # 1 = display number of servers, 2 = display total players/total maxplayers, 3 = display each server one by one every 10 minutes
        if len(self.server_list) == 0:
            activity_text = f'Command: {PREFIX}dgsm'
        if PRESENCE_TYPE <= 1:
            activity_text = f'{self.servers.get_distinct_server_count()} game servers'
        elif PRESENCE_TYPE == 2:
            total_activeplayers = total_maxplayers = 0
            for server in self.server_list:
                server_cache = ServerCache(server["address"], server["port"])
                data = server_cache.get_data()
                if data and server_cache.get_status() == "Online":
                    total_activeplayers += int(data["players"])
                    total_maxplayers += int(data["maxplayers"])
                  
            activity_text = f'{total_activeplayers}/{total_maxplayers} active players' if total_maxplayers > 0 else "0 players" 
        elif PRESENCE_TYPE >= 3:
            if self.current_display_server >= len(self.server_list):
                self.current_display_server = 0

            server_cache = ServerCache(self.server_list[self.current_display_server]["address"], self.server_list[self.current_display_server]["port"])
            data = server_cache.get_data()
            if data and server_cache.get_status() == "Online":
                activity_text = f'{data["players"]}/{data["maxplayers"]} on {data["name"]}' if int(data["maxplayers"]) > 0 else "0 players"
            else:
                activity_text = None

            self.current_display_server += 1

        if activity_text != None:
            try:
                await client.change_presence(status=discord.Status.online, activity=discord.Activity(name=activity_text, type=3))
                self.print_to_console(f'Discord presence updated | {activity_text}')
            except Exception as e:
                self.print_to_console(f'ERROR: Unable to update presence.\n{e}')

    def print_to_console(self, value):
        print(datetime.now().strftime("%Y-%m-%d %H:%M:%S: ") + value)

    async def try_get_message_to_update(self, server):
        try:
            message = await client.get_channel(server["channel"]).fetch_message(server["message_id"])
            return message
        except Exception as e:
            self.print_to_console(f'ERROR: Failed to fetch message for server: {self.get_server_info(server)}. \n{e}')
            return None
        finally:
            await asyncio.sleep(SEND_DELAY)

    async def query_servers(self):
        try:    
            self.server_list = self.servers.refresh()
            self.servers.query()
        except Exception as e:
            self.print_to_console(f'Error Querying servers: \n{e}')
        self.print_to_console(f'{self.servers.get_distinct_server_count()} servers queried.')

    def get_value(self, dataset, field, default = None):
        if type(dataset) != dict or field not in dataset or dataset[field] is None or dataset[field] == "": 
            return default
        return dataset[field]

    def get_server_info(self, server):
        return self.get_value(server, "comment", f'{server["address"]}:{server["port"]}')
    
    def get_server_list(self):
        return self.server_list

    def get_embed(self, server):
        server_cache = ServerCache(server["address"], server["port"])
        data = server_cache.get_data()
        cache_status = server_cache.get_status()

        # Evaluate fields
        lock = (server["locked"] if type(self.get_value(server, "locked")) == bool 
            else data["password"] if type(self.get_value(data, "password")) == bool 
            else False)

        title = self.get_value(server, "title") or self.get_value(data, "game") or self.get_value(server, "game")
        title = f':lock: {title}' if lock else  f':unlock: {title}'
        
        description = self.get_value(server, "custom")
        
        status = (f':green_circle: **{FIELD_ONLINE}**' if cache_status == "Online" 
            else f':red_circle: **{FIELD_OFFLINE}**' if cache_status == "Offline" and data is not False 
            else f':yellow_circle: **{FIELD_UNKNOWN}**')

        hostname = self.get_value(server, "hostname") or self.get_value(data, "name") or SPACER
        players_string = self.determinePlayerString(server, data, cache_status)   
        port = self.get_value(data, "port")
        address = self.get_value(server, "public_address") or self.get_value(data, "address") and port and f'{data["address"]}:{port}' or SPACER
        password = self.get_value(server, "password")
        country = self.get_value(server, "country")
        map = None if  self.get_value(server, "map") == False else self.get_value(server, "map") or self.get_value(data, "map")
        image_url = self.get_value(server, "image_url")
        steam_id = self.get_value(server, "steam_id")
        direct_join = self.get_value(server, "direct_join")
        color = self.determineColor(server, data, cache_status)

        # Build embed
        embed = (discord.Embed(title=title, description=description, color=color) if description 
            else discord.Embed(title=title, color=color))

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
        if steam_id:
            if direct_join:
                if password:
                    embed.add_field(name=FIELD_JOIN, value=f'steam://connect/{data["address"]}:{port}/{password}', inline=False)
                else:
                    embed.add_field(name=FIELD_JOIN, value=f'steam://connect/{data["address"]}:{port}', inline=False)
            else:
                embed.add_field(name=FIELD_LAUNCH, value=f'steam://rungameid/{steam_id}', inline=False)
        if image_url:
            embed.set_thumbnail(url=image_url)
        embed.set_footer(text=f'DiscordGSM v.{VERSION} | Game Server Monitor | {FIELD_LASTUPDATE}: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}{SPACER}', icon_url=CUSTOM_IMAGE_URL)
        
        return embed

    def determineColor(self, server, data, cache_status):
        players = self.get_value(data, "players", "?")  
        maxplayers = self.get_value(data, "maxplayers") or self.get_value(server, "maxplayers") or "?"

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

        return color

    def determinePlayerString(self,server, data, cache_status):

        players = self.get_value(data, "players", "?")  
        maxplayers = self.get_value(data, "maxplayers") or self.get_value(server, "maxplayers") or "?"

        bots = self.get_value(data, "bots")

        if cache_status == "Offline": 
            players = 0
            bots = None
        if data is False: 
            players = "?"
            bots = None

        return f'{players}({bots})/{maxplayers}' if bots is not None and bots > 0 else f'{players}/{maxplayers}'

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
    await discordgsm.repost_messages()
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

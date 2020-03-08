import os
import discord
from discord.ext import commands
from settings import Settings

bot = discord.Client()

settings = Settings.get()
TOKEN = os.getenv('DGSM_TOKEN', settings['token'])

@bot.event
async def on_ready():
    print('--------------------')
    print(f'DiscordGSM invite link: https://discordapp.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=268954704&scope=bot')
    print('--------------------')
    
    await bot.close()

bot.run(TOKEN)

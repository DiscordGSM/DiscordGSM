import os
import discord
from discord.ext import commands

bot = discord.Client()

TOKEN = os.environ["DGSM_TOKEN"]

@bot.event
async def on_ready():
    print('--------------------')
    print(f'DiscordGSM invite link: https://discordapp.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=268954704&scope=bot')
    print('--------------------')
    
    await bot.close()

bot.run(TOKEN)

import discord
from discord.ext import commands
import time
import asyncio

f=open("token.txt", "r")

TOKEN=f.readlines()[0]

connections=[]

f.close()

print(TOKEN)

bot=commands.Bot(command_prefix = "")

@bot.event
@bot.event
async def on_ready():
    print("Everything's all ready to go~")

@bot.command()
async def join(ctx):
    channel = ctx.author.voice.channel 
    print(channel)
    await channel.connect()

@bot.command()
async def disconnect(ctx):
   for vc in bot.voice_clients:
       if vc.channel==ctx.author.voice.channel:
           print("disconnecting from: ", vc.channel)
           await vc.disconnect()

@bot.command()
async def ping(ctx):
    '''
    This text will be shown in the help command
    '''
    # Get the latency of the bot
    latency = bot.latency  # Included in the Discord.py library
    # Send it to the user
    await ctx.send("pong! "+str(bot.latency))


@bot.command()
async def echo(ctx, *, content:str):
    await ctx.send(content)


bot.run(TOKEN)

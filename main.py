import discord
from discord.ext import commands

f=open("token.txt", "r")

TOKEN=f.readline()

f.close()

print(TOKEN)

client=commands.Bot(command_prefix = "-")

@client.event
async def on_ready():
    print("Hello human")

@client.command(pass_context=True)
async def join(ctx):
    channel = ctx.message.author.voice.voice_channel
    print("joining channel ", channel)
    await client.join_voice_channel(channel)

#print("Hello human")


client.run(TOKEN)

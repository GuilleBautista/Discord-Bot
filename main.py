import discord
from discord.ext import commands

TOKEN="jnphZKuvmrPP_gy7u4ksNiirDImCyM7i"


client=commands.Bot(command_prefix = "holi")

@client.event
async def on_ready():
    print("Ready to go")

@client.command(pass_context=True)
async def join(ctx):
    channel = ctx.message.author.voice.voice_channel
    await client.join_voice_channel(channel)

print("Hello human")


client.run(TOKEN)

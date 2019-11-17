import discord
from discord.ext import commands

f=open("token.txt", "r")

TOKEN=f.readlines()[0]

f.close()

print(TOKEN)

client=commands.Bot(command_prefix = "-")

@client.event
async def on_ready():
    print("Hello human")

@client.command(pass_context=True)
async def join(ctx):
    #print(ctx.message)
    channel = ctx.message.author.voice.channel
    print("joining channel ", channel)
    await channel.connect()

@client.command(pass_context=True)
async def play(ctx):
    #print(ctx.message)
    await ctx.send("que voy e que voy")

    voice = get(client.voice_clients, guild=ctx.guild)

    ydl_opts = {
        'format' : 'bestaudio/best',
        'postprocessors' : [(
            'key' : 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        )]
    }
    #play( open("musica.mp3") )

    voice.play(discord.FFmpegExtractAudio)


#print("Hello human")


client.run(TOKEN)

import os

import time
import discord
from discord.ext import commands, tasks
import time
import asyncio

import subprocess
import threading

import youtube_dl as yt

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from pprint import pprint


DOWNLOADS = "./downloads/"

DOWNLOADS_FILE = "./downloads/queue.txt"

QUEUE="./queue/"

PLACEHOLDER = ";;;;;"

"""
================AUX FUNCTIONS===================
"""

def queue_func(server, song_title, song_url, search, web_url):
    with open(QUEUE+str(server), "a") as f:
        f.write(song_title+PLACEHOLDER+song_url+PLACEHOLDER+search+PLACEHOLDER+web_url+PLACEHOLDER+"\n")

def queue_download(song_title, search):
    with open(DOWNLOADS_FILE, "a") as f:
        f.write(song_title+PLACEHOLDER+search+PLACEHOLDER+"\n")

def dequeue_func(server):
    with open(QUEUE+str(server), "r") as f:
        lines = f.readlines()

    with open(QUEUE+str(server), "w") as f:        
        out = ""
        for i in range(1, len(lines)):
            out += lines[i]
        f.write(out)

    return lines[0]

def dequeue_download():
    with open(DOWNLOADS_FILE, "r") as f:
        lines = f.readlines()

    if len(lines)==0:
        return "", ""

    with open(DOWNLOADS_FILE, "w") as f:        
        out = ""
        for i in range(1, len(lines)):
            out += lines[i]
        f.write(out)

    out = lines[0].split(PLACEHOLDER)

    return out[0], out[1]

async def checkConnected(channel):
    #Check for the user's channel
    connected = False
    for vclient in bot.voice_clients:
        if vclient.channel==channel:
            connected = True
    return connected

async def joinUserChannel(ctx):
    #Join the user's channel
    channel = ctx.author.voice.channel 
    print("Joining channel... "+str(channel))
    await channel.connect()
    #await ctx.send("Joined channel: "+str(channel))
    return channel

#Returns url, videotitle, song_searched and video_webpage
def queryYt(song):
    try:
        ydl = yt.YoutubeDL({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }],
            'ffmpeg-location': './',
            'outtmpl': DOWNLOADS+'%(id)s.%(ext)s'
            })

        with ydl:
            result = ydl.extract_info(
                "ytsearch:"+song,
                download=False
            )
    
        return result['entries'][0]['formats'][0]['url'], result['entries'][0]['title'], song, result['entries'][0]['webpage_url']

    except:
        return "empty_url", "empty_title", song, "web_url"

def yt_download(song_arg, search_arg):
    song = song_arg.replace("|", "_")
    search = search_arg.replace("|", "_")
    ydl = yt.YoutubeDL({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }],
            'ffmpeg-location': './',
            'outtmpl': DOWNLOADS+'%(title)s.%(ext)s'
            })

    if not os.path.exists(DOWNLOADS+song+".mp3"):
        print(DOWNLOADS+song+".mp3")
        with ydl:
            result = ydl.extract_info(
                "ytsearch:"+song,
                download=True
            )
    
    if search[0] == " ":
        search = search[1:]

    if not os.path.exists(DOWNLOADS+search+".mp3"):
        print(DOWNLOADS+search+".mp3")
        subprocess.run(["ln", str(DOWNLOADS+""+song+".mp3"), str(DOWNLOADS+""+search+".mp3")])

"""
# Queue a given song, specifying if it should be downloaded or played.
# It also searches locally to prevent unnecesary net conections
"""
def queueSong(ctx, song, download, play):
    print("Getting Song: ", song, " Server: ", ctx.guild.id)
    #Search locally
    if os.path.exists(DOWNLOADS+song+".mp3"):
        title = song
        url = DOWNLOADS+song+".mp3"
        search = song
        web_url = DOWNLOADS+song+".mp3"
    else:
        url, title, search, web_url = queryYt(song)
    
    if download: queue_download(title, search)

    if play: queue_func(str(ctx.guild.id), title, url, search, web_url)

    return title, web_url

    
def getSpotifyPlaylist(ctx, pl_id, download, play):

    sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

    offset = 0

    playlist_ids = []

    #Retrieve songs until there are no more left
    while True:
        response = sp.playlist_items(pl_id,
                                    offset=offset,
                                    fields='items.track.id,total',
                                    additional_types=['track'])
        
        if len(response['items']) == 0:
            break
        
        pprint(response['items'])
        for i in response['items']:
            playlist_ids.append(i['track']['id'])

        offset = offset + len(response['items'])
        print(offset, "/", response['total'])

    for i in playlist_ids:
        track = sp.track(i)
        name = track['name']
        #album = track['album']['name']
        
        artists = ""
        for j in track['artists']:
            if j['name'] not in name:
                artists +=j['name']+", "
        
        if artists[-2:] == ", ":
            artists = artists[:-2]
        
        #Queue every song
        queueSong(ctx, name+" - "+artists, download, play)



"""
================BOT DECLARATION===================
"""

f=open("token.txt", "r")

TOKEN=f.readlines()[0]

connections=[]

f.close()

bot=commands.Bot(command_prefix = ".")


"""
================BOT LOOPS===================
"""

@tasks.loop(seconds=1)
async def play_music():
    for vclient in bot.voice_clients:
        try:
            if os.path.exists(QUEUE+str(vclient.guild.id)):
                if not vclient.is_playing() and not vclient.is_paused():
                    line = dequeue_func(vclient.guild.id).split(PLACEHOLDER)
                    
                    song_title = line[0]
                    song_url = line[1]
                    song_search = line[2]
                    
                    if os.path.exists(DOWNLOADS+song_title+".mp3"):
                        source = discord.FFmpegPCMAudio(DOWNLOADS+song_title+".mp3")
                        vclient.play(source)

                    elif os.path.exists(DOWNLOADS+song_search+".mp3"):
                        source = discord.FFmpegPCMAudio(DOWNLOADS+song_search+".mp3")
                        vclient.play(source)

                    else: 
                        if song_title == "empty_title":
                            continue

                        try:
                            source = discord.FFmpegPCMAudio(song_url)
                            vclient.play(source)
                        except:
                            try:
                                time.sleep(0.1)
                                vclient.play(source)
                            except:
                                try:
                                    time.sleep(0.1)
                                    vclient.play(source)
                                except:
                                    pass

        except:     
            pass

@tasks.loop(seconds=60)
async def download_music():
    song, search = dequeue_download()
    if len(song) > 0:
        #if not os.path.exists(DOWNLOADS+song+".mp3"):
        t = threading.Thread(target=yt_download, args=(song, search))
        t.start()
        #t.join()


@bot.event
async def on_ready():
    play_music.start()
    download_music.start()
    print("Everything's all ready to go~")



"""
================BOT COMMANDS===================
"""


@bot.command()
async def join(ctx):
    channel = ctx.author.voice.channel 
    print(channel)
    await channel.connect()
    #await ctx.send("Joined channel: "+str(channel))

@bot.command()
async def disconnect(ctx):
    for vc in bot.voice_clients:
        if vc.channel==ctx.author.voice.channel:
            print("disconnecting from: ", vc.channel)
            await vc.disconnect()

@bot.command()
async def dc(ctx):
    for vc in bot.voice_clients:
        if vc.channel==ctx.author.voice.channel:
            print("disconnecting from: ", vc.channel)
            await vc.disconnect()

@bot.command()
async def play(ctx):
    if await checkConnected(ctx.author.voice.channel)==False:
        await joinUserChannel(ctx)

    song = ctx.message.content[6:]

    if len(song) > 0:
        if "open.spotify.com/playlist" in song:
            sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

            pl_id = 'spotify:playlist:'+song.split("playlist/")[1].split("?")[0]
        
            response = sp.playlist_items(pl_id,
                                        offset=0,
                                        fields='items.track.id,total',
                                        additional_types=['track'])

            if response['total'] > 100:
                msg = "Añadiendo "+str(response['total'])+" canciones a la cola (tremenda tula)"
            else:
                msg = "Añadiendo "+str(response['total'])+" canciones a la cola"

            await ctx.send(msg)

            t = threading.Thread(target=getSpotifyPlaylist, args=(ctx, pl_id, False, True))              
            t.start()

        else:
            title, url = queueSong(ctx, song, False, True)
            await ctx.send(title, url)
        
    else:
        for vclient in bot.voice_clients:
            if vclient.channel == ctx.author.voice.channel:
                if vclient.is_paused():
                    vclient.resume()

@bot.command()
async def playd(ctx):
    if await checkConnected(ctx.author.voice.channel)==False:
        await joinUserChannel(ctx)

    song = ctx.message.content[6:]

    if len(song) > 0:
        if "open.spotify.com/playlist" in song:
            sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

            pl_id = 'spotify:playlist:'+song.split("playlist/")[1].split("?")[0]
        
            response = sp.playlist_items(pl_id,
                                        offset=0,
                                        fields='items.track.id,total',
                                        additional_types=['track'])

            if response['total'] > 100:
                msg = "Añadiendo "+str(response['total'])+" canciones a la cola (tremenda tula)"
            else:
                msg = "Añadiendo "+str(response['total'])+" canciones a la cola"

            await ctx.send(msg)

            t = threading.Thread(target=getSpotifyPlaylist, args=(ctx, pl_id, True, True))              
            t.start()

        else:
            title, url = queueSong(ctx, song, False, True)
            await ctx.send(title, url)    
            
    else:
        for vclient in bot.voice_clients:
            if vclient.channel == ctx.author.voice.channel:
                if vclient.is_paused():
                    vclient.resume()

@bot.command()
async def download(ctx):
    song = ctx.message.content[6:]

    if len(song) > 0:
        if "open.spotify.com/playlist" in song:
            sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

            pl_id = 'spotify:playlist:'+song.split("playlist/")[1].split("?")[0]
        
            response = sp.playlist_items(pl_id,
                                        offset=0,
                                        fields='items.track.id,total',
                                        additional_types=['track'])

            if response['total'] > 100:
                msg = "Añadiendo "+str(response['total'])+" canciones a la cola (tremenda tula)"
            else:
                msg = "Añadiendo "+str(response['total'])+" canciones a la cola"

            await ctx.send(msg)

            t = threading.Thread(target=getSpotifyPlaylist, args=(ctx, pl_id, True, False))              
            t.start()

        else:
            title, url = queueSong(ctx, song, False, True)
            await ctx.send(title, url)         
        

@bot.command()
async def resume(ctx):
    for vclient in bot.voice_clients:
        if vclient.channel == ctx.author.voice.channel:
            if vclient.is_paused():
                vclient.resume()

@bot.command()
async def stop(ctx):
    for vclient in bot.voice_clients:
        if vclient.channel == ctx.author.voice.channel:
            if vclient.is_playing():
                vclient.pause()

@bot.command()
async def pause(ctx):
    for vclient in bot.voice_clients:
        if vclient.channel == ctx.author.voice.channel:
            if vclient.is_playing():
                vclient.pause()

@bot.command()
async def next(ctx):
    for vclient in bot.voice_clients:
        if vclient.channel == ctx.author.voice.channel:
            if vclient.is_playing():
                vclient.stop()

@bot.command()
async def skip(ctx):
    for vclient in bot.voice_clients:
        if vclient.channel == ctx.author.voice.channel:
            if vclient.is_playing():
                vclient.stop()

@bot.command()
async def queue(ctx):
    try:
        server = str(ctx.guild.id)
        
        with open(QUEUE+str(server), "r") as f:
            lines = f.readlines()
        
        out=""
        i=0
        for l in lines:
            i+=1
            s = l.split(PLACEHOLDER)
            out+=str(i)+". " + s[0] + "\n" + s[3] + "\n"
        
        if len(out) > 0:
            await ctx.send(out)
        else:
            await ctx.send("La cola está vacía como el corazón de ella.")
    except:
        await ctx.send("La cola está vacía como el corazón de ella.")

@bot.command()
async def clear(ctx):
    server = str(ctx.guild.id)
    os.system("rm -rf "+QUEUE+str(server))
    await ctx.send("He borrado la cola como mi ex borró mi autoestima")

@bot.command()
async def ping(ctx):
    '''
    Ping-Pong
    '''
    # Get the latency of the bot
    latency = bot.latency  # Included in the Discord.py library
    # Send it to the user
    await ctx.send("pong! "+str(bot.latency))


@bot.command()
async def echo(ctx, *, content:str):
    await ctx.send(content)


bot.run(TOKEN)

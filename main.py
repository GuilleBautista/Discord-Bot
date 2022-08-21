import os

import random
import time
import discord
from discord.ext import commands, tasks
import asyncio

import subprocess
import threading

import yt_dlp as yt

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from pprint import pprint

import music_tag
import json
import requests
import shutil

DOWNLOADS = "./downloads/"

DOWNLOADS_FILE = "./downloads/queue.txt"
FINISHED_FILE = "./downloads/finished.txt"

QUEUE="./queue/"

VOICE_CLIENTS="./voice_clients/"

PLACEHOLDER = ";;;;;"

global MAX_DOWNLOAD_THREADS
MAX_DOWNLOAD_THREADS = 10

global SONG_DB
SONG_DB = {}

#Timeout in seconds for the bot to leave a voice client
TIMEOUT = 300

"""
================AUX FUNCTIONS===================
"""

def queue_func(server, song_title, song_url, search, web_url, text_channel):
    with open(QUEUE+str(server), "a") as f:
        f.write(song_title+PLACEHOLDER+song_url+PLACEHOLDER+search+PLACEHOLDER+web_url+PLACEHOLDER+str(text_channel)+PLACEHOLDER+"\n")

def queue_download(song_title, search, guild, text_channel, metadata):
    #TODO: metadata
    with open(DOWNLOADS_FILE, "a") as f:
        f.write(song_title+PLACEHOLDER+search+PLACEHOLDER+str(guild)+PLACEHOLDER+str(text_channel)+PLACEHOLDER+json.dumps(metadata).replace("\'", "\"")+PLACEHOLDER+"\n")

def queue_finished(song_title, search, guild, text_channel):
    with open(FINISHED_FILE, "a") as f:
        f.write(song_title+PLACEHOLDER+search+PLACEHOLDER+str(guild)+PLACEHOLDER+str(text_channel)+PLACEHOLDER+"\n")


def dequeue_func(server):
    with open(QUEUE+str(server), "r") as f:
        lines = f.readlines()

    with open(QUEUE+str(server), "w") as f:
        out = ""
        for i in range(1, len(lines)):
            out += lines[i]

        if out!="":
            f.write(out)
        else:
            os.system("rm -rf "+QUEUE+str(server))

    return lines[0]

def dequeue_download():
    with open(DOWNLOADS_FILE, "r") as f:
        lines = f.readlines()

    if len(lines)==0:
        return "", "", "", "", ""

    with open(DOWNLOADS_FILE, "w") as f:
        out = ""
        for i in range(1, len(lines)):
            out += lines[i]
        f.write(out)

    out = lines[0].split(PLACEHOLDER)
    #print("AAAAAAAAAAAAAAAAAAAAAAAA"+str(out))
    if len(out)>=4:
        try:
            return out[0], out[1], out[2], out[3], json.loads(out[4].replace("'", ""))
        except:
            print("BBBBBBBBBBBBBBBBBBBAAAAAAAAAAAAAAAAA"+str(out))
            return out[0], out[1], "", "", ""
    else: return out[0], out[1], "", "", json.loads(out[4].replace("'", ""))

def dequeue_finished():

    with open(FINISHED_FILE, "r") as f:
        lines = f.readlines()

    if len(lines)==0:
        return "", "", "", ""

    with open(FINISHED_FILE, "w") as f:
        out = ""
        for i in range(1, len(lines)):
            out += lines[i]
        f.write(out)

    out = lines[0].split(PLACEHOLDER)

    if len(out)>=4: return out[0], out[1], out[2], out[3]
    else: return out[0], out[1], "", ""


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
        return result['entries'][0]['url'], result['entries'][0]['title'], song, result['entries'][0]['webpage_url']

    except:
        return "empty_url", "empty_title", song, "web_url"

def yt_download(song_arg, search_arg, guild, text_channel, metadata):
    song = song_arg.replace("|", "_").replace("?", "9")
    search = search_arg.replace("|", "_")
    result = None
    global SONG_DB
    if search not in SONG_DB:
        ydl = yt.YoutubeDL({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }],
                'ffmpeg-location': './',
                'outtmpl': DOWNLOADS+'%(title)s.%(ext)s'
                })

        with ydl:
            result = ydl.extract_info(
                "ytsearch:"+song,
                download=True
            )

    if search[0] == " ":
        search = search[1:]

    if result!=None:
        queue_finished(song, result['entries'][0]['webpage_url'], guild, text_channel)
        #modify metadata
        f = music_tag.load_file(DOWNLOADS+result['entries'][0]['title'].replace("|", "_").replace("?", "").replace("__", "_").replace("/", "_").replace("*", "_")+".mp3")
        f['title']=metadata['title']
        f['artist']=metadata['artist']
        f['album']=metadata['album']

        #Check if album image has already been downloaded
        if not os.path.exists(DOWNLOADS+"images/"+metadata['album']):
            res = requests.get(metadata['cover']['url'], stream=True)
            with open(DOWNLOADS+"images/"+metadata['album'],'wb') as a:
                shutil.copyfileobj(res.raw, a)

        with open(DOWNLOADS+'images/'+metadata['album'], 'rb') as img_in:
            f['artwork'] = img_in.read()

        f.save()

    else:
        queue_finished(song, "was already downloaded", guild, text_channel)

"""
# Queue a given song, specifying if it should be downloaded or played.
# It also searches locally to prevent unnecesary net conections
"""
def queueSong(ctx, song, download, play, verbose, metadata):
    print("Getting Song: ", song, " Server: ", ctx.guild.id)
    #Search locally
    global SONG_DB
    if song in SONG_DB:
        title = SONG_DB[song]
        url = DOWNLOADS+SONG_DB[song]+".mp3"
        search = song
        web_url = DOWNLOADS+SONG_DB[song]+".mp3"
    else:
        url, title, search, web_url = queryYt(song)

    if verbose and download: queue_download(title, search, ctx.guild.id, ctx.message.channel.id, metadata)
    elif download: queue_download(title, search, "", "", metadata)

    if play: queue_func(str(ctx.guild.id), title, url, search, web_url, ctx.message.channel.id)

    return title, web_url

def renewTime(vc):
    with open(VOICE_CLIENTS+str(vc.session_id), "w") as f:
        f.write(str(time.time()))

async def disconnectVc(vc):
    print("disconnecting from: ", vc.channel)
    await vc.disconnect()
    checkVcTime(vc)
    os.system("rm -rf "+VOICE_CLIENTS+vc.session_id)

def removeVc(vc):
    os.system("rm -rf "+VOICE_CLIENTS+vc.session_id)

def checkVcTime(vc):
    with open(VOICE_CLIENTS+str(vc.session_id), "r") as f:
        t0 = f.read()

    return time.time() - float(t0)


def getSpotifyPlaylist(ctx, pl_id, download, play, verbose):
    offset = 0

    playlist_ids = []

    #Retrieve songs until there are no more left
    while True:
        response = SP.playlist_items(pl_id,
                                    offset=offset,
                                    fields='items.track.id,total',
                                    additional_types=['track'])

        if len(response['items']) == 0:
            break

        for i in response['items']:
            playlist_ids.append(i['track']['id'])

        offset = offset + len(response['items'])
        print(offset, "/", response['total'])

    for i in playlist_ids:
        print(i)
        """
        track = SP.track(i)
        name = track['name']
        #album = track['album']['name']

        artists = ""
        for j in track['artists']:
            if j['name'] not in name:
                artists +=j['name']+", "

        if artists[-2:] == ", ":
            artists = artists[:-2]
        metadata = {
            "artist": artists,
            "title": name,
            "album": track['album']['name'],
            #best image quality, worst would be the last of the list
            "cover": track['album']['images'][0],
        }
        """
        global MAX_DOWNLOAD_THREADS
        while (threading.active_count() > MAX_DOWNLOAD_THREADS):
            time.sleep(1)
            print("Waiting for thread to finish...")
        #Queue every song
        t = threading.Thread(target=getSpotifySong, args=(ctx, i, download, play, verbose))
        t.start()


def getSpotifySong(ctx, song_id, download, play, verbose):
    #TODO
    track = SP.track(song_id)
    name = track['name']
    #album = track['album']['name']

    artists = ""
    for j in track['artists']:
        if j['name'] not in name:
            artists +=j['name']+", "

    if artists[-2:] == ", ":
        artists = artists[:-2]
    metadata = {
        "artist": artists,
        "title": name,
        "album": track['album']['name'],
        #best image quality, worst would be the last of the list
        "cover": track['album']['images'][0],
    }

    #Queue every song
    queueSong(ctx, name+" - "+artists, download, play, verbose, metadata)

def load_db():
    with open(DOWNLOADS+"db.txt", "r") as f:
        lines = f.readlines()

    for i in lines:
        l = i.split(PLACEHOLDER)
        global SONG_DB
        SONG_DB[l[0]] = l[1][:-1]

def write_db(song_title, song_search):
    while song_search[0]==" ":
        song_search=song_search[1:]

    with open(DOWNLOADS+"db.txt", "a") as f:
        f.write(song_search+PLACEHOLDER+song_title+"\n")
    
    global SONG_DB
    SONG_DB[song_search] = song_title



"""
================BOT DECLARATION===================
"""

with open("token.txt", "r") as f:
    lines = f.readlines()
    TOKEN=lines[0][:-1]
    SPOTIFY_ID = lines[1][:-1]
    SPOTIFY_SECRET = lines[2][:-1]

connections=[]

SP = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(SPOTIFY_ID, SPOTIFY_SECRET))


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

                    song_title = line[0].replace("?", "9")
                    song_url = line[1]
                    song_search = line[2]
                    web_url = line[3]
                    text_channel = line[4]
                    global SONG_DB
                    if song_title in SONG_DB:
                        source = discord.FFmpegPCMAudio(DOWNLOADS+SONG_DB[song_title]+".mp3")
                        vclient.play(source)
                    elif song_search in SONG_DB:
                        source = discord.FFmpegPCMAudio(DOWNLOADS+SONG_DB[song_search]+".mp3")
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
                    
                    if(len(text_channel) > 0):
                        for tc in vclient.guild.text_channels :
                            if str(tc.id) == text_channel:
                                await tc.send(song_title+"\n"+web_url)

        except:
            pass

@tasks.loop(seconds=6)
async def download_music():
    global MAX_DOWNLOAD_THREADS
    if (threading.active_count() < MAX_DOWNLOAD_THREADS):
        song, search, guild, text_channel, metadata = dequeue_download()
        if len(song) > 0:
            global SONG_DB
            if search not in SONG_DB and not os.path.exists(DOWNLOADS+song+".mp3"):
                t = threading.Thread(target=yt_download, args=(song, search, guild, text_channel, metadata))
                t.start()
                if len(text_channel) > 0:
                    g = bot.get_guild(int(guild))
                    for tc in g.text_channels:
                        if str(tc.id) == text_channel:
                            await tc.send("Downloading "+song)
                write_db(song, search)
            else:
                queue_finished(song, "was already downloaded", guild, text_channel)
                if search not in SONG_DB:
                    write_db(song, search)


@tasks.loop(seconds=1)
async def notify_finished():
    song, web_url, guild, text_channel = dequeue_finished()
    if len(song) > 0:
        if len(text_channel) > 0:
            g = bot.get_guild(int(guild))
            for tc in g.text_channels:
                if str(tc.id) == text_channel:
                    await tc.send("Downloaded "+song + "\n" + web_url)

@tasks.loop(seconds=120)
async def remove_timedout_vc():
    for vclient in bot.voice_clients:
        if checkVcTime(vclient) > TIMEOUT or not os.path.exists(VOICE_CLIENTS+vclient.session_id):
            await disconnectVc(vclient)
            print("Exited ", vclient.session_id)

@tasks.loop(seconds=10)
async def renew_playing_vc():
    for vclient in bot.voice_clients:
        if vclient.is_playing() or not os.path.exists(VOICE_CLIENTS+vclient.session_id):
            renewTime(vclient)


@bot.event
async def on_ready():
    #Start daemons
    play_music.start()
    download_music.start()
    notify_finished.start()
    renew_playing_vc.start()
    remove_timedout_vc.start()

    #Clean up
    os.system("rm -rf "+VOICE_CLIENTS+"*")
    os.system("rm -rf "+QUEUE+"*")

    load_db()
    print("Everything's all ready to go~")



"""
================BOT COMMANDS===================
"""


@bot.command()
async def join(ctx):
    channel = ctx.author.voice.channel 
    print(channel)
    vc = await channel.connect()
    #await ctx.send("Joined channel: "+str(channel))
    renewTime(vc)

@bot.command()
async def database(ctx):
    out = ""
    global SONG_DB
    for i in SONG_DB:
        out+=i+" : "+SONG_DB[i]+"\n"
    
    if(len(out) == 0):
        out="Database empty"

    await ctx.send(out)

@bot.command()
async def disconnect(ctx):
    for vc in bot.voice_clients:
        if vc.channel==ctx.author.voice.channel:
            disconnectVc(vc)

@bot.command()
async def dc(ctx):
    for vc in bot.voice_clients:
        if vc.channel==ctx.author.voice.channel:
            await disconnectVc(vc)

@bot.command()
async def play(ctx):
    if await checkConnected(ctx.author.voice.channel)==False:
        await joinUserChannel(ctx)

    song = ctx.message.content[6:]

    if len(song) > 0:
        if "open.spotify.com/playlist" in song:
            pl_id = 'spotify:playlist:'+song.split("playlist/")[1].split("?")[0]
        
            response = SP.playlist_items(pl_id,
                                        offset=0,
                                        fields='items.track.id,total',
                                        additional_types=['track'])

            if response['total'] > 100:
                msg = "Añadiendo "+str(response['total'])+" canciones a la cola (tremenda tula)"
            else:
                msg = "Añadiendo "+str(response['total'])+" canciones a la cola"

            await ctx.send(msg)

            t = threading.Thread(target=getSpotifyPlaylist, args=(ctx, pl_id, False, True, False))              
            t.start()
        elif "open.spotify.com/track" in song:
            pl_id = song.split("track/")[1].split("?")[0]
        
            t = threading.Thread(target=getSpotifySong, args=(ctx, pl_id, False, True, False))              
            t.start()
        else:
            title, url = queueSong(ctx, song, False, True, False, None)
        
    else:
        for vclient in bot.voice_clients:
            if vclient.channel == ctx.author.voice.channel:
                if vclient.is_paused():
                    vclient.resume()

@bot.command()
async def playd(ctx):
    if await checkConnected(ctx.author.voice.channel)==False:
        await joinUserChannel(ctx)

    song = ctx.message.content[7:]

    if len(song) > 0:
        if "open.spotify.com/playlist" in song:
            pl_id = 'spotify:playlist:'+song.split("playlist/")[1].split("?")[0]
        
            response = SP.playlist_items(pl_id,
                                        offset=0,
                                        fields='items.track.id,total',
                                        additional_types=['track'])

            if response['total'] > 100:
                msg = "Añadiendo "+str(response['total'])+" canciones a la cola (tremenda tula)"
            else:
                msg = "Añadiendo "+str(response['total'])+" canciones a la cola"

            await ctx.send(msg)

            t = threading.Thread(target=getSpotifyPlaylist, args=(ctx, pl_id, True, True, False))              
            t.start()
        elif "open.spotify.com/track" in song:
            pl_id = song.split("track/")[1].split("?")[0]
        
            t = threading.Thread(target=getSpotifySong, args=(ctx, pl_id, True, True, False))              
            t.start()

        else:
            title, url = queueSong(ctx, song, True, True, False, None)
           
    else:
        for vclient in bot.voice_clients:
            if vclient.channel == ctx.author.voice.channel:
                if vclient.is_paused():
                    vclient.resume()

@bot.command()
async def playdv(ctx):
    if await checkConnected(ctx.author.voice.channel)==False:
        await joinUserChannel(ctx)

    song = ctx.message.content[7:]

    if len(song) > 0:
        if "open.spotify.com/playlist" in song:
            pl_id = 'spotify:playlist:'+song.split("playlist/")[1].split("?")[0]
        
            response = SP.playlist_items(pl_id,
                                        offset=0,
                                        fields='items.track.id,total',
                                        additional_types=['track'])

            if response['total'] > 100:
                msg = "Añadiendo "+str(response['total'])+" canciones a la cola (tremenda tula)"
            else:
                msg = "Añadiendo "+str(response['total'])+" canciones a la cola"

            await ctx.send(msg)

            t = threading.Thread(target=getSpotifyPlaylist, args=(ctx, pl_id, True, True, True))              
            t.start()
        elif "open.spotify.com/track" in song:
            pl_id = song.split("track/")[1].split("?")[0]
        
            t = threading.Thread(target=getSpotifySong, args=(ctx, pl_id, True, True, True))              
            t.start()

        else:
            title, url = queueSong(ctx, song, True, True, True, None)
            
    else:
        for vclient in bot.voice_clients:
            if vclient.channel == ctx.author.voice.channel:
                if vclient.is_paused():
                    vclient.resume()


@bot.command()
async def download(ctx):
    song = ctx.message.content[10:]

    if len(song) > 0:
        if "open.spotify.com/playlist" in song:
            pl_id = 'spotify:playlist:'+song.split("playlist/")[1].split("?")[0]
        
            response = SP.playlist_items(pl_id,
                                        offset=0,
                                        fields='items.track.id,total',
                                        additional_types=['track'])

            if response['total'] > 100:
                msg = "Añadiendo "+str(response['total'])+" canciones a la cola (tremenda tula)"
            else:
                msg = "Añadiendo "+str(response['total'])+" canciones a la cola"

            await ctx.send(msg)

            t = threading.Thread(target=getSpotifyPlaylist, args=(ctx, pl_id, True, False, False))              
            t.start()
        elif "open.spotify.com/track" in song:
            pl_id = song.split("track/")[1].split("?")[0]
        
            t = threading.Thread(target=getSpotifySong, args=(ctx, pl_id, True, False, False))              
            t.start()

        else:
            #Download=True, Play=False
            title, url = queueSong(ctx, song, True, False, False, None)

@bot.command()
async def downloadv(ctx):
    song = ctx.message.content[10:]

    if len(song) > 0:
        if "open.spotify.com/playlist" in song:
            pl_id = 'spotify:playlist:'+song.split("playlist/")[1].split("?")[0]
        
            response = SP.playlist_items(pl_id,
                                        offset=0,
                                        fields='items.track.id,total',
                                        additional_types=['track'])

            if response['total'] > 100:
                msg = "Añadiendo "+str(response['total'])+" canciones a la cola (tremenda tula)"
            else:
                msg = "Añadiendo "+str(response['total'])+" canciones a la cola"

            await ctx.send(msg)

            t = threading.Thread(target=getSpotifyPlaylist, args=(ctx, pl_id, True, False, True))              
            t.start()
        elif "open.spotify.com/track" in song:
            pl_id = song.split("track/")[1].split("?")[0]
        
            t = threading.Thread(target=getSpotifySong, args=(ctx, pl_id, True, False, True))              
            t.start()

        else:
            #Download=True, Play=False
            title, url = queueSong(ctx, song, True, False, True, None)


@bot.command()
async def rm(ctx):
    number = int(ctx.message.content[4:])
    try:
        server = str(ctx.guild.id)
        
        with open(QUEUE+str(server), "r") as f:
            lines = f.readlines()
        
        if len(lines)>0:

            if len(lines) >= number and number > 0:

                with open(QUEUE+str(server), "w") as f:
                    f.writelines(lines[:number-1]+lines[number:])
                    await ctx.send("Canción borrada correctamente")
        
            else:
                await ctx.send("El número introducido no está en la cola.")
        else:
            await ctx.send("La cola está vacía como el corazón de ella.")
    except FileNotFoundError:
        await ctx.send("La cola está vacía como el corazón de ella.")


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
            #We can only send messages with up to 2000 characters
            if len(out) + len(str(i)+". " + s[0] + "\n" + s[3] + "\n") > 2000:
                await ctx.send("La cola es muy grande para mandártela entera, te mando los primeros " + str(i-1) + " elementos.")
                break
            else:
                out += str(i)+". " + s[0] + "\n" + s[3] + "\n"
        
        if len(out) > 0:
            msg = await ctx.send(out)
            await msg.edit(suppress=True)

        else:
            await ctx.send("La cola está vacía como el corazón de ella.")
    except FileNotFoundError:
        await ctx.send("La cola está vacía como el corazón de ella.")

@bot.command()
async def queued(ctx):
    try:
        with open(DOWNLOADS_FILE, "r") as f:
            lines = f.readlines()
        
        out=""
        i=0
        for l in lines:
            i+=1
            s = l.split(PLACEHOLDER)
            #We can only send messages with up to 2000 characters
            if len(out) + len(str(i)+". " + s[0] + "\n" + s[3] + "\n") > 2000:
                await ctx.send("La cola es muy grande para mandártela entera, te mando las primeras " + str(i-1) + " canciones. En total hay " +str(len(lines)) + " canciones.")
                break
            else:
                out += str(i)+". " + s[0] + "\n" + s[3] + "\n"
        
        if len(out) > 0:
            msg = await ctx.send(out)
            await msg.edit(suppress=True)

        else:
            await ctx.send("La cola está vacía como el corazón de ella.")
    except FileNotFoundError:
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
async def playnext(ctx):
    await play(ctx)
    
    with open(QUEUE+str(ctx.guild.id), "r") as f:
        lines = f.readlines()
    
    with open(QUEUE+str(ctx.guild.id), "w") as f:
        f.write(lines[-1])
        f.writelines(lines[:-1])

@bot.command()
async def playdnext(ctx):
    await playd(ctx)
    
    with open(QUEUE+str(ctx.guild.id), "r") as f:
        lines = f.readlines()
    
    with open(QUEUE+str(ctx.guild.id), "w") as f:
        f.write(lines[-1])
        f.writelines(lines[:-1])

@bot.command()
async def echo(ctx, *, content:str):
    await ctx.send(content)

@bot.command()
async def shuffle(ctx):
    with open(QUEUE+str(ctx.guild.id), "r") as f:
        lines = f.readlines()
    
    random.shuffle(lines)

    with open(QUEUE+str(ctx.guild.id), "w") as f:
        f.writelines(lines)
    
    await ctx.send("Mezclando las canciones como el ron con la cocacola.")


bot.run(TOKEN)

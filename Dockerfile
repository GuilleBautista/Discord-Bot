FROM python:latest
WORKDIR /

#Python dependencies
RUN pip install --upgrade pip
RUN pip install discord
RUN pip install yt-dlp
RUN pip install spotipy
RUN pip install PyNaCl

#ffmpeg
RUN apt update
RUN apt install -y ffmpeg

RUN pip install aiohttp

#Create queue and directory structure
RUN mkdir /downloads
RUN touch /downloads/queue.txt
RUN mkdir /queue
RUN mkdir /voice_clients

COPY main.py /
COPY token.txt /

CMD [ "python3", "./main.py"]

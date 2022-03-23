FROM python:latest
WORKDIR /

COPY main.py /
COPY token.txt /

#Python dependencies
RUN pip install --upgrade pip
RUN pip install discord
RUN pip install youtube_dl
RUN pip install spotipy
RUN pip install PyNaCl

#ffmpeg
RUN apt update
RUN apt install -y ffmpeg

#Create queue and directory structure
RUN mkdir /downloads
RUN touch /downloads/queue.txt
RUN mkdir /queue

CMD [ "python3", "./main.py"]

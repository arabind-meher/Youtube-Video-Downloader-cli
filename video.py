import os
from os.path import join
import sys

import cv2
import requests
import datetime
import numpy as np

from random import randint
from num2words import num2words
from hurry.filesize import size

import ffmpeg
from ffmpeg import Error as FFmpegError

from pytube import YouTube
from pytube.cli import on_progress
from pytube import exceptions


class YouTubeVideos:
    def __init__(self, link, media, pixel):
        """ __init__ """

        try:
            # get video from 'YouTube'
            self.video = YouTube(link, on_progress_callback=on_progress)
        except exceptions.ExtractError as error:
            print('ExtractError:', error)
            sys.exit()
        except exceptions.VideoUnavailable as error:
            print('VideoUnavailable:', error)
            sys.exit()
        except exceptions.HTMLParseError as error:
            print('HTMLParseError:', error)
            sys.exit()
        except exceptions.PytubeError as error:
            print('PytubeError:', error)
            sys.exit()

        # path of current working directory
        self.path = os.getcwd()

        # video data
        self.link = link  # video link
        self.title = self.video.title  # video title
        self.author = self.video.author  # video creator
        self.length = self.video.length  # length of video in seconds
        self.views = self.video.views  # no. of views in video
        self.rating = self.video.rating  # video rating

        # printing video data
        print('Title: ' + self.title)
        print('Author: ' + self.author)
        print('Length: ' + str(datetime.timedelta(seconds=self.length)) + ' (' + str(self.length) + 's)')
        print('Views: ' + str(num2words(self.views)) + ' (' + str(self.views) + ')')
        print('Rating: ' + str(self.rating))

        print('*Note: Select same media type for better result.')
        input("\npress 'Enter' to continue.")
        print(end='\n')

        # collecting video & audio stream details
        self.get_video_streams(media, pixel)

        # storing data related to video
        self.store_video_data()

        # downloading video thumbnail
        self.download_video_thumbnail()

        # saving video description
        self.save_video_description()

        # generating all captions for video
        self.generate_video_caption()

    def get_video_streams(self, media, pixel):
        """ Get Video & Audio Stream Details """

        # correcting video & audio media type
        v_media = media if media is None else 'video/' + media
        a_media = media if media is None else 'audio/' + media

        # Video Streams
        videos_dict = dict()
        streams = self.video.streams.filter(
            type='video', mime_type=v_media, res=pixel
        ).order_by('resolution').desc()
        for stream in streams:
            videos_dict[str(stream).split('"')[1]] = ', '.join(str(stream).split()[2:5])

        if len(videos_dict) == 0:
            print('Video with given specifications not found')
            sys.exit()
        elif len(videos_dict) == 1:
            itag = str(list(videos_dict.keys())[0])
            print(
                '%3s' % itag, ':', '\t',
                str(videos_dict[itag].split('"')[1]), '\t',
                str(videos_dict[itag].split('"')[3]), '\t',
                str(videos_dict[itag].split('"')[5])
            )
            video_itag = str(list(videos_dict.keys())[0])
        else:
            streams = videos_dict.keys()
            for itag in streams:
                print(
                    '%3s' % itag, ':', '\t',
                    str(videos_dict[itag].split('"')[1]), '\t',
                    str(videos_dict[itag].split('"')[3]), '\t',
                    str(videos_dict[itag].split('"')[5])
                )
            while True:
                video_itag = input('>>> Enter video itag: ')
                if video_itag in streams:
                    break

        # Audio Streams
        audios_dict = dict()
        audios = self.video.streams.filter(type='audio', mime_type=a_media)
        for audio in audios:
            audios_dict[str(audio).split('"')[1]] = ', '.join(str(audio).split()[2:5])
        streams = audios_dict.keys()
        print(end='\n')
        for itag in audios_dict:
            print(
                '%3s' % itag, ':', '\t',
                str(audios_dict[itag].split('"')[1]), '\t',
                str(audios_dict[itag].split('"')[3]), '\t',
                str(audios_dict[itag].split('"')[5])
            )
        while True:
            audio_itag = input('>>> Enter audio itag: ')
            if audio_itag in streams:
                break

        # to download video and audio file
        self.download_streams(video_itag, audio_itag)

    def download_streams(self, video_itag, audio_itag):
        """ Download Video & Audio """

        # get specific video stream
        video_stream = self.video.streams.get_by_itag(video_itag)
        video_filename = 'video'  # video file name
        video_filesize = video_stream.filesize  # video file size

        # get specific audio stream
        audio_stream = self.video.streams.get_by_itag(audio_itag)
        audio_filename = 'audio'  # audio file name
        audio_filesize = audio_stream.filesize  # audio file size

        # printing video & audio details
        print(end='\n')
        print('  ' + video_filename + ': ' + size(video_filesize))
        print('  ' + audio_filename + ': ' + size(audio_filesize))
        print('  Total Download Size: ' + size(video_filesize + audio_filesize))
        print(end='\n')
        # if the user watns to proceed with downloads or not
        while True:
            i = input('>>> Proceed to Download? [y/n]: ')
            if i == 'y':
                break
            elif i == 'n':
                sys.exit()
            else:
                continue

        # create a directory inside current working directory
        try:
            os.mkdir(join(self.path, self.video.title))
            self.path = join(self.path, self.video.title)
        except OSError:
            random = str(randint(0, 100))
            os.mkdir(join(self.path, self.video.title + ' - ' + random))
            self.path = join(self.path, self.video.title + ' - ' + random)
        print('\n**Creating Directory: ' + self.path)

        # downloading video
        print('  Downloading Video: ' + video_filename)
        video_stream.download(output_path=self.path, filename=video_filename)
        # downloading audio
        print('\n\n  Downloading Audio: ' + audio_filename)
        audio_stream.download(output_path=self.path, filename=audio_filename)

        print(end='\n\n')

        filename = video_stream.default_filename  # final output file name
        video_name = video_filename + '.' + video_stream.default_filename.split('.')[-1]  # video file extension
        audio_name = audio_filename + '.' + audio_stream.default_filename.split('.')[-1]  # audio file extension

        # to merge downloaded video & audio
        self.merge_video_audio(filename, video_name, audio_name)

    def merge_video_audio(self, filename, video, audio):
        """ Merge Video & Audio """

        print('Merging Video & Audio')

        video_file = ffmpeg.input(join(self.path, video))  # get video file to merge
        audio_file = ffmpeg.input(join(self.path, audio))  # get audio file to merge

        try:
            # merging video and audio file
            ffmpeg.concat(video_file, audio_file, v=1, a=1).output(join(self.path, filename)).run()
        except FFmpegError as error:
            print('FFmpegError:', error)
        print('  Video & Audio Merged!')

        os.remove(join(self.path, video))  # remove existed video file
        os.remove(join(self.path, audio))  # remove existed audio file

    def store_video_data(self):
        """ Storing Video Data """

        # writing video data to a text file
        with open(join(self.path, self.title + '.txt'), 'w') as file:
            file.write('Title: ' + self.title + '\n')
            file.write('Author: ' + self.author + '\n')
            file.write(
                'Length: ' + str(datetime.timedelta(seconds=self.length)) + ' (' + str(self.length) + 's)' + '\n'
            )
            file.write('Views: ' + str(num2words(self.views)) + ' (' + str(self.views) + ')' + '\n')
            file.write('Rating: ' + str(self.rating))
            file.write('\nLink: ' + self.link)

    def download_video_thumbnail(self):
        """ Downloading Video Thumbnail """

        print('  Downloading Video Thumbnail')

        # downloading thumbnail in existing format
        response = requests.get(self.video.thumbnail_url, stream=True).raw
        image = cv2.imdecode(np.asarray(bytearray(response.read()), dtype='uint8'), cv2.IMREAD_COLOR)
        cv2.imwrite(join(self.path, self.video.title + '.' + self.video.thumbnail_url.split('.')[-1]), image)

    def save_video_description(self):
        """ Saving Video Description """

        print('  Saving Video Description')

        # writing video description to a text file
        with open(join(self.path, self.video.title + '(Description).txt'), 'w') as file:
            file.write(self.video.description)

    def generate_video_caption(self):
        """ Generating Video Captions """

        print('  Generating Caption')

        # creating a directory to store multiple captions
        caption_path = join(self.path, 'Captions')
        os.mkdir(caption_path)

        # getting captions for the video and storing them in '.srt' file
        captions = self.video.captions
        for caption in captions:
            with open(join(caption_path, self.title + ' - ' + caption.code + '.srt'), 'w') as file:
                print('    downloading - ' + str(caption))
                file.write(self.video.captions[caption.code].generate_srt_captions())

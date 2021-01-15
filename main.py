import argparse

from video import YouTubeVideos


def arguments():
    parser = argparse.ArgumentParser(description='YouTube Video Downloader')
    parser.add_argument('link', help='Link of video')

    # Media Type
    parser.add_argument(
        '-m', '--media',
        choices=['mp4', 'webm'],
        help='media type'
    )

    # Video Quality
    parser.add_argument(
        '-p', '--pixel',
        choices=['144p', '240p', '360p', '480p', '720p', '1080p', '1440p', '2160p'],
        help='video pixel quality'
    )

    return parser.parse_args()


if __name__ == '__main__':
    args = arguments()
    YouTubeVideos(args.link, media=args.media, pixel=args.pixel)

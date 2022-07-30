import os

class Video():
    def __init__(self, user, video_name):
        self.name = video_name
        self.comments = []
        self.likes = []
        self.dislike = []
        self.limitations = []
        self.uploader = user


class VideoException(Exception):
    pass



class VideoManager():
    def __init__(self):
        self.videos = []

    def like_video(self, video_name, user_name):
        video = self.find_video(video_name)
        if user_name in video.likes:
            raise VideoException("You have already liked the video")
        else: video.likes.append(user_name)

    def dislike_video(self, video_name, user_name):
        video = self.find_video(video_name)
        if user_name in video.dislike:
            raise VideoException("You have already disliked the video")
        else:
            video.dislike.append(user_name)

    def add_comment(self, video_name, comment, user_name):
        video = self.find_video(video_name)
        video.comments.append(f'{user_name}: {comment}')

    def add_detail(self, video_name, detail, user_name):
        video = self.find_video(video_name)
        video.limitations.append(f'admin {user_name}: {detail}')

    def find_video(self, video_name):
        for video in self.videos:
            if video.name == video_name:
                return video
        raise VideoException("video not found")

    def delete_video(self, video_name):
        video = self.find_video(video_name)
        self.videos.remove(video)
        os.remove(f'server_file/{video_name}')
        return video


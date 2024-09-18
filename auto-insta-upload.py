from instagrapi import Client
import os
import time
import json

def get_session_dict_from_env(env_var):
    session_str = os.getenv(env_var)
    if session_str:
        try:
            return json.loads(session_str)  # Convert the JSON string to a dictionary
        except json.JSONDecodeError as e:
            print(f"Error decoding session data: {e}")
    return {}

def get_days():
    if "DAYS" in os.listdir(os.getcwd()):
        with open("DAYS", 'r') as file:
            day = file.readline()
        with open("DAYS", "w") as file:
            file.write(str(int(day) + 1))
    return int(day)

DAY = get_days()

def video_upload(USERNAME, PASSWORD, PATH, CAPTION,SESSION):
    Insta = Client()
    Insta.login(USERNAME, PASSWORD)
    time.sleep(5)
    print(f"Logging in as {Insta.user_id}")
    Insta.clip_upload(PATH, CAPTION)
    print(f"Video uploaded: {PATH}")

def scheduled_upload():
    time.sleep(10)
    USERNAME = str(os.getenv('USERNAME1'))
    PASSWORD = str(os.getenv('PASSWORD1'))
    SESSION = get_session_dict_from_env(os.getenv('SESSION1'))
    PATH = "grandpa.mp4"
    global DAY
    CAPTION = f'''DAY {DAY} \n #meme #trending #trending #viral #instagram #explorepage #explore #instagood #love #reels #follow #trend #like #photography #india #fyp #instadaily #tiktok #foryou #trendingreels #trendingnow #style #memes #photooftheday #music #reelsinstagram #viralpost #model #insta'''
    video_upload(USERNAME, PASSWORD, PATH, CAPTION,SESSION)

def scheduled_upload_benson():
    time.sleep(10)
    USERNAME = str(os.getenv('USERNAME2'))
    PASSWORD = str(os.getenv('PASSWORD2'))
    SESSION = get_session_dict_from_env(os.getenv('SESSION2'))
    PATH = "video.mp4"
    global DAY
    CAPTION = f"DAY {DAY+1} \n #meme #trending #trending #viral #instagram #explorepage #explore #instagood #love #reels #follow #trend #like #photography #india #fyp #instadaily #tiktok #foryou #trendingreels #trendingnow #style #memes #photooftheday #music #reelsinstagram #viralpost #model #insta"
    video_upload(USERNAME, PASSWORD, PATH, CAPTION,SESSION)
scheduled_upload()
scheduled_upload_benson()

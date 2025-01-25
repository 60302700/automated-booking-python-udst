import time
import datetime
import os

def get_time_day():
    time_zone = time.tzname
    hour = datetime.datetime.now().hour
    day = datetime.datetime.now().strftime('%A')

    if time_zone == ('+03','+03'):
        hour += 3
    set_values(hour,day)


def set_values(hour,day):
    os.environ['Hour'] = hour
    os.environ['Day'] = day
    with open(os.getenv('GITHUB_ENV'), 'a') as env_file:
        env_file.write(f'Hour={os.environ['Hour']}\n')
        env_file.write(f'Day={os.environ['Day']}\n')

#main

get_time_day()

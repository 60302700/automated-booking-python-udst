import datetime
import os

def get_time_day(tz_offset_hours: int = 0):
    # Use UTC as the source of truth in GitHub Actions.
    # Allow an optional TZ offset (e.g. 3 for Qatar) via argument.
    now_utc = datetime.datetime.utcnow()
    hour = (now_utc.hour + tz_offset_hours) % 24
    day = (now_utc + datetime.timedelta(hours=tz_offset_hours)).strftime('%A')
    set_values(hour, day)


def set_values(hour, day):
    os.environ['Hour'] = str(hour)
    os.environ['Day'] = day
    github_env = os.getenv('GITHUB_ENV')
    if github_env:
        with open(github_env, 'a') as env_file:
            env_file.write(f'Hour={hour}\n')
            env_file.write(f'Day={day}\n')
    else:
        # Fallback for local runs / debugging
        print(f'Hour={hour} Day={day} (GITHUB_ENV not set)')


if __name__ == '__main__':
    try:
        tz_offset = int(os.getenv('TZ_OFFSET', '0'))
    except ValueError:
        tz_offset = 0
    get_time_day(tz_offset)

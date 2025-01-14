import requests
from datetime import datetime, timedelta
import argparse
import logging
from bs4 import BeautifulSoup
import random
import json


# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("booking_log.log"),
        logging.StreamHandler()
    ]
)

def future_day(day):
    date = datetime.now() + timedelta(days=day)
    return date.strftime("%B %d %Y")

def get_time_for_gaming(time):
    # End-time for gaming is 6 hours ahead, and is capped at 21
    adjusted_time = time + 6 
    if adjusted_time > 21: adjusted_time = 21
    if adjusted_time % 1 == 0:
        return str(int(adjusted_time))
    return str(float(adjusted_time))


def get_csrf_token_from_page(session, url):
    """Extract CSRF token from a given page URL."""
    response = session.get(url,timeout=(10, 30),verify=True)
    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_token = soup.find('input', {'name': '_token'})['value']
    return csrf_token

def login(id_udst, password):
    """Login and return the session with cookies and CSRF token for further requests."""
    session = requests.Session()

    # Step 1: Get the login page CSRF token
    login_url = "https://udstsport.udst.edu.qa/login"
    csrf_token = get_csrf_token_from_page(session, login_url)

    # Step 2: Perform login
    login_data = {
        '_token': csrf_token,  # Pass the CSRF token for login
        'user_login': id_udst,
        'password': password
    }

    login_response = session.post(login_url, data=login_data,timeout=(10, 30),)
    soup = BeautifulSoup(login_response.text, 'html.parser')
    # Find the script tag containing the 'login_cs' value
    script_tag = soup.find('script', string=lambda s: s and 'planyo_login' in s)
    # Extract the script content
    try:
        script_content = script_tag.text
    except Exception as e:
        print(e)
        print('Most likely a passowrd issue')
        exit()        

    # Use string manipulation to find and extract the 'login_cs' value
    login_cs_start = script_content.find("planyo_login['login_cs']=\"") + len("planyo_login['login_cs']=\"")
    login_cs_end = script_content.find("\"", login_cs_start)
    login_cs = script_content[login_cs_start:login_cs_end]
    if login_response.status_code == 200:
        # Check for successful login by analyzing the response
        soup = BeautifulSoup(login_response.text, 'html.parser')
        if soup.find('div', {'class': 'alert alert-danger'}):
            logging.error("Login failed, check credentials.")
            return None
        else:
            logging.info("Login successful")
            return session,login_cs # Return the session to keep cookies and authenticated state
    else:
        logging.error(f"Login failed with status code: {login_response.status_code}")
        return None

def book_slot(session, first_name, last_name, id_udst, date, time, category, range_time, login_cs):
    """Make a booking using the authenticated session and necessary data."""
    logging.info(f"Booking for {first_name} {last_name} ({id_udst}) on {date} at {time}")

    # Step 3: Navigate to the booking page to extract the CSRF token
    booking_page_url = "https://udstsport.udst.edu.qa/booking"
    booking_csrf_token = get_csrf_token_from_page(session, booking_page_url)

    # Step 4: Prepare data for booking
    booking_url = "https://udstsport.udst.edu.qa/sportsbooking/planyo/ulap.php"

    data = {
        'mode': 'make_reservation',
        'site_id': '56012',
        'resource_id': category,
        'one_date': date,
        'start_time': time,  # Assuming this is in hours (7.5 = 7:30 AM)
        'end_time': time,  # Should this be the same as the start time? Might need adjustment
        'time_mode': 'part_day',
        #! SEE COMMENT BELOW: 'rental_time_fixed_value': range_time,  # 1.5-hour rental
        'quantity': '1',
        'first': first_name,
        'last': last_name,
        'email': f'{id_udst}@udst.edu.qa',
        'verify_data': 'true',
        'granulation': '15',
        'is_night': '0',
        'first_working_hour': '6',  # 6 AM
        'last_working_hour': '20',  # 8 PM
        'submitted': 'true',
        'feedback_url':f'https://udstsport.udst.edu.qa/booking?ppp_upcoming_av_day_choices=7,15,30&ppp_res_period=1725861600-1725866999&planyo_lang=EN&mode=reserve&prefill=true&one_date={date}&start_date={date}&start_time={time}&resource_id={category}',
        'ulap_url': 'https://www.planyo.com/rest/planyo-reservations.php',
        'language': 'en',
        'plugin_mode': '10',
        'dynm': '1',
        'login_cs': login_cs,  # Your session token
        'login_email': f'{id_udst}@udst.edu.qa',
        'ppp_upcoming_av_day_choices': '7,15,30',
        'ppp_res_period': '1725861600-1725866999',  # Reservation period in Unix time
        'user_agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
    }

    if category in ['235824','235845']:    # FOR GAMING BOOKING
        data['rental_time_value'] = range_time 
        data['rental_duration_text'] = f"{range_time} Hour Booking"
        data['granulation'] = '60'
        data['first_working_hour'] = '7'
        data['last_working_hour'] = '19'    # from 22 -> 19
        data['feedback_url'] = 'https://udstsport.udst.edu.qa/booking'
        #data['end_time'] = get_time_for_gaming(time)
    else:
        # DEFAULT VALUE FOR OTHER BOOKINGS
        data['rental_time_fixed_value'] = range_time

    # Step 5: Prepare headers for the booking request
    post_headers = {
        'Host': 'udstsport.udst.edu.qa',
        'Content-Length': str(len(data)),
        'Sec-Ch-Ua': '"Not-A.Brand";v="99", "Chromium";v="124", "Google Chrome";v="124"',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Sec-Ch-Ua-Mobile': '?0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.60 Safari/537.36',
        'Origin': 'https://udstsport.udst.edu.qa',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://udstsport.udst.edu.qa/',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'X-CSRF-Token': booking_csrf_token,
    }

    # Headers For Only Guest List
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "connection": "keep-alive",
        'Referer': 'https://udstsport.udst.edu.qa/',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
    }

    #Testing Guest Lists For Futsal Or Padel Or Other Sports

    # Sooner Going to change it into a format where it gonna try to book for both the ground
    # if the one of them aint workin then it tries for the next one
    if category in ['209258','209259']:
        students = session.get("https://udstsport.udst.edu.qa/guest-list",headers=headers)
        print("---")
        student = students.json()
        st_no = 1 #guest_no for loop below
        # Based On The Requests they have options for staff student faculty alumini and public
        data['rental_prop_Count_Guest_Staff'] = 0
        data['rental_prop_Count_Guest_Student'] = 0
        data['rental_prop_Count_Guest_Faculty'] = 0
        data['rental_prop_Count_Guest_Alumni'] = 0
        data['rental_prop_Count_Guest_Public'] = 0
        for info in student:
            data[f'rental_prop_Guest_name_{st_no}'] = info['name']
            data[f'rental_prop_Guest_email_{st_no}'] = info['email']
            data[f'rental_prop_CNA_Q_ID_{st_no}'] = info['cnaq_id']
            data[f'rental_prop_National_ID_{st_no}'] = info['national_id']
            data[f'rental_prop_Guest_ID_{st_no}'] = info['id']
            data[f'rental_prop_Guest_category_{st_no}'] = info['category']

            if info['category'] == 'Student':
                data['rental_prop_Count_Guest_Student'] += 1
            if info['category'] == 'Alumini':
                data['rental_prop_Count_Guest_Alumni'] += 1
            if info['category'] == 'Public':
                data['rental_prop_Count_Guest_Public'] += 1
            if info['category'] == 'Staff':
                data['rental_prop_Count_Guest_Staff'] += 1
            if info['category'] == 'Faculty':
                data['rental_prop_Count_Guest_Faculty'] += 1
            
            st_no += 1

    data['rental_prop_Please_specify_the_sporting_code_'] = 'Futsal'
    #Data Testing
    for i in data:
        print(f'{i} : {data[i]}')

    try:
        # Step 6: Send the booking request
        response = session.post(booking_url, headers=post_headers, data=data,timeout=(10, 30))
        if response.status_code == 200:
            logging.info("Booking successful!")
            Data = json.loads(response.text)
            if 'data' in Data.keys():
                user_text = BeautifulSoup(Data['data']['user_text'],'html.parser')
                user_text = user_text.get_text()
            else:
                user_text = Data['response_message'].split('<script')[0].strip()
            print(user_text)
        else:
            logging.warning(f"Booking failed with status code: {response.status_code}")
            logging.debug(response.text)
    except requests.RequestException as e:
        logging.error(f"Request failed: {e}")


#Main

# Create the parser
parser = argparse.ArgumentParser(description='Gym script for booking a slot.')

# Add other arguments as necessary
parser.add_argument('--pa', required=True, type=str, help='Password')
parser.add_argument('--fn', type=str, help='First Name')
parser.add_argument('--ln', type=str, help='Last Name')
parser.add_argument('--i', required=True, type=str, help='User ID for login')
parser.add_argument('--ca', type=int, required=True, help='Category index')
parser.add_argument('--t',type=str,required=True,help="Time In 24 hrs format , 12:30 = 12.5")
parser.add_argument('--fd',type=int,help="7 days ahead booking")
parser.add_argument('--d',type=str,help="set the day and date")
parser.add_argument('--duration', type=str, help="Add custom duration to booking")

# Parse the arguments
args = parser.parse_args()

# Login using the parsed arguments
session, login_cs = login(id_udst=args.i, password=args.pa)

# GYM, SWIMMING, STANDARD, HIGH-END GAMING (in order)
category = ['178388', '178795', '235825','235824','209258','209259']
range_time = ['1.5', '1', '2']
'''
cats = [0:('178388','1.5'),1:('178795','1'),2:('235825',2),3:('235824',),]
#need to complete this to make it better
'''
if args.duration is not None:
    # If custom duration is provided
    range_time_chosen = args.duration
else:
    # Otherwise use category-default timings
    range_time_chosen = range_time[args.ca]

#Example of how to calculate the date and time
if not args.fd:
    book_slot(session=session, first_name=args.fn, last_name=args.ln, id_udst=args.i, date=args.d, time=args.t, category=category[args.ca], range_time=range_time_chosen, login_cs=login_cs)
else:
    date = future_day(args.fd)
    book_slot(session=session, first_name=args.fn, last_name=args.ln, id_udst=args.i, date=date, time=args.t, category=category[args.ca], range_time=range_time_chosen, login_cs=login_cs)

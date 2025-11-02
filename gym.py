import requests
from datetime import datetime, timedelta
import argparse
import logging
from bs4 import BeautifulSoup
import random
import json
#from sport_types import SportType


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

def format_time_for_gaming(time: float) -> str:
    # End-time for gaming is 6 hours ahead, and is capped at 21
    adjusted_time = time + 6 
    if adjusted_time > 21:
        adjusted_time = 21
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

def post_booking_request(session: requests.Session, data: dict, headers: dict) -> requests.Response:
    # Step 4: Prepare data for booking
    booking_url = "https://udstsport.udst.edu.qa/sportsbooking/planyo/ulap.php"

    # Step 6: Send the booking request
    try:
        response = session.post(booking_url, headers=headers, data=data,timeout=(10, 30))
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
    except requests.JSONDecodeError as e:
        logging.error(f"Encountered JSONDecodeError. Please check submission data. {e}")
    except requests.RequestException as e:
        logging.error(f"Request failed for unknown reason: {e}")

    return response

def get_DB(session,login_cs,udst_email):
    payload = {
    "mode": "upcoming_availability_search",
    "output": "json",
    "site_id": "56012",
    "sort_fields": "prop_res_sort_order",
    "sort": "prop_res_sort_order",
    "ppp_current_page": "1",
    "ppp_results_per_page": "200",
    "upcoming-until-dates": "2025-09-16_2025-10-16",
    "prop_res_client": "UDST Community",
    "prop_res_gender": "",
    "prop_res_indoor_or_outdoor": "none",
    "extra_search_fields": "client,gender,indoor_or_outdoor,",
    "ppp_hidden_fields": "prop_res_client",
    "submitted": "true",
    "feedback_url": "https://udstsport.udst.edu.qa/booking?ppp_upcoming_av_fixed_days=30&mode=upcoming_availability&extra_search_fields=prop_res_gender%2Cprop_res_client%2Cprop_res_indoor_or_outdoor&prop_res_client=UDST%2BCommunity&ppp_hidden_fields=prop_res_client",
    "ulap_url": "https://www.planyo.com/rest/planyo-reservations.php",
    "language": "EN",
    "plugin_mode": "0",
    "dynm": "0",
    "login_cs": login_cs,
    "login_email": udst_email,
    "ppp_upcoming_av_fixed_days": "30",
    "ppp_upcoming_av_day_choices": "7,15,30",
    "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
}
    headers = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://udstsport.udst.edu.qa",
    "Pragma": "no-cache",
    "Referer": "https://udstsport.udst.edu.qa/booking?ppp_upcoming_av_fixed_days=30&mode=upcoming_availability&extra_search_fields=prop_res_gender%2Cprop_res_client%2Cprop_res_indoor_or_outdoor&prop_res_client=UDST%2BCommunity&ppp_hidden_fields=prop_res_client",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "x-csrf-token": get_csrf_token_from_page(session,"https://udstsport.udst.edu.qa/booking"),
    "X-Requested-With": "XMLHttpRequest",
    "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
}
    data = BeautifulSoup(session.post("https://udstsport.udst.edu.qa/sportsbooking/planyo/ulap.php",data=payload,headers=headers).json()['data']['code'],"html.parser").find_all(class_="wi-search-results__card-body")
    rental_time = session.post("https://www.planyo.com/fetch-data.php?&id=56012&with_resources=1")
    rental_time = rental_time.json()["resources"]
    Database = {}
    for index in range(len(data)):
        name = data[index].find("a").text.replace("\r\n","").replace("\n","").strip()
        resource_id = dict(map(lambda x:x.split("="),data[index].find_all("a")[0].get("href").split("&")))['resource_id']
        rental_time_max = rental_time[resource_id]["max_rental_time"]
        if float(rental_time_max) < 12:
         Database[name] = {"id":resource_id,"rental_time":rental_time_max}
    
    return Database


def book_gym(session: requests.Session, data: dict, post_headers: dict):
    # post_headers['Content-Length'] = str(len(data)); Can use if needed.

    for times in range(3):
        response = post_booking_request(session, data=data, headers=post_headers)
        if response.status_code == 200:
            break

def book_gaming(session: requests.Session, data: dict, post_headers: dict):
    del data['rental_time_fixed_value'] # delete rental_time_fixed_value as gaming booking data does not have this
    data['rental_time_value'] = range_time 
    data['rental_duration_text'] = f"{range_time} Hour Booking"
    data['granulation'] = '60'
    data['first_working_hour'] = '7'
    data['last_working_hour'] = '19'    # from 22 -> 19
    data['feedback_url'] = 'https://udstsport.udst.edu.qa/booking'
    # data['end_time'] = format_time_for_gaming(time)

    post_headers['Content-Length'] = str(len(data))

    for times in range(3):
        response = post_booking_request(session, data=data, headers=post_headers)
        if response.status_code == 200:
            break

def add_guests_to_data(session: requests.Session, data: dict) -> dict:
    # Headers For Only Guest List
    guest_request_headers = {
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

    # Testing Guest Lists For Futsal Or Padel Or Other Sports

    # Sooner Going to change it into a format where it gonna try to book for both the ground
    # if the one of them aint workin then it tries for the next one

    students = session.get("https://udstsport.udst.edu.qa/guest-list",headers=guest_request_headers)
    print("-"*15)
    student = students.json()
    student_count = 1 #guest_no for loop below
    for info in student:
        data[f'rental_prop_Guest_name_{student_count}'] = info.get('name')
        data[f'rental_prop_Guest_email_{student_count}'] = info.get('email')
        data[f'rental_prop_CNA_Q_ID_{student_count}'] = info.get('cnaq_id')
        data[f'rental_prop_National_ID_{student_count}'] = info.get('national_id')
        data[f'rental_prop_Guest_ID_{student_count}'] = info.get('id')
        data[f'rental_prop_Guest_category_{student_count}'] = info.get('category')

        count_guest_key = f"rental_prop_Count_Guest_{ info['category'].capitalize() }"

        if count_guest_key not in data:
            data[count_guest_key] = 0

        data[count_guest_key] += 1
        student_count += 1

    return data


def book_multi_purpose(session: requests.Session, data: dict, post_headers: dict, sport: str = "Futsal"):
    data['rental_prop_Please_specify_the_sporting_code_'] = sport
    # data['rental_prop_Sporting_Code'] = sport [ONLY FOR MULTI-SPORT HALL in B18]

    # TODO: Booking random sports 

    #! Review: Is this useful? (Since we already book on time, and only Futsal has this feature)
    alternate_booking = False
    alternate_courts_list = [('209258','209259')]
    if sport == "Futsal":
        alternate_booking = True
        court_options = alternate_courts_list[0]        # To be replaced with a sport's specific index
        alternative_court = court_options[0]
        if alternative_court == data['resource_id']:
            alternative_court = court_options[1]

    # dictionaries are passed by reference, so they are mutable by functions. you can choose to omit
    # the `data =` if you think it looks clearer
    data = add_guests_to_data(session, data=data)

    # TODO: Think of some better ways to do this (to me)
    post_headers['Content-Length'] = str(len(data))

    #! Note: To detect when cannot rent resource, response will have a response code of 4. Can use this
    # The reason I'm repeating this code is to enable customization of booking for alternative courts when booking a sport
    for times in range(3):
        response = post_booking_request(session,data=data, headers=post_headers)
        try:
            response_json = response.json()
            # If we allow for alternative booking AND we get an error signifying spot is taken...
            if alternate_booking and response.status_code == 200 and response_json['response_code'] == 4:
                print(f"Slot is already booked for {sport}. Trying with alternative court.")
                data['resource_id'] = alternative_court 
            elif response.status_code == 200:
                break
            else:
                print(f"Response returned status code {response.status_code}")
        except requests.JSONDecodeError as e:
            logging.error(f"Encountered JSONDecodeError. Please check submission data. {e}")

def book_slot(session, first_name, last_name, id_udst, date, time, category, range_time, login_cs, sport: str = "Futsal"):
    """Make a booking using the authenticated session and necessary data."""
    logging.info(f"Booking for {first_name} {last_name} ({id_udst}) on {date} at {time}")

    # Step 3: Navigate to the booking page to extract the CSRF token
    booking_page_url = "https://udstsport.udst.edu.qa/booking"
    booking_csrf_token = get_csrf_token_from_page(session, booking_page_url)

    data = {
        'mode': 'make_reservation',
        'site_id': '56012',
        'resource_id': category,
        'one_date': date,
        'start_time': time,  # Assuming this is in hours (7.5 = 7:30 AM)
        'end_time': float(time)+float(range_time),  # Should this be the same as the start time? Might need adjustment
        'time_mode': 'part_day',
        #! SEE COMMENT BELOW: 'rental_time_fixed_value': range_time,  # 1.5-hour rental
        'quantity': '1',
        'first': first_name,
        'last': last_name,
        'email': f'{id_udst}@udst.edu.qa',
        'rental_time_fixed_value': range_time,
        'verify_data': 'true',
        'granulation': '60',
        'is_night': '0',
        'first_working_hour': '7',  # 6 AM
        'last_working_hour': '23',  # 8 PM
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

    if category in {'235824','235845'}:    # FOR GAMING BOOKING
        book_gaming(session, data, post_headers)
    elif category in {'209258','209259'}:
        book_multi_purpose(session, data, post_headers, sport)
    else:
        book_gym(session, data, post_headers)

    #Data Testing
    for i in data:
        print(f'{i} : {data[i]}')


#Main

# Create the parser
parser = argparse.ArgumentParser(description='Gym script for booking a slot.')

# Add other arguments as necessary
parser.add_argument('--pa', required=True, type=str, help='Password')
parser.add_argument('--fn', type=str, help='First Name')
parser.add_argument('--ln', type=str, help='Last Name')
parser.add_argument('--i', required=True, type=str, help='User ID for login')
parser.add_argument('--ca', type=str, required=True, help='Category index')
parser.add_argument('--t',type=str,required=True,help="Time In 24 hrs format , 12:30 = 12.5")
parser.add_argument('--fd',type=int,help="7 days ahead booking")
parser.add_argument('--d',type=str,help="set the day and date")
parser.add_argument('--duration', type=str, help="Add custom duration to booking")
parser.add_argument('--s', type=str, help="For The Sport To Be Selected At The Court")
parser.add_argument('--list', type=str, help="Listing Options")

# Parse the arguments
args = parser.parse_args()

# Login using the parsed arguments
session, login_cs = login(id_udst=args.i, password=args.pa)

# GYM, SWIMMING, STANDARD, HIGH-END GAMING (in order)
category = ['178388', '244923', '235825','235824','209258','209259']
range_time = ['1.5', '1', '2']

category_ids = [
        ('178388','1.5'),   # Gym
        ('244934','1'),     # Swimming
        ('235825','2'),     # Gaming Standard
        ('235824', '2'),    # Gaming High-End
        ('209258', '1'),    # MPH Court 1
        ('209259', '1')     # MPH Court 2
]

if args.duration is not None:
    # If custom duration is provided
    range_time_chosen = args.duration

if args.s:
    # Experimenting with enums. Could add later? (Due to repetition)
    if args.s.upper() not in SportType:
        print("Invalid sport type. Reverting to Futsal")
        # sport = SportType.FUTSAL
        sport = "Futsal"
    else:
        # sport = SportType[args.s]
        sport = args.s
else:
    sport = "Futsal" 

Database = get_DB(session,login_cs,f'{id}@udst.edu.qa')
#{"facility" : {id,rental duration}}

facility = Database.get(args.ca)
rental_time = facility.get("rental_time")
id = facility.get("id")

if args.list:
    for k in ['Turf Football Pitch', '8- Lane Running Track (Event Park)', 'Multi-Sport Hall-Building 18', 'Beach Volleyball Court', 'Cricket Batting Cages', 'Female Fitness Class: Yoga', 'Female Fitness Room', 'Mixed Class: SpinFIT', 'Female Fitness Class: Female SpinFIT', 'Female Fitness Class: Pilates', 'Female Fitness Class: SuperFIT (Advanced Users)', 'Female Fitness Class: Zumba®️', 'MPH Multi-Sport Court 1 (Futsal, Volleyball & Basketball)', 'Female Fitness Class: Les Mills Body Pump', 'Female Swimming Pool', 'E- gaming Playstation', 'E- gaming Premium', 'Outdoor Padel Court 1 (Private Court)', 'MPH Indoor Squash Court 1 (60-Minute Bookings)', 'E- gaming Standard', 'Outdoor Tennis Courts', 'Outdoor Padel Court 3', 'Outdoor Padel Court 2', 'MPH Indoor Padel Court 3 (Private Court)', 'MPH Indoor Padel Court 1', 'Male Swimming Pool', 'Male Fitness Room', 'PADI Starfish Learn to Swim Program - LEVEL 1', 'PADI Starfish Learn to Swim Program - LEVEL 2', 'PADI Starfish Learn to Swim Program - LEVEL 3', 'PADI Starfish Learn to Swim Program - LEVEL 4', 'PADI Starfish Learn to Swim Program - LEVEL 5', 'PADI Starfish Learn to Swim Program - LEVEL 6', 'Multi-Sport Hall-Building 17', 'UDST Wolves Tennis Academy: Spring Term from Sept 7th – Dec 6th ,2025 (13-week program) - For Children Born in 2021', 'Female Fitness Class: Female Virtual SpinFIT', 'Male Fitness Class: Male Virtual SpinFIT', 'Female Fitness Class: AquaFIT', 'MPH Multi-Sport Court 2 (Futsal, Handball & Tennis)', 'MPH – Auxiliary Rooms', 'Natural Grass Cricket Ground', 'Natural Grass Football Pitch (Event Park)', 'MPH Indoor Squash Court 2 (90-Minute Bookings)', 'MPH Indoor Padel Court 2']:
        print(k)
#Example of how to calculate the date and time
if not args.fd:
    book_slot(session=session, first_name=args.fn, last_name=args.ln, id_udst=args.i, date=args.d, time=args.t, category=id, range_time=rental_time, login_cs=login_cs)
else:
    date = future_day(args.fd)
    book_slot(session=session, first_name=args.fn, last_name=args.ln, id_udst=args.i, date=date, time=args.t, category=id, range_time=rental_time, login_cs=login_cs)

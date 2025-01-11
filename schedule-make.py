def write_data(data,name):
	with open(f'{name}.yml','w') as file:
		file.write(data)
		print('yml generated')
def gym_or_pool():
	global cat
	cat = error_handle(cat,'''Enter Which Do You Pick Gym type - 0 / Pool type - 1''','1 or 0',1)
	return cat

def time_to_cron(hr,min,day):
	D = {'Sunday':0,'Monday':1,'Tuesday':2,'Wednesday':3,'Thursday':4}
	DD = day
	day = D[day.capitalize()]
	return f"{DD.capitalize()}",f'{min} {hr} * * {day}'


def add_res(c,time,name,Day):
	return f'''      - name: {Day}-Gym
        shell: powershell
        if: ${{ steps.get_datetime.outputs.current_day == '{Day}' && steps.get_datetime.outputs.current_hour >= {time} && steps.get_datetime.outputs.current_hour <= {time+1} }}
        run: python gym.py --pa ${{ secrets.PASS_{name} }} --i ${{ secrets.ID_{name} }} --ln ${{ secrets.LAST_NAME_{name} }} --fn ${{ secrets.ME_FIRST_{name} }} --ca {c} --t 13.5 --fd True'''

def error_handle(v,s,t,f='h'):
	while True:
		try:
			if type(f) == str:
				v = input(s)
			elif type(f) == int:
				v = int(input(s))
			break
		except:
			print(f'Please enter a {t}')
	return v

def get_time():
	global hr
	global min
	global day
	hr = error_handle(hr,'Please Enter Hour(24hr format): ','Hour',1)
	min = error_handle(hr,'Please Enter Min: ','Hour',2)
	while True:
		day = error_handle(hr,'Please Enter Day: ','Hour')
		if day.lower() not in ['sunday','monday','tuesday','wednesday','thursday']:
			print('rewrite day again please')
		else:break
	D,cron = time_to_cron(hr,min,day)
	return D,cron

output = ""
times = None
time = ''
name = ''
hr = None
min = None
day = None
crons = []
name = error_handle(name,'Enter Your Name Or Id: ','Id Or Name')
cat = ''
res = []

output += f'name: {name}\n'



while type(times) != str:
	try:
		times = input('How many times in a week do you go to both gyum and pool: ')
	except:
		print('Please Enter A Number')
	
output += '''on:\n  schedule:\n'''
for i in range(int(times)):
	D,cron = get_time()
	crons.append(cron)
	res.append(add_res(gym_or_pool(),int(crons[-1].split()[1]),name,D))
	print('next day:')
	print()
	output += f"    - cron: '{cron}'\n"

output += '''jobs:
  Automated-Booking:
    runs-on: self-hosted
    steps:
    
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Set up Python 3.x
        uses: actions/setup-python@v4
        with:
          python-version: '3.x'
    
      - name: Get Day and Time
        id: get_datetime
        shell: powershell
        run: |
          $current_hour = Get-Date -Format 'HH'
          $current_day = Get-Date -Format 'dddd'
          echo "::set-output name=current_hour::$current_hour"
          echo "::set-output name=current_day::$current_day"
      
      - name: Date And Time
        run: |
          echo "Current Day: ${{ steps.get_datetime.outputs.current_day }}"
          echo "Current Hour: ${{ steps.get_datetime.outputs.current_hour }}"
'''

for i in res:
	output += f"{i}\n"
	output += "\n"

#print(output)

write_data(output,name)

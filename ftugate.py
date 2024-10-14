import os
import requests
import json
from pwinput import pwinput
from tabulate import tabulate
from datetime import datetime, timedelta, timezone
from ics import Calendar, Event
from time import sleep

# Function to log in to Ftugate
def login():
	username = input("Nhập mã sinh viên: ")
	password = pwinput(prompt='Nhập mật khẩu: ', mask='*') 

	login_response = requests.post('https://ftugate.ftu.edu.vn/api/auth/login', 
		headers={'accept': 'application/json, text/plain, */*', 'authorization': ''},
		data={'username': username, 'password': password, 'grant_type': 'password'}).json()

	access_token = login_response.get('access_token')
	name = login_response.get('name')

	if access_token is None:
		return None
	else:
		print("Đăng nhập thành công.")
		os.system('cls' if os.name == 'nt' else 'clear')
		print(f"Xin chào, {name}!\n")
		return access_token

def reg_response(access_token, class_name, id_to_hoc, is_checked):
	reg_response = requests.post(
		'https://ftugate.ftu.edu.vn/api/dkmh/w-xulydkmhsinhvien',
		headers = {'Authorization': f'Bearer {access_token}', "Host": "ftugate.ftu.edu.vn","Content-Type": "application/json"},
		json={"filter": {"id_to_hoc": id_to_hoc, "is_checked": is_checked, "sv_nganh": 1}})

	if reg_response.status_code==200:
		data = reg_response.json()['data']
		if 'is_thanh_cong'==True:
			if is_checked==True:
				print(f"Đăng ký thành công lớp tín chỉ '{class_name}'.\n")
				return True
			else:
				print(f"Huỷ đăng ký thành công lớp tín chỉ '{class_name}'.\n")
		else:
			if is_checked==True:
				print(f"Không thể đăng ký lớp tín chỉ '{class_name}'.")
			else:
				print(f"Không thể huỷ đăng ký lớp tín chỉ '{class_name}'.")
			print(f"{data['thong_bao_loi']}")
			if data['thong_bao_loi']=="Cảnh báo: tài khoản của bạn không được đăng ký/hủy đăng ký ở thời điểm hiện tại.":
				return True
			else:
				return False
	else:
		print("Tên lớp tín chỉ không hợp lệ. Vui lòng thử lại")
		return True
		

# Function to register classes
def register_class(access_token, class_name):
	id_to_hoc = next((item['id_to_hoc'] for item in class_list['data']['ds_nhom_to'] if item['nhom_to'] == class_name), '')
	is_checked=True
	reg_response(access_token, class_name, id_to_hoc, is_checked)

# Function to cancel class registration
def cancel_class(access_token, class_name):
	id_to_hoc = next((item['id_to_hoc'] for item in class_list['data']['ds_nhom_to'] if item['nhom_to'] == class_name), '')
	is_checked=False
	reg_response(access_token, class_name, id_to_hoc, is_checked)

# Function to spam register classes
def spam_register_class(access_token, class_name):
	id_to_hoc = next((item['id_to_hoc'] for item in class_list['data']['ds_nhom_to'] if item['nhom_to'] == class_name), '')

	attempt_count = 0

	while True:
		attempt_count += 1
		is_checked = True
		print(f"\nKết quả lần thử {attempt_count}:")
		if reg_response(access_token, class_name, id_to_hoc, is_checked)==True:
			print(f"\nDừng đăng ký sau {attempt_count} lần thử.")
			break
		if attempt_count >= 100:
			print(f"\nDừng đăng ký sau {attempt_count} lần thử.")
			break

def format_semester_name(hoc_ky):
	hoc_ky = str(hoc_ky)
	year_part = hoc_ky[:4]  # First 4 digits are the year part (e.g., 2024)
	semester_code = hoc_ky[-1]  # Last digit determines the semester (1, 2, or 3)
	
	if semester_code == '1':
		semester_name = f"Học kỳ 1 Năm học {year_part}-{int(year_part) + 1}"
	elif semester_code == '2':
		semester_name = f"Học kỳ 2 Năm học {year_part}-{int(year_part) + 1}"
	elif semester_code == '3':
		semester_name = f"Học kỳ Hè Năm học {year_part}-{int(year_part) + 1}"
	else:
		semester_name = f"Unknown Semester ({hoc_ky})"
	
	return semester_name

def export_timetable(access_token):
	print("\nNhập tên học kỳ muốn xuất thời khoá biểu")
	
	# Fetch the list of available semesters
	sem_list = requests.post(
		'https://ftugate.ftu.edu.vn/api/sch/w-locdshockytkbuser',
		headers={'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'},
		json={"filter":{"is_tieng_anh": None},"additional":{"paging":{"limit":100,"page":1},"ordering":[{"name":"hoc_ky","order_type":1}]}}
	).json()

	# List all semesters with numerical options and their full description
	semesters = sem_list['data']['ds_hoc_ky']
	if semesters:
		print("\nDanh sách các học kỳ có sẵn:")
		for idx, sem in enumerate(semesters, 1):
			formatted_semester = format_semester_name(sem['hoc_ky'])
			print(f"{idx}. {formatted_semester}")
		
		# User selects a semester by entering the corresponding number or just hitting Enter for the nearest semester
		choice = input("\nNhập số thứ tự để chọn học kỳ (nhập Enter để chọn học kỳ gần nhất): ").strip()
		if not choice:
			semester = semesters[0]['hoc_ky']
			print(f"\nKhông có lựa chọn, tự động chọn học kỳ gần nhất: {format_semester_name(semester)}")
		else:
			try:
				choice = int(choice)
				if 1 <= choice <= len(semesters):
					semester = semesters[choice - 1]['hoc_ky']
					print(f"\nĐang xuất thời khoá biểu cho {format_semester_name(semester)}...\n")
				else:
					print("Lựa chọn không hợp lệ, sẽ chọn học kỳ gần nhất.")
					semester = semesters[0]['hoc_ky']
			except ValueError:
				print("Lựa chọn không hợp lệ, sẽ chọn học kỳ gần nhất.")
				semester = semesters[0]['hoc_ky']
	else:
		print("Không có học kỳ nào để lựa chọn.")
		return

	# Fetch the timetable for the selected semester
	timetable = requests.post(
		'https://ftugate.ftu.edu.vn/api/sch/w-locdstkbhockytheodoituong',
		headers={'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'},
		json={"hoc_ky": f'{semester}', "loai_doi_tuong": 1, "id_du_lieu": ''}
	).json()

	timetable_data = timetable['data']['ds_nhom_to']
	cal = Calendar()
	utc_offset = timezone(timedelta(hours=7))

	for class_info in timetable_data:
		subject = class_info['ten_mon']
		class_code = class_info['ma_mon']
		class_group = class_info['nhom_to']
		room = class_info['phong']
		start_date_str, end_date_str = class_info['tkb'].split(' đến ')
		start_date = datetime.strptime(start_date_str, "%d/%m/%y")
		end_date = datetime.strptime(end_date_str, "%d/%m/%y")

		start_time = datetime.strptime(class_info['tu_gio'], "%H:%M").time()
		end_time = (datetime.combine(datetime.min, start_time) + timedelta(hours=2, minutes=30)).time()

		current_date = start_date
		while current_date <= end_date:
			event = Event()
			event.name = f"{subject} ({class_code})"
			event.description = f"{class_group}\nPhòng: {room}"

			start_datetime = datetime.combine(current_date, start_time, tzinfo=utc_offset)
			end_datetime = datetime.combine(current_date, end_time, tzinfo=utc_offset)
			event.begin = start_datetime
			event.end = end_datetime

			cal.events.add(event)
			current_date += timedelta(weeks=1)

	exported_filename=f'{semester}.ics'

	with open(exported_filename, 'w', encoding='utf-8-sig', newline='') as f:
		f.writelines(cal)

	file_path = os.path.abspath(exported_filename)
	print(f'Xuất thời khoá biểu học kỳ thành công tại: {file_path}')

# Function to display registration summary
def display_registration_summary(access_token):
	reg_summary = requests.post(
		'https://ftugate.ftu.edu.vn/api/dkmh/w-locdskqdkmhsinhvien',
		headers={'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'},
		json={'is_CVHT': False, 'is_Clear': False}).json()

	fields = ["Tên môn học", "Lớp tín chỉ", "Ngày đăng ký"]
	data = []
	if reg_summary.get('data', {}).get('ds_kqdkmh'):
		for item in reg_summary['data']['ds_kqdkmh']:
			date_str = item['ngay_dang_ky']
			date_parts = date_str.split('T')
			time_part = date_parts[1][:8]
			date_part = date_parts[0]
			formatted_date = "/".join(date_part.split('-')[::-1])
			formatted_datetime = f"{formatted_date} {time_part}"
			data.append((item['to_hoc']['ten_mon'], item['to_hoc']['nhom_to'], formatted_datetime))

	sorted_data = sorted(data, key=lambda x: datetime.strptime(x[2], "%d/%m/%Y %H:%M:%S"), reverse=True)
	table = tabulate(sorted_data, headers=fields, tablefmt='grid')
	print("\nDanh sách môn học đã đăng ký:")
	print(table)

# Main program
def main():
	access_token = None
	while True:
		if access_token is None:
			access_token = login()
			if access_token is None:
				print("Đăng nhập không thành công. Vui lòng thử lại.\n")
				continue

		global class_list
		class_list = (requests.post(
			"https://ftugate.ftu.edu.vn/api/dkmh/w-locdsnhomto",
			headers={'Authorization': f'Bearer {access_token}', "Host": "ftugate.ftu.edu.vn", "Content-Type": "application/json"},
			json={"is_CVHT": False, "additional": {"paging": {"limit": 99999,"page": 1},"ordering": [{"name": "","order_type": ""}]}})).json()

		print("\nMenu:")
		print("1. Đăng ký lớp tín chỉ")
		print("2. Huỷ đăng ký lớp tín chỉ")
		print("3. Spam đăng ký lớp tín chỉ")
		print("4. Xuất thời khoá biểu học kỳ ra file .ics")
		print("5. Xem danh sách môn học đã đăng ký")
		print("6. Đăng xuất")
		print("7. Thoát")

		choice = input("Chọn chức năng (1-7): ")

		if choice == '1':
			classes = input("\nNhập tên lớp tín chỉ (ngăn cách tên các lớp bằng dấu cách nếu đăng ký nhiều lớp): ").split()
			for class_name in classes:
				register_class(access_token, class_name)
			display_registration_summary(access_token)

		elif choice == '2':
			classes = input("\nNhập tên lớp tín chỉ cần huỷ (ngăn cách tên các lớp bằng dấu cách nếu huỷ nhiều lớp): ").split()
			for class_name in classes:
				cancel_class(access_token, class_name)
			display_registration_summary(access_token)

		elif choice == '3':
			classes = input("\nNhập tên lớp tín chỉ cần đăng ký (Vui lòng chỉ nhập 1 lớp, mở lại trong cửa sổ khác để đăng ký nhiều lớp): ").split()
			for class_name in classes:
				spam_register_class(access_token, class_name)
			display_registration_summary(access_token)

		elif choice == '4':
			export_timetable(access_token)

		elif choice == '5':
			display_registration_summary(access_token)

		elif choice == '6':
			access_token = None
			print("\nĐã đăng xuất. Vui lòng đăng nhập lại.")

		elif choice == '7':
			print()
			for i in range(5, 0, -1):
				print(f"Tự động thoát trong {i} giây...", end='\r')
				sleep(1)
			break

		else:
			print("Lựa chọn không hợp lệ. Vui lòng chọn lại.")

if __name__ == "__main__":
	main()

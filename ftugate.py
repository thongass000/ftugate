import requests
import json
from pwinput import pwinput
from tabulate import tabulate
from datetime import datetime
from time import sleep

# Function to log in ftugate
def login():
    username = input("Nhập mã sinh viên: ")
    password = pwinput(prompt='Nhập mật khẩu: ', mask='*') 

    # Make a request to obtain an access token using password grant type
    login_response = requests.post(
        'http://ftugate.ftu.edu.vn/cq/hanoi/api/auth/login',
        data={'username': username, 'password': password, 'grant_type': 'password'},
        verify=False  # Disabling SSL verification, consider using it in production
    ).json()

    # Extract values from the response
    access_token = login_response.get('access_token')
    name = login_response.get('name')

    if access_token is None:
        return None
    else:
        print("Đăng nhập thành công.")
        print(f"Xin chào, {name}!")
        print()
        return access_token

# Function to register classes
def register_class(access_token, class_name):
    # Get the list of classes open for registration
    class_list = requests.post(
        'http://ftugate.ftu.edu.vn/cq/hanoi/api/dkmh/w-locdsnhomto',
        headers={'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'},
        json={'is_CVHT': False, 'additional': {'paging': {'limit': 8000, 'page': 1}, 'ordering': [{'name': '', 'order_type': ''}]}}
    ).json()

    # Get the class id for the desired classes
    id_to_hoc = next((item['id_to_hoc'] for item in class_list['data']['ds_nhom_to'] if item['nhom_to'] == class_name), '')

    # Send request to register the classes
    reg_response = requests.post(
        'http://ftugate.ftu.edu.vn/cq/hanoi/api/dkmh/w-xulydkmhsinhvien',
        headers={'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'},
        json={'filter': {'id_to_hoc': id_to_hoc, 'is_checked': True, 'sv_nganh': 1}}
    ).json()

    # Check if the request is successful
    is_thanh_cong = reg_response['data']['is_thanh_cong']
    reg_error_message = reg_response['data']['thong_bao_loi']

    if is_thanh_cong:
        print(f"Đăng ký thành công lớp tín chỉ '{class_name}'.")
        print()
    else:
        print(f"Không thể đăng ký lớp tín chỉ '{class_name}'.")
        print(reg_error_message)
        print()

# Main program
login_needed = True

while True:
    # prompt the user to enter classes
    classes = input("Nhập tên lớp tín chỉ (ngăn cách tên các lớp bằng dấu cách nếu đăng ký nhiều lớp): ")
    print()

    # Check if any classes were entered
    if not classes:
        print("Vui lòng nhập ít nhất một lớp tín chỉ.")
        continue  # Loop back to the beginning

    # Split the entered classes on spaces into a list
    classes = classes.split()

    if login_needed:
        # Proceed with login if needed
        access_token = login()  # Attempt to login
        while access_token is None:
            print("Đăng nhập không thành công. Vui lòng thử lại.\n")
            access_token = login()  # Retry login

    for class_name in classes:
        register_class(access_token, class_name)

    # Display the summary of course registration
    reg_summary = requests.post(
        'http://ftugate.ftu.edu.vn/cq/hanoi/api/dkmh/w-locdskqdkmhsinhvien',
        headers={'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'},
        json={'is_CVHT': False, 'is_Clear': False}
    ).json()

    # Extracted fields
    fields = ["Tên môn học", "Lớp tín chỉ", "Ngày đăng ký"]

    # Process and format the date for each item
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

    # Sort data by date (latest to oldest)
    sorted_data = sorted(data, key=lambda x: datetime.strptime(x[2], "%d/%m/%Y %H:%M:%S"), reverse=True)

    # Format data into a table
    table = tabulate(sorted_data, headers=fields, tablefmt='grid')

    # Print the table
    print("Danh sách môn học đã đăng ký:")
    print(table)

    # Ask the user if they want to continue registering
    print()
    choice = input("Bạn muốn tiếp tục đăng ký lớp tín chỉ không? (y/n): ")

    while choice.lower() not in ['y', 'n']:
        print("Vui lòng nhập 'y' hoặc 'n'.")
        choice = input("Bạn muốn tiếp tục đăng ký lớp tín chỉ không? (y/n): ")

    if choice.lower() == 'n':
        print("\nChúc bạn một học kỳ full A!!!")
        
        # Countdown for 5 seconds
        for i in range(5, 0, -1):
            print(f"Chương trình sẽ tự động thoát trong {i} giây...", end='\r')
            sleep(1)

        print("\nKết thúc chương trình.")
        break
    elif choice.lower() == 'y':
        login_needed = False
        print()
        continue

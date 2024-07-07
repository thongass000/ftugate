#!/bin/bash

# Function to log in ftugate
login() {
	echo -n "Nhập mã sinh viên: "
	read username

	echo -n "Nhập mật khẩu: "
	read -s password
	echo

	# Make a request to obtain an access token using password grant type and capture the response
	login_response=$(curl --no-progress-meter 'http://ftugate.ftu.edu.vn/cq/hanoi/api/auth/login' \
		--data-raw "username=$username&password=$password&grant_type=password" \
		--compressed \
		--insecure)

	# Extract values from the response using Python and store in variables
	access_token=$(echo $login_response | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
	name=$(echo $login_response | python3 -c "import sys, json; print(json.load(sys.stdin)['name'])")
	if [ "$access_token" == "None" ]; then
		echo $(echo $login_response | python3 -c "import sys, json; print(json.load(sys.stdin)['message'])")
		echo
		login
	else
		echo "Đăng nhập thành công."
		echo "Xin chào, $(echo $login_response | python3 -c "import sys, json; print(json.load(sys.stdin)['name'])")!"
		echo
	fi
}

# Function to register classes
register_class() {
	class_name="$1"

	# Get the list of classes open for registration
	class_list=$(mktemp)
	curl --no-progress-meter 'http://ftugate.ftu.edu.vn/cq/hanoi/api/dkmh/w-locdsnhomto' \
		-H "Authorization: Bearer $access_token" \
		-H 'Content-Type: application/json' \
		--data-raw '{"is_CVHT":false,"additional":{"paging":{"limit":8000,"page":1},"ordering":[{"name":"","order_type":""}]}}' \
		--compressed \
		--insecure \
	> "$class_list"

	# Get the class id for the desired classes
	id_to_hoc=$(python3 -c "
import json
import sys

with open('$class_list') as f:
	data = json.load(f)

class_name = '$class_name'
matches = [item['id_to_hoc'] for item in data['data']['ds_nhom_to'] if item['nhom_to'] == class_name]
print(matches[0] if matches else '', end='')" | tr -d '\n')

	rm "$class_list"

	# Send request to register the classes and capture the response
	reg_response=$(curl --no-progress-meter 'http://ftugate.ftu.edu.vn/cq/hanoi/api/dkmh/w-xulydkmhsinhvien' \
		-H "Authorization: Bearer $access_token" \
		-H 'Content-Type: application/json' \
		--data-raw '{"filter": {"id_to_hoc": "'"$id_to_hoc"'", "is_checked": true, "sv_nganh": 1}}' \
		--compressed \
		--insecure)

	# Check if the request is successful
	reg_success_check=$(python3 -c "import json; data = json.loads('''$reg_response'''); is_thanh_cong = data['data']['is_thanh_cong']; print(is_thanh_cong)")

	reg_error_message=$(python3 -c "import json; data = json.loads('''$reg_response'''); thong_bao_loi = data['data']['thong_bao_loi']; print(thong_bao_loi)")

	if [ "$reg_success_check" == "True" ]; then
		echo "Đăng ký thành công lớp tín chỉ '$class_name'."
		echo
	else
		echo "Không thể đăng ký lớp tín chỉ '$class_name'."
		echo "$reg_error_message"
		echo
	fi
}

login_needed=true

while true; do
	if [ "$login_needed" = true ]; then
		# Proceed with login
		login
	fi

	if [ "$#" -eq 0 ]; then
		# prompt the user to enter classes
		read -rp "Nhập tên lớp tín chỉ (ngăn cách tên các lớp bằng dấu cách nếu đăng ký nhiều lớp): " classes
		echo

		# Check if any classes were entered
		if [[ -z "$classes" ]]; then
			echo "Vui lòng nhập ít nhất một lớp tín chỉ."
			continue  # Loop back to the beginning
		fi

		# Split the entered classes on spaces into an array
		read -ra classes <<< "$classes"
	else
		# Classes were provided as arguments
		read -ra classes <<< "$1"
	fi

	for class in "${classes[@]}"; do
		register_class "$class"
	done

	# Display the summary of course registration
	reg_summary=$(curl --no-progress-meter 'http://ftugate.ftu.edu.vn/cq/hanoi/api/dkmh/w-locdskqdkmhsinhvien' \
		-H "Authorization: Bearer $access_token" \
		-H 'Content-Type: application/json' \
		--data-raw '{"is_CVHT":false,"is_Clear":false}' \
		--compressed \
		--insecure)

	python3 <<EOF | column -t -s $'\t'
import json

data = json.loads('''$reg_summary''')

# Extracted fields
fields = ["Tên môn học", "Lớp tín chỉ", "Ngày đăng ký"]
blanks = ["-----------", "-----------", "------------"]

# Sort data by date (latest to oldest)
sorted_data = sorted(data["data"]["ds_kqdkmh"], key=lambda x: x['ngay_dang_ky'], reverse=True)

# Print the header
print("\t".join(fields))
print("\t".join(blanks))


# Print the sorted data
for item in sorted_data:
	# Separate time and date
	date_parts = item['ngay_dang_ky'].split('T')
	time_part = date_parts[1][:8]  # Extract the time part
	date_part = date_parts[0]  # Extract the date part

	# Reformat date to dd/mm/yyyy
	formatted_date = "/".join(date_part.split('-')[::-1])

	# Print the formatted output
	print(f"{item['to_hoc']['ten_mon']}\t{item['to_hoc']['nhom_to']}\t{formatted_date} {time_part}")
EOF
	
	# Ask the user if they want to continue registering
	echo
	read -r -n 1 -p "Bạn muốn tiếp tục đăng ký lớp tín chỉ không? (y/n): " choice 
	while [[ -z "$choice" || ! $choice =~ [YyNn] ]]; do
		echo -e "\nVui lòng nhập 'y' hoặc 'n'."
		read -r -n 1 -p "Bạn muốn tiếp tục đăng ký lớp tín chỉ không? (y/n): " choice
	done

	case "$choice" in
		[Nn]*)
			echo -e "\nChúc bạn một học kỳ full A!!!"
			exit;;
		[Yy]*)
			login_needed=false
			echo
			continue;;
	esac
done

from flask import Flask, render_template, request, redirect, flash, url_for, jsonify
import pymysql
from datetime import datetime
import config
import re
from flask_paginate import Pagination, get_page_parameter
from collections import defaultdict

app = Flask(__name__)
app.config.from_object(config.Config)
app.secret_key = 'supersecretkey'

all_strings = [f"{i:03}" for i in range(1000)]

def get_db_connection():
    try:
        connection = pymysql.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            database=app.config['MYSQL_DB'],
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except pymysql.MySQLError as e:
        print(f"Error connecting to MySQL Database: {e}")
        return None

def is_valid_car_plate(car_plate):
    pattern = r'^[\u4e00-\u9fa5][A-Za-z0-9]{6}$'
    return re.match(pattern, car_plate)

def is_valid_badge_number(badge_number):
    return badge_number.isdigit() and len(badge_number) == 3

def mask_car_plate(car_plate):
    # 脱敏处理车牌号的第四、第五和第六位字符
    return car_plate[:3] + "***" + car_plate[6:]

@app.route('/query_available_badge', methods=['POST'])
def query_available_badge():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT badge_number FROM car_club")
    existing_badge = cursor.fetchall()

    existing_badge = [item['badge_number'] for item in existing_badge]
    print(existing_badge)
    filtered_strings = [s for s in all_strings if s not in existing_badge]
    # 筛选以指定参数开头的字符串
    # matching_strings = [s for s in filtered_strings if s.startswith(badge_number)]
    # TODO 根据matching_strings 的开头数字分组
    grouped_by_first_letter = defaultdict(list)
    for number in filtered_strings:
        first_letter = number[0]
        grouped_by_first_letter[first_letter].append(number)

    cursor.close()
    connection.close()
    return jsonify(grouped_by_first_letter)

@app.route('/', methods=['GET', 'POST'])
def index():
    connection = get_db_connection()
    if connection is None:
        flash('无法连接到数据库。', 'danger')
        return render_template('index.html', car_club_data=[])

    cursor = connection.cursor()

    if request.method == 'POST':
        if 'search_badge' in request.form:
            badge_number = request.form['search_badge']
            if badge_number == "":
                flash('请输入三位数字会标号。', 'danger')
                return redirect(url_for('index'))
            elif not is_valid_badge_number(badge_number):
                flash('输入的会标号格式错误，请重新输入。', 'danger')
                return redirect(url_for('index'))
            else:
                cursor.execute("SELECT * FROM car_club WHERE badge_number = %s ORDER BY badge_number ASC", (badge_number,))
                car_club_data = cursor.fetchall()
        else:
            nickname = request.form['nickname']
            car_plate = request.form['car_plate']
            badge_number = request.form['badge_number']

            if not is_valid_car_plate(car_plate):
                flash('车牌号必须为七位字符，其中第一位为中文字符。', 'danger')
                return redirect(url_for('index'))

            if not is_valid_badge_number(badge_number):
                flash('车友会会标号必须为三位数字。', 'danger')
                return redirect(url_for('index'))

            cursor.execute("SELECT * FROM car_club WHERE badge_number = %s", (badge_number,))
            existing_badge = cursor.fetchone()

            if existing_badge:
                flash('该车友会会标号已被使用。', 'danger')
            else:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute(
                    "INSERT INTO car_club (nickname, car_plate, badge_number, timestamp) VALUES (%s, %s, %s, %s)",
                    (nickname, car_plate, badge_number, timestamp)
                )
                connection.commit()
                flash('会标已成功申请，请等待制作。', 'success')
            return redirect(url_for('index'))
    else:
        cursor.execute("SELECT * FROM car_club ORDER BY badge_number ASC")
        car_club_data = cursor.fetchall()

    cursor.close()
    connection.close()

    # 对车牌号进行脱敏处理
    for row in car_club_data:
        row['car_plate'] = mask_car_plate(row['car_plate'])

    # 获取当前页数
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 20
    offset = (page - 1) * per_page
    total = len(car_club_data)
    car_club_data_paginated = car_club_data[offset: offset + per_page]

    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')

    return render_template('index.html', car_club_data=car_club_data_paginated, pagination=pagination)

if __name__ == '__main__':
    app.run(debug=True)

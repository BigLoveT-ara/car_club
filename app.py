from flask import Flask, render_template, request, redirect, flash, jsonify
import pymysql
from datetime import datetime
import config
import re
from collections import defaultdict

app = Flask(__name__)
app.config.from_object(config.Config)


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
        nickname = request.form['nickname']
        car_plate = request.form['car_plate']
        badge_number = request.form['badge_number']

        if not is_valid_car_plate(car_plate):
            flash('车牌号必须为七位字符，其中第一位为中文字符。', 'danger')
            return redirect('/')

        if not is_valid_badge_number(badge_number):
            flash('车友会会标号必须为三位数字。', 'danger')
            return redirect('/')

        cursor.execute("SELECT id,nickname,car_plate,badge_number,timestamp FROM car_club WHERE badge_number = %s", (badge_number,))
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
            flash('会标信息已成功提交。', 'success')
        return redirect('/')

    cursor.execute("SELECT id,nickname,car_plate,badge_number,timestamp FROM car_club order by badge_number")
    car_club_data = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template('index.html', car_club_data=car_club_data)


if __name__ == '__main__':
    app.run(debug=True)


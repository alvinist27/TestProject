import datetime
import os
from flask import Flask, render_template
from googleapiclient.discovery import build
from google.oauth2 import service_account
import matplotlib.pyplot as plt


# Переменные для работы фреймворка Flask
app = Flask(__name__)
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['DEBUG'] = True

# Настройка для работы с Google API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, 'credentials.json')
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# Данные для взаимодействия со страницей
SAMPLE_SPREADSHEET_ID = '1U4G8PifSmewHiE33ByoSYeyJFrvpsEOMBjyDi9TkTN8'
SAMPLE_RANGE_NAME = 'Лист1'

service = build('sheets', 'v4', credentials=credentials).spreadsheets().values()


# Функция представления корневого адреса
@app.route('/')
@app.route('/test')
def main_page():
    # Чтение данных из таблицы
    labels = []
    values = []
    dictionary = dict()

    result = service.get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME, majorDimension='COLUMNS').execute()
    data_from_sheet = result.get('values', [])
    sum_value = sum(map(int, data_from_sheet[2][1:]))

    labels = [datetime.datetime.strptime(i, "%d.%m.%Y") for i in data_from_sheet[3][1:]]
    values = list(map(int, data_from_sheet[2][1:]))

    for i in range(len(labels)):
        if labels[i] in dictionary:
            dictionary[labels[i]] += values[i]
        else:
            dictionary[labels[i]] = values[i]
    sorted_dictionary = dict(sorted(dictionary.items(), key=lambda x: x[0]))

    plt.plot(sorted_dictionary.keys(), sorted_dictionary.values(), color='b')
    plt.title("График полученной прибыли по датам")
    plt.ylabel("Стоимость, $")
    plt.xticks(rotation=45, fontsize = 5)
    plt.savefig('static/img/plot.png')
    plt.clf()
    return render_template('index.html', data=data_from_sheet, sum=sum_value, url='/static/img/plot.png')


app.run('0.0.0.0', port=5000)

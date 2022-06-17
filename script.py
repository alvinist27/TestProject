import os.path
import time
import requests
import xml.etree.ElementTree as ET
import psycopg2
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from googleapiclient.discovery import build
from google.oauth2 import service_account


def fill_table(cursor, data_from_sheet):
    # Запрос для заполнения базы данных
    url = 'https://www.cbr.ru/scripts/XML_daily.asp'
    cursor.execute(f'''INSERT INTO TEST(NUM, ORD_NUM, COST_USD, DATE_P, COST_RUB)
                          VALUES ('{data_from_sheet[0][0]}', '{data_from_sheet[0][1]}', '{data_from_sheet[0][2]}', '{data_from_sheet[0][3]}', 'стоимость,руб.')''')
    rate_usd = float(
        ET.fromstring(requests.get(url).text).find("./Valute[CharCode='USD']/Value")
        .text.replace(",", ".")
    )
    for values in data_from_sheet[1:]:
        if len(values) > 3:
            cost_r = str(round(float(values[2]) * rate_usd, 4))
            cursor.execute(f'''INSERT INTO TEST(NUM, ORD_NUM, COST_USD, DATE_P, COST_RUB)
                              VALUES ('{values[0]}', '{values[1]}', '{values[2]}', '{values[3]}', '{cost_r}')''')
    connection.commit()


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

# Чтение данных из таблицы
result = service.get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME).execute()
data_from_sheet = result.get('values', [])

# Данные базы данных поо умолчанию
USER = "postgres"
PASSWORD = "password"
HOST = "127.0.0.1"
PORT = "5432"
DBNAME = 'postgres_db'

try:
    # Подключение к существующей базе данных
    connection = psycopg2.connect(
        user=USER, password=PASSWORD, host=HOST, port=PORT
    )
    print("Соединение с PostgreSQL открыто")
    connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    # Создание курсора для выполнения операций с базой данных
    cursor = connection.cursor()

    # Запрос для создания базы данных
    sql_create_database = 'CREATE database postgres_db'
    cursor.execute(sql_create_database)
    print("База данных успешно создана!")
    cursor.close()
    connection.close()
except (Exception, Error) as error:
    print("Ошибка при работе с PostgreSQL", error)
finally:
    if connection:
        cursor.close()
        connection.close()
        print("Соединение с PostgreSQL закрыто")

try:
    connection = psycopg2.connect(
        dbname=DBNAME, user=USER, password=PASSWORD, host=HOST, port=PORT
    )
    print("\nСоединение с базой данных в PostgreSQL открыто")
    cursor = connection.cursor()

    # Запрос для создания таблицы
    sql_create_table = '''CREATE TABLE TEST(
       NUM VARCHAR(255),
       ORD_NUM VARCHAR(255),
       COST_USD VARCHAR(255),
       DATE_P VARCHAR(255),
       COST_RUB VARCHAR(255)
    )'''
    cursor.execute(sql_create_table)
    connection.commit()
    print("Таблица успешно создана!")
    fill_table(cursor, data_from_sheet)
    print("Таблица успешно заполнена!")
except (Exception, Error) as error:
    print("Ошибка при работе с PostgreSQL", error)
finally:
    if connection:
        cursor.close()
        connection.close()
        print("Соединение с базой данных в PostgreSQL закрыто")


    try:
        connection = psycopg2.connect(
            dbname=DBNAME, user=USER, password=PASSWORD, host=HOST, port=PORT
        )
        print("\nСоединение с таблицей PostgreSQL открыто")
        cursor = connection.cursor()

        result = service.get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME).execute()
        data_from_sheet = result.get('values', [])
        last_data = data_from_sheet
        # Цикл обновления данных
        while True:
            time.sleep(5)
            result = service.get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME).execute()
            data_from_sheet = result.get('values', [])
            if last_data != data_from_sheet:
                last_data = data_from_sheet
                # Запрос для удаления записей
                sql_delete_all = '''DELETE FROM TEST'''
                cursor.execute(sql_delete_all)
                connection.commit()
                # Заполнение таблицы новыми данными
                fill_table(cursor, data_from_sheet)
                print("Данные успешно обновлены!")

    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL", error)
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("Соединение с таблицей PostgreSQL закрыто")

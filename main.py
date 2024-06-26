import telebot
import datetime
import sqlite3
import re

class DataBase:
    def __init__(self, db_name):
        self.db_name = db_name
        self.__create_table()

    def __create_table(self):
        sql = self.connect_db()
        sql["cursor"].execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER          PRIMARY KEY AUTOINCREMENT,
                id_telegram         INTEGER NOT NULL UNIQUE,
                username            TEXT,
                first_name          TEXT,
                last_name           TEXT,
                date_registration   DATE, 
                access              BOOLEAN DEFAULT 1        
            )
        ''')
        sql["cursor"].execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER      PRIMARY KEY AUTOINCREMENT,
                id_user         INTEGER NOT NULL,
                message_id      INTEGER NOT NULL,
                message_text    TEXT NOT NULL,
                date_send       DATE,                 
                status          BOOLEAN DEFAULT 0 CHECK(status IN (0, 1)),
                FOREIGN KEY (id_user) REFERENCES users(id)
            )
        ''')
        self.close(sql['cursor'], sql['connect'])

    def connect_db(self):
        with sqlite3.connect(self.db_name) as connect:
            cursor = connect.cursor()
        return {'connect': connect, 'cursor': cursor}

    def check_user(self, user_id):
        sql = self.connect_db()
        sql['cursor'].execute('''
            SELECT * FROM users WHERE id_telegram = ?
        ''', (user_id, ))

        info_users = sql['cursor'].fetchone()
        self.close(sql['cursor'], sql['connect'])

        if info_users is None:
            return {
                'status': False
            }
        return {
            'status': True,
            'info_users': info_users
        }

    def create_user(self, message: dict):
        sql = self.connect_db()
        date = datetime.datetime.now().strftime('%Y-%m-%d')
        sql['cursor'].execute('''
            INSERT INTO users (
                id_telegram, username, first_name, last_name, date_registration
            ) VALUES (?, ?, ?, ?, ?)
        ''', (
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name,
            message.from_user.last_name,
            date

        ))
        sql['connect'].commit()
        self.close(sql['cursor'], sql['connect'])

    def insert_message(self, message: dict):          
        date = datetime.datetime.now().strftime('%Y-%m-%d')

        info_user = self.check_user(message.from_user.id)
        if not info_user['status']:
            self.create_user(message)
            id_user = self.check_user(message.from_user.id)['info_users'][0]
        else:
            id_user = self.check_user(message.from_user.id)['info_users'][0]
        sql = self.connect_db()

        sql['cursor'].execute('''
            INSERT INTO messages (
                id_user, message_id, message_text, date_send
            ) VALUES (?, ?, ?, ?)
        ''', (
            id_user, message.message_id, message.text, date
        ))
        sql['connect'].commit()

        id_message = sql['cursor'].lastrowid

        self.close(sql['cursor'], sql['connect'])

        return id_message
    
    def check_application(self, id_application: int):
        sql = self.connect_db()
        sql['cursor'].execute('''
            SELECT message_id from messages WHERE id = ?
        ''', (id_application, ))

        data_message = sql['cursor'].fetchone()
        self.close(sql['cursor'], sql['connect'])

        return data_message
    
    def close(self, cursor, connect):
        cursor.close()
        connect.close()


class TelegramBot(DataBase):
    def __init__(self, db_name, token):
        super().__init__(db_name)
        self.bot = telebot.TeleBot(token)
        self.admin_chat_id = -4229502991
        self.router()

    def router(self):

        @self.bot.message_handler(commands=['start'])
        def start(message):
            text = ''
            if self.check_user(message.from_user.id)['status']:
                text += 'С возвращением'
            else:
                self.create_user(message)
                text += f'Добро пожаловать, {message.from_user.first_name}!'

            self.bot.send_message(
                message.chat.id,
                text
            )

        @self.bot.message_handler(func=lambda message: True)
        def echo_all(message):
            if message.chat.id != self.admin_chat_id:
                id_message = self.insert_message(message)
                self.bot.reply_to(
                    message,
                    'Сообщение отправлено админу'
                )            
                text = f'''
Номер заявки №{id_message}
id пользователя {message.from_user.id}
Сообщение: {message.text}
                '''                
                self.bot.send_message(self.admin_chat_id, text)    

            elif message.chat.id == self.admin_chat_id and message.reply_to_message != None:
                reply_message = str(message.reply_to_message.text)
                
                id_application = re.search(
                    r'Номер заявки №(\d+)', reply_message).group(1)
                id_user = re.search(
                    r'id пользователя (\d+)', reply_message).group(1)               

                id_messare_user = self.check_application(id_application)                

                self.bot.send_message(
                    id_user,
                    f"Ответ от администратора: {id_messare_user}",                    
                    reply_to_message_id=id_messare_user[0]                    
                )

                
        self.bot.polling()

TelegramBot(
    db_name='tg.db',
    token='6822316148:AAGwWNs-BaX40hr-kEP7aTjUw0uG3VL8uP0'
)
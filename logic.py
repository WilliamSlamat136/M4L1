import sqlite3
from datetime import datetime
from config import DATABASE 
import os
import cv2
import numpy as np
import os
from logic import *
from math import sqrt, ceil, floor

class DatabaseManager:
    def __init__(self, database):
        self.database = database

    def create_tables(self):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_score INTEGER, 
                user_id INTEGER PRIMARY KEY,
                user_name TEXT
            )
        ''')

            conn.execute('''
            CREATE TABLE IF NOT EXISTS prizes (
                prize_id INTEGER PRIMARY KEY,
                image TEXT,
                used INTEGER DEFAULT 0
            )
        ''')

            conn.execute('''
            CREATE TABLE IF NOT EXISTS winners (
                user_id INTEGER,
                prize_id INTEGER,
                win_time TEXT,
                FOREIGN KEY(user_id) REFERENCES users(user_id),
                FOREIGN KEY(prize_id) REFERENCES prizes(prize_id)
            )
        ''')

            conn.commit()

    def add_user(self, user_score, user_id, user_name):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('INSERT OR IGNORE INTO users VALUES (?, ?, ?)', (user_score, user_id, user_name))
            conn.commit()

    def add_prize(self, data):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.executemany('''INSERT INTO prizes (image) VALUES (?)''', data)
            conn.execute('UPDATE users SET user_score = user_score + ABS(RANDOM()) % 4 + 2 WHERE user_id = users.user_id')
            conn.commit()

    def add_winner(self, user_id, prize_id):
        win_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor() 
            cur.execute("SELECT * FROM winners WHERE user_id = ? AND prize_id = ?", (user_id, prize_id))
            if cur.fetchall():
                return 0
            else:
                conn.execute('''INSERT INTO winners (user_id, prize_id, win_time) VALUES (?, ?, ?)''', (user_id, prize_id, win_time))
                conn.commit()
                return 1

  
    def mark_prize_used(self, prize_id):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('''UPDATE prizes SET used = 1 WHERE prize_id = ?''', (prize_id,))
            conn.commit()


    def get_users(self):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor() 
            cur.execute("SELECT * FROM users")
            return [x[1] for x in cur.fetchall()] 
        
    def get_prize_img(self, prize_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor() 
            cur.execute("SELECT image FROM prizes WHERE prize_id = ?", (prize_id,))
            return cur.fetchall()[0][0]
        
    def get_random_prize(self):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor() 
            cur.execute("SELECT * FROM prizes WHERE used = 0 ORDER BY RANDOM()")
            return cur.fetchall()[0]
        
    def get_winners_count(self, prize_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute('SELECT COUNT(*) FROM winners WHERE prize_id = ?', (prize_id, ))
            return cur.fetchall()[0][0]
       
    def get_rating(self):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute('''
    SELECT user_score, user_name, COUNT(*) AS total FROM users
                            INNER JOIN winners 
                            ON users.user_id = winners.user_id 
                            GROUP BY users.user_id
                            ORDER BY total DESC
                            LIMIT 10
    ''')
            return cur.fetchall()
        
    def get_winners_img(self, user_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute(''' 
        SELECT image FROM winners 
        INNER JOIN prizes ON 
        winners.prize_id = prizes.prize_id
        WHERE user_id = ?''', (user_id, ))
            return cur.fetchall()
    
def create_collage(image_paths, thumb_size=(300, 300)):
    images = []

    for path in image_paths:
        img = cv2.imread(path)
        if img is None:
            continue
        img = cv2.resize(img, thumb_size)
        images.append(img)

    if not images:
        return None

    num_images = len(images)
    num_cols = ceil(sqrt(num_images))
    num_rows = ceil(num_images / num_cols)

    h, w, _ = images[0].shape
    collage = np.zeros((num_rows * h, num_cols * w, 3), dtype=np.uint8)

    for i, image in enumerate(images):
        row = i // num_cols
        col = i % num_cols
        collage[row*h:(row+1)*h, col*w:(col+1)*w] = image

    return collage


m = DatabaseManager(DATABASE)
info = m.get_winners_img("user_id")
prizes = [x[0] for x in info]
image_paths = os.listdir('img')
image_paths = [f'img/{x}' if x in prizes else f'hidden_img/{x}' for x in image_paths]
collage = create_collage(image_paths)

cv2.imshow('Collage', collage)
cv2.waitKey(0)
cv2.destroyAllWindows()
    
  
def hide_img(img_name):
    image = cv2.imread(f'img/{img_name}')
    blurred_image = cv2.GaussianBlur(image, (15, 15), 0)
    pixelated_image = cv2.resize(blurred_image, (30, 30), interpolation=cv2.INTER_NEAREST)
    pixelated_image = cv2.resize(pixelated_image, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_NEAREST)
    cv2.imwrite(f'hidden_img/{img_name}', pixelated_image)

if __name__ == '__main__':
    manager = DatabaseManager(DATABASE)
    manager.create_tables()
    prizes_img = os.listdir('img')
    data = [(x,) for x in prizes_img]
    manager.add_prize(data)
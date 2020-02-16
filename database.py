import sqlite3

conn = sqlite3.connect("settings.db")
cursor = conn.cursor()


def close():
    cursor.close()
    conn.close()


class Settings:
    def __init__(self):
        cursor.execute("""
            SELECT * FROM settings;
        """)
        settings = cursor.fetchall()[0]

        self.speed = settings[1]
        self.size = settings[2]
        self.time = settings[3]

    def update(self, speed=None, size=None, time=None):
        if speed is None:
            speed = self.speed
        if size is None:
            size = self.size
        if time is None:
            time = self.time

        cursor.execute("""
            UPDATE settings
            SET speed = ?, size = ?, time = ?
            WHERE id = ?
        """, (speed, size, time, 1))
        conn.commit()

        self.speed = speed
        self.size = size
        self.time = time

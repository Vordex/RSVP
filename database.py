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
        self.language = settings[4]

    def update(self, speed=None, size=None, time=None, language=None):
        if speed is None:
            speed = self.speed
        if size is None:
            size = self.size
        if time is None:
            time = self.time
        if language is None:
            language = self.language

        cursor.execute("""
            UPDATE settings
            SET speed = ?, size = ?, time = ?, language = ?
            WHERE id = ?
        """, (speed, size, time, language, 1))
        conn.commit()

        self.speed = speed
        self.size = size
        self.time = time
        self.language = language

import sqlite3


class Database:
    def __init__(self):
        try:
            self.__conn = sqlite3.connect('database/bot.db')
        except sqlite3.Error as e:
            print(f"Error connecting to sqlite3: {e}")
            raise e

        with self.__conn.cursor() as cursor:
            cursor.execute(
                """
                    CREATE TABLE IF NOT EXISTS preferences(
                        preference_name TEXT PRIMARY KEY,
                        preference_description TEXT                
                    );
                    
                    CREATE TABLE IF NOT EXISTS tg_users(
                        tg_user_id INT PRIMARY KEY,
                        ui_language TEXT CHECK(ui_language IN ('English', 'Русский')) DEFAULT 'Русский',
                        day_of_feed INT DEFAULT 0,
                        current_layout_id INT DEFAULT 10,
                        looking_at_content TEXT REFERENCES preferences(preference_name)
                    );
                    
                    CREATE TABLE IF NOT EXISTS content(
                        content_id INT PRIMARY KEY AUTOINCREMENT,
                        preference TEXT REFERENCES preferences(preference_name) NOT NULL,
                        type TEXT CHECK(type IN ('image', 'video', 'link')) NOT NULL,
                        day INT NOT NULL,
                        content TEXT UNIQUE NOT NULL
                    );
                    
                    CREATE TABLE IF NOT EXISTS likes(
                        tg_user_id INT REFERENCES tg_users(tg_user_id),
                        content_id INT REFERENCES content(content_id),
                        PRIMARY KEY (tg_user_id, content_id)
                    );
                    
                    CREATE TABLE IF NOT EXISTS user_preferences(
                        tg_user_id INT REFERENCES tg_users(tg_user_id),
                        content_type TEXT REFERENCES preferences(preference_name),
                        PRIMARY KEY (tg_user_id, content_type)
                    );
                """
            )

    def close(self) -> None:
        self.__conn.close()

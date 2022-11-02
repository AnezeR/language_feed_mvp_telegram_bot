import sqlite3
from strenum import StrEnum
import os


class ValTypes(StrEnum):
    image = 'image'
    video = 'video'
    link = 'link'


class Language(StrEnum):
    english = 'English',
    russian = 'Русский'


# todo: try making working wrappers because this looks poorly


class Database:
    def __init__(self):
        try:
            self.__dir = os.path.dirname(__file__)
            self.__conn = sqlite3.connect(f'{self.__dir}/database.sqlite', check_same_thread=False)
        except sqlite3.Error as e:
            print(f"Error connecting to sqlite3: {e}")
            raise e

    def close(self) -> None:
        self.__conn.close()

    def execute_init_script(self) -> None:
        cursor = self.__conn.cursor()
        cursor.executescript(open(f'{self.__dir}/init.sql').read())
        self.__conn.commit()
        cursor.close()

    """Preferences section"""

    def preference_add_preference(self, preference_name: str, preference_description: str) -> None:
        cursor = self.__conn.cursor()
        cursor.execute("INSERT INTO preferences (preference_name, preference_description) VALUES (?, ?)", (preference_name, preference_description))
        self.__conn.commit()
        cursor.close()

    def preference_get_all_preferences(self) -> list[str]:
        cursor = self.__conn.cursor()
        cursor.execute("SELECT preference_name FROM preferences;")
        result = [content[0] for content in cursor.fetchall()]
        cursor.close()
        return result

    def preference_get_content_for_day(self, preference_name: str, day: int) -> list[int]:
        cursor = self.__conn.cursor()
        cursor.execute("SELECT content_id FROM content WHERE day = ? AND preference = ?", (day, preference_name))
        result = [content[0] for content in cursor.fetchall()]
        cursor.close()
        return result

    def preference_get_description(self, preference_name: str) -> str:
        cursor = self.__conn.cursor()
        cursor.execute("SELECT preference_description FROM preferences WHERE preference_name = ?", (preference_name,))
        result = cursor.fetchone()[0]
        cursor.close()
        return result

    """Content section"""

    def content_add_content(self, preference_name: str, content: str, val_type: str, day: int) -> None:
        cursor = self.__conn.cursor()
        cursor.execute("INSERT INTO content (preference, type, day, content) VALUES (?, ?, ?, ?)", (preference_name, val_type, day, content))
        self.__conn.commit()
        cursor.close()

    def content_get_ids_to_preload(self) -> list[int]:
        cursor = self.__conn.cursor()
        cursor.execute("SELECT content_id FROM content WHERE type IN('video', 'image')")
        result = [content[0] for content in cursor.fetchall()]
        cursor.close()
        return result

    def content_set_file_id(self, content_id: int, file_id: str) -> None:
        cursor = self.__conn.cursor()
        cursor.execute("UPDATE content SET file_id = ? WHERE content_id = ?", (file_id, content_id))
        self.__conn.commit()
        cursor.close()

    def content_get_file_id(self, content_id: int) -> str:
        cursor = self.__conn.cursor()
        cursor.execute("SELECT file_id FROM content WHERE content_id = ?", (content_id,))
        result = cursor.fetchone()[0]
        cursor.close()
        return result

    def content_get_preference_name(self, content_id: int) -> str:
        cursor = self.__conn.cursor()
        cursor.execute("SELECT preference FROM content WHERE content_id = ?", (content_id,))
        result = cursor.fetchone()[0]
        cursor.close()
        return result

    def content_get_val_type(self, content_id: int) -> str:
        cursor = self.__conn.cursor()
        cursor.execute("SELECT type FROM content WHERE content_id = ?", (content_id,))
        result = cursor.fetchone()[0]
        cursor.close()
        return result

    def content_get_content(self, content_id: int) -> str:
        cursor = self.__conn.cursor()
        cursor.execute("SELECT content FROM content WHERE content_id = ?", (content_id,))
        result = cursor.fetchone()[0]
        cursor.close()
        return result

    """User section"""

    def user_get_all_users(self) -> list[int]:
        cursor = self.__conn.cursor()
        cursor.execute("SELECT tg_user_id FROM tg_users WHERE day_of_feed <> 0 and day_of_feed <> 8")
        result = [content[0] for content in cursor.fetchall()]
        cursor.close()
        return result

    def user_exists(self, tg_user_id: int) -> bool:
        cursor = self.__conn.cursor()
        cursor.execute("SELECT tg_user_id FROM tg_users WHERE tg_user_id = ?", (tg_user_id,))
        result = bool(len(cursor.fetchall()))
        cursor.close()
        return result

    def user_create(self, tg_user_id: int) -> None:
        cursor = self.__conn.cursor()
        cursor.execute("INSERT INTO tg_users (tg_user_id) VALUES (?)", (tg_user_id,))
        self.__conn.commit()
        cursor.close()

    def user_get_day_of_feed(self, tg_user_id: int) -> int:
        cursor = self.__conn.cursor()
        cursor.execute("SELECT day_of_feed FROM tg_users WHERE tg_user_id = ?", (tg_user_id,))
        result = cursor.fetchone()[0]
        cursor.close()
        return result

    def user_increase_day_of_feed(self, tg_user_id: int) -> None:
        cursor = self.__conn.cursor()
        cursor.execute("UPDATE tg_users SET day_of_feed = day_of_feed + 1 WHERE tg_user_id = ?", (tg_user_id,))
        self.__conn.commit()
        cursor.close()

    def user_set_looking_at_preference(self, tg_user_id: int, preference: str | None) -> None:
        cursor = self.__conn.cursor()
        cursor.execute("UPDATE tg_users SET looking_at_preference = ? WHERE tg_user_id = ?", (preference, tg_user_id))
        self.__conn.commit()
        cursor.close()

    def user_get_looking_at_preference(self, tg_user_id: int) -> str:
        cursor = self.__conn.cursor()
        cursor.execute("SELECT looking_at_preference FROM tg_users WHERE tg_user_id = ?", (tg_user_id,))
        result = cursor.fetchone()[0]
        cursor.close()
        return result

    def user_set_language(self, tg_user_id: int, language: str) -> None:
        cursor = self.__conn.cursor()
        cursor.execute("UPDATE tg_users SET ui_language = ? WHERE tg_user_id = ?", (language, tg_user_id))
        self.__conn.commit()
        cursor.close()

    def user_get_language(self, tg_user_id: int) -> str:
        cursor = self.__conn.cursor()
        cursor.execute("SELECT ui_language FROM tg_users WHERE tg_user_id = ?", (tg_user_id,))
        result = cursor.fetchone()[0]
        cursor.close()
        return result

    def user_set_layout(self, tg_user_id: int, layout_id: int) -> None:
        cursor = self.__conn.cursor()
        cursor.execute("UPDATE tg_users SET current_layout_id = ? WHERE tg_user_id = ?", (layout_id, tg_user_id))
        self.__conn.commit()
        cursor.close()

    def user_get_layout(self, tg_user_id: int) -> int:
        cursor = self.__conn.cursor()
        cursor.execute("SELECT current_layout_id FROM tg_users WHERE tg_user_id = ?", (tg_user_id,))
        result = cursor.fetchone()[0]
        cursor.close()
        return result

    """Setting preferences section"""

    def user_preferences_are_set(self, tg_user_id: int) -> bool:
        cursor = self.__conn.cursor()
        cursor.execute("SELECT tg_user_id FROM user_preferences WHERE tg_user_id = ?", (tg_user_id,))
        result = bool(len(cursor.fetchall()))
        cursor.close()
        return result

    def user_preference_is_liked(self, tg_user_id: int, preference_name: str) -> bool:
        cursor = self.__conn.cursor()
        cursor.execute("SELECT tg_user_id FROM user_preferences WHERE (tg_user_id, preference_name) = (?, ?)", (tg_user_id, preference_name))
        result = bool(len(cursor.fetchall()))
        cursor.close()
        return result

    def user_preference_add_like(self, tg_user_id: int, preference_name: str) -> None:
        cursor = self.__conn.cursor()
        cursor.execute("INSERT INTO user_preferences (tg_user_id, preference_name) VALUES (?, ?)", (tg_user_id, preference_name))
        self.__conn.commit()
        cursor.close()

    def user_preference_remove_like(self, tg_user_id: int, preference_name: str) -> None:
        cursor = self.__conn.cursor()
        cursor.execute("DELETE FROM user_preferences WHERE (tg_user_id, preference_name) = (?, ?)", (tg_user_id, preference_name))
        self.__conn.commit()
        cursor.close()

    """Likes section"""

    def user_content_is_liked(self, tg_user_id: int, content_id: int) -> bool:
        cursor = self.__conn.cursor()
        cursor.execute("SELECT tg_user_id FROM likes WHERE (tg_user_id, content_id) = (?, ?)", (tg_user_id, content_id))
        result = bool(len(cursor.fetchall()))
        cursor.close()
        return result

    def user_content_add_like(self, tg_user_id: int, content_id: int) -> None:
        cursor = self.__conn.cursor()
        cursor.execute("INSERT INTO likes (tg_user_id, content_id, like_date) VALUES (?, ?, CURRENT_TIMESTAMP)", (tg_user_id, content_id))
        self.__conn.commit()
        cursor.close()

    def user_content_remove_like(self, tg_user_id: int, content_id: int) -> None:
        cursor = self.__conn.cursor()
        cursor.execute("DELETE FROM likes WHERE (tg_user_id, content_id) = (?, ?)", (tg_user_id, content_id))
        self.__conn.commit()
        cursor.close()

    """Likes page section"""

    def user_likes_get_current_page(self, tg_user_id: int) -> int:
        cursor = self.__conn.cursor()
        cursor.execute("SELECT current_likes_page FROM tg_users WHERE tg_user_id = ?", (tg_user_id,))
        result = cursor.fetchone()[0]
        cursor.close()
        return result

    def user_likes_set_current_page(self, tg_user_id: int, page: int) -> None:
        cursor = self.__conn.cursor()
        cursor.execute("UPDATE tg_users SET current_likes_page = ? WHERE tg_user_id = ?", (page, tg_user_id))
        self.__conn.commit()
        cursor.close()

    def user_likes_buffer(self, tg_user_id: int) -> None:
        cursor = self.__conn.cursor()
        cursor.execute("INSERT INTO buffered_likes SELECT * FROM likes WHERE tg_user_id = ?", (tg_user_id,))
        self.__conn.commit()
        cursor.close()

    def user_likes_delete_buffer(self, tg_user_id: int) -> None:
        cursor = self.__conn.cursor()
        cursor.execute("DELETE FROM buffered_likes WHERE tg_user_id = ?", (tg_user_id,))
        self.__conn.commit()
        cursor.close()

    def user_likes_get_buffered_likes_count(self, tg_user_id: int) -> int:
        cursor = self.__conn.cursor()
        cursor.execute("SELECT tg_user_id FROM buffered_likes WHERE tg_user_id = ?", (tg_user_id,))
        result = len(cursor.fetchall())
        cursor.close()
        return result

    def user_likes_get_content_for_current_page(self, tg_user_id: int) -> list[int]:
        cursor = self.__conn.cursor()
        current_page = self.user_likes_get_current_page(tg_user_id)
        cursor.execute(
            """
            SELECT content_id FROM buffered_likes
            WHERE tg_user_id = ?
            ORDER BY like_date DESC
            LIMIT 3 OFFSET ?
            """,
            (tg_user_id, current_page * 3)
        )
        result = [content[0] for content in cursor.fetchall()]
        cursor.close()
        return result

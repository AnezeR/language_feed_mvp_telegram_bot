import mariadb
from strenum import StrEnum


class ContentType(StrEnum):
    image = 'image'
    video = 'video'
    link = 'link'


class Language(StrEnum):
    english = 'English',
    russian = 'Русский'


class Database:

    def __init__(self, user: str, password: str, database: str):
        try:
            self.__conn = mariadb.connect(
                user=user,
                password=password,
                host="localhost",
                port=3306,
                database=database
            )
            self.__conn.auto_reconnect = True

        except mariadb.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")
            raise e

    def close(self) -> None:
        self.__conn.close()

    def get_all_users(self) -> list[int]:
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT tg_user_id FROM tg_users WHERE day_of_feed <> 0 and day_of_feed <> 8")
            return [content[0] for content in cursor.fetchall()]

    def user_exists(self, tg_user_id: int) -> bool:
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT tg_user_id FROM tg_users WHERE tg_user_id = ?", (tg_user_id,))
            return bool(len(cursor.fetchall()))

    def create_user(self, tg_user_id: int, chat_id: int) -> None:
        with self.__conn.cursor() as cursor:
            cursor.execute("INSERT INTO tg_users (tg_user_id, chat_id) VALUES (?, ?)", (tg_user_id, chat_id))
            self.__conn.commit()

    def increase_feed_day_for_user(self, tg_user_id: int) -> None:
        with self.__conn.cursor() as cursor:
            cursor.execute("UPDATE tg_users SET day_of_feed = day_of_feed + 1 WHERE tg_user_id = ?", (tg_user_id,))
            self.__conn.commit()

    def get_language_for_user(self, tg_user_id: int) -> str:
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT ui_language FROM tg_users WHERE tg_user_id = ?", (tg_user_id,))
            return cursor.fetchone()[0]

    def set_user_looking_at_content_type(self, tg_user_id: int, content_type: str | None) -> None:
        with self.__conn.cursor() as cursor:
            cursor.execute("UPDATE tg_users SET looking_at_content = ? WHERE tg_user_id = ?", (content_type, tg_user_id))
            self.__conn.commit()

    def get_content_type_user_is_looking_at(self, tg_user_id: int) -> str:
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT looking_at_content FROM tg_users WHERE tg_user_id = ?", (tg_user_id,))
            return cursor.fetchone()[0]

    def set_language_for_user(self, tg_user_id: int, language: str) -> None:
        with self.__conn.cursor() as cursor:
            cursor.execute("UPDATE tg_users SET ui_language = ? WHERE tg_user_id = ?", (language, tg_user_id))
            self.__conn.commit()

    def get_chat_id_for_user(self, tg_user_id):
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT chat_id FROM tg_users WHERE tg_user_id = ?", (tg_user_id,))
            return cursor.fetchone()[0]

    def get_user_layout(self, tg_user_id: int) -> int:
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT current_layout_id FROM tg_users WHERE tg_user_id = ?", (tg_user_id,))
            return cursor.fetchone()[0]

    def set_user_layout(self, tg_user_id: int, layout_id: int) -> None:
        with self.__conn.cursor() as cursor:
            cursor.execute("UPDATE tg_users SET current_layout_id = ? WHERE tg_user_id = ?", (layout_id, tg_user_id))
            self.__conn.commit()

    def get_content_for_user(self, tg_user_id: int) -> list[int]:
        with self.__conn.cursor() as cursor:
            cursor.execute(
                "SELECT content_id FROM content "
                "WHERE content_id IN ("
                "    SELECT content_id FROM type_content_days "
                "    WHERE content_type IN ("
                "        SELECT content_type FROM content_preferences WHERE tg_user_id = ?"
                "    ) AND day_of_feed = ("
                "        SELECT day_of_feed FROM tg_users WHERE tg_user_id = ?"
                "    )"
                ")",
                (tg_user_id, tg_user_id)
            )
            return [content[0] for content in cursor.fetchall()]

    def get_likes_for_user(self, tg_user_id: int) -> list[int]:
        with self.__conn.cursor() as cursor:
            cursor.execute(
                "SELECT content_id FROM content "
                "WHERE content_id IN (SELECT content_id FROM likes WHERE tg_user_id = ?)",
                (tg_user_id,)
            )
            return [content[0] for content in cursor.fetchall()]

    def is_content_liked_by_user(self, tg_user_id: int, content_id: int) -> bool:
        with self.__conn.cursor() as cursor:
            cursor.execute(
                "SELECT tg_user_id FROM likes WHERE (tg_user_id, content_id) = (?, ?)",
                (tg_user_id, content_id)
            )
            return bool(len(cursor.fetchall()))

    def set_like_for_user(self, tg_user_id: int, content_id: int) -> None:
        with self.__conn.cursor() as cursor:
            cursor.execute("INSERT INTO likes (tg_user_id, content_id) VALUES (?, ?)", (tg_user_id, content_id))
            self.__conn.commit()

    def remove_like_for_user(self, tg_user_id: int, content_id: int) -> None:
        with self.__conn.cursor() as cursor:
            cursor.execute("DELETE FROM likes WHERE (tg_user_id, content_id) = (?, ?)", (tg_user_id, content_id))
            self.__conn.commit()

    def get_content_types(self) -> list[str]:
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT type FROM content_types;")
            return [content[0] for content in cursor.fetchall()]

    def get_description_for_content_type(self, content_type: str) -> str:
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT content_type_description FROM content_types WHERE type = ?", (content_type,))
            return cursor.fetchone()[0]

    def get_content_ids_to_preload(self) -> list[int]:
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT content_id FROM content WHERE type IN('video', 'image');")
            return [content[0] for content in cursor.fetchall()]

    def get_test_content_for_content_type(self, content_type: str) -> list[int]:
        with self.__conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT content_id FROM content
                WHERE content_id IN (
                    SELECT content_id FROM type_content_days
                    WHERE content_type = ? AND day_of_feed = 0
                )
                """,
                (content_type,)
            )
            return [content[0] for content in cursor.fetchall()]

    def are_preferences_not_set(self, tg_user_id: int) -> bool:
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT day_of_feed FROM tg_users WHERE tg_user_id = ?", (tg_user_id,))
            return cursor.fetchone()[0] == 0

    def are_there_zero_preferences(self, tg_user_id: int) -> bool:
        with self.__conn.cursor() as cursor:
            cursor.execute(
                "SELECT tg_user_id FROM content_preferences WHERE (tg_user_id) = (?)",
                (tg_user_id,)
            )
            return not bool(len(cursor.fetchall()))

    def end_setting_preferences_and_set_first_day(self, tg_user_id: int) -> None:
        with self.__conn.cursor() as cursor:
            cursor.execute(
                "UPDATE tg_users SET day_of_feed = 1 WHERE tg_user_id = ?",
                (tg_user_id,)
            )
            self.__conn.commit()

    def get_setting_preferences_content(self) -> list[int]:
        with self.__conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT content_id
                FROM content WHERE content_id IN (
                    SELECT content_id FROM type_content_days
                    WHERE content_type IN (SELECT type FROM content_types) AND day_of_feed = 0
                );
                """
            )
            return [content[0] for content in cursor.fetchall()]

    def get_content_types_for_content(self, content_id: int) -> list[str]:
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT content_type FROM type_content_days WHERE content_id = ?", (content_id,))
            return [content[0] for content in cursor.fetchall()]

    def is_content_type_liked_by_user(self, tg_user_id: int, content_type: str) -> bool:
        with self.__conn.cursor() as cursor:
            cursor.execute(
                "SELECT tg_user_id FROM content_preferences WHERE (tg_user_id, content_type) = (?, ?)",
                (tg_user_id, content_type)
            )
            return bool(len(cursor.fetchall()))

    def like_a_content_type_for_user(self, tg_user_id: int, content_type: str) -> None:
        with self.__conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO content_preferences (tg_user_id, content_type) VALUES (?, ?)",
                (tg_user_id, content_type)
            )
            self.__conn.commit()

    def remove_like_a_content_type_for_user(self, tg_user_id: int, content_type: str) -> None:
        with self.__conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM content_preferences WHERE (tg_user_id, content_type) = (?, ?)",
                (tg_user_id, content_type)
            )
            self.__conn.commit()

    def add_content_type(self, content_type: str, content_type_description: str) -> None:
        with self.__conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO content_types (type, content_type_description) VALUES (?, ?)",
                (content_type, content_type_description)
            )
            self.__conn.commit()

    def get_value_type_of_content(self, content_id: int) -> str:
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT type FROM content WHERE content_id = ?", (content_id,))
            return cursor.fetchone()[0]

    def get_content_content(self, content_id: int) -> str:
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT content FROM content WHERE content_id = ?", (content_id,))
            return cursor.fetchone()[0]

    def delete_content_type(self, content_type: str) -> None:
        with self.__conn.cursor() as cursor:
            cursor.execute("DELETE FROM content_types WHERE type = ?", (content_type,))
            self.__conn.commit()

    def add_content(self, content_type: str, content: str, val_type: str, day: int) -> None:
        with self.__conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO content (type, content) VALUES (?, ?)",
                (val_type, content)
            )
            cursor.execute(
                "INSERT INTO type_content_days (content_type, day_of_feed, content_id)"
                "VALUES (?, ?, (SELECT content_id FROM content WHERE content = ?))",
                (content_type, day, content)
            )
            self.__conn.commit()

    def remove_content(self, content_id: int) -> None:
        with self.__conn.cursor() as cursor:
            cursor.execute("DELETE FROM type_content_days WHERE content_id = ?", (content_id,))
            cursor.execute("DELETE FROM content WHERE content_id = ?", (content_id,))
            self.__conn.commit()

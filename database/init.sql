CREATE TABLE preferences(
    preference_name TEXT PRIMARY KEY,
    preference_description TEXT
);

CREATE TABLE tg_users(
    tg_user_id INTEGER PRIMARY KEY,
    ui_language TEXT CHECK(ui_language IN ('English', 'Русский')) DEFAULT 'Русский',
    day_of_feed INTEGER DEFAULT 0,
    current_layout_id INTEGER DEFAULT 10,
    current_likes_page INTEGER DEFAULT 0,
    looking_at_preference TEXT REFERENCES preferences(preference_name)
);

CREATE TABLE content(
    content_id INTEGER PRIMARY KEY AUTOINCREMENT,
    preference TEXT REFERENCES preferences(preference_name) NOT NULL,
    type TEXT CHECK(type IN ('image', 'video', 'link')) NOT NULL,
    day INTEGER NOT NULL,
    content TEXT UNIQUE NOT NULL,
    file_id TEXT
);

CREATE TABLE likes(
    tg_user_id INTEGER REFERENCES tg_users(tg_user_id),
    content_id INTEGER REFERENCES content(content_id),
    like_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (tg_user_id, content_id)
);

CREATE TABLE buffered_likes(
    tg_user_id INTEGER REFERENCES tg_users(tg_user_id),
    content_id INTEGER REFERENCES content(content_id),
    like_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (tg_user_id, content_id)
);

CREATE TABLE user_preferences(
    tg_user_id INTEGER REFERENCES tg_users(tg_user_id),
    preference_name TEXT REFERENCES preferences(preference_name),
    PRIMARY KEY (tg_user_id, preference_name)
);
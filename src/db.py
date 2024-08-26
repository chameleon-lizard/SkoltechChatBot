import psycopg2


class BotDB:
    """
    A class to interact with a PostgreSQL database for a Telegram bot.
    """

    def __init__(
        self,
        db_name,
        db_user,
        db_password,
        host,
        port,
        bot_id,
        bot_username,
        bot_email=None,
    ):
        """
        Initializes a new instance of the TelegramBotDatabase class.

        Args:
            db_name (str): The name of the PostgreSQL database.
            db_user (str): The username to use for the database connection.
            db_password (str): The password to use for the database connection.
            host (str): The host to use for the database connection.
            port (int): The port to use for the database connection.
            bot_id (int): The ID of the Telegram bot.
            bot_username (str): The username of the Telegram bot.
            bot_email (str, optional): The email address of the Telegram bot. Defaults to None.

        Returns:
            None
        """
        self.conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=host,
            port=port,
        )
        self.cursor = self.conn.cursor()

        self.drop_schema()

        self.create_schema()

        self.add_user(bot_id, bot_username)
        self.cursor.execute(
            "UPDATE users SET role = 'bot', email = %s WHERE telegram_id = %s",
            (bot_email, bot_id),
        )
        self.conn.commit()

    def create_schema(self):
        """
        Creates the database schema if it does not already exist.

        The schema includes two tables: users and messages. The users table
        stores information about each user, including their Telegram ID,
        username, role, and email. The messages table stores information about
        each message, including the user who sent it, the text of the message,
        and the date and time it was sent.

        Args:
            None

        Returns:
            None
        """
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id BIGINT PRIMARY KEY,
                telegram_id BIGINT NOT NULL UNIQUE,
                username TEXT,
                role TEXT NOT NULL CHECK(role IN ('admin', 'user', 'unauthorized', 'moderator', 'bot', 'staff', 'waiting_for_code')),
                email TEXT DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
        )
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id BIGINT PRIMARY KEY,
                chat_id BIGINT NOT NULL,
                message_text TEXT NOT NULL,
                reply_to BIGINT,
                message_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chat_id) REFERENCES users (telegram_id)
            );
        """
        )
        self.conn.commit()

    def add_user(self, telegram_id, username=None):
        """
        Adds a new user to the database.

        Args:
            telegram_id (int): The Telegram ID of the user.
            username (str, optional): The username of the user. Defaults to None.

        Returns:
            None
        """
        self.cursor.execute(
            "INSERT INTO users (id, telegram_id, username, role) VALUES (%s, %s, %s, 'unauthorized')",
            (telegram_id, telegram_id, username),
        )
        self.conn.commit()

    def add_message(self, message_id, telegram_id, message_text, reply_to=None):
        """
        Adds a new message to the database.

        Args:
            message_id (int): The ID of the message.
            telegram_id (int): The Telegram ID of the user who sent the message.
            message_text (str): The text of the message.
            reply_to (int, optional): The ID of the message that this message is a reply to. Defaults to None.

        Returns:
            None
        """
        # Check if the user exists
        self.cursor.execute(
            "SELECT COUNT(*) FROM users WHERE telegram_id = %s", (telegram_id,)
        )
        user_exists = self.cursor.fetchone()[0]

        if not user_exists:
            # Add the user if they don't exist
            self.add_user(telegram_id)

        # Now insert the message
        self.cursor.execute(
            "INSERT INTO messages (id, chat_id, message_text, reply_to) VALUES (%s, %s, %s, %s)",
            (message_id, telegram_id, message_text, reply_to),
        )
        self.conn.commit()

    def get_last_n_messages(self, chat_id, n):
        """
        Retrieves the last n messages sent by a user.

        Args:
            chat_id (int): The ID of the user.
            n (int): The number of messages to retrieve.

        Returns:
            list: A list of tuples, where each tuple contains the text of a message and the date and time it was sent.
        """
        self.cursor.execute(
            "SELECT message_text FROM messages WHERE chat_id = %s ORDER BY message_date DESC LIMIT %s",
            (chat_id, n),
        )
        return self.cursor.fetchall()

    def authorize_user(self, telegram_id, email):
        """
        Authorizes a user by setting their role to 'user' and storing their email address.

        Args:
            telegram_id (int): The Telegram ID of the user.
            email (str): The email address of the user.

        Returns:
            None
        """
        self.cursor.execute(
            "UPDATE users SET role = 'user', email = %s WHERE telegram_id = %s",
            (email, telegram_id),
        )
        self.conn.commit()

    def get_user_role(self, telegram_id):
        """
        Retrieves the role of a user.

        Args:
            telegram_id (int): The Telegram ID of the user.

        Returns:
            str: The role of the user.
        """
        self.cursor.execute(
            "SELECT role FROM users WHERE telegram_id = %s", (telegram_id,)
        )
        return self.cursor.fetchone()[0]

    def list_all_users(self):
        """
        Retrieves a list of all users in the database.

        Args:
            None

        Returns:
            list: A list of tuples, where each tuple contains the Telegram ID, username, role, and email of a user.
        """
        self.cursor.execute("SELECT telegram_id, username, role, email FROM users")
        return self.cursor.fetchall()

    def close(self):
        """
        Closes the database connection.

        Args:
            None

        Returns:
            None
        """
        self.conn.close()

    def remove_user(self, telegram_id):
        """
        Removes a user from the database.

        Args:
            telegram_id (int): The Telegram ID of the user to remove.

        Returns:
            None
        """
        self.cursor.execute(
            "DELETE FROM messages WHERE chat_id IN (SELECT id FROM users WHERE telegram_id = %s)",
            (telegram_id,),
        )
        self.cursor.execute("DELETE FROM users WHERE telegram_id = %s", (telegram_id,))
        self.conn.commit()

    def drop_schema(self):
        """
        Drops the database schema.

        Args:
            None

        Returns:
            None
        """
        self.cursor.execute("DROP TABLE IF EXISTS messages")
        self.cursor.execute("DROP TABLE IF EXISTS users")
        self.conn.commit()


if __name__ == "__main__":
    db = BotDB(
        db_name="scbdb",
        db_user="scbuser",
        db_password="U2tvbHRlY2hQYXNzd29yZAo",
        host="localhost",
        port="5432",
        bot_id=123456789,
        bot_username="@CyberBorisBot",
        bot_email="my_bot@example.com",
    )
    db.drop_schema()

    db.create_schema()
    db.add_user(123, "test_user")
    db.cursor.execute("SELECT * FROM users WHERE telegram_id = 123")
    user = db.cursor.fetchone()
    assert user[1] == 123, user[1]
    assert user[2] == "test_user", user[2]
    assert user[3] == "unauthorized", user[3]
    db.drop_schema()

    db.create_schema()
    db.add_user(123, "test_user")
    db.add_message(1, 123, "Hello, world!")
    db.cursor.execute("SELECT * FROM messages WHERE id = 1")
    message = db.cursor.fetchone()
    assert message[1] == 123, message[1]
    assert message[2] == "Hello, world!", message[2]
    db.drop_schema()

    db.create_schema()
    db.add_user(123, "test_user")
    db.add_message(2, 123, "Hello, world")
    db.add_message(3, 123, "This is a test.")
    messages = db.get_last_n_messages(123, 2)
    assert len(messages) == 2, len(messages)
    assert messages[0][0] == "This is a test.", messages[0][0]
    assert messages[1][0] == "Hello, world", messages[1][0]
    db.drop_schema()

    db.create_schema()
    db.add_user(123, "test_user")
    db.authorize_user(123, "test@example.com")
    db.cursor.execute("SELECT * FROM users WHERE telegram_id = 123")
    user = db.cursor.fetchone()
    assert user[3] == "user", user[3]
    assert user[4] == "test@example.com", user[4]
    db.drop_schema()

    db.create_schema()
    db.add_user(123, "test_user")
    assert db.get_user_role(123) == "unauthorized", db.get_user_role(123)
    db.authorize_user(123, "test@example.com")
    assert db.get_user_role(123) == "user", db.get_user_role(123)
    db.drop_schema()

    db.create_schema()
    db.add_user(123, "test_user1")
    db.add_user(456, "test_user2")
    users = db.list_all_users()
    assert len(users) == 2, len(users)
    assert users[0][0] == 123, users[0][0]
    assert users[1][0] == 456, users[1][0]
    db.drop_schema()

    db.close()

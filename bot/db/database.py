import os

import psycopg2

def create_connection():
    try:
        connection = psycopg2.connect(
            dbname=os.environ.get("POSTGRES_NAME"),
            user=os.environ.get("POSTGRES_USER"),
            password=os.environ.get("POSTGRES_PASSWORD"),
            host=os.environ.get("POSTGRES_HOST"),
            port=int(os.environ.get("POSTGRES_PORT"))
        )
        return connection
    except psycopg2.Error as e:
        print(f"Error connecting to db: {e}")

def get_applicant_telegram(conn, user_id: int):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM accounts_applicantlinkedtelegram WHERE user_id=%s;", (user_id, ))
    applicant = cursor.fetchone()
    cursor.close()
    return applicant

def activate_applicant_linked_telegram(conn, user_id: int, chat_id: int):
    cursor = conn.cursor()
    query = """
        UPDATE accounts_applicantlinkedtelegram 
        SET chat_id = %s, is_active = True 
        WHERE user_id = %s;
    """
    cursor.execute(query, (chat_id, user_id))
    conn.commit()
    cursor.close()
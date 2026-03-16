import os

import psycopg
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the connection string from the environment variable
conn_string = os.getenv("DATABASE_URL")

def select_flashcard(chatid, title):
    try:
        with psycopg.connect(conn_string) as conn:
            print("Connection to neondb established")

            # Open a cursor to perform database operations
            with conn.cursor() as cur:
                
                cur.execute("SELECT chatid, card_title, flashcard, intervals FROM flashcards WHERE flashcards.chatid = (%s)::text AND flashcards.card_title = (%s)::text LIMIT 1;", 
                            (chatid, title))
                row = cur.fetchone()
                print("Selected 1 flashcard.")
                return row
                
    except Exception as e:
        print("Connection failed.")
        print(e)
        
def select_all_flashcards():
    try:
        with psycopg.connect(conn_string) as conn:
            print("Connection to neondb established")

            # Open a cursor to perform database operations
            with conn.cursor() as cur:
                
                cur.execute("SELECT chatid, card_title, flashcard, intervals FROM flashcards", 
                            )
                rows = cur.fetchall()
                print(f"Selected {len(rows)} flashcards.")
                return rows
                
    except Exception as e:
        print("Connection failed.")
        print(e)
        
        
# def update_lastrun(chatid, title):
#     try:
#         with psycopg.connect(conn_string) as conn:
#             print("Connection to neondb established")

#             # Open a cursor to perform database operations
#             with conn.cursor() as cur:
                
#                 cur.execute("UPDATE flashcards SET WHERE chatid = %s AND card_title = %s;", 
#                             (chatid, title))
#                 row = cur.fetchone()
#                 print("Selected 1 flashcard.")
#                 return row
                
#     except Exception as e:
#         print("Connection failed.")
#         print(e)
        
def insert_flashcard(chatid, title, content, intervals):
    try:
        with psycopg.connect(conn_string) as conn:
            print("Connection to neondb established")

            # Open a cursor to perform database operations
            with conn.cursor() as cur:

                # Insert a flashcard
                cur.execute(
                    "INSERT INTO flashcards (chatid, card_title, flashcard, intervals) VALUES (%s, %s, %s, %s);",
                    (chatid, title, content, intervals),
                )
                print("Inserted 1 flashcard.")
                
    except Exception as e:
        print("Connection failed.")
        print(e)
        
def delete_flashcard(chatid, title):
    try:
        with psycopg.connect(conn_string) as conn:
            print("Connection to neondb established")

            # Open a cursor to perform database operations
            with conn.cursor() as cur:

                cur.execute("DELETE FROM flashcards WHERE chatid = (%s)::text AND card_title = (%s)::text;", 
                            (chatid, title)
                            )
                print("Deleted 1 flashcard.")

    except Exception as e:
        print("Connection failed.")
        print(e)
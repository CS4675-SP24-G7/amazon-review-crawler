import sqlite3
from enum import Enum


class Status(Enum):
    PROCESSING = 1
    COMPLETED = 2
    FAILED = 3
    NOT_FOUND = 4


connection = sqlite3.connect("CRAWLER.db")

# create a table if not exists

cursor = connection.cursor()
cursor.execute(
    "CREATE TABLE IF NOT EXISTS status (ISBN text, status integer, lastest_update text, time_taken text, one_star integer, two_star integer, three_star integer, four_star integer, five_star integer, product_title text, PRIMARY KEY (ISBN))")
connection.commit()
cursor.close()


def Insert_Status(ISBN, lastest_update, time_taken, one_star, two_star, three_star, four_star, five_star, product_title, status=Status):
    """
    @params: ISBN, status, lastest_update, time_taken, one_star, two_star, three_star, four_star, five_star, product_title, data_path
    """
    cursor = connection.cursor()
    cursor.execute("INSERT OR REPLACE INTO status (ISBN, status, lastest_update, time_taken, one_star, two_star, three_star, four_star, five_star, product_title) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   (ISBN, status.value, lastest_update, time_taken, one_star, two_star, three_star, four_star, five_star, product_title))
    connection.commit()
    cursor.close()


def Get_Status(ISBN):
    """
    get status field from status table
    """
    cursor = connection.cursor()
    cursor.execute("SELECT status FROM status WHERE ISBN=?", (ISBN,))
    status = cursor.fetchone()
    cursor.close()
    if status is None:
        return Status.NOT_FOUND.name
    for s in Status:
        if s.value == status[0]:
            return s.name


status = Get_Status("9780062316097")

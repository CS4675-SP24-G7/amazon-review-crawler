import sqlite3
from enum import Enum


class Status(Enum):
    PROCESSING = 1
    COMPLETED = 2
    FAILED = 3
    NOT_FOUND = 4


def Insert_Status(ISBN, status: Status, lastest_update, time_taken, one_star, two_star, three_star, four_star, five_star, product_title):
    """
    @params: ISBN, status, lastest_update, time_taken, one_star, two_star, three_star, four_star, five_star, product_title, data_path
    """

    connection = sqlite3.connect("CRAWLER.db")

    # create a table if not exists

    cursor = connection.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS status (ISBN text, status integer, lastest_update text, time_taken text, one_star integer, two_star integer, three_star integer, four_star integer, five_star integer, product_title text, PRIMARY KEY (ISBN))")
    connection.commit()
    cursor.close()

    cursor = connection.cursor()
    cursor.execute("INSERT OR REPLACE INTO status (ISBN, status, lastest_update, time_taken, one_star, two_star, three_star, four_star, five_star, product_title) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   (ISBN, status.value, lastest_update, time_taken, one_star, two_star, three_star, four_star, five_star, product_title))
    connection.commit()
    cursor.close()


def Get_Status(ISBN):
    """
    get status field from status table
    """

    connection = sqlite3.connect("CRAWLER.db")

    cursor = connection.cursor()
    cursor.execute("SELECT status FROM status WHERE ISBN=?", (ISBN,))
    status = cursor.fetchone()
    cursor.close()
    if status is None:
        return Status.NOT_FOUND.name
    for s in Status:
        if s.value == status[0]:
            return s.name


def Get_Stats(ISBN):
    """
    get all fields from status table
    """

    connection = sqlite3.connect("CRAWLER.db")

    cursor = connection.cursor()
    cursor.execute("SELECT * FROM status WHERE ISBN=?", (ISBN,))
    status = cursor.fetchone()
    cursor.close()

    # return json
    return {
        "ISBN": status[0],
        "status": Status(status[1]).name,
        "lastest_update": status[2],
        "time_taken": status[3],
        "one_star": status[4],
        "two_star": status[5],
        "three_star": status[6],
        "four_star": status[7],
        "five_star": status[8],
        "product_title": status[9]
    }

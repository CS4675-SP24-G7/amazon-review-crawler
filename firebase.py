import json
import firebase_admin
from firebase_admin import db
from enum import Enum
import os


class Review_Type(Enum):
    ONE_STAR = 1,
    TWO_STAR = 2,
    THREE_STAR = 3,
    FOUR_STAR = 4,
    FIVE_STAR = 5


class Status(Enum):
    PROCESSING = 1
    COMPLETED = 2
    FAILED = 3
    NOT_FOUND = 4


class Firebase:

    ref = None

    def __init__(self) -> None:
        cred = firebase_admin.credentials.Certificate("firebase-admin.json")
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://cs4675-cpfs-default-rtdb.firebaseio.com/'
        })
        self.ref = db.reference("/")

    def getRef(self):
        return self.ref

    def Insert(self, path, data):
        self.ref.child(path).set(data)

    def Delete(self, path):
        self.ref.child(path).delete()

    def Set_Status(self, ISBN, status: Status, extra_data):
        if status != None:
            self.ref.child(f"status/{ISBN}").update({"status": status.name})
        self.ref.child(f"status/{ISBN}").update(extra_data)
    
    def Remove_Status(self, ISBN):
        self.Delete(f"status/{ISBN}")

    def Remove_Review(self, ISBN):
        self.Delete(f"reviews/{ISBN}")

    def Set_Field(self, path, field, value):
        self.ref.child(path).update({field: value})

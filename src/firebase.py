import json
import firebase_admin
from firebase_admin import db
from src.Shared import Status, Review_Type
import os


class Firebase:

    ref = None

    def __init__(self) -> None:

        # read input from firebase-admin.json
        with open('/app/cred/firebase-admin.json', 'r') as f:
            firebase_json = json.load(f)

        cred = firebase_admin.credentials.Certificate(firebase_json)
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
            self.ref.child(f"STATUS/{ISBN}").update({"status": status.name})
        if extra_data != None:
            self.ref.child(f"STATUS/{ISBN}").update(extra_data)

    def Get_Status(self, ISBN):
        data = self.ref.child(f"COMPLETED/{ISBN}").get()
        if data is None:
            return {
                "status": Status.NOT_FOUND.name
            }
        return self.ref.child(f"STATUS/{ISBN}").get()

    def Remove_Status(self, ISBN):
        self.Delete(f"STATUS/{ISBN}")

    def Get_Review(self, ISBN):
        return self.ref.child(f"{Status.COMPLETED.name}/{ISBN}").get()

    def Remove_Review(self, ISBN):
        self.Delete(f"{Status.COMPLETED.name}/{ISBN}")

    def Set_Field(self, path, field, value):
        self.ref.child(path).update({field: value})


Firebase = Firebase()

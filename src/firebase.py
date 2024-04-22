import firebase_admin
from firebase_admin import db
from src.Shared import Status


class Firebase:

    ref = None

    def __init__(self) -> None:

        cred = firebase_admin.credentials.Certificate("cred/firebase_key.json")
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

    def Set_Filter_Status(self, ISBN, filter_status: bool):
        self.ref.child(f"STATUS/{ISBN}").update({"filtered": filter_status})

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

    # get value of key "filtered" inside COMPLETED/ISBN
    def Get_Filters(self, ISBN):
        return self.ref.child(f"{Status.COMPLETED.name}/{ISBN}/filtered").get()
    
    def Get_Reddit(self, ISBN):
        return self.ref.child(f"{Status.COMPLETED.name}/{ISBN}/reddit").get()

    # set value of key "filtered" inside COMPLETED/ISBN
    def Set_Filters(self, ISBN, filters):
        self.ref.child(
            f"{Status.COMPLETED.name}/{ISBN}").update({"filtered": filters})
        self.Set_Filter_Status(ISBN, True)

    def Set_Field(self, path, field, value):
        self.ref.child(path).update({field: value})

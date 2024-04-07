import base64
import json
import firebase_admin
from firebase_admin import db
from src.Shared import Status, Review_Type
import os
from dotenv import load_dotenv, dotenv_values, find_dotenv


class Firebase:

    ref = None

    def __init__(self) -> None:

        load_dotenv(find_dotenv())
        encoded_key = os.getenv("SERVICE_ACCOUNT_KEY")
        encoded_key = str(encoded_key)[2:-1]

        original_service_key = json.loads(
            base64.b64decode(encoded_key).decode('utf-8'))

        firebase_key = {
            "type": original_service_key["type"],
            "project_id": original_service_key["project_id"],
            "private_key_id": original_service_key["private_key_id"],
            "private_key": original_service_key["private_key"],
            "client_email": original_service_key["client_email"],
            "client_id": original_service_key["client_id"],
            "auth_uri": original_service_key["auth_uri"],
            "token_uri": original_service_key["token_uri"],
            "auth_provider_x509_cert_url": original_service_key["auth_provider_x509_cert_url"],
            "client_x509_cert_url": original_service_key["client_x509_cert_url"],
            "universe_domain": original_service_key["universe_domain"]
        }

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

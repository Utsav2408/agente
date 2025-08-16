import os, certifi
from pymongo.mongo_client import MongoClient
from pymongo.errors import ConnectionFailure

from dotenv import load_dotenv

load_dotenv()

class MongoDBConnection:
    def __init__(self):
        self._client = None

    def set_connection(self):
        """Set the MongoDB URI and initialize the client."""
        self._client = MongoClient(f'mongodb+srv://{os.getenv("MONGODB_USER")}:{os.getenv("MONGODB_PASSWORD")}@agente.ymgjjki.mongodb.net/?retryWrites=true&w=majority&appName=AgentE', tlsCAFile=certifi.where())
        try:
            self._client.admin.command('ping')
            print("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            print("Connection failed:", e)
            self._client = None

    def get_connection(self):
        """Return the MongoDB client, and reconnect if necessary."""
        if self._client is None:
            print("MongoDB client is not initialized. Attempting to connect...")
            self.set_connection()
        else:
            try:
                self._client.admin.command('ping')
            except ConnectionFailure:
                print("MongoDB client is not connected. Reconnecting...")
                self.set_connection()

        return self._client

    def close_connection(self):
        if self._client:
            self._client.close()
            print("MongoDB connection closed.")
            self._client = None

mongo = MongoDBConnection()
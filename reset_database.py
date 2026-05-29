import os

DB_PATH = "database/app.db"

if os.path.exists(DB_PATH):

    os.remove(DB_PATH)

    print("Database deleted.")

else:

    print("Database not found.")
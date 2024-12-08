import sqlite3

# Function to clean the database.
def clean_database():
    conn = sqlite3.connect("caption_image.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM vlm_data")
    conn.commit()
    conn.close()
    print("The 'vlm_data' table has been emptied.")

clean_database()
import sqlite3
import sys

# Helper function to check if a table exists
def check_table_exists(cursor):
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vlm_data';")
    if cursor.fetchone() is None:
        print("The 'vlm_data' table does not exist.")
        return False
    return True

# Function to display the contents of the database without including imageData
def display_table():
    conn = sqlite3.connect("caption_image.db")
    cursor = conn.cursor()

    # Check if the table exists
    if not check_table_exists(cursor):
        conn.close() 
        return

    cursor.execute("SELECT dbID, assigneedID, image_url, original_caption, vlm_caption, total_latency FROM vlm_data")
    rows = cursor.fetchall()

    if len(rows) == 0:
        print("No data found in the 'vlm_data' table.")
    else:
        print("Displaying the contents of the 'vlm_data' table (excluding imageData):")
        print(f"{'dbID':<10} {'assigneedID':<15} {'image_url':<20} {'original_caption':<20} {'vlm_caption':<20} {'total_latency':<7}")
        print("-" * 150)
        
        for row in rows:
            dbID, assigneedID, image_url, original_caption, vlm_caption, total_latency = row
            print(f"{dbID:<10} {assigneedID:<15} {image_url:<20} {original_caption:<20} {vlm_caption:<20} {total_latency:<7}")

    conn.close()

# Function to display the captions (original and vlm)
def display_captions(iterID=None):
    conn = sqlite3.connect("caption_image.db")
    cursor = conn.cursor()

    # Check if the table exists
    if not check_table_exists(cursor):
        conn.close()
        return

    if iterID is None:
        cursor.execute("SELECT dbID, assigneedID, image_url, original_caption, vlm_caption FROM vlm_data ORDER BY RANDOM() LIMIT 1")
    else:
        cursor.execute("SELECT dbID, assigneedID, image_url, original_caption, vlm_caption FROM vlm_data WHERE dbID = ?", (iterID,))
    
    row = cursor.fetchone()

    if row is None:
        print(f"No data found for image ID: {iterID}" if iterID else "No captions found in the database.")
    else:
        dbID, assigneedID, image_url, original_caption, vlm_caption = row

        print(f"Displaying captions for image ID: {assigneedID}:")
        print(f"\nImage URL:\n{image_url}")
        print(f"\nOriginal Caption:\n{original_caption}")
        print(f"\nVLM Caption:\n{vlm_caption}")

    conn.close()

# Main function to execute commands based on the passed argument
if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == "table":
        display_table()
    elif sys.argv[1] == "image":
        if len(sys.argv) == 3:
            try:
                iterID = int(sys.argv[2])
                display_captions(iterID)
            except ValueError:
                print("iterID must be an integer.")
        else:
            display_captions() 
    else:
        print("Invalid option. Use 'table' to display the table or 'image' [iterID] to display captions.")

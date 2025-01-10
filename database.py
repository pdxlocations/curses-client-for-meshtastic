import sqlite3
import globals

nodeinfo_table = "nodeinfo"

def initialize_database():
    conn = sqlite3.connect(globals.db_file_path)
    db_cursor = conn.cursor()
    # Create the nodeinfo table for storing nodeinfos
    query = f'CREATE TABLE IF NOT EXISTS {nodeinfo_table} (user_id TEXT, long_name TEXT, short_name TEXT)'
    db_cursor.execute(query)

    # Create the messages table for storing messages
    table_name = globals.channel_list[globals.selected_channel] + "_messages"
    query = f'CREATE TABLE IF NOT EXISTS {table_name} (user_id TEXT,message_text TEXT)'
    db_cursor.execute(query)

def save_message_to_db(channel, user_id, message_text):

    conn = sqlite3.connect(globals.db_file_path)
    table_name = f"{channel}_messages"
    db_cursor = conn.cursor()
    query = f'''
        INSERT INTO {table_name} (user_id, message_text)
        VALUES (?, ?)
    '''
    db_cursor.execute(query, (user_id, message_text))
    conn.commit()
    conn.close()

def maybe_store_nodeinfo_in_db(packet):
    """Save nodeinfo unless that record is already there."""

    try:
        with sqlite3.connect(globals.db_file_path) as db_connection:
            db_cursor = db_connection.cursor()

            # Check if a record with the same user_id already exists
            existing_record = db_cursor.execute(f'SELECT * FROM {nodeinfo_table} WHERE user_id=?', (packet['from'],)).fetchone()

            if existing_record is None:

                # No existing record, insert the new record
                db_cursor.execute(f'''
                    INSERT INTO {nodeinfo_table} (user_id, long_name, short_name)
                    VALUES (?, ?, ?)
                ''', (packet['from'], packet['decoded']['user']['longName'], packet['decoded']['user']['shortName']))
                db_connection.commit()

            else:
                # Check if long_name or short_name is different, update if necessary
                if existing_record[1] != packet['decoded']['user']['longName'] or existing_record[2] != packet['decoded']['user']['shortName']:

                    db_cursor.execute(f'''
                        UPDATE {nodeinfo_table}
                        SET long_name=?, short_name=?
                        WHERE user_id=?
                    ''', (packet['longName'], packet['shortName'], packet['from']))
                    db_connection.commit()

                    # Fetch the updated record
                    updated_record = db_cursor.execute(f'SELECT * FROM {nodeinfo_table} WHERE user_id=?', (packet['from'],)).fetchone()


    except sqlite3.Error as e:
        print(f"SQLite error in maybe_store_nodeinfo_in_db: {e}")

    finally:
        db_connection.close()

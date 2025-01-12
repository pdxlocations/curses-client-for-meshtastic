import sqlite3
import globals
from utilities.utils import get_nodeNum, get_node_list, get_name_from_number


def init_nodedb():
    """Initialize the node database and update it with nodes from the interface."""
    try:
        with sqlite3.connect(globals.db_file_path) as db_connection:
            db_cursor = db_connection.cursor()

            # Table name construction
            table_name = f"{str(get_nodeNum())}_nodedb"
            nodeinfo_table = f'"{table_name}"'  # Quote the table name because it might begin with numerics

            # Step 1: Create the table if it doesn't exist
            create_table_query = f'''
                CREATE TABLE IF NOT EXISTS {nodeinfo_table} (
                    user_id TEXT PRIMARY KEY,
                    long_name TEXT,
                    short_name TEXT
                )
            '''
            db_cursor.execute(create_table_query)

            # Step 2: Get the list of nodes from the interface
            node_list = get_node_list()

            # Step 3: Insert nodes into the database if they don't already exist
            for node in node_list:
                insert_query = f'''
                    INSERT OR IGNORE INTO {nodeinfo_table} (user_id, long_name, short_name)
                    VALUES (?, ?, ?)
                '''
                # Replace placeholders with actual data for the node
                db_cursor.execute(insert_query, (node, get_name_from_number(node, "long"), get_name_from_number(node, "short")))

            db_connection.commit()

    except sqlite3.Error as e:
        print(f"SQLite error in init_and_update_nodedb: {e}")
    except Exception as e:
        print(f"Unexpected error in init_and_update_nodedb: {e}")




def save_message_to_db(channel, user_id, message_text):
    """Save messages to the database, ensuring the table exists."""
    try:
        with sqlite3.connect(globals.db_file_path) as db_connection:
            db_cursor = db_connection.cursor()

            # Construct the table name
            table_name = f"{str(get_nodeNum())}_{channel}_messages"
            quoted_table_name = f'"{table_name}"'  # Quote the table name becuase we begin with numerics

            # Ensure the table exists
            create_table_query = f'''
                CREATE TABLE IF NOT EXISTS {quoted_table_name} (
                    user_id TEXT,
                    message_text TEXT
                )
            '''
            db_cursor.execute(create_table_query)

            # Insert the message
            insert_query = f'''
                INSERT INTO {quoted_table_name} (user_id, message_text)
                VALUES (?, ?)
            '''
            db_cursor.execute(insert_query, (user_id, message_text))

            db_connection.commit()

    except sqlite3.Error as e:
        print(f"SQLite error in save_message_to_db: {e}")

    except Exception as e:
        print(f"Unexpected error in save_message_to_db: {e}")


def load_messages_from_db():
    """Load messages from the database for all channels and update globals.all_messages and globals.channel_list."""
    try:
        with sqlite3.connect(globals.db_file_path) as db_connection:
            db_cursor = db_connection.cursor()

            # Retrieve all table names that match the pattern
            query = "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?"
            db_cursor.execute(query, (f"{str(get_nodeNum())}_%_messages",))
            tables = [row[0] for row in db_cursor.fetchall()]

            # Reset the channel list before populating
            globals.channel_list = []

            # Iterate through each table and fetch its messages
            for table_name in tables:
                query = f'SELECT user_id, message_text FROM "{table_name}"'

                try:
                    # Fetch all messages from the table
                    db_cursor.execute(query)
                    db_messages = [(row[0], row[1]) for row in db_cursor.fetchall()]  # Save as tuples
                    
                    # Extract the channel name from the table name
                    channel = table_name.split("_")[1]

                    # Determine the correct channel name
                    if channel.isdigit():
                        friendly_channel_name = get_name_from_number(int(channel))
                    else:
                        friendly_channel_name = channel

                    # Add the channel to globals.channel_list if not already present
                    if friendly_channel_name not in globals.channel_list:
                        globals.channel_list.append(friendly_channel_name)

                    # Ensure the channel exists in globals.all_messages
                    if friendly_channel_name not in globals.all_messages:
                        globals.all_messages[friendly_channel_name] = []

                    # Add messages to globals.all_messages in tuple format
                    for user_id, message in db_messages:

                        formatted_message = (f"{globals.message_prefix} {get_name_from_number(int(user_id), 'short')}: ", message)
                        if formatted_message not in globals.all_messages[friendly_channel_name]:
                            globals.all_messages[friendly_channel_name].append(formatted_message)


                except sqlite3.Error as e:
                    print(f"SQLite error while loading messages from table '{table_name}': {e}")


    except sqlite3.Error as e:
        print(f"SQLite error in load_messages_from_db: {e}")




def maybe_store_nodeinfo_in_db(packet):
    """Save nodeinfo unless that record is already there."""
    try:
        with sqlite3.connect(globals.db_file_path) as db_connection:

            table_name = f"{str(get_nodeNum())}_nodedb"
            nodeinfo_table = f'"{table_name}"'  # Quote the table name becuase we might begin with numerics
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
                    # TODO display new node name in nodelist
                    # updated_record = db_cursor.execute(f'SELECT * FROM {nodeinfo_table} WHERE user_id=?', (packet['from'],)).fetchone()


    except sqlite3.Error as e:
        print(f"SQLite error in maybe_store_nodeinfo_in_db: {e}")

    finally:
        db_connection.close()

import sqlite3
import time
from datetime import datetime
import logging

from utilities.utils import get_name_from_number
import default_config as config
import globals

def get_table_name(channel):
    # Construct the table name
    table_name = f"{str(globals.myNodeNum)}_{channel}_messages"
    quoted_table_name = f'"{table_name}"'  # Quote the table name becuase we begin with numerics and contain spaces
    return quoted_table_name

def save_message_to_db(channel, user_id, message_text):
    """Save messages to the database, ensuring the table exists."""
    try:
        with sqlite3.connect(config.db_file_path) as db_connection:
            db_cursor = db_connection.cursor()

            quoted_table_name = get_table_name(channel)

            # Ensure the table exists
            create_table_query = f'''
                CREATE TABLE IF NOT EXISTS {quoted_table_name} (
                    user_id TEXT,
                    message_text TEXT,
                    timestamp INTEGER,
                    ack_type TEXT
                )
            '''

            db_cursor.execute(create_table_query)

            timestamp = int(time.time())

            # Insert the message
            insert_query = f'''
                INSERT INTO {quoted_table_name} (user_id, message_text, timestamp, ack_type)
                VALUES (?, ?, ?, ?)
            '''
            db_cursor.execute(insert_query, (user_id, message_text, timestamp, None))
            db_connection.commit()

            return timestamp

    except sqlite3.Error as e:
        logging.error(f"SQLite error in save_message_to_db: {e}")

    except Exception as e:
        logging.error(f"Unexpected error in save_message_to_db: {e}")

def update_ack_nak(channel, timestamp, message, ack):
    try:
        with sqlite3.connect(config.db_file_path) as db_connection:
            db_cursor = db_connection.cursor()
            update_query = f"""
                UPDATE {get_table_name(channel)}
                SET ack_type = ?
                WHERE user_id = ? AND
                      timestamp = ? AND
                      message_text = ?
            """

            db_cursor.execute(update_query, (ack, str(globals.myNodeNum), timestamp, message))
            db_connection.commit()

    except sqlite3.Error as e:
        logging.error(f"SQLite error in update_ack_nak: {e}")

    except Exception as e:
        logging.error(f"Unexpected error in update_ack_nak: {e}")


from datetime import datetime

def load_messages_from_db():
    """Load messages from the database for all channels and update globals.all_messages and globals.channel_list."""
    try:
        with sqlite3.connect(config.db_file_path) as db_connection:
            db_cursor = db_connection.cursor()

            # Retrieve all table names that match the pattern
            query = "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?"
            db_cursor.execute(query, (f"{str(globals.myNodeNum)}_%_messages",))
            tables = [row[0] for row in db_cursor.fetchall()]

            # Iterate through each table and fetch its messages
            for table_name in tables:
                quoted_table_name = f'"{table_name}"'  # Quote the table name because we begin with numerics and contain spaces
                table_columns = [i[1] for i in db_cursor.execute(f'PRAGMA table_info({quoted_table_name})')]
                if "ack_type" not in table_columns:
                    update_table_query = f"ALTER TABLE {quoted_table_name} ADD COLUMN ack_type TEXT"
                    db_cursor.execute(update_table_query)

                query = f'SELECT user_id, message_text, timestamp, ack_type FROM {quoted_table_name}'

                try:
                    # Fetch all messages from the table
                    db_cursor.execute(query)
                    db_messages = [(row[0], row[1], row[2], row[3]) for row in db_cursor.fetchall()]  # Save as tuples
                    
                    # Extract the channel name from the table name
                    channel = table_name.split("_")[1]
                    
                    # Convert the channel to an integer if it's numeric, otherwise keep it as a string
                    channel = int(channel) if channel.isdigit() else channel
                    
                    # Add the channel to globals.channel_list if not already present
                    if channel not in globals.channel_list:
                        globals.channel_list.append(channel)

                    # Ensure the channel exists in globals.all_messages
                    if channel not in globals.all_messages:
                        globals.all_messages[channel] = []

                    # Add messages to globals.all_messages grouped by hourly timestamp
                    hourly_messages = {}
                    for user_id, message, timestamp, ack_type in db_messages:
                        hour = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:00')
                        if hour not in hourly_messages:
                            hourly_messages[hour] = []
                        
                        ack_str = config.ack_unknown_str
                        if ack_type == "Implicit":
                            ack_str = config.ack_implicit_str
                        elif ack_type == "Ack":
                            ack_str = config.ack_str
                        elif ack_type == "Nak":
                            ack_str = config.nak_str

                        if user_id == str(globals.myNodeNum):
                            formatted_message = (f"{config.sent_message_prefix}{ack_str}: ", message)
                        else:
                            formatted_message = (f"{config.message_prefix} {get_name_from_number(int(user_id), 'short')}: ", message)
                        
                        hourly_messages[hour].append(formatted_message)

                    # Flatten the hourly messages into globals.all_messages[channel]
                    for hour, messages in sorted(hourly_messages.items()):
                        globals.all_messages[channel].append((f"-- {hour} --", ""))
                        globals.all_messages[channel].extend(messages)

                except sqlite3.Error as e:
                    logging.error(f"SQLite error while loading messages from table '{table_name}': {e}")

    except sqlite3.Error as e:
        logging.error(f"SQLite error in load_messages_from_db: {e}")


def init_nodedb():
    """Initialize the node database and update it with nodes from the interface."""
    try:
        with sqlite3.connect(config.db_file_path) as db_connection:
            db_cursor = db_connection.cursor()

            # Table name construction
            table_name = f"{str(globals.myNodeNum)}_nodedb"
            nodeinfo_table = f'"{table_name}"'  # Quote the table name because it might begin with numerics

            # Create the table if it doesn't exist
            create_table_query = f'''
                CREATE TABLE IF NOT EXISTS {nodeinfo_table} (
                    user_id TEXT PRIMARY KEY,
                    long_name TEXT,
                    short_name TEXT,
                    hw_model TEXT,
                    is_licensed TEXT,
                    role TEXT,
                    public_key TEXT
                )
            '''
            db_cursor.execute(create_table_query)

            # Iterate over nodes and insert them into the database
            if globals.interface.nodes:
                for node in globals.interface.nodes.values():
                    role = node['user'].get('role', 'CLIENT')
                    is_licensed = node['user'].get('isLicensed', '0')
                    public_key = node['user'].get('publicKey', '')

                    insert_query = f'''
                        INSERT OR IGNORE INTO {nodeinfo_table} (user_id, long_name, short_name, hw_model, is_licensed, role, public_key)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    '''

                    db_cursor.execute(insert_query, (
                        node['num'],
                        node['user']['longName'],
                        node['user']['shortName'],
                        node['user']['hwModel'],
                        is_licensed,
                        role,
                        public_key
                    ))
                    
            db_connection.commit()

    except sqlite3.Error as e:
        logging.error(f"SQLite error in init_nodedb: {e}")
    except Exception as e:
        logging.error(f"Unexpected error in init_nodedb: {e}")

def maybe_store_nodeinfo_in_db(packet):
    """Save nodeinfo unless that record is already there."""
    try:
        with sqlite3.connect(config.db_file_path) as db_connection:

            table_name = f"{str(globals.myNodeNum)}_nodedb"
            nodeinfo_table = f'"{table_name}"'  # Quote the table name becuase we might begin with numerics
            db_cursor = db_connection.cursor()

            # Check if a record with the same user_id already exists
            existing_record = db_cursor.execute(f'SELECT * FROM {nodeinfo_table} WHERE user_id=?', (packet['from'],)).fetchone()

            if existing_record is None:
                role = packet['decoded']['user'].get('role', 'CLIENT')
                is_licensed = packet['decoded']['user'].get('isLicensed', '0')
                public_key = packet['decoded']['user'].get('publicKey', '')

                # No existing record, insert the new record
                insert_query = f'''
                    INSERT INTO {nodeinfo_table} (user_id, long_name, short_name, hw_model, is_licensed, role, public_key)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                '''

                db_cursor.execute(insert_query, (
                    packet['from'], 
                    packet['decoded']['user']['longName'], 
                    packet['decoded']['user']['shortName'], 
                    packet['decoded']['user']['hwModel'], 
                    is_licensed, 
                    role, 
                    public_key
                ))

                db_connection.commit() 

            else:
                # Check if values are different, update if necessary
                # Extract existing values
                existing_long_name = existing_record[1]
                existing_short_name = existing_record[2]
                existing_is_licensed = existing_record[4]
                existing_role = existing_record[5]
                existing_public_key = existing_record[6]

                # Extract new values from the packet
                new_long_name = packet['decoded']['user']['longName']
                new_short_name = packet['decoded']['user']['shortName']
                new_is_licensed = packet['decoded']['user'].get('isLicensed', '0')
                new_role = packet['decoded']['user'].get('role', 'CLIENT')
                new_public_key = packet['decoded']['user'].get('publicKey', '')

                # Check for any differences
                if (
                    existing_long_name != new_long_name or
                    existing_short_name != new_short_name or
                    existing_is_licensed != new_is_licensed or
                    existing_role != new_role or
                    existing_public_key != new_public_key
                ):
                    # Perform necessary updates
                    update_query = f'''
                        UPDATE {nodeinfo_table}
                        SET long_name = ?, short_name = ?, is_licensed = ?,  role = ?, public_key = ?
                        WHERE user_id = ?
                    '''
                    db_cursor.execute(update_query, (
                        new_long_name, 
                        new_short_name, 
                        new_is_licensed, 
                        new_role, 
                        new_public_key, 
                        packet['from']
                    ))

                db_connection.commit()

                    # TODO display new node name in nodelist


    except sqlite3.Error as e:
        logging.error(f"SQLite error in maybe_store_nodeinfo_in_db: {e}")
    finally:
        db_connection.close()

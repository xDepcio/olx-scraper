from psycopg2 import connect

def get_connection():
    hostname = "localhost"
    database = "olx-scraper"
    username = "admin"
    password = "admin"
    port_id = 5432

    connection = connect(host=hostname, dbname=database, user=username, password=password, port=port_id)

    db_cursor = connection.cursor()
    return db_cursor

def load_schema(path, cursor):
    script = open(path, "r").read()
    cursor.execute(script)

def execute_script(path: str, cursor):
    script = open(path, "r").read()
    cursor.execute(script)

if __name__ == '__main__':
    cursor = get_connection()

    load_schema("./schema.sql", cursor)
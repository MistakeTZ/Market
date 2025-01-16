import sqlite3
from sqlite3 import Connection, Error
import logging
from os import path

conn: Connection


def get_db_connection():
    global conn
    conn = sqlite3.connect(path.join('database', 'database.db'), check_same_thread=False)
    tables = select("select name from sqlite_master where type='table'", one_argument=True)
    create_tables([table for table in [
            "users", "categories", "products"
        ] if table not in tables])


def select(prompt, values=[], is_one=False, one_argument=False):
    cursor = conn.cursor()
    answer = []
    try:
        cursor.execute(prompt, values)
    except Error as e:
        logging.warning(e)
        return answer
    if is_one:
        answer = cursor.fetchone()
        if one_argument:
            answer = answer[0]
    else:
        answer = cursor.fetchall()
        if one_argument:
            answer = [ans[0] for ans in answer]
    cursor.close()
    return answer


def commit(prompt, values=[]):
    cursor = conn.cursor()
    try:
        cursor.execute(prompt, values)
    except Error as e:
        logging.warning(e)
        return False
    conn.commit()
    cursor.close()
    return True


def fields(table):
    table_fields = select("PRAGMA table_info('{}')".format(table))
    return [field[1] for field in table_fields]


def create_tables(tables):
    if "users" in tables:
        logging.info("Creating table users")
        commit("""create table users (
                id integer primary key autoincrement,
                ipv4 varchar(16),
                name varchar(50),
                pass_hash varchar(50),
                address text,
                role varchar(15) not null default 'user',
                registered timestamp
                )""")

    if "categories" in tables:
        logging.info("Creating table categories")
        commit("""create table categories (
                id integer primary key autoincrement,
                category text
                )""")

    if "products" in tables:
        logging.info("Creating table products")
        commit("""create table products (
                id integer primary key autoincrement,
                product_category integer,
                name text,
                price integer,
                price_modificator integer default 100,
                count integer,
                photo_sources text,
                previous_price integer,
                description text,
                tags text,
                slug text,
                foreign key(product_category) references categories(id),
                unique (slug) ON CONFLICT IGNORE
                )""")


def close_db_connection():
    conn.close()

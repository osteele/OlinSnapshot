import psycopg2
from psycopg2.extensions import AsIs
from psycopg2.extras import RealDictCursor
from app.config import connect, close_conn, no_commit_close_conn
from datetime import date, datetime, time
import time as t


def create_schema(cur, sch_name):
    """ Given a cursor and a name,
    makes a schema with that name."""
    try:
        sch_make = """CREATE SCHEMA %s"""
        cur.execute(sch_make, (AsIs(sch_name),))
        print("Schema Made")
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    return 1


def create_cat_tab(cur, sch_name):
    """ Given a cursor to a database
    and a table name, as well as a list
    of columns, creates that table.
    """
    try:
        tab_name = sch_name + ".cats"
        tab_make = """CREATE TABLE %s(cat_id serial PRIMARY KEY, cat_name character(10), duration integer)"""
        cur.execute(tab_make, (AsIs(tab_name),))
        make_rows_cat(cur, tab_name)
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    return 1


def create_join_tab(cur, sch_name):
    """ Given a cursor to a database
    and a table name, as well as a list
    of columns, creates that table.
    """
    try:
        tab_name = sch_name + ".msg_to_cat"
        tab_make = """CREATE TABLE %s(msg_id integer, cat_id integer)"""
        cur.execute(tab_make, (AsIs(tab_name),))
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    return 1


def create_msg_tab(cur, sch_name):
    """ Given a cursor to a database
    and a table name, as well as a list
    of columns, creates that table.
    """
    try:
        tab_name = sch_name + ".msg"
        tab_make = """CREATE TABLE %s(msg_id serial PRIMARY KEY,
									name varchar(80),
									body text,
									-- event_time time, # TODO: Add time and date back in
									-- event_date date,
									event_place varchar(50),
									value integer,
									who varchar(100))"""
        cur.execute(tab_make, (AsIs(tab_name),))
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    return 1


def add_email(cur, email_dict):
    """ Given a dictionary containing the necessary information,
    creates an entry in the msg and msg_to_cat tables.
    email_dict form:
            {
                    'name': str,
                    'body': str,
                    'event_time': datetime.time, <= CURRENTLY DELETED
                    'event_date': datetime.date, <= CURRENTLY DELETED
                    'event_place': str,
                    'who': str,
                    'value':5,
                    'categories':any combination of ['Food', 'Event', 'Lost', 'Other']
            }
    """
    cat_list = email_dict['categories']
    print("Got cat list")
    del email_dict['categories']
    print("Deleted categories")
    msg_id = insert_from_dict(cur, 'emails.msg', email_dict, 'msg_id')
    print("Adding Email...")
    populate_join_tab(cur, 'emails', msg_id, cat_list)


def insert_from_dict(cur, tab_name, datadict, id_name=None):
    """ Inserts a row into the table named by tab_name
    as specified by the keys and values of dict

    takes:
    cur      - cursor of the above connection
    tab_name - string name of the table to be inserted into
    dict     - dictionary object with keys as the column names
                            and the values as values to be inserted
    """
    columns = datadict.keys()
    print(columns)
    values = [datadict[column] for column in columns]

    return_id = None
    try:
        if id_name is None:
            insert_statement = 'insert into %s (%s) values %s'
            cur.execute(insert_statement, (AsIs(tab_name), AsIs(','.join(columns)), tuple(values)))
        else:
            insert_statement = 'insert into %s (%s) values %s returning %s'
            cur.execute(insert_statement, (AsIs(tab_name), AsIs(','.join(columns)), tuple(values), AsIs(id_name)))
            return_id = cur.fetchone()[0]
        print("Executed")

    except (Exception, psycopg2.DatabaseError) as error:
        print("Error:", error)

    return return_id


def make_rows_cat(cur, tab_name):
    """ Populate the category table from dictionaries.
    input:
            cur-cursor object
            tab_name-string name of the new table
    """
    food_dict = {
        "cat_name": "Food",
        "duration": 1}
    event_dict = {
        "cat_name": "Event",
        "duration": 2}
    lost_dict = {
        "cat_name": "Lost",
        "duration": 12}
    other_dict = {
        "cat_name": "Other",
        "duration": 24}
    insert_from_dict(cur, "emails.cats", food_dict)
    insert_from_dict(cur, "emails.cats", event_dict)
    insert_from_dict(cur, "emails.cats", lost_dict)
    insert_from_dict(cur, "emails.cats", other_dict)


def get_cat_id(cur, sch_name, cat_name):
    """ Given a schema name and the desired category, returns the
    cat_id
    """
    tab_name = sch_name + '.cats'
    sql = """SELECT cat_id FROM %s WHERE %s.cat_name = %s"""
    cur.execute(sql, (AsIs(tab_name), AsIs(tab_name), cat_name))
    return cur.fetchone()[0]


def populate_join_tab(cur, sch_name, email_id, cat_list):
    """ Given the connection, cursor, email id (as represented in the msg_tab),
    and list of categories the given email corresponds to, fills in the join_tab
    """
    tab_name = sch_name + ".msg_to_cat"
    insert_statement = 'insert into %s (msg_id, cat_id) values %s'

    for cat in cat_list:
        print("Adding", cat + "...")
        cat_id = get_cat_id(cur, sch_name, cat)
        cur.execute(insert_statement, (AsIs(tab_name), tuple((email_id, cat_id))))

if __name__ == '__main__':
    conn, cur = connect()
    sch_name = 'emails'

    create_schema(cur, sch_name)
    create_cat_tab(cur, sch_name)
    create_join_tab(cur, sch_name)
    create_msg_tab(cur, sch_name)
    close_conn(conn, cur)

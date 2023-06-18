import mysql.connector

import private as p

def sql_connect(): 
    mysql_connection = mysql.connector.connect(
        host=p.mysql['host'],
        port=p.mysql['port'],
        user=p.mysql['user'],
        password=p.mysql['password'],
        database='youtube_shorts_generator',
    )
    return {
        'conn': mysql_connection,
        'cursor': mysql_connection.cursor(),
    }

def sql_disconnect(db_engine):
    db_engine['cursor'].close()
    db_engine['conn'].close()
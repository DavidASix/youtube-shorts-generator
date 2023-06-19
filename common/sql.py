import mysql.connector

import common.private as p

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

def insert_df(df, loc):
    db_engine = sql_connect()
    cols = df.columns.values.tolist()
    cols = list(map(lambda c: f'{c}', cols))
    colNames = ','.join(cols)
    qMarks = ','.join(['%s'] * len(cols))
    query = f'INSERT INTO {loc} ({colNames}) VALUES ({qMarks})'
    try:
        f_data = [tuple(row) for row in df.values]
    except:
        print('Error formatting data for insert into', loc)
    # Insert data formatted as rows
    try:
        db_engine['cursor'].executemany(query, f_data)
        db_engine['conn'].commit()
    except Exception as e:
        print('Error inserting data')
        print(e)
    finally:
        sql_disconnect(db_engine)
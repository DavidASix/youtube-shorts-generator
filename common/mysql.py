import mysql.connector

import common.private as p

class sql:
    # Method is auto called when new class instance is created
    def __init__(self):
        self.connection = mysql.connector.connect(
            host=p.mysql['host'],
            port=p.mysql['port'],
            user=p.mysql['user'],
            password=p.mysql['password'],
            database='youtube_shorts_generator',
        )
        self.cursor = self.connection.cursor()

    def close(self):
        self.cursor.close()
        self.connection.close()

    def insert_df(self, df, loc):
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
            self.cursor.executemany(query, f_data)
            self.connection.commit()
        except Exception as e:
            print('Error inserting data')
            print(e)
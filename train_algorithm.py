import pandas as pd
from common.sql import sql


def get_sample_df():
    db_engine = sql()
    query = 'SELECT * FROM manual_page_classifications'
    df = pd.read_sql_query(query, db_engine.connection)
    print(df)


def main():
    get_sample_df()
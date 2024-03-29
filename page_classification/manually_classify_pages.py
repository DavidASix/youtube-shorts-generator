import re
import os
import pandas as pd
import sqlite3
import questionary
from pprint import pprint
from common.media_wiki import MediaWiki
import os

fandom_title = 'fallout'

# https://fandom-py.readthedocs.io/en/latest/fandom.html
# Working on new laptop

def get_pages_to_classify(pages_to_get=10):
    wiki = MediaWiki(fandom_title, 'en')
    columns = ['page_id', 'title', 'url', 'categories', 'sections', 'non_english', 'file_page', 'short_page', 'total_length', 'target_words_in_section_titles', 'section_count', 'image_count', 'audio_count']
    df = pd.DataFrame(columns=columns)
    # Get a list of 10 random site pages 
    while len(df) < pages_to_get:
        try:
            # Pull a random wiki page and get its id
            id = wiki.random_pages()[0]['id']
            print(f'Getting page {id}')
            output_page = wiki.parse_page_classification_information(id)
            df = pd.concat([df, pd.DataFrame([output_page])], ignore_index=True)
        except Exception as e:
            print(e)
    # Return the list of viable pages
    return df

def classify_df(df):
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_colwidth', None)
    print('\nNow you will classify the rows in this DF on viability')
    ratings = []
    for i, r in df.iterrows():
        print('Issue Found' if r['non_english'] or r['file_page'] else 'Short' if r['short_page'] else 'Good')
        print(r['target_words_in_section_titles'], 'Target Words.', r['section_count'], 'Sections')
        pprint(r)
        question = questionary.select(
            f'How would you rate {r["title"]}',
            choices=['unusable', 'bad', 'fine', 'good', 'viral', 'EXIT'])
        rating = question.ask()
        if rating == 'EXIT':
            exit()
        ratings.append(rating)
        os.system('clear')
    df['rating_class'] = ratings
    return df

def save_classified_df(classified_df):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    parent_dir_path = os.path.dirname(dir_path)
    dataset_path = os.path.join(parent_dir_path, 'ytsg-dataset.db')
    conn = sqlite3.connect(dataset_path)
    cursor = conn.cursor()

    # Check if the fandom has an entry in the niches table
    try:
        # create the niches table if it doesn't exist
        cursor.execute('CREATE TABLE IF NOT EXISTS niches (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT UNIQUE)')
        # insert the fandom title into the table if it doesn't exist
        cursor.execute('INSERT OR IGNORE INTO niches (title) VALUES (?)', (fandom_title,))
        conn.commit()
        # select the id of the fandom title
        cursor.execute('SELECT id FROM niches WHERE title = ?', (fandom_title,))
        fandom_id = cursor.fetchone()[0]

    except Exception as e:
        print('Error getting fandom_id', e)
    
    # Get the maximum rank group that has been completed
    try:
        # Check if the rank_group table currently exists
        cursor.execute('SELECT 1 FROM sqlite_master WHERE type = "table" AND name = "manual_page_classifications"')
        if cursor.fetchone() is None:
            # Table does not exist, set max_rank_group to 0
            max_rank_group = 0
        else:
            # Table exists, get the maximum rank_group value
            cursor.execute('SELECT MAX(rank_group) FROM manual_page_classifications')
            max_rank_group = cursor.fetchone()[0]
    except Exception as e:
        print('Error getting max rank_group', e)
    
    # Assign the niche ID and the next consecutive rank_group to the rows
    df = classified_df
    df['rank_group'] = max_rank_group + 1
    df['niche_id'] = fandom_id

    # Insert the new group of classified rows
    try:
        # Check if the table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='manual_page_classifications'")
        exists = cursor.fetchone() is not None
        print('EXISTs', exists)
        # If it doesn't, create it and ensure that the niche_id key is an integer
        if not exists:
            cols = df.columns.tolist()
            cols.remove('niche_id')
            sql = f"""CREATE TABLE manual_page_classifications (
                {', '.join(cols)}, 
                niche_id INTEGER,
                FOREIGN KEY (niche_id) REFERENCES niches(id))"""
            cursor.execute(sql)

        # Insert the DF into the table, creating it if it didn't exist
        df.to_sql("manual_page_classifications", conn, if_exists="append", index=False)
        conn.commit()
    except Exception as e:
        print('Error inserting classified df')
        raise e
    # Close the connection
    conn.close()

def manually_classify_pages():
    df = get_pages_to_classify()
    classified_df = classify_df(df)
    save_classified_df(classified_df)
    print(f'Inserted {len(classified_df)} new classified rows')

def main():
    manually_classify_pages()
    next = questionary.select(
            'Would you like to classify more?',
            choices=['Yes', 'No'])
    next = next.ask()
    if (next == 'Yes'): main()

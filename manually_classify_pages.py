import re
import os
import pandas as pd
import sqlite3
import questionary
from pprint import pprint
from common.media_wiki import MediaWiki
from common.mysql import sql

fandom_title = 'fallout'

# https://fandom-py.readthedocs.io/en/latest/fandom.html
# Working on new laptop

def get_viable_pages():
    wiki = MediaWiki(fandom_title, 'en')
    pages = []
    # Get a list of 10 random site pages 
    while len(pages) < 10:
        try:
            output_page = {}
            # Pull a random wiki page and get its basic info
            p = wiki.random_pages(1)[0]
            
            page = wiki.get_page_information(p['id'])
            # Pages should be long enough for a 30 second video, and should not be about game files
            short_page = page['length'] < 1000
            # Find pages with titles like 'abc.mp3' to avoid file related pages
            file_page = re.match(r".+\..{2,}", page['title']) != None
            # Get page content
            page_content = wiki.get_page_content(p['id'])
            page_images = wiki.get_page_images(p['id'])
            page_audio = wiki.get_page_audio_files(p['id'])

            # Start adding to output file object
            output_page.update({
                'id': p['id'],
                'lang': 'en',
                'title': page['title'], 
                'url': page['url'], 
                'sections': page['sections'],
                'categories': page['categories'],
                'short_page': short_page,
                'file_page': file_page,
                'plain_text': page_content['content'], 
                'infobox': page_content['infobox'], 
                'images': page_images,
                'audio': page_audio
            })
            pages.append(output_page)
        except Exception as e:
            print(e)
    # Return the list of viable pages
    return pages

def get_pages_df(pages):
    df = pd.DataFrame({
        'page_id': [],
        'title': [],
        'url': [],
        'categories': [],
        'sections': [],
        'non_english': [],
        'file_page': [],
        'short_page': [],
        'total_length': [],
        'target_words_in_section_titles': [],
        'section_count': [],
        'image_count': [],
        'audio_count': [],
        #'infobox_value_count': []
        })
    for p in pages:
        #section_concat = ''.join(v for k, v in p['section_text'].items() if k.lower() != 'references')
        #overview_length = len(p['plain_text']) - len(section_concat)
        #first_section_title = p['sections'][0] if len(p['sections']) > 0 else ''
        #first_section_length = 0#len(p['section_text'].get(first_section_title, ''))
        # Search the section titles for words that indicate the section might be rich in content creation text.
        targetted_section_words = ['background', 'description', 'lore', 'biography', 'overview', 'personality', 'history', 'context', 'backstory', 'origins', 'explanation', 'summary', 'synopsis', 'introduction']
        target_words_in_section_titles = 0
        for w in targetted_section_words:
            if w in '|'.join(p['sections']).lower():
                target_words_in_section_titles += 1
        
        new_row = pd.DataFrame({
            'page_id': [p['id']],
            'title': [p['title']],
            'url': [p['url']], 
            'categories':['||'.join(p['categories'])],
            'sections': ['||'.join(p['sections']).lower()],
            'non_english': [p['lang'] != 'en' * 1],
            'file_page': [p['file_page'] * 1],
            'short_page': [p['short_page'] * 1],
            'total_length': [len(p['plain_text'])],  # Change to total lenth
            'target_words_in_section_titles': [target_words_in_section_titles], # Change this to search all section titles, so what if the first one has it?
            'section_count': [len(p['sections'])], 
            'image_count': [len(p['images'])],
            'audio_count': [len(p['audio'])]
        })
        df = pd.concat([df, new_row], ignore_index=True)
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
    conn = sqlite3.connect('ytsg-dataset.db')
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
    pages = get_viable_pages()
    df = get_pages_df(pages)
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

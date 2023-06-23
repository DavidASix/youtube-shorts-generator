import re
import os
import pandas as pd
import questionary

from common.media_wiki import MediaWiki
from common.sql import sql

fandom_title = 'rickandmorty'

# https://fandom-py.readthedocs.io/en/latest/fandom.html
# Working on new laptop

def get_viable_pages():
    wiki = MediaWiki('fallout')
    pages = []
    # Get a list of 10 random site pages 
    while len(pages) < 3:
        try:
            output_page = {}
            # Pull a random wiki page and get its basic info
            p = wiki.random_pages(1)[0]
            page = wiki.get_page_information(p['id'])
            print(page)
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
                'title': page['title'], 
                'url': page['url'], 
                'sections': page['sections'],
                'categories': page['categories'],
                'short_page': short_page,
                'file_page': file_page,
                #'plain_text': page_content['content'], 
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
        'pageid': [],
        'title': [],
        'url': [],
        'categories': [],
        'file_page': [],
        'short_page': [],
        'total_length': [],
        'text_before_sections': [],
        'mean_section_length': [],
        'median_section_length': [],
        'target_words_in_section_titles': [],
        'section_count': [],
        'image_count': [],
        'audio_count': [],
        'infobox_value_count': []
        })
    for p in pages:
        #section_concat = ''.join(v for k, v in p['section_text'].items() if k.lower() != 'references')
        #overview_length = len(p['plain_text']) - len(section_concat)
        first_section_title = p['sections'][0] if len(p['sections']) > 0 else ''
        first_section_length = len(p['section_text'].get(first_section_title, ''))
        # Search the section titles for words that indicate the section might be rich in content creation text.
        targetted_section_words = ['background', 'description', 'lore', 'biography', 'overview', 'personality', 'history', 'context', 'backstory', 'origins', 'explanation', 'summary', 'synopsis', 'introduction']
        target_words_in_section_titles = 0
        for w in targetted_section_words:
            if w in '|'.join(p['sections']).lower():
                target_words_in_section_titles += 1
        
        new_row = pd.DataFrame({
            'title': [p['title']], 
            'url': [p['url']], 
            'categories':['|'.join(p['categories'])],
            'total_length': [len(p['plain_text'])],  # Change to total lenth
            'non_english': [p['non_english'] * 1],
            'file_page': [p['file_page'] * 1],
            'short_page': [p['short_page'] * 1],
            'first_section_length': [first_section_length], 
            'target_words_in_section_titles': [target_words_in_section_titles], # Change this to search all section titles, so what if the first one has it?
            'section_count': [len(p['sections'])], 
            'image_count': [len(p['images'])],
            'audio_count': [len(p['audio'])]
        })
        df = pd.concat([df, new_row], ignore_index=True)
    return df

def classify_df(df):
    print('\nNow you will classify the rows in this DF on viability')
    ratings = []
    for i, r in df.iterrows():
        print('Issue Found' if r['non_english'] or r['file_page'] else 'Short' if r['short_page'] else 'Good')
        print(r['target_words_in_section_titles'], 'Target Words.', r['section_count'], 'Sections')
        print(r)
        question = questionary.select(
            f'How would you rate {r["title"]}',
            choices=['unusable', 'bad', 'fine', 'good', 'viral'])
        rating = question.ask()
        ratings.append(rating)
        os.system('cls')
    df['rating_class'] = ratings
    return df

def mysql_test(): 
    db_engine = sql()
    db_engine.cursor.execute('SHOW DATABASES')
    result = db_engine.cursor.fetchall()
    for row in result:
        print(row)
    db_engine.close()

def save_classified_df(classified_df):
    # Check if the fandom has an entry in the niches table
    print('saving DF')
    try:
        db_engine = sql()
        db_engine.cursor.execute('SELECT id FROM niches WHERE title = %s', (fandom_title,))
        fandom_id = db_engine.cursor.fetchone()
        print('FandomID', fandom_id)
        if fandom_id is None:
            # Fandom ID does not exist, insert it
            db_engine.insert_df(pd.DataFrame({'title': [fandom_title]}), 'niches')
            db_engine.cursor.execute('SELECT * FROM niches WHERE title = %s', (fandom_title,))
            fandom_id = db_engine.cursor.fetchone()
        fandom_id = fandom_id[0]
        db_engine.close()
    except Exception as e:
        print('Error getting fandom_id', e)
    # First get the maximum rank_group that currently exists
    try:
        db_engine = sql()
        db_engine.cursor.execute('SELECT COALESCE(MAX(rank_group), 0) FROM youtube_shorts_generator.manual_page_classifications')
        max_rank_group = db_engine.cursor.fetchone()[0]
        db_engine.close()
    except Exception as e:
        print('Error getting max rank_group', e)
    # Assign the next consecutive rank_group as the new groups value
    df = classified_df
    df['rank_group'] = max_rank_group + 1
    df['niche_id'] = fandom_id
    # Insert the new group
    try:
        db_engine = sql()
        db_engine.insert_df(df, 'manual_page_classifications')
    except Exception as e:
        print('Error inserting classified df')
        raise e

def manually_classify_pages():
    pages = get_viable_pages()
    df = get_pages_df(pages)
    classified_df = classify_df(df)
    print(classified_df)
    save_classified_df(classified_df)
    print(f'Inserted {len(classified_df)} new classified rows')

def main():
    manually_classify_pages()
    next = questionary.select(
            'Would you like to classify more?',
            choices=['Yes', 'No'])
    next = next.ask()
    if (next == 'Yes'): main()

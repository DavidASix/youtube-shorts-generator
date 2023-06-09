import re
import os
import pandas as pd
from bs4 import BeautifulSoup
import fandom
import questionary
import mysql.connector

# https://fandom-py.readthedocs.io/en/latest/fandom.html
# Working on new laptop

def get_viable_pages():
    fandom_type = 'fallout'
    fandom.set_wiki(fandom_type)

    pages = []
    viable_pages = 0
    # Get a list of 10 random site pages 
    while viable_pages < 2:
        # Pages are returned as a tuple like (title, page_id)
        #r_pages = [('Paul_(Fallout)', 999)]
        p = fandom.random(1)[0]
        # Pages should be long enough for a 30 second video, and should not be about game files
        try:
            page = fandom.page(p)
            output_page = {}
            vde_delimiter = ' • '
            # 'v · d · e'
            # Some pages have the characters "v · d · e" for View Template, Discussion, Edit
            # The text after this delimiter can be very long with many links to other semi-related articles
            # Unfortuantely this text is captured in whatever final section appears on the page, after the scrape
            page_body = page.plain_text.split(vde_delimiter)[0]
            
            short_page = 'Expansion required' in page_body or len(page_body) < 1200
            non_english = page.language != 'en'
            # Find pages with titles like 'abc.mp3' to avoid file related pages
            file_page = re.match(r".+\..{2,}", page.title) != None

            if (not short_page and not non_english and not file_page):
                viable_pages += 1
                print('Page Suitable!')
            else:
                print('Page Not Suitable')
            # Start adding to output file object
            output_page.update({
                'title': page.title, 
                'url': page.url, 
                'sections': page.sections, 
                'summary': page.summary,
                'short_page': short_page,
                'non_english': non_english,
                'file_page': file_page,
                'plain_text': page_body})

            output_page['section_text'] = {}
            for s in page.sections:
                output_page['section_text'][s] = page.section(s).split(vde_delimiter)[0]
                    
            # Add additional scrapped information to output page
            # Categories
            soup = BeautifulSoup(page.html, 'html.parser')
            cats = soup.select('[class*="category"]')
            output_page['categories'] = list(map(lambda e: e.text.replace('\n', ''), cats))

            # Audio file urls
            audio = soup.find_all('audio')
            output_page['audio'] = [a['src'] for a in audio]

            # Notes from top of aticle
            notes = soup.find_all('[role="note"]')
            output_page['notes'] = list(map(lambda n: n.text.replace('\n', ''), notes))

            imgs = soup.find_all('img')
            output_page['images'] = [i['src'] for i in imgs if 
                '.net/'+fandom_type in i['src'] 
                and 'icon' not in i['src']
                and 'site-logo' not in i['src'].lower()]

            pages.append(output_page)
        except Exception as e:
            print(e)
    # Return the list of viable pages
    return pages

def get_pages_df(pages):
    df = pd.DataFrame({
        'title': [],
        'url': [],
        'first_section_title': [],
        'categories': [],
        'non_english': [],
        'file_page': [],
        'short_page': [],
        'length': [],
        'first_section_length': [],
        'target_words_found': [],
        'sections': [],
        'images': [],
        'audio': []
        })
    for p in pages:
        #section_concat = ''.join(v for k, v in p['section_text'].items() if k.lower() != 'references')
        #overview_length = len(p['plain_text']) - len(section_concat)
        first_section_title = p['sections'][0] if len(p['sections']) > 0 else ''
        first_section_length = len(p['section_text'].get(first_section_title, ''))
        # Search the section titles for words that indicate the section might be rich in content creation text.
        targetted_section_words = ['background', 'description', 'lore', 'biography', 'overview', 'personality', 'history', 'context', 'backstory', 'origins', 'explanation', 'summary', 'synopsis', 'introduction']
        targetted_words_found = 0
        for w in targetted_section_words:
            if w in '|'.join(p['sections']).lower():
                targetted_words_found += 1
        
        new_row = pd.DataFrame({
            'title': [p['title']], 
            'url': [p['url']], 
            'first_section_title': [first_section_title],
            'categories':['|'.join(p['categories'])],
            'length': [len(p['plain_text'])],  # Change to total lenth
            'non_english': [p['non_english'] * 1],
            'file_page': [p['file_page'] * 1],
            'short_page': [p['short_page'] * 1],
            'first_section_length': [first_section_length], 
            'target_words_found': [targetted_words_found], # Change this to search all section titles, so what if the first one has it?
            'sections': [len(p['sections'])], 
            'images': [len(p['images'])],
            'audio': [len(p['audio'])]
        })
        df = pd.concat([df, new_row], ignore_index=True)
    return df

def classify_df(df):
    print('\nNow you will classify the rows in this DF on viability')
    ratings = []
    for i, r in df.iterrows():
        print(r)
        question = questionary.select(
            'How would you rate ' + r['title'],
            choices=['unusable', 'bad', 'fine', 'good', 'viral'])
        rating = question.ask()
        ratings.append(rating)
        os.system('cls')
    df['rating_class'] = ratings
    return df

def save_classified_df(df):
    cxn = mysql.connector.connect()#)
    crs = cxn.cursor()
    crs.execute("SHOW DATABASES")

    for x in crs:
        print(x)

def test(): 
    # SSH tunnel configuration
    ssh_host = 'your_ssh_host'
    ssh_user = 'your_ssh_username'
    ssh_password = 'your_ssh_password'
    ssh_port = 22

    # MySQL server configuration
    mysql_host = 'your_mysql_host'
    mysql_user = 'your_mysql_username'
    mysql_password = 'your_mysql_password'
    mysql_port = 3306

    # Create an SSH tunnel connection
    ssh_tunnel = connect(
        host=ssh_host,
        port=ssh_port,
        username=ssh_user,
        password=ssh_password,
    )

    # Create a MySQL connection through the SSH tunnel
    mysql_connection = mysql.connector.connect(
        host=mysql_host,
        port=mysql_port,
        user=mysql_user,
        password=mysql_password,
        database='your_database',
        ssh=ssh_tunnel.get_transport(),
    )

    # Perform database operations
    cursor = mysql_connection.cursor()
    cursor.execute('SELECT * FROM your_table')
    result = cursor.fetchall()
    for row in result:
        print(row)

    # Close the connections
    cursor.close()
    mysql_connection.close()
    ssh_tunnel.close()


def main():
    pages = get_viable_pages()
    print('\n', len(pages), 'found')
    df = get_pages_df(pages)
    classified_df = classify_df(df)
    print(classified_df)

save_classified_df('test')

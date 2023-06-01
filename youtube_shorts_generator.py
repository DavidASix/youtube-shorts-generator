import re
import pandas as pd
from bs4 import BeautifulSoup
import fandom
# https://fandom-py.readthedocs.io/en/latest/fandom.html

def get_viable_pages():
    fandom_type = 'fallout'
    fandom.set_wiki(fandom_type)

    viable_pages = []
    # Get a list of 10 random site pages 
    while len(viable_pages) < 2:
        # Pages are returned as a tuple like (title, page_id)
        #r_pages = [('Paul_(Fallout)', 999)]
        p = fandom.random(1)[0]
        # Pages should be long enough for a 30 second video, and should not be about game files
        try:
            page = fandom.page(p)
            output_page = {}
            # Some pages have the characters "v · d · e" for View Template, Discussion, Edit
            # The text after this delimiter can be very long with many links to other semi-related articles
            # Unfortuantely this text is captured in whatever final section appears on the page, after the scrape
            page_body = page.plain_text.split('v · d · e')[0]
            
            # Remove pages matching certain criteria 
            if 'Expansion required' in page_body or len(page_body) < 1200:
                raise ValueError('Page short')
            if page.language != 'en':
                raise ValueError('Page Not English')
            # Filter out pages with titles like 'abc.mp3' to avoid file related pages
            if re.match(r".+\..{2,}", page.title):
                raise ValueError('File Page')
            
            print('Page Suitable!')

            # Start adding to output file object
            output_page.update({'title': page.title, 'url': page.url, 'sections': page.sections, 'summary': page.summary})
            output_page['plain_text'] = page_body
            output_page['section_text'] = {}
            for s in page.sections:
                output_page['section_text'][s] = page.section(s).split('v · d · e')[0]
                    
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

            viable_pages.append(output_page)
        except Exception as e:
            print(e)
    # Return the list of viable pages
    return viable_pages

def identify_best_page(pages):
    df = pd.DataFrame({'title': [], 'length': [], 'first_section_title': [],'first_section_length': [], 'secions': [], 'images': [], 'audio': []})
    for p in pages:
        #section_concat = ''.join(v for k, v in p['section_text'].items() if k.lower() != 'references')
        #overview_length = len(p['plain_text']) - len(section_concat)
        background_length = len(p['section_text'].get('Background', ''))
        first_section_length = len(p['section_text'].get(p['sections'][0], ''))
        new_row = pd.DataFrame({
            'title': [p['title']], 
            'length': [len(p['plain_text'])], 
            'first_section_title': [p['sections'][0]],
            'first_section_length': [first_section_length], 
            'secions': [len(p['sections'])], 
            'images': [len(p['images'])],
            'audio': [len(p['audio'])]
        })
        df = pd.concat([df, new_row], ignore_index=True)
    print(df)
    # Idea's for choosing the best article:
    # Drop reference section, count sections
    # count images without icons
    # Count audio files

    # Compare total length vs concat of articles minus ref, this is the summary length
    # check background length
    #print(pages)

    
def main():
    pages = get_viable_pages()
    print('\n', len(pages), 'found')
    identify_best_page(pages)

main()

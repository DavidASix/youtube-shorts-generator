import re
from bs4 import BeautifulSoup
import fandom
# https://fandom-py.readthedocs.io/en/latest/fandom.html

def get_viable_pages():
    fandom_type = 'fallout'
    fandom.set_wiki(fandom_type)

    viable_pages = []
    # Get a list of 10 random site pages 
    # Pages are returned as a tuple like (title, page_id)
    r_pages = fandom.random(30)
    # Loop through list and find potential candidates
    for p in r_pages:
        # Pages should be long enough for a 30 second video, and should not be about game files
        # 2000 characters seems like a good minimum
        try:
            page = fandom.page(p[0])
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
            output_page['plain_text'] = ''#page_body
            output_page['section_text'] = {}
            for s in page.sections:
                output_page['section_text'][s] = ''#page.section(s).split('v · d · e')[0]
            
            output_page['images'] = []
            for i in page.images:
                if 'icon' not in i.lower():
                    output_page['images'].append(i)
        
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

            viable_pages.append(output_page)
        except Exception as e:
            print(e)
    # Return the list of viable pages
    return viable_pages

def main():
    pages = get_viable_pages()
    print('\n', len(pages), 'found')
    for p in pages: 
        print(p['url'])
        print(p['notes'])

    # Idea's for choosing the best article:
    # Drop reference section, count sections
    # count images without icons
    # Count audio files

main()

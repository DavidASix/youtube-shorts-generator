import re
import fandom
# https://fandom-py.readthedocs.io/en/latest/fandom.html

def main():
    fandom_type = 'fallout'
    fandom.set_wiki(fandom_type)

    selected_pages = []
    # Get a list of 10 random site pages 
    # Pages are returned as a tuple like (title, page_id)
    r_pages = fandom.random(10)
    #r_pages = [('IIPIT.MSG', 999)]
    # Loop through list and find potential candidates
    for p in r_pages:
        # Pages should be long enough for a 30 second video, and should not be about game files
        # 2000 characters seems like a good minimum
        try:
            page = fandom.page(p[0])
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
            
            print('---Page:', page.title, 'Actual length', len(page_body))
            print(page.url)

            s = page.sections
            for section in s:
                section_body = page.section(section).split('v · d · e')[0]
                print(section, 'length', len(section_body))
                #print(section_body)
            selected_pages.append(page)
        except Exception as e:
            print(e)
        print('\n')
    
    for p in selected_pages:
        print(p.title)
main()

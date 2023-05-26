import fandom
# https://fandom-py.readthedocs.io/en/latest/fandom.html

def main():
    fandom_type = 'fallout'
    fandom.set_wiki(fandom_type)

    # Get a list of 10 random site pages 
    # Pages are returned as a tuple like (title, page_id)
    r_pages = fandom.random(10)
    # Loop through list and find potential candidates
    for p in r_pages:
        # Pages should be long enough for a 30 second video, and should not be about game files
        # 2000 characters seems like a good minimum
        try:
            page = fandom.page(p[0])
            # Some pages have the characters "v · d · e" for View Template, Discussion, Edit
            # The text after this delimiter can be very long with many links to other semi-related articles
            # Unfortuantely this text is captured in whatever final section appears on the page, after the scrape
            length = len(page.plain_text.split('v · d · e')[0])
            print('---Page:', page.title)
            print('Actual length', length)
            print(page.url)

            s = page.sections
            for section in s:
                print(section, 'length', len(page.section(section).split('v · d · e')[0]))
        except Exception as e:
            print(e)
        print('\n')
    
main()
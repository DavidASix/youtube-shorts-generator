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
            print(page)
            print('---Page:', page.title, 'total length', len(page.plain_text))
            print(page.url)
            s = page.sections
            for section in s:
                print(section, 'length', len(page.section(section)))
        except Exception as e:
            print(e)
        print('\n')
    
main()
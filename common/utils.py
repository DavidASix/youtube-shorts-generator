def get_curly_content(content):
    # receives a string like "{my content {} {} {{nested curlies}} end content}"
    # Will return whatever string is between the opening and closing curlies
    string = content.strip()
    open_brackets = 0
    end_pos = 0
    for i, char in enumerate(string):
        open_brackets += 1 if char == '{' else 0
        open_brackets -= 1 if char == '}' else 0
        if open_brackets == 0:
            end_pos = i
            break
    return string[1:end_pos]
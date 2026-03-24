print("PARSER LOADED")

import re


def clean_text(s):

    s = s.replace("_", " ")
    s = s.replace("-", " ")
    s = s.replace(".", " ")

    s = re.sub(r"\s+", " ", s)

    return s.strip()


def parse_name(filename):

    name = filename

    # убрать расширение
    name = re.sub(r"\.(fb2|epub|pdf|djvu|docx?|mobi)(\.zip)?$", "", name, flags=re.I)

    name = clean_text(name)

    parts = name.split()

    if not parts:
        return None, filename

    # если одно слово
    if len(parts) == 1:
        return parts[0], ""

    # если 2 слова
    if len(parts) == 2:
        return parts[0], parts[1]

    # если больше
    author = parts[0]
    title = " ".join(parts[1:])

    return author, title
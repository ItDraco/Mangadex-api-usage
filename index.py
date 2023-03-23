import requests, json, os
from manga import Manga, search_manga, create_template, save_json

data = search_manga("berserk")
Berserk = Manga(manga=create_template(data["data"][1]))
a = Berserk.get_chapter_image_urls(0)
for i in a:
    print(i)
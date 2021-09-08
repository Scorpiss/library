import eel
from eel import expose
import os
import json
import numpy as np
from PIL import Image
from io import BytesIO
import base64
from mainElastic import Book, show_warn, get_all_categories
from recommendation_ai.ai_rec import get_similarity, get_cosine_book
from sys import exit

db = Book()


def add_stat(name_stat, item):
    with open("stats_log.json", "r", encoding="utf8") as f:
        data = json.load(f)
    with open("stats_log.json", "w", encoding="utf8") as f:
        if type(data[name_stat]) == list:
            data[name_stat].append(item)
        elif type(data[name_stat]) == dict:
            data[name_stat][item[0]] = data[name_stat].get(item[0], [])
            if name_stat == "viewed":
                try:
                    check_exist = np.where(np.array(data[name_stat][item[0]]) == item[1])[0][0]
                    data[name_stat][item[0]].pop(check_exist)
                except:
                    pass
            data[name_stat][item[0]].append(item[1])
        json.dump(data, f, ensure_ascii=False, indent=4)


@expose
def del_stat(name_stat, item):
    data = json.load(open("stats_log.json", "r", encoding="utf8"))
    with open("stats_log.json", "w", encoding="utf8") as f:
        if type(data[name_stat]) == list:
            data[name_stat].pop(np.where(np.array(data[name_stat]) == item)[0][0])
        elif type(data[name_stat]) == dict:
            data[name_stat][item[0]] = data[name_stat].get(item[0], [])
            data[name_stat][item[0]].pop(np.where(np.array(data[name_stat][item[0]]) == item[1])[0][0])
        json.dump(data, f, ensure_ascii=False, indent=4)


@expose
def get_stat(what="all"):
    data = json.load(open("stats_log.json", "r", encoding="utf8"))
    if what == "all":
        return data
    else:
        return data[what]


@expose
def check_favorite(author, title):
    data = get_stat("favorite")
    try:
        check = np.where(np.array(data) == [author, title])[0][0]
        return True
    except:
        return False


@expose
def stat_add(name_stat, item): add_stat(name_stat, item)


@expose
def get_viewed_books():
    with open("stats_log.json", "r", encoding="utf8") as f:
        data = json.load(f)
        books = data["viewed"]["All"]
        clear_all = []
        for x in books:
            if not x in clear_all:
                clear_all.append(x)
        return clear_all[-5:][::-1]


@expose
def all_categories(): return get_all_categories()


@expose
def random_book_category(category): return db.get_random_book_category(category)


@expose
def search_book(query):
    books_author = db.author_books(query)
    books_title = db.find_book(query)
    if books_author != [] or books_title != []:
        add_stat("search", query)
    return [books_author, books_title]


@expose
def info_book(author, title): return db.info_book(author, title)


@expose
def get_book_id(id_): return db.get_book_id(id_)


@expose
def get_text(author, title): return db.get_book(author, title)


@expose
def open_pdf(author, title, category):
    if not os.path.isfile(f"web/books_pdf/{author} [[]] {title.replace('?', '')}.pdf"):
        open(f"web/books_pdf/{author} [[]] {title.replace('?', '')}.pdf", "wb").write(
            db.get_pdf_bytes_book(author, title)
        )

    add_stat("viewed", (category, (author, title)))
    add_stat("viewed", ("All", (author, title)))
    cosine_stat = get_stat("books_viewed_cosine")
    if len(cosine_stat) >= 11:
        mean_cosines = np.mean(cosine_stat)
        set_stat("books_viewed_cosine", [mean_cosines])
    try:
        add_stat("books_viewed_cosine", get_cosine_book(author, title))
    except:
        print("Книги нет в векторизированных")
    return os.path.abspath(f"web/books_pdf/{author} [[]] {title.replace('?', '')}.pdf")


@expose
def add_book(author, title, text, category, cover=None):
    text = text.encode("utf-8").decode("utf-8")
    try:
        if cover != None:
            image = Image.open(BytesIO(base64.b64decode(cover.replace("data:image/jpeg;base64,", ""))))
            image.thumbnail((190, 288), Image.ANTIALIAS)
            image = db.get_cover_bytes(image)
        else:
            image = None
        res = db.add_book(author=author, title=title, category=category, text=text, cover_book=image)
        if not np.where(np.array(get_stat("user_books")) == [author, title])[0] and not res:
            add_stat("user_books", [author, title])
        return res
    except:
        import traceback
        print(traceback.format_exc())
        return "ERROR ADD BOOK"


@expose
def del_book(author, title, category):
    try:
        del_stat("user_books", [author, title])
        del_stat("viewed", (category, (author, title)))
        del_stat("viewed", ("All", (author, title)))
        if check_favorite(author, title):
            del_stat("favorite", (author, title))
        db.del_book(author, title)

        return True
    except:
        import traceback
        print(traceback.format_exc())
        return False


@expose
def books_category_paginated(category, page):
    return db.get_category_book(category, page, 25)


@expose
def get_count_category(category):
    return db.count_category(category)


@expose
def get_recommendation(author, title, count=5):
    result = []
    try:
        for author, title in get_similarity(author, title, count):
            result.append(info_book(author, title))
        return result
    except:
        return None


@expose
def average_cosine_rec(count=10):
    books_cosine = get_stat("books_viewed_cosine")
    if len(books_cosine) < 1:
        return []
    result = []
    for author, title in get_similarity(cosine=np.mean(books_cosine), count=count):
        result.append(info_book(author, title))
    return result


@expose
def set_stat(stat_name, new_data):
    data = get_stat("all")
    with open("stats_log.json", "w", encoding="utf8") as f:
        if type(stat_name) == str:
            data[stat_name] = new_data
        elif type(stat_name) == list:
            way_str = "data"
            for stat in stat_name:
                way_str += f"['{stat}']"
            way_str += " = new_data"
            exec(way_str, globals(), locals())
        json.dump(data, f, ensure_ascii=False, indent=4)


@expose
def fast_search(query):
    search_result = db.similarity_search(query)
    return {"authors": search_result[0][:5], "titles": search_result[1][:5]}


@expose
def get_user_book_info():
    books = list(set([(x[0], x[1]) for x in get_stat("user_books")]))
    books_info = []
    for book in books:
        books_info.append(db.info_book(book[0], book[1]))
    return books_info


def create_stats():
    if not os.path.isfile("stats_log.json"):
        with open("stats_log.json", "w", encoding="utf8") as f:
            data = {
                "viewed": {"All": []},
                "favorite": [],
                "search": [],
                "books_viewed_cosine": [],
                "user_books": []
            }
            json.dump(data, f, ensure_ascii=False, indent=4)
    try:
        check = json.load(open("stats_log.json", "r", encoding="utf8"))
    except json.decoder.JSONDecodeError:
        with open("stats_log.json", "w", encoding="utf8") as f:
            data = {
                "viewed": {"All": []},
                "favorite": [],
                "search": [],
                "books_viewed_cosine": [],
                "user_books": []
            }
            json.dump(data, f, ensure_ascii=False, indent=4)


create_stats()


def clear_books():
    if not os.path.isdir("web/books_pdf"):
        os.mkdir("web/books_pdf")
    favorites = [f"{book[0]} [[]] {book[1]}.pdf".replace('?', '') for book in get_stat("favorite")]
    for book in os.listdir("web/books_pdf/"):
        if book not in favorites:
            os.remove(f"web/books_pdf/{book}")


clear_books()

options = {
    'mode': "chrome",
    'host': "localhost",
    'port': 7521,
    'size': (1600, 1000)
}

if __name__ == '__main__':
    eel.init('web')
    eel.browsers.set_path("chrome", os.path.abspath("chrome-win\\chrome.exe"))
    eel.start("index.html", options=options, suppress_error=True, cmdline_args=['--no-experiments', '--incognito'],
              disable_cache=True, close_callback=None)


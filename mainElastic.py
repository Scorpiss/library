from PIL import ImageDraw, Image, ImageFont
from io import BytesIO
import os
import base64
from fpdf import FPDF
from random import getrandbits
from elasticConnector import es, show_warn


def hex2bytes(hex_: str):
    return bytes.fromhex(hex_)


def get_all_categories():
    return ['Детективы и Триллеры', 'Детское', 'Драматургия', 'Любовные романы',
            'Поэзия', 'Приключения', 'Проза', 'Фантастика', 'Юмор']


class Book:
    def __init__(self):
        self.es = es

    def generate_cover(self, book_name, author, category_name, color_cover="#c8c8c8", size=(190, 288)):
        def break_fix(text, width, font, draw):
            if not text:
                return
            lo = 0
            hi = len(text)
            while lo < hi:
                mid = (lo + hi + 1) // 2
                t = text[:mid]
                w, h = draw.textsize(t, font=font)
                if w <= width:
                    lo = mid
                else:
                    hi = mid - 1
            t = text[:lo]
            w, h = draw.textsize(t, font=font)
            yield t, w, h
            yield from break_fix(text[lo:], width, font, draw)

        def fit_text(img, text, color, font):
            width = img.size[0] - 2
            draw = ImageDraw.Draw(img)
            pieces = list(break_fix(text, width, font, draw))
            height = sum(p[2] for p in pieces)
            if height > img.size[1]:
                raise ValueError("text doesn't fit")
            y = (img.size[1] - height) // 2
            for t, w, h in pieces:
                x = (img.size[0] - w) // 2
                draw.text((x, y), t, font=font, fill=color)
                y += h

        def get_complementary(color):
            color = color[1:]
            color = int(color, 16)
            comp_color = 0xFFFFFF ^ color
            comp_color = "#%06X" % comp_color
            return comp_color

        color_text = get_complementary(color_cover)

        W, H = size
        img = Image.new("RGB", (W, H), color=color_cover)
        fit_text(img, book_name, color_text, ImageFont.truetype("impact.ttf", 17))

        draw = ImageDraw.Draw(img)

        # Имя автора
        font = ImageFont.truetype(os.path.abspath(r"fonts\Raleway-Regular.ttf"), 15)
        w, h = draw.textsize(author, font=font)
        draw.text(((W - w) - 6, (H - h) - 6), author, font=font, fill=color_text)

        # Название категории
        font = ImageFont.truetype(os.path.abspath(r"fonts\Raleway-Bold.ttf"), 12)
        w, h = draw.textsize(category_name, font=font)
        draw.text((6, 6), category_name, font=font, fill=color_text)

        return img

    def text2pdf_bytes(self, text):
        pdf = FPDF()
        pdf.add_page()
        pdf.add_font("ArialAll", "", r"fonts\ARIALUNI.TTF", uni=True)
        pdf.set_font("ArialAll", size=14)
        pdf.set_top_margin(10)
        text_clear = bytes(text, "utf8").decode("utf8", "ignore")

        pdf.multi_cell(190, 5, txt=text_clear, align="L")
        pdf.output("default.pdf")
        with open("default.pdf", "rb") as f:
            bytes_ = f.read()
        os.remove("default.pdf")
        return bytes_

    def add_book(self, author, title, category, color="#c8c8c8", cover_book=None, text=None, text_txt_path=None):
        if cover_book == None:
            cover_book = self.get_cover_bytes(self.generate_cover(title, author, category, color))
        else:
            try:
                image = Image.open(cover_book)
                image.thumbnail((190, 288), Image.ANTIALIAS)
                cover_book = self.get_cover_bytes(image)
            except FileNotFoundError:
                cover_book = cover_book
            except:
                cover_book = self.get_cover_bytes(self.generate_cover(title, author, category, color))
        if text_txt_path and not text:
            text = open(text_txt_path, "r", encoding="utf8").read()

        print("Start generate data")
        try:
            pdf_ = self.text2pdf_bytes(text).hex()
        except:
            import traceback
            print(traceback.format_exc())
            return "ERROR: INVALID TEXT"
        data = {
            "author": author,
            "author_lower": author.lower(),
            "title": title,
            "title_lower": title.lower(),
            "category": category,
            "cover": cover_book.hex(),
            "pdf": pdf_
        }

        check_exist = self.es.multi_search([{"author_lower": author.lower()},
                                            {"title_lower": title.lower()}])["hits"]["hits"]
        if check_exist != []:
            new_id = check_exist[0]["_id"]
            self.es.delete(id_=new_id)
        else:
            new_id = self.es.count({})["count"]
        print("Book added")
        self.es.create(id_=new_id, body_=data)

        return False

    def get_pdf_bytes_book(self, author, title):
        return hex2bytes(self.es.multi_search([
            {"author": author},
            {"title": title}
        ])["hits"]["hits"][0]["_source"]["pdf"])

    def info_book(self, author, title, id_=None):
        try:
            if id_ != None:
                res = self.es.get(id_)["_source"]
                author, title, category, cover = res["author"], res["title"], res["category"], res["cover"]
            else:
                res = \
                    self.es.multi_search([{"author": author}, {"title": title}], ["_id", "category", "cover"])["hits"][
                        "hits"][0]
                id_, category, cover = res["_id"], res["_source"]["category"], res["_source"]["cover"]
            return {"author": author,
                    "title": title,
                    "category": category,
                    "cover_base64": self.get_cover_base64(hex2bytes(cover)),
                    "id": id_
                    }
        except:
            return None

    def get_book(self, author, title):
        try:
            return self.es.multi_search([{"author_lower": author.lower()},
                                         {"title_lower": title.lower()}])["hits"]["hits"][0]["_source"]
        except:
            return None

    def find_book(self, title):
        try:
            return [x["_source"]["author"] for x in
                    self.es.search({"query": {"match": {"title_lower": title.lower()}}, "_source": ["author"]})["hits"][
                        "hits"]]
        except:
            return None

    def author_books(self, author):
        try:
            return [x["_source"]["title"] for x in
                    self.es.search({"query": {"match": {"author_lower": author.lower()}}, "_source": ["title"]})[
                        "hits"]["hits"]]
        except:
            return None

    def similarity_search(self, query):
        try:
            query = f'*{"*".join(query.lower())}*'.split()

            authors = self.es.search(body_={"query": {"bool": {"must":
                                                                   [{"wildcard": {"author_lower": q_a}} for q_a in
                                                                    query]
                                                               }},
                                            "_source": ["author"]}
                                     )
            authors = [x["_source"]["author"] for x in authors["hits"]["hits"]] if authors else []

            titles = self.es.search(body_={"query": {"bool": {"must":
                                                                  [{"wildcard": {"title_lower": q_a}} for q_a in query]
                                                              }},
                                           "_source": ["title"]}
                                    )
            titles = [x["_source"]["title"] for x in titles["hits"]["hits"]] if titles else []

            return list(set(authors)), list(set(titles))
        except:
            import traceback
            return [], []

    def get_random_book_category(self, category, count=5):
        book = self.es.search(body_={"query": {"function_score":
                                                   {"query": {"match": {"category": category}},
                                                    "functions": [{"random_score": {"seed": getrandbits(50)}}]}},
                                     "_source": ["_id"], "size": count})["hits"]["hits"]
        return [self.get_book_id(id_["_id"]) for id_ in book]

    def get_cover_bytes(self, image: Image = None, author=None, title=None):
        if author == None:
            img = image
            img_bytes = BytesIO()
            img.save(img_bytes, format="PNG")
            img_bytes = img_bytes.getvalue()
        else:
            img = Image.open(self.info_book(author, title)["cover_bytes"])
            img_bytes = BytesIO()
            img.save(img_bytes, format="PNG")
            img_bytes = img_bytes.getvalue()

        return img_bytes

    def get_cover_base64(self, bytes_):
        return base64.b64encode(bytes_).decode("utf8")

    def get_book_id(self, id_):
        return self.info_book("", "", id_)

    def del_book(self, author, title):
        id_ = int(self.es.multi_search([{"author": author}, {"title": title}], ["_id"])["hits"]["hits"][0]["_id"])
        self.es.delete(id_=id_)
        return True

    def get_category_book(self, category, page, page_count):
        get_books = [x["_id"] for x in self.es.search(body_={"query": {"match": {"category": category}},
                                                             "from": int(page_count * page),
                                                             "size": int(page_count),
                                                             "_source": ["_id"]})["hits"]["hits"]]
        result = []
        for id_ in get_books:
            result.append(self.get_book_id(id_))
        return result

    def count_category(self, category):
        return self.es.count({"query": {"match": {"category": category}}})["count"]

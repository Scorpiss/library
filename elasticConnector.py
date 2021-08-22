from elasticsearch import Elasticsearch, exceptions
from ast import literal_eval


def show_warn(title, msg):
    import tkinter as tk
    from tkinter import messagebox
    tk.Tk().withdraw()
    tk.messagebox.showwarning(title, msg)
    exit()


class CustomElastic:
    def __init__(self, index, kwargs):
        self.index = index
        self.es = Elasticsearch(**kwargs)
        if not self.ping_test():
            show_warn("Ошибка подключения", "При подключении к базе данных произошла ошибка")
            return

    def ping_test(self):
        return self.es.ping()

    def index(self, body_):
        return self.es.index(index=self.index, body=body_)

    def search(self, body_):
        result = self.es.search(index=self.index, body=body_)
        if not result["hits"]["hits"]:
            return False
        else:
            return result

    def delete(self, id_):
        return self.es.delete(index=self.index, id=id_)

    def count(self, body_):
        return self.es.count(index=self.index, body=body_)

    def create(self, id_, body_):
        return self.es.create(index=self.index, id=id_, body=body_)

    def get(self, id_):
        return self.es.get(index=self.index, id=id_)

    def multi_search(self, query_match: list, return_fields: list = None):
        if return_fields == None:
            return self.es.search(index=self.index, body={"query": {"bool": {"must":
                                                                                 [{"match": x} for x in query_match]
                                                                             }}})
        else:
            return self.es.search(index=self.index,
                                  body={"query": {"bool": {"must": [{"match": x} for x in query_match]}},
                                        "_source": return_fields})

    def close(self):
        self.es.close()


exec(bytes.fromhex("636f6e6e5f61726773203d207b0a2020202022686f7374223a2062797465732e66726f6d6865782827373336313665363137343631366532653732373527292e6465636f646528227574663822292c0a2020202022706f7274223a20696e742862797465732e66726f6d6865782827333733353332333227292e6465636f64652822757466382229292c0a2020202022687474705f61757468223a206c69746572616c5f6576616c2862797465732e66726f6d68657828273562323237353733363537323232326332303232373537333635373235663631373037303232356427292e6465636f64652822757466382229290a7d").decode("utf8"), locals(), globals())
es = CustomElastic("library", conn_args)
es_matrix = CustomElastic("books_matrix", conn_args)

# download latest amiibo data and merge to amiibo_data.csv


from urllib.request import urlopen
import json
import os
import csv

class Amiibo:
    def __init__(self):
        self.id = None
        self.name_en = None
        self.name_cn = None

class Game:
    def __init__(self):
        self.id = None
        self.parent_id = None
        self.name_en = None
        self.name_cn = None
        self.order = None

class Link:
    def __init__(self):
        self.game_id = None
        self.amiibo_id = None
        self.note_en = None
        self.note_cn = None



def get_prorject_directory():
    return os.path.abspath(os.path.dirname(__file__)+"/../")


def fetch_amiibo_from_api():
    conn = urlopen("https://www.amiiboapi.com/api/amiibo/")
    body = json.loads(conn.read())
    amiibos = list()
    for ami in body["amiibo"]: 
        amiibo = Amiibo()
        amiibo.id = ami["head"] + ami["tail"]
        amiibo.name_en = ami["name"]
        amiibos.append(amiibo)
    return amiibos


def read_amiibo_from_csv():
    csv_file = get_prorject_directory() + "/data/amiidb_amiibo.csv"
    if not os.path.exists(csv_file):
        return list()
    amiibos = list()
    with open(csv_file, "r", encoding="utf8") as f:
        for r in csv.reader(f):
            amiibo = Amiibo()
            amiibo.id = r[0]
            amiibo.name_en = r[1]
            amiibo.name_cn = r[2]
            amiibos.append(amiibo)
    
    return amiibos


def write_amiibo_to_csv(amiibos):
    csv_file = get_prorject_directory() + "/data/amiidb_amiibo.csv"
    with open(csv_file, "w", encoding="utf8", newline="") as f:
        w = csv.writer(f)
        for amiibo in amiibos:
            r = list()
            r.append(amiibo.id)
            r.append(amiibo.name_en)
            r.append(amiibo.name_cn)
            w.writerow(r)


def merge_amiibo(amiibos_csv, amiibos_api):
    amiibos_merged = dict()
    for amiibo in amiibos_csv:
        amiibos_merged[amiibo.id] = amiibo

    for amiibo in amiibos_api:
        if amiibos_merged.get(amiibo.id) == None:
            amiibos_merged[amiibo.id] = amiibo
            print("Found new amiibo: [%s] %s " % (amiibo.id, amiibo.name_en))
    amiibos = list()
    for k in amiibos_merged:
        amiibos.append(amiibos_merged[k])
    return amiibos

def gen_amiibo_data_c_file(amiibos):
    c_file = get_prorject_directory() + "/application/src/amiidb/db_amiibo.c"
    with open(c_file, "w+", newline="\n", encoding="utf8") as f:
        f.write('#include "db_header.h"\n')
        f.write('const db_amiibo_t amiibo_list[] = {\n')
        for amiibo in amiibos:

            f.write('{0x%s, 0x%s, "%s", "%s"}, \n' % 
                    (amiibo.id[0:8], amiibo.id[8:16], amiibo.name_en, 
             amiibo.name_cn))
        f.write("{0, 0, 0, 0}\n")
        f.write("};\n")


def read_games_from_csv():
    csv_file = get_prorject_directory() + "/data/amiidb_game.csv"
    if not os.path.exists(csv_file):
        return list()
    games = list()
    with open(csv_file, "r", encoding="utf8") as f:
        for r in csv.reader(f):
            game = Game()
            game.id = r[0]
            game.parent_id = r[1]
            game.name_en = r[2]
            game.name_cn = r[3]
            game.order = r[4]
            games.append(game)
    return games


def read_link_from_csv():
    csv_file = get_prorject_directory() + "/data/amiidb_link.csv"
    if not os.path.exists(csv_file):
        return list()
    links = list()
    with open(csv_file, "r", encoding="utf8") as f:
        for r in csv.reader(f):
            link = Link()
            link.game_id = r[0]
            link.amiibo_id = r[1]
            link.note_en = r[2]
            link.note_cn = r[3]
            links.append(link)
    return links


def count_game_links(games, links, game_id):

    count = 0
    for link in links:
        if link.game_id == game_id:
            count = count + 1
    for game in games:
        if game.parent_id == game_id:
            count = count + count_game_links(games, links, game.id)

    return count


def gen_amiibo_link_c_file(links):
    c_file = get_prorject_directory() + "/application/src/amiidb/db_link.c"
    with open(c_file, "w+", newline="\n", encoding="utf8") as f:
        f.write('#include "db_header.h"\n')
        f.write('const db_link_t link_list[] = {\n')
        for link in links:

            f.write('{%s, 0x%s, 0x%s, "%s", "%s"}, \n' % 
                    (link.game_id, link.amiibo_id[0:8], link.amiibo_id[8:16], link.note_en, 
             link.note_cn))
        f.write("{0, 0, 0, 0, 0}\n")
        f.write("};\n")

def gen_amiibo_game_c_file(games, links):
    c_file = get_prorject_directory() + "/application/src/amiidb/db_game.c"
    with open(c_file, "w+", newline="\n", encoding="utf8") as f:
        f.write('#include "db_header.h"\n')
        f.write('const db_game_t game_list[] = {\n')
        for game in games:
            f.write('{%s, %s, "%s", "%s", %s, %s}, \n' % 
                    (game.id, game.parent_id, game.name_en, 
             game.name_cn, game.order, count_game_links( games, links, game.id)))
        f.write("{0, 0, 0, 0, 0}\n")
        f.write("};\n")    
    
def gen_other_link(amiibos, links):
    linked_amiibo_ids = set()
    new_link = list()
    for link in links:
        linked_amiibo_ids.add(link.amiibo_id)
    for amiibo in amiibos:
        if amiibo.id not in linked_amiibo_ids:
            link = Link()
            link.game_id = "255" # other
            link.amiibo_id = amiibo.id
            link.note_en = ""
            link.note_cn = ""
            new_link.append(link)
            print("uncategorized amiibo (%s, %s)" % (link.amiibo_id, amiibo.name_en))
    if len(new_link) > 0:
        print("add %d uncategoried amiibo to other." %(len(new_link)))
    for link in new_link:
        links.append(link)
    return links


amiibos_api = fetch_amiibo_from_api()
amiibos_csv = read_amiibo_from_csv()
amiibos_merged = merge_amiibo(amiibos_csv, amiibos_api)
write_amiibo_to_csv(amiibos_merged)
print("Found %d amiibo records." % len(amiibos_merged))
gen_amiibo_data_c_file(amiibos_merged)
games = read_games_from_csv()
links = read_link_from_csv()
links = gen_other_link(amiibos_merged, links)
gen_amiibo_game_c_file(games, links)
gen_amiibo_link_c_file(links)


import json
from tqdm import tqdm

def chebychev_distance(m1, m2):
    return max(abs(m1[0] - m2[0]), abs(m1[1] - m2[1]))

def movestr(move):
    return f"{move[2].upper()} {move[0]}, {move[1]}"

def dereflect(sequence):
    if sequence[0][:2] == [9, 9]:
        if len(sequence) == 1: return [[9, 9, "b"]]
        while sequence[1][0] > 9 or sequence[1][1] > 9:
            sequence = [[m[1], 18-m[0], m[2]] for m in sequence]
    else:
        while sequence[0][0] > 9 or sequence[0][1] > 9:
            sequence = [[m[1], 18-m[0], m[2]] for m in sequence]
    for m in sequence:
        if m[0] > m[1]:
            sequence = [[m[1], m[0], m[2]] for m in sequence]
            break
        if m[1] > m[0]:
            break
    if sequence[0][2] == "w":
        sequence = [[m[0], m[1], "w" if m[2] == "b" else "b"] for m in sequence]
    return [[m[0] + 1, m[1] + 1, m[2]] for m in sequence]

def setup_joseki(game, threshold=5):
    joseki = [[], [], [], [], []] # One for each corner + nonjoseki
    for move in game["moves"][:4]:
        if len(joseki[0]) == 0 and chebychev_distance(move, [0, 0]) <= threshold:
            joseki[0].append(move)
        if len(joseki[1]) == 0 and chebychev_distance(move, [18, 0]) <= threshold:
            joseki[1].append(move)
        if len(joseki[2]) == 0 and chebychev_distance(move, [0, 18]) <= threshold:
            joseki[2].append(move)
        if len(joseki[3]) == 0 and chebychev_distance(move, [18, 18]) <= threshold:
            joseki[3].append(move)
    if any(len(j) == 0 for j in joseki[:4]):
        raise ValueError("Nontraditional Game")
    return joseki

def is_joseki(joseki, min_dists, adding_thresholds):
    min_dist = min(min_dists)
    # If a move is equidistant to multiple joseki, it's non-joseki
    if min_dists.count(min_dist) > 1:
        return False
    # If a joseki has at least 20 stones, it can't have anything added
    idx = min_dists.index(min_dist)
    if len(joseki[idx]) >= 20:
        return False
    # If the move is out of range, it can't be added
    a = [d for t, d in adding_thresholds if t <= len(joseki[idx])][-1]
    if min_dist > a:
        return False
    # If the move is already in the sequence, assume a ko fight
    if min_dist == 0:
        return False
    return True

def get_joseki(game, initial_threshold=7, adding_thresholds=[(0, 6), (6, 4), (10, 3)]):
    joseki = setup_joseki(game, initial_threshold)
    for move in game["moves"][4:]:
        min_dists = [min((chebychev_distance(m, move) for m in j), default=100) for j in joseki]
        if not is_joseki(joseki, min_dists, adding_thresholds):
            joseki[4].append(move)
        else:
            joseki[min_dists.index(min(min_dists))].append(move)
        if min(map(len, joseki)) >= 20 or len(joseki[4]) >= 50:
            break
    return joseki[:4]

def get_all_joseki(games):
    joseki = []
    for game in games:
        try:
            new_joseki = get_joseki(game)
            joseki += list(map(dereflect, new_joseki))
        except ValueError:
            continue
    return joseki

def read_file(fname):
    with open(fname, 'r') as F:
        lines = F.readlines()
        data = [json.loads(line) for line in lines] if len(lines) > 1 else json.loads(lines[0])
        return data

def filter_games(games):
    return [
        game for game in games
        if game["start_time"] >= 1609459200
        and game["width"] == 19
        and game["height"] == 19
        and game["handicap"] == 0
        and "rank" in game["players"]["black"]
        and game["players"]["black"]["rank"] is not None
        and "rank" in game["players"]["white"]
        and game["players"]["white"]["rank"] is not None
        and 50 >= game["players"]["black"]["rank"] >= 25
        and 50 >= game["players"]["white"]["rank"] >= 25
    ]

def process_games(games):
    return [{
        "moves": [
            [m[0], m[1], "b" if i%2 == 0 else "w"] 
            for i, m in enumerate(game["moves"])
        ]
    } for game in games]

def add_to_tree(joseki, tree):
    if len(joseki) == 0:
        return
    ms = movestr(joseki[0])
    if ms not in tree:
        tree[ms] = {
            "freq": 0,
            "move": joseki[0],
            "tree": {}
        }
    tree[ms]["freq"] += 1
    add_to_tree(joseki[1:], tree[ms]["tree"])

def get_joseki_tree(joseki):
    tree = {}
    for j in joseki:
        add_to_tree(j, tree)
    return tree

def prune_joseki_tree(tree, min_freq=10):
    for k, v in list(tree.items()):
        if v["freq"] < min_freq:
            del tree[k]
        elif "tree" not in v:
            continue
        elif len(v["tree"]) == 0:
            del v["tree"]
        else:
            prune_joseki_tree(v["tree"], min_freq)
    return tree

def display_joseki_tree(tree, depth=0):
    s = ""
    branches = sorted(tree.values(), key=lambda v: v["freq"], reverse=True)
    for b in branches:
        s += "\t" * depth + f"- {movestr(b['move'])}: {b['freq']}\n"
        if "tree" in b:
            s += display_joseki_tree(b["tree"], depth+1)
    return s

def sgfify(move, comment):
    a = "abcdefghijklmnopqrstuvwxyz"
    return f";{move[2].upper()}[{a[19-move[0]]}{a[move[1]-1]}]C[{comment}]"

def make_sgf(tree, setup=True):
    sgf = ""
    if setup:
        sgf += "(;GM[1]FF[4]CA[UTF-8]AP[Toast's Joseki Scraper]KM[6.5]SZ[19]"
        sgf += make_sgf(tree, False)
    else:
        if len(tree) > 1:
            for branch in sorted(tree.values(), key=lambda x: x["freq"], reverse=True):
                sgf += "("
                sgf += sgfify(branch["move"], "Count: " + str(branch["freq"]))
                if "tree" in branch:
                    sgf += make_sgf(branch["tree"], False)
                sgf += ")"
        elif len(tree) == 1:
            branch = [*tree.values()][0]
            sgf = sgfify(branch["move"], "Count: " + str(branch["freq"]))
            if "tree" in branch:
                sgf += make_sgf(branch["tree"], False)
            return sgf
        else:
            return ""
    if setup:
        sgf += ")"
    return sgf

def save_file(data, fname):
    with open(fname, 'w') as F:
        F.write(data)

def bulk_game_process(infname, outfname):
    processed = []
    with open(infname, 'r') as F:
        for line in tqdm(F, unit="games", desc="Processing Games"):
            game = json.loads(line)
            if len(filter_games([game])) > 0:
                processed.append(process_games([game])[0])
    with open(outfname, 'w') as F:
        F.write(json.dumps(processed))

if __name__ == "__main__":
    # Bulk process and skip to loading games step for large files
    # Slower for small files
    # bulk_game_process("../ogs2021/ogs_games_2013_to_2021-08.json", "./processed.json")
    print("Reading raw games")
    games = read_file("./sample-100k.json")
    print("Filtering games")
    games = filter_games(games)
    print("Processing games")
    games = process_games(games)
    save_file(json.dumps(games), "./processed.json")
    print("Loading games")
    games = read_file("./processed.json")
    print("Finding joseki")
    joseki = get_all_joseki(tqdm(games))
    print("Organizing joseki")
    tree = get_joseki_tree(tqdm(joseki))
    save_file(json.dumps(tree), "./raw_tree.json")
    print("Pruning joseki")
    tree = read_file("./raw_tree.json")
    tree = prune_joseki_tree(tree, len(games) / 100)
    save_file(json.dumps(tree), "./tree.json")
    print("Outputting")
    tree = read_file("./tree.json")
    output = make_sgf(tree)
    save_file(output, "./OGS-joseki.sgf")

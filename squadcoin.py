from flask import Flask, request
from Crypto.Random import get_random_bytes
import hashlib
import string
import time
import random
app = Flask(__name__)

HASH_LENGTH = 5
HASH_MASK = 0x3ffffffff
SEED_LENGTH = 8

def hex_representation(bytestring):
    return " ".join([hex(b)[2:].zfill(2) for b in bytestring])

class Hasher:
    def __init__(self):
        pass

    def make_hash(self, seed, word):
        return hashlib.md5(seed + word.encode('ascii')).digest()[:HASH_LENGTH]

    def get_state_from_int(self, time_seed):
        random.seed(time_seed)
        retval = {}
        retval["seed"] = random.randbytes(SEED_LENGTH)
        retval["hash"] = random.randbytes(HASH_LENGTH)
        retval["time"] = time_seed
        return retval

    def get_current_state(self):
        with open('seed_time.txt', 'r') as saved_hash:
            seed_time = saved_hash.readline().strip()
        with open('solved_hashes.txt', 'r') as solved_times:
            solved = [line.strip() for line in solved_times]
        if seed_time in solved:
            seed_time = time.time_ns()
            print("Changing hash!")
            with open('seed_time.txt','w') as saved_hash:
                saved_hash.write(str(seed_time))
        else:
            seed_time = int(seed_time)
        return self.get_state_from_int(seed_time)

    def mask(self, word):
        return int.from_bytes(word, "big") & HASH_MASK

    def validate(self, some_input):
        state = self.get_current_state()
        return {
            "success":(self.mask(self.make_hash(state['seed'], some_input))
             == self.mask(state['hash'])),
             "state":state
        }

class Coins:
    def __init__(self):
        self.users = {}

    def add_coin(self, username, word, state):
        with open("database.csv","a+") as database:
            database.write(f"{username},{word},{state['hash']}"+
                f",{state['seed']}\n")
        with open("solved_hashes.txt","a+") as hashfile:
            hashfile.write(str(state["time"]) + "\n")

    def sanitise(self, name):
        return "".join([s for s in name.lower() if s in string.ascii_lowercase])

@app.route('/ledger')
def get_ledger():
    db = []
    with open("database.csv","r") as database:
        for line in database:
            if line.strip():
                db.append(line.strip().split(","))
    users = {}
    for line in db[1:]:
        user = coins.sanitise(line[0])
        if user not in users:
            users[user] = 1
        else:
            users[user] += 1
    retval = "<table><tr><th>User</th><th>Coins</th>"
    for user in users:
        retval += f"<tr><td>{user}</td><td>{users[user]}</td></tr>"
    retval += "</table>"
    return retval


@app.route('/', methods=["GET","POST"])
def hello_world():
    message = "<p> Have a guess! </p>"
    state = hasher.get_current_state()
    if request.method == "POST":
        token = hasher.validate(request.form['word'])
        if token["success"]:
            coins.add_coin(request.form['username'], request.form['word'],
                           token["state"])
            message = "<p> Good job! </p>"
        else:
            message = f"""<p> That's not right! You hashed to:
                {hasher.make_hash(state['seed'],request.form['word'])}</p>"""
    message += "<p> See the <a href='/ledger'>ledger</a></p>"
    return f"""<h1>Squad Coins!</h1><p>So you wanna mine a squadcoin? I will
        give you some hash H, and some seed. You have to send me some message M
        such that MD5(seed || M)[:5] = H. To make it easier, though, I will mask
        off the first six bits of your hash and the original H.</p>
        <p>The hash is: {hex_representation(state['hash'])}</p>
        <p> The prepended random bytes are: {hex_representation(state['seed'])}
        </p>
        <p> {message} <form action="/" method="post"> <p>What is a word that
        hashes to this value?</p>
        <input id="word" name="word" type="text"></input>
        <p>What is your username?</p> <input type="text" name="username"
        id="username"></input><input type="submit"></input></form>"""

hasher = Hasher()
coins = Coins()

from flask import Flask, request
from Crypto.Random import get_random_bytes
import hashlib
import string
import time
import random
import binascii
app = Flask(__name__)

NUM_BITS = 34
HASH_MASK = int("1"*NUM_BITS, 2)
HASH_LENGTH = NUM_BITS//8 + bool(NUM_BITS%8)
SEED_LENGTH = 8

BAD_HEX_ERR = 'bad hex value'

def hex_representation(bytestring):
    return " ".join([hex(b)[2:].zfill(2) for b in bytestring])

class Hasher:
    def __init__(self):
        pass

    def make_hash(self, seed, hexword):
        try:
            return hashlib.md5(seed + binascii.unhexlify(hexword)).digest()
        except binascii.Error:
            return BAD_HEX_ERR

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
        inputhash = self.make_hash(state['seed'], some_input)
        if inputhash == BAD_HEX_ERR:
            return {
                "success": False,
                "state":state
            }
        return {
            "success": self.mask(inputhash) == self.mask(state['hash']),
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

@app.route("/api")
def api():
    state = hasher.get_current_state()
    state.update({"bitmask":NUM_BITS})
    state["seed"] = hex(int.from_bytes(state["seed"], "big"))[2:]
    state["hash"] = hex(int.from_bytes(state["hash"], "big"))[2:]
    return f"{state}"

@app.route("/index.css")
def css():
    with open("index.css","r") as cssfile:
        retval = cssfile.read()
    return retval

@app.route("/update_log")
def get_updates():
    retval = "<ul>"
    with open("updates.txt","r") as updatelog:
        for line in updatelog:
            retval += f"<li>{line}</li>"
    retval += "</ul>"
    return retval

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
    return f"""<link type="text/css" rel="stylesheet" href="index.css">
        <div align="center">
        <h1>Squad Coins!</h1><p>So you wanna mine a squadcoin? I will
        give you some hash H, and some seed.<br> You have to send me some message M
        (encoded in hex) such that MD5(seed || M) matches H in the final
        {NUM_BITS} bits.</p><br><br>
        <p>The hash is: {hex_representation(state['hash'])}</p>
        <p> The prepended random bytes are: {hex_representation(state['seed'])}
        </p>
         {message} <br><form action="/" method="post"> <p>What is a hex value
        that hashes to this value?</p>
        <input id="word" name="word" type="text"></input>
        <p>What is your username?</p> <input type="text" name="username"
        id="username"></input><input type="submit"></input></form>

        <a href="https://github.com/uqcybersquad/squadcoin">Github</a></div>"""

hasher = Hasher()
coins = Coins()

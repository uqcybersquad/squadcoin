from flask import Flask, request
from Crypto.Random import get_random_bytes
import hashlib
import string
app = Flask(__name__)

HASH_LENGTH = 4

class Hasher:
    def __init__(self):
        self.refresh()

    def make_hash(self, some_input):
        return hashlib.md5(self.seed + some_input.encode()).digest()[:HASH_LENGTH]

    def get_seed(self):
        return " ".join([hex(b)[2:] for b in self.seed])

    def get_current_hash(self):
        return " ".join([hex(b)[2:] for b in self.hash])

    def refresh(self):
        self.seed = get_random_bytes(8)
        self.hash = get_random_bytes(HASH_LENGTH)

    def validate(self, some_input):
        return int.from_bytes(self.make_hash(some_input), "big") & 0x3fffffff == int.from_bytes(self.hash, "big") & 0x3fffffff

class Coins:
    def __init__(self):
        self.users = {}

    def add_coin(self, username, word):
        with open("database.csv","a+") as database:
            database.write(f"{username},{word},{hasher.get_current_hash()},{hasher.seed}\n")
        if username not in self.users:
            self.users[username] = 1
        else:
            self.users[username] += 1

    def sanitise(self, name):
        return "".join([s for s in name.lower() if s in string.ascii_lowercase])

    def get_scores(self):
        retval = "<p> Current totals:</p> <ul>"
        for user, score in self.users.items():
            retval += f"<li>{self.sanitise(user)} {score}</li>"
        retval += "</ul>"
        return retval

@app.route('/', methods=["GET","POST"])
def hello_world():
    message = "<p> Have a guess! </p>"
    if request.method == "POST":
        if hasher.validate(request.form['word']):
            coins.add_coin(request.form['username'], request.form['word'])
            hasher.refresh()
            message = "<p> Good job! </p>"
        else:
            message = f"<p> That's not right! You hashed to: {hasher.make_hash(request.form['word'])}</p>"
    message += coins.get_scores()
    return f"""<h1>Squad Coins!</h1><p>So you wanna mine a squadcoin? I will give you some hash H, and some seed. You have to send me some message M such that MD5(seed || M)[:4] = H. To make it easier, though, I will mask off the first two bits of your hash and the original H.</p>
        <p>The hash is: {hasher.get_current_hash()}</p>
        <p> The prepended random bytes are: {hasher.get_seed()} </p> <p> {message}
        <form action="/" method="post"> <p>What is a word that hashes to this
        value?</p> <input id="word" name="word" type="text"></input>
        <p>What is your username?</p> <input type="text" name="username"
        id="username"></input><input type="submit"></input></form>"""

hasher = Hasher()
coins = Coins()


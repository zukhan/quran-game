'''
'Guess the Surah' Game

Displays a minimal length unique phrase from the Qur'an and asks you to guess
which surah the phrase is from. You can specify the starting and ending surahs
that you would like to be tested on. To play, run the following command from
the command line:

    $ python3 guess_the_surah.py <start_surah> <end_surah>

<start_surah> - (optional, default 0) starting surah number
<end_surah> - (optional, default 114) ending surah number

For example, if you want unique phrases starting from surah 78 until surah 90,
run:

    $ python3 guess_the_surah.py 78 90

Actions:

    'help' - see available actions with descriptions
    'hint' or 'h' - adds an extra word to the phrase to make it easier to guess
    'skip' or 's' - displays the answer and moves onto the next phrase
    'quit' or 'q' - exits the program
'''

import os
import sys
import json
import random
import secrets
import datetime
import subprocess

from flask import Flask, render_template, request, session

app = Flask(__name__)
app.secret_key = secrets.token_bytes(32)

# { 1: (1:1, 2:141), 2: (2:142, 2:252), ... }
juz_num_to_ayah_range = {}

# { '1:3':'1:2', '2:1':'1:7' }
ayah_num_to_prev_ayah_num = {}

# { '1:3': 'الرَّحْمَـٰنِ الرَّحِيمِ' }
ayah_num_to_ayah = {}

# { 1: '1 Al-Fatihah', 2: '2 Al-Baqarah' }
surah_num_to_name = {}

# { 110: ['الْعَالَمِينَ', 'الْحَمْدُ'] }
surah_num_to_phrases = {}

# { 'الْعَالَمِينَ' : '2:30' }
phrase_to_ayah_num = {}

#
# Prefixes an additional word to the phrase until it gets to the beginning of
# the ayah, and then it starts prefixing words from the previous ayah.
#
def add_word_to_phrase(phrase, ayah_num, word_idx):
    ayah_num = ayah_num if ayah_num else phrase_to_ayah_num[phrase]
    ayah = ayah_num_to_ayah[ayah_num]
    ayah_words = ayah.split(' ')

    # For the first hint, we need to find the location of the phrase in the ayah
    if word_idx == None:
        #
        # English example to help visualize the math...
        #
        # ayah: "My name is Zubair Khan"
        # phrase: "is Zubair",
        # num_remaining_words = 3,
        # word_idx = 5 - 3 - 1 = 1
        # ayah_words[word_idx] = "name"
        #
        char_idx = ayah.index(phrase) # will return char index of phrase in ayah
        # find out how many words are there between the phrase start and ayah end
        num_remaining_words = len(ayah[char_idx:].split(' '))
        word_idx = len(ayah_words) - num_remaining_words - 1

    # Still have words in the current ayah to prefix
    if word_idx >= 0:
        phrase = f"{ayah_words[word_idx]} {phrase}"
        return (phrase, ayah_num, word_idx - 1)

    # Done with the current ayah, go to previous ayah and start prefixing
    # words from the end of the previous ayah
    prev_ayah_num = ayah_num_to_prev_ayah_num.get(ayah_num)

    if not prev_ayah_num:
        print("Already at the beginning of the surah. "\
                + "Looks like you need to revise more...")
        return (phrase, ayah_num, word_idx)

    print("Done with current ayah, prefixing words from previous ayah.")

    prev_ayah_words = ayah_num_to_ayah[prev_ayah_num].split(' ')
    prev_word_idx = len(prev_ayah_words) - 1
    phrase = f"{prev_ayah_words[prev_word_idx]} ● {phrase}"

    return (phrase, prev_ayah_num, prev_word_idx - 1)

def print_help_message():
    print(
'''
Available actions:
    'help' - see available actions with descriptions
    'hint' or 'h' - adds an extra word to the phrase to make it easier to guess
    'skip' or 's' - displays the answer and moves onto the next phrase
    'quit' - exits the program
'''
    )

def process_input(surah_num, phrase):
    guess = input(f"\nWhich surah is this from?\n{phrase}\n> ").strip()

    ayah_num, ayah_idx = None, None
    num_wrong = 0
    while guess != str(surah_num):

        if guess == 'quit' or guess == 'q':
            sys.exit("See you soon. Don't forget to revise!")

        if guess == 'help':
            print_help_message()

        elif guess == 'hint' or guess == 'h':
            (phrase, ayah_num, ayah_idx) = \
                    add_word_to_phrase(phrase, ayah_num, ayah_idx)

        elif guess == 'skip' or guess == 's':
            print(f"The phrase was from surah {surah_num}")
            break

        else:
            num_wrong += 1

            err_msg = "Incorrect, try again."
            hint_msg = f"{err_msg} Type 'hint' to add a word to the phrase."

            print(err_msg if num_wrong < 3 else hint_msg)

        guess = input(f"{phrase}\n> ").strip()
    return guess

def get_random_phrase(start_surah, end_surah):
    surah_num = str(random.randint(start_surah, end_surah))
    phrase = random.choice(surah_num_to_phrases[surah_num])
    return (surah_num, phrase)

#
# The main loop that runs the game in the console
#
def guess_the_surah():
    start_surah = 0 if not len(sys.argv) > 1 else int(sys.argv[1])
    end_surah = 114 if not len(sys.argv) > 2 else int(sys.argv[2])

    while True:
        surah_num, phrase = get_random_phrase(start_surah, end_surah)
        guess = process_input(surah_num, phrase)

        if guess == str(surah_num):
            print("Correct!")

#
# Reads the lookup indexes from files and stores them in memory. The indexes
# are built by 'build_indexes.py' file which parses the Qur'an, builds the
# indexes, and outputs them to a file, which can then be used during
# game initialization.
#
def bootstrap_indexes():
    if os.path.exists("resources/indexes"):
        dir = "resources/indexes"
    else:
        dir = "/home/qurangame/mysite/quran-utils/resources/indexes"

    global juz_num_to_ayah_range, ayah_num_to_prev_ayah_num, surah_num_to_name
    global ayah_num_to_ayah, surah_num_to_phrases, phrase_to_ayah_num

    with open(f"{dir}/juz_num_to_ayah_range.json") as file:
        juz_num_to_ayah_range = json.loads(file.read())

    with open(f"{dir}/ayah_num_to_prev_ayah_num.json") as file:
        ayah_num_to_prev_ayah_num = json.loads(file.read())

    with open(f"{dir}/surah_num_to_name.json") as file:
        surah_num_to_name = json.loads(file.read())

    with open(f"{dir}/ayah_num_to_ayah.json", encoding="utf_8") as file:
        ayah_num_to_ayah = json.loads(file.read())

    with open(f"{dir}/surah_num_to_phrases.json", encoding="utf_8") as file:
        surah_num_to_phrases = json.loads(file.read())

    with open(f"{dir}/phrase_to_ayah_num.json", encoding="utf_8") as file:
        phrase_to_ayah_num = json.loads(file.read())

def load_new_phrase():
    load_session_start_end_surah()

    start_surah = int(session['start_surah'].split(' ')[0])
    end_surah = int(session['end_surah'].split(' ')[0])
    surah_num, phrase = get_random_phrase(start_surah, end_surah)

    session['surah_name'] = surah_num_to_name[str(surah_num)]
    session['unique_phrase'] = phrase
    session['phrase'] = phrase
    session['hint_ayah_num'] = None
    session['word_idx'] = None

def load_session_start_end_surah():
    start_surah = session.get('start_surah')
    end_surah = session.get('end_surah')
    session['start_surah'] = surah_num_to_name['1'] if not start_surah else start_surah
    session['end_surah'] = surah_num_to_name['114'] if not end_surah else end_surah

def render():
    load_session_start_end_surah()
    start = session['start_surah']
    end = session['end_surah']
    surah_names = list(surah_num_to_name.values())
    return render_template("home.html", surah_names=surah_names, start=start, end=end)

def build_quran_com_link(unique_phrase):
    surah_ayah_num = phrase_to_ayah_num[unique_phrase]
    surah_num = surah_ayah_num.split(':')[0].strip()
    ayah_num = surah_ayah_num.split(':')[1].strip()
    return f"<a href=\"https://quran.com/{surah_num}/{ayah_num}\" target=\"_blank\">{surah_ayah_num}</a>"

@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(minutes=30)
    session.modified = True

@app.route("/", methods=['GET'])
def index():
    score = session.get('score')
    session['score'] = score if score else 0

    session['result'] = ''
    load_session_start_end_surah()
    load_new_phrase()
    return render()

@app.route("/", methods=['POST'])
def index_post():
    score = session.get('score')
    session['score'] = score if score else 0

    form_start = request.form.get('start_surah')
    form_end = request.form.get('end_surah')

    session['result'] = ''

    unique_phrase = session.get('unique_phrase')
    if not unique_phrase:
        load_new_phrase()
        return render()

    quran_com_link = build_quran_com_link(unique_phrase)

    # Different start or end surah was selected, reload phrase
    if session.get('start_surah') != form_start or session.get('end_surah') != form_end:
        session['start_surah'] = form_start
        session['end_surah'] = form_end
        load_new_phrase()

    if request.form.get('skip') == 'Skip':
        surah_name = session['surah_name'].split(' ')[1]
        session['result'] = f"« {unique_phrase} » was from {quran_com_link} ('{surah_name}')"
        session['result_color'] = "red"
        load_new_phrase()

    elif request.form.get('guess') == 'Guess':
        guess = request.form['surah']
        session['guess'] = guess

        if guess.strip() == session['surah_name']:
            score = session.get('score')
            session['score'] = score + 1 if score else 1
            surah_name = session['surah_name'].split(' ')[1]
            session['result'] = f"Correct! Good job! « {unique_phrase} » is from {quran_com_link} ('{surah_name}')"
            session['result_color'] = "green"
            load_new_phrase()
        else:
            session['result'] = "Incorrect. Try again."
            session['result_color'] = "red"

    elif request.form.get('hint') == 'Hint':
        phrase, hint_ayah_num, word_idx = add_word_to_phrase(
                session['phrase'],
                session['hint_ayah_num'],
                session['word_idx'])

        session['phrase'] = phrase
        session['hint_ayah_num'] = hint_ayah_num
        session['word_idx'] = word_idx

    return render()

#
# To run in console mode, comment out the main method below and uncomment the
# last lines of this file.
#
bootstrap_indexes()
if __name__ == '__main__':
    app.run()

# This method runs the game in console mode
#bootstrap_indexes()
#guess_the_surah()

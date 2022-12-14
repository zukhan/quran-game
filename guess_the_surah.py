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

from flask import *

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

# { 1: '١ الفاتحة', 2: '٢ البقرة' }
surah_num_to_arabic_name = {}

# { 1: ['1:1', '1:2', '1:3'], 2: ['2:1'] }
surah_num_to_ayah_nums = {}

# { 110: ['الْعَالَمِينَ', 'الْحَمْدُ'] }
surah_num_to_phrases = {}

# { 'الْعَالَمِينَ' : '2:30' }
phrase_to_ayah_num = {}

# { '١ الفاتحة': '1 Al-Fatihah' }
surah_name_ar_to_en = {}

# { '1 Al-Fatihah': '١ الفاتحة' }
surah_name_en_to_ar = {}

#
# Adds another ayah before the current ayah
#
def prefix_ayah(phrase, surah_ayah_num):
    if not surah_ayah_num:
        surah_ayah_num = f"{session['surah_num']}:{session['ayah_num']}"

    prev_ayah_num = ayah_num_to_prev_ayah_num.get(surah_ayah_num)

    if not prev_ayah_num:
        session['result'] = "No more hints. Already at the beginning of the surah!"
        session['result_color'] = 'red'

        return (phrase, surah_ayah_num)

    prev_ayah = ayah_num_to_ayah[prev_ayah_num]
    phrase = f"{prev_ayah} ● {phrase}"

    return (phrase, prev_ayah_num)

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
        session['result'] = "No more hints. Already at the beginning of the surah!"
        session['result_color'] = 'yellow'

        return (phrase, ayah_num, word_idx)

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
            if session['easy_mode']:
                (phrase, ayah_num) = prefix_ayah(phrase, ayah_num)
            else:
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
    ayah_num = phrase_to_ayah_num[phrase].split(':')[1]
    return (surah_num, ayah_num, phrase)

def get_random_ayah(start_surah, end_surah):
    surah_num = str(random.randint(start_surah, end_surah))
    surah_ayah_num = random.choice(surah_num_to_ayah_nums[surah_num])
    ayah_num = surah_ayah_num.split(':')[1]

    # Skip the first ayah, it's too easy
    while ayah_num == '1':
        surah_ayah_num = random.choice(surah_num_to_ayah_nums[surah_num])
        ayah_num = surah_ayah_num.split(':')[1]

    return (surah_num, ayah_num, ayah_num_to_ayah[surah_ayah_num])

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

    global juz_num_to_ayah_range, ayah_num_to_prev_ayah_num, \
            surah_num_to_ayah_nums, surah_num_to_name, ayah_num_to_ayah, \
            surah_num_to_arabic_name, surah_num_to_phrases, phrase_to_ayah_num

    with open(f"{dir}/juz_num_to_ayah_range.json") as file:
        juz_num_to_ayah_range = json.loads(file.read())

    with open(f"{dir}/ayah_num_to_prev_ayah_num.json") as file:
        ayah_num_to_prev_ayah_num = json.loads(file.read())

    with open(f"{dir}/surah_num_to_ayah_nums.json") as file:
        surah_num_to_ayah_nums = json.loads(file.read())

    with open(f"{dir}/surah_num_to_name.json") as file:
        surah_num_to_name = json.loads(file.read())

    with open(f"{dir}/surah_num_to_arabic_name.json", encoding="utf_8") as file:
        surah_num_to_arabic_name = json.loads(file.read())

    with open(f"{dir}/ayah_num_to_ayah.json", encoding="utf_8") as file:
        ayah_num_to_ayah = json.loads(file.read())

    with open(f"{dir}/surah_num_to_phrases.json", encoding="utf_8") as file:
        surah_num_to_phrases = json.loads(file.read())

    with open(f"{dir}/phrase_to_ayah_num.json", encoding="utf_8") as file:
        phrase_to_ayah_num = json.loads(file.read())

    for surah_num in range(1, 115):
        en_surah_name = surah_num_to_name[str(surah_num)]
        ar_surah_name = surah_num_to_arabic_name[str(surah_num)]

        surah_name_en_to_ar[en_surah_name] = ar_surah_name
        surah_name_ar_to_en[ar_surah_name] = en_surah_name

def get_surah_name_from_num(surah_num):
    surah_num = str(surah_num)
    if session['arabic_mode']:
        return surah_num_to_arabic_name[surah_num]
    return surah_num_to_name[surah_num]

def get_surah_num_from_name(surah_name):
    surah_map = surah_num_to_name
    if session['arabic_mode']:
        surah_map = surah_num_to_arabic_name
    return list(surah_map.keys())[list(surah_map.values()).index(surah_name)]

def create_surah_name_to_num_map():
    surah_map = {}
    for surah_num, surah_name in surah_num_to_name.items():
        surah_map[surah_name] = surah_num
    for surah_num, surah_name in surah_num_to_arabic_name.items():
        surah_map[surah_name] = surah_num
    return surah_map

def get_surah_names():
    if session['arabic_mode']:
        return list(surah_num_to_arabic_name.values())
    return list(surah_num_to_name.values())

def load_new_phrase():
    load_session_start_end_surah()

    start_surah = int(get_surah_num_from_name(session['start_surah']))
    end_surah = int(get_surah_num_from_name(session['end_surah']))

    if session['easy_mode']:
        surah_num, ayah_num, phrase = get_random_ayah(start_surah, end_surah)
    else:
        surah_num, ayah_num, phrase = get_random_phrase(start_surah, end_surah)

    session['surah_name'] = get_surah_name_from_num(surah_num)
    session['arabic_surah_name'] = surah_num_to_arabic_name[str(surah_num)]
    session['surah_num'] = str(surah_num)
    session['ayah_num'] = str(ayah_num)
    session['unique_phrase'] = phrase
    session['phrase'] = phrase
    session['hint_ayah_num'] = None
    session['word_idx'] = None

def load_session_start_end_surah():
    start_surah = session.get('start_surah')
    end_surah = session.get('end_surah')

    default_start = '1' if not session['easy_mode'] else '100';
    if not start_surah:
        session['start_surah'] = get_surah_name_from_num(default_start)
    session['end_surah'] = get_surah_name_from_num('114') if not end_surah else end_surah

def render():
    load_session_start_end_surah()
    start = session['start_surah']
    end = session['end_surah']
    language = "arabic" if session['arabic_mode'] else "english"
    surah_names = get_surah_names()
    surah_map = create_surah_name_to_num_map()
    return render_template("home.html", surah_names=surah_names, surah_map=surah_map, \
                           language=language, start=start, end=end)

def build_quran_com_link(unique_phrase):
    surah_num = session['surah_num']
    ayah_num = session['ayah_num']
    surah_ayah_num = f"{surah_num}:{ayah_num}"
    return f"<a href=\"https://quran.com/{surah_num}/{ayah_num}\" target=\"_blank\">{surah_ayah_num}</a>"

def convert_surah_names(arabic_mode):
    surah_name_map = surah_name_en_to_ar if arabic_mode else surah_name_ar_to_en

    first_item = next(iter( surah_name_map.items() ))

    if session.get('start_surah') and session.get('end_surah'):
        session['start_surah'] = surah_name_map[session['start_surah']]
        session['end_surah'] = surah_name_map[session['end_surah']]
    if session.get('guess'):
        session['guess'] = surah_name_map[session['guess']]

@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(minutes=30)
    session.modified = True

    prev_arabic_mode = session.get('arabic_mode')
    if 'mode' in request.args:
        session['easy_mode'] = request.args['mode'] != 'hard'
    if 'locale' in request.args:
        arabic_mode = request.args['locale'] == 'ar'
        session['arabic_mode'] = arabic_mode

        if prev_arabic_mode != None and prev_arabic_mode != arabic_mode:
            convert_surah_names(arabic_mode)

    arabic_mode = session.get('arabic_mode')
    session['arabic_mode'] = False if arabic_mode == None else arabic_mode

    easy_mode = session.get('easy_mode')
    session['easy_mode'] = True if easy_mode == None else easy_mode

@app.route("/", methods=['GET'])
def index():
    return get()

@app.route("/easy", methods=['GET'])
def index_easy():
    session['easy_mode'] = True
    return get()

def get():
    if 'locale' in request.args and session.get('phrase'):
        return render()

    score = session.get('score')
    session['score'] = score if score else 0

    session['result'] = ''
    load_session_start_end_surah()
    load_new_phrase()
    return render()

@app.route("/", methods=['POST'])
def index_post():
    return post()

@app.route("/easy", methods=['POST'])
def index_post_easy():
    session['easy_mode'] = True
    return post()

def post():
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
        session['result'] = f"« {unique_phrase} » was from {quran_com_link} ({surah_name})"
        session['result_color'] = "red"
        load_new_phrase()

    elif request.form.get('guess') == 'Guess':
        guess = request.form['surah']
        session['guess'] = guess

        if guess.strip() == session['surah_name']:
            score = session.get('score')
            session['score'] = score + 1 if score else 1
            surah_name = session['surah_name'].split(' ')[1]
            session['result'] = f"Correct! Good job! « {unique_phrase} » is from {quran_com_link} ({surah_name})"
            session['result_color'] = "green"
            session['guess'] = session['start_surah']
            load_new_phrase()
        else:
            session['result'] = "Incorrect. Try again."
            session['result_color'] = "red"

    elif request.form.get('hint') == 'Hint':

        word_idx = None

        if session['easy_mode']:
            phrase, hint_ayah_num = prefix_ayah(
                    session['phrase'],
                    session['hint_ayah_num'])
        else:
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

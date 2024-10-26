'''
'Guess the Surah' Game

Displays a minimal length unique phrase from the Qur'an and asks you to guess
which surah the phrase is from. You can specify the starting and ending surahs
that you would like to be tested on.

www.qurangame.com
'''

import os
import sys
import json
import random
import secrets
import datetime
import subprocess

from flask import *
from tashkeel_utils import remove_dots, strip_tashkeel

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

# { '1:1': 'Guide us to the straight path -' }
ayah_num_to_translation = {}

# { '١ الفاتحة': '1 Al-Fatihah' }
surah_name_ar_to_en = {}

# { '1 Al-Fatihah': '١ الفاتحة' }
surah_name_en_to_ar = {}

# { 'Language:': 'اللغة:' }
arabic_translation = {}

#
# Returns the translated 'string', or 'string' itself if no translation found
#
def _(string):
    language = "arabic" if session['arabic_mode'] else "english"
    if language not in ["arabic"]:
        return string
    return arabic_translation.get(string, string)

#
# Adds another ayah before the current ayah
#
def prefix_ayah(phrase, surah_ayah_num):
    if not surah_ayah_num:
        surah_ayah_num = f"{session['surah_num']}:{session['ayah_num']}"

    prev_ayah_num = ayah_num_to_prev_ayah_num.get(surah_ayah_num)

    if not prev_ayah_num:
        session['result'] = _("No more hints. Already at the beginning of the surah!")
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
        session['result'] = _("No more hints. Already at the beginning of the surah!")
        session['result_color'] = 'yellow'

        return (phrase, ayah_num, word_idx)

    prev_ayah_words = ayah_num_to_ayah[prev_ayah_num].split(' ')
    prev_word_idx = len(prev_ayah_words) - 1
    phrase = f"{prev_ayah_words[prev_word_idx]} ● {phrase}"

    return (phrase, prev_ayah_num, prev_word_idx - 1)

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

def get_surah_name_from_num(surah_num):
    surah_num = str(surah_num)
    if session['arabic_mode']:
        return surah_num_to_arabic_name[surah_num]
    return surah_num_to_name[surah_num]

def get_surah_num_from_name(surah_name):
    surah_map = surah_num_to_name
    if session['arabic_mode']:
        surah_map = surah_num_to_arabic_name

    keys = list(surah_map.keys())
    surah_idx = list(surah_map.values()).index(surah_name)
    if not keys[surah_idx]:
        print(f"Something is wrong... surah_idx = '{surah_idx}', keys = '{keys}', surah_map = '{surah_map}'")
    return keys[surah_idx]

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
    session['surah_ayah_num'] = f"{surah_num}:{ayah_num}"
    session['unique_phrase'] = phrase
    session['phrase'] = phrase
    session['hint_ayah_num'] = None
    session['word_idx'] = None
    session['translation'] = None

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
                           language=language, start=start, end=end, _=_)

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
    if session.get('surah_name'):
        session['surah_name'] = surah_name_map[session['surah_name']]

def get_surah_name():
    surah_name_tokens = session['surah_name'].split(' ')
    return ' '.join(surah_name_tokens[1:])

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


@app.route('/rasm')
def redirect_to_tashkeel():
    return redirect('/tashkeel', code=301)

@app.route('/tashkeel', methods=['GET', 'POST'])
def tashkeel_remover():
    result = ""
    if request.method == 'POST':
        text = request.form.get('text')
        remove_dots_option = 'remove_dots' in request.form
        if text:
            # Always remove tashkeel by default
            result = strip_tashkeel(text)
            # Optionally remove dots if the checkbox is checked
            if remove_dots_option:
                result = remove_dots(result)
    return render_template('tashkeel.html', result=result)


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

    session['result-pre'] = ''
    session['result-arabic'] = ''
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
    guessed_surah = request.form.get('surah')

    session['result-pre'] = ''
    session['result-arabic'] = ''
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

    if request.form.get('skip') == _('Skip'):
        surah_name = get_surah_name()
        session['result-arabic'] = f"« {unique_phrase} » "
        session['result'] = f"{_('was from')} {quran_com_link} ( {surah_name} )"
        session['result_color'] = "red"
        load_new_phrase()

    elif request.form.get('guess') == _('Guess') or guessed_surah != "Select Surah":
        session['guess'] = guessed_surah

        if guessed_surah.strip() == session['surah_name']:
            score = session.get('score')
            session['score'] = score + 1 if score else 1
            surah_name = get_surah_name()
            session['result-pre'] = f"{_('Correct! Good job!')} "
            session['result-arabic'] = f"« {unique_phrase} » "
            session['result'] = f"{_('is from')} {quran_com_link} ( {surah_name} )"
            session['result_color'] = "green"
            session['guess'] = session['start_surah']
            load_new_phrase()
        else:
            session['result'] = _("Incorrect. Try again.")
            session['result_color'] = "red"

    elif request.form.get('hint') == _('Hint'):

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

    elif request.form.get('translate') == _('Translate'):
        session['translation'] = ayah_num_to_translation[session["surah_ayah_num"]]

    return render()

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
            surah_num_to_arabic_name, surah_num_to_phrases, phrase_to_ayah_num, \
            ayah_num_to_translation, arabic_translation

    with open(f"{dir}/juz_num_to_ayah_range.json") as file:
        juz_num_to_ayah_range = json.loads(file.read())

    with open(f"{dir}/ayah_num_to_prev_ayah_num.json") as file:
        ayah_num_to_prev_ayah_num = json.loads(file.read())

    with open(f"{dir}/surah_num_to_ayah_nums.json") as file:
        surah_num_to_ayah_nums = json.loads(file.read())

    with open(f"{dir}/surah_num_to_name.json") as file:
        surah_num_to_name = json.loads(file.read())

    with open(f"{dir}/ayah_num_to_translation.json") as file:
        ayah_num_to_translation = json.loads(file.read())

    with open(f"{dir}/surah_num_to_arabic_name.json", encoding="utf_8") as file:
        surah_num_to_arabic_name = json.loads(file.read())

    with open(f"{dir}/ayah_num_to_ayah.json", encoding="utf_8") as file:
        ayah_num_to_ayah = json.loads(file.read())

    with open(f"{dir}/surah_num_to_phrases.json", encoding="utf_8") as file:
        surah_num_to_phrases = json.loads(file.read())

    with open(f"{dir}/phrase_to_ayah_num.json", encoding="utf_8") as file:
        phrase_to_ayah_num = json.loads(file.read())
    
    with open(f"{dir}/arabic_translation.json",  encoding="utf_8") as file:
        arabic_translation = json.loads(file.read())

    for surah_num in range(1, 115):
        en_surah_name = surah_num_to_name[str(surah_num)]
        ar_surah_name = surah_num_to_arabic_name[str(surah_num)]

        surah_name_en_to_ar[en_surah_name] = ar_surah_name
        surah_name_ar_to_en[ar_surah_name] = en_surah_name

bootstrap_indexes()
if __name__ == '__main__':
    app.run()

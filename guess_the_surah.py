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

NOTE: The Arabic text does not display properly in the console. I've made it so
that the Arabic phrase is automatically copied to Mac OS clipboard so you just
need to paste it into another text editor like TextEdit (no need to copy it).
'''

import subprocess
import random
import json
import sys

# { 1: (1:1, 2:141), 2: (2:142, 2:252), ... }
juz_num_to_ayah_range = {}

# { '1:3':'1:2', '2:1':'1:7' }
ayah_num_to_prev_ayah_num = {}

# { '1:3': 'الرَّحْمَـٰنِ الرَّحِيمِ' }
ayah_num_to_ayah = {}

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
    phrase = f"{prev_ayah_words[prev_word_idx]} | {phrase}"

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

        # Copies the Arabic text to Mac OS clipboard to allow for easy pasting
        subprocess.run("pbcopy", universal_newlines=True, input=phrase)

        guess = input(f"{phrase}\n> ").strip()
    return guess

#
# The main loop that runs the game
#
def guess_the_surah():
    start_surah = 0 if not len(sys.argv) > 1 else int(sys.argv[1])
    end_surah = 114 if not len(sys.argv) > 2 else int(sys.argv[2])

    while True:
        surah_num = random.randint(start_surah, end_surah)
        phrase = random.choice(surah_num_to_phrases[str(surah_num)])

        # Copies the Arabic text to Mac OS clipboard to allow for easy pasting
        subprocess.run("pbcopy", universal_newlines=True, input=phrase)

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
    dir = "resources/indexes"

    global juz_num_to_ayah_range, ayah_num_to_prev_ayah_num
    global ayah_num_to_ayah, surah_num_to_phrases, phrase_to_ayah_num

    with open(f"{dir}/juz_num_to_ayah_range.json") as file:
        juz_num_to_ayah_range = json.loads(file.read())

    with open(f"{dir}/ayah_num_to_prev_ayah_num.json") as file:
        ayah_num_to_prev_ayah_num = json.loads(file.read())

    with open(f"{dir}/ayah_num_to_ayah.json", encoding="utf_8") as file:
        ayah_num_to_ayah = json.loads(file.read())

    with open(f"{dir}/surah_num_to_phrases.json", encoding="utf_8") as file:
        surah_num_to_phrases = json.loads(file.read())

    with open(f"{dir}/phrase_to_ayah_num.json", encoding="utf_8") as file:
        phrase_to_ayah_num = json.loads(file.read())

bootstrap_indexes()
guess_the_surah()

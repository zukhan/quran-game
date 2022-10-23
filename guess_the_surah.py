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
import sys

# { 1: (1:1, 2:141), 2: (2:142, 2:252), ... }
juz_num_to_ayah_range = {}

# {'2:30': 'الْعَالَمِينَ'}
ayah_num_to_phrases = {}

# { 110: ['الْعَالَمِينَ', 'الْحَمْدُ'] }
surah_num_to_phrases = {}

# { 'الْعَالَمِينَ' : '2:30' }
phrase_to_ayah_num = {}

# ['مِنْ', 'إِنَّ اللَّهَ']
non_unique_phrases = set()

# { '1:3': 'الرَّحْمَـٰنِ الرَّحِيمِ' }
ayah_num_to_ayah = {}

# { '1:3':'1:2', '2:1':'1:7' }
ayah_num_to_prev_ayah_num = {}

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
        phrase = random.choice(list(surah_num_to_phrases[surah_num]))

        # Copies the Arabic text to Mac OS clipboard to allow for easy pasting
        subprocess.run("pbcopy", universal_newlines=True, input=phrase)

        guess = process_input(surah_num, phrase)

        if guess == str(surah_num):
            print("Correct!")

#
# For a given ayah, this function populates the 'ayah_phrases' set with all of
# the phrases in that ayah. To take an English example, for the sentence,
# "I am Sherlock", after this method executes, 'ayah_phrases' will be populated
# with the following phrases:
#
#   ["I", "am", I am", "Sherlock", "am Sherlock", "I am Sherlock"]
#
def populate_phrases(ayah_words, ayah_phrases):
    prev_phrases = []
    cur_phrases = []

    for ayah_word in ayah_words:
        cur_phrases.append(ayah_word)
        for prev_phrase in prev_phrases:
            cur_phrases.append(f"{prev_phrase} {ayah_word}")

        ayah_phrases.update(cur_phrases)
        prev_phrases = cur_phrases
        cur_phrases = []

#
# This function populates the map which defines the juz boundaries (starting
# and ending ayahs).
#
def populate_juz_maps():
    with open("resources/juz_boundaries.csv") as file:
        for line in file:
            tokens = line.strip().split(',')
            juz_num = int(tokens[0])
            ayah_range = tokens[1].split('-')

            juz_num_to_ayah_range[juz_num] = (ayah_range[0], ayah_range[1])

#
# Given an 'ayah_range' tuple (e.g. '(2:52, 3:20)') and a 'target_ayah_num'
# (e.g. '2:52'), this function determines whether the target_ayah_num is less
# than the ayah_range, within the ayah_range, or greater than the ayah_range.
#
# Returns:
#   -1 if the target ayah is less than the range
#   0 if the target ayah is within the range
#   1 if the target ayah is greater than the range
#
def compare_ayah(ayah_range, target_ayah_num):
    (start_ayah, end_ayah) = ayah_range
    surah_num = int(target_ayah_num.split(':')[0])
    ayah_num = int(target_ayah_num.split(':')[1])

    start_surah_num = int(start_ayah.split(':')[0])
    start_ayah_num = int(start_ayah.split(':')[1])

    end_surah_num = int(end_ayah.split(':')[0])
    end_ayah_num = int(end_ayah.split(':')[1])

    # target surah is less than start surah
    if surah_num < start_surah_num:
        return -1

    # target surah is greater than end surah
    if surah_num > end_surah_num:
        return 1

    # target surah is in between start and end surahs
    if surah_num > start_surah_num and surah_num < end_surah_num:
        return 0

    # target surah is equal to the starting and ending surahs
    if surah_num == start_surah_num and surah_num == end_surah_num:
        if ayah_num < start_ayah_num:
            return -1
        if ayah_num > end_ayah_num:
            return 1
        return 0

    # target surah is equal to the starting surah in the range
    if surah_num == start_surah_num:
        if ayah_num < start_ayah_num:
            return -1
        return 0

    # target surah is equal to the ending surah in the range
    if surah_num == end_surah_num:
        if ayah_num > end_ayah_num:
            return 1
        return 0

    raise Exception("There is a bug in the compare_ayah logic")

#
# Given an ayah_num (e.g. '2:210'), this function finds and returns the number
# of the juz that the ayah resides in.
#
def find_juz_num(ayah_num):
    start_idx = 1
    end_idx = 30

    while start_idx <= end_idx:
        mid_idx = (start_idx + end_idx) // 2

        res = compare_ayah(juz_num_to_ayah_range[mid_idx], ayah_num)
        if res == 0:
            return mid_idx
        if res < 0:
            end_idx = mid_idx - 1
        else:
            start_idx = mid_idx + 1

    raise Exception("There is a bug in the find_juz_num logic")

#
# This function reads the entire Qur'an from a file and finds the minimal length
# unique phrases for each ayah and builds up lookup index maps based on various
# parameters (e.g. by juz number, surah number, ayah number, etc.)
#
def parse_quran():
    with open("resources/quran-simple-plain.txt", encoding="utf_8") as file:
        lines = [l.rstrip() for l in file if l.rstrip() and not l.startswith('#')]

    prev_ayah_num = None
    for line in lines:
        # 'line' has the following format: "1|2|الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ"
        tokens = line.split('|')
        ayah_num = tokens[0] + ':' + tokens[1]
        ayah_words = tokens[2].split(' ')
        ayah_phrases = set()

        ayah_num_to_ayah[ayah_num] = tokens[2].strip()

        populate_phrases(ayah_words, ayah_phrases)

        for ayah_phrase in ayah_phrases:
            if ayah_phrase in phrase_to_ayah_num:
                non_unique_phrases.add(ayah_phrase)
            else:
                phrase_to_ayah_num[ayah_phrase] = ayah_num

        # Do not go outside the surah boundary
        if prev_ayah_num and ayah_num.split(':')[0] == prev_ayah_num.split(':')[0]:
            ayah_num_to_prev_ayah_num[ayah_num] = prev_ayah_num
        prev_ayah_num = ayah_num

    # Remove duplicates
    for non_unique_phrase in non_unique_phrases:
        del phrase_to_ayah_num[non_unique_phrase]

    # Build reverse indexes
    for phrase, ayah_num in phrase_to_ayah_num.items():
        if ayah_num not in ayah_num_to_phrases:
            ayah_num_to_phrases[ayah_num] = set()
        ayah_num_to_phrases[ayah_num].add(phrase)

        surah_num = int(ayah_num.split(':')[0])
        if surah_num not in surah_num_to_phrases:
            surah_num_to_phrases[surah_num] = set()
        surah_num_to_phrases[surah_num].add(phrase)

    # Only keep the phrases per ayah that have the fewest words
    for ayah_num, phrases in ayah_num_to_phrases.items():
        min_phrase_words = 10000
        for phrase in phrases:
            min_phrase_words = min(min_phrase_words, len(phrase.split(' ')))

        surah_num = int(ayah_num.split(':')[0])
        for phrase in phrases.copy():
            if len(phrase.split(' ')) != min_phrase_words:
                phrases.remove(phrase)
                del phrase_to_ayah_num[phrase]
                surah_num_to_phrases[surah_num].remove(phrase)


populate_juz_maps()
parse_quran()
guess_the_surah()

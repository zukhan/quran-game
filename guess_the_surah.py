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

NOTE: The Arabic text does not display properly in the console. I've made it so
that the Arabic phrase is automatically copied to Mac OS clipboard so you just 
need to paste it into another text editor like TextEdit (no need to copy it).
'''

import subprocess
import random
import sys

MIN_WORDS = 1

# { 1: (1:1, 2:141), 2: (2:142, 2:252), ... }
juz_num_to_ayah_range = {}

# { 1: {'2:30': 'الْعَالَمِينَ'} }
juz_num_to_ayah_phrases = {}

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
# the ayah, and then it starts appending words to the phrase until the whole
# ayah is complete.
#
def add_word_to_phrase(phrase, phrase_with_hint):
    ayah_num = phrase_to_ayah_num[phrase]
    ayah = ayah_num_to_ayah[ayah_num]
    ayah_words = ayah.split(' ')
    phrase_words = phrase_with_hint.split(' ')

    word_idx = 0
    while word_idx < len(ayah_words):
        if ayah_words[word_idx] == phrase_words[0]:
            break
        word_idx += 1

    if word_idx != 0:
        return ayah_words[word_idx - 1] + ' ' + phrase_with_hint

    # Can't prefix anymore words because already at the beginning of the ayah
    # Append words to the phrase instead until you get to the end of the ayah
    word_idx = 0
    while word_idx < len(ayah_words):
        if ayah_words[word_idx] == phrase_words[len(phrase_words) - 1]:
            break
        word_idx += 1

    if word_idx < len(ayah_words) - 1:
        return phrase_with_hint + ' ' + ayah_words[word_idx + 1]

    print("That is the whole ayah. No more hints! Type 'skip' to accept defeat.")
    return phrase_with_hint


def print_help_message():
    print(
'''
Available actions:
    'help' - see available actions with descriptions
    'hint' or 'h' - adds an extra word to the phrase to make it easier to guess
    'skip' or 's' - displays the answer and moves onto the next phrase
'''
    )

#
# The main loop that runs the game and processes the user's input
#
def guess_the_surah():
    start_surah = 0
    end_surah = 114

    if len(sys.argv) > 1:
        start_surah = int(sys.argv[1])
    if len(sys.argv) > 2:
        end_surah = int(sys.argv[2])

    while True:
        surah_num = random.randint(start_surah, end_surah)
        phrase = random.choice(list(surah_num_to_phrases[surah_num]))

        subprocess.run("pbcopy", universal_newlines=True, input=phrase)
        guess = input('\nWhich surah is this phrase from? ' + phrase + '\n> ').strip()

        phrase_with_hint = phrase
        num_incorrect = 0
        while guess != str(surah_num):
            if guess == 'help':
                print_help_message()
            elif guess == 'hint' or guess == 'h':
                phrase_with_hint = add_word_to_phrase(phrase, phrase_with_hint)
            elif guess == 'skip' or guess == 's':
                print('The phrase was from surah ' + str(surah_num))
                break
            else:
                num_incorrect += 1
                if num_incorrect > 2:
                    print("Incorrect, try again. Type 'hint' to add a word to the phrase.")
                else:
                    print('Incorrect, try again.')

            subprocess.run("pbcopy", universal_newlines=True, input=phrase_with_hint)
            guess = input(phrase_with_hint + '\n> ').strip()

        if guess == str(surah_num):
            print('Correct!')


#
# For a given ayah, this function populates the 'ayah_phrases' set with all of
# the phrases in that ayah that are at least MIN_WORDS long. To take an English
# example, for the sentence, "I am Sherlock Holmes", after this method executes
# with MIN_WORDS set to 2, 'ayah_phrases' will be populated with the following
# phrases: ["I am", "I am Sherlock", "I am Sherlock Holmes", "am Sherlock",
# "am Sherlock Holmes", "Sherlock Holmes"]
#
def populate_phrases(ayah_words, word_idx, ayah_phrases, cur_phrase, cache):
    cache_key = cur_phrase + str(word_idx)
    if cache_key in cache:
        return

    cur_phrase = cur_phrase.strip()
    if len(cur_phrase.split(' ')) >= MIN_WORDS:
        ayah_phrases.add(cur_phrase)

    if word_idx >= len(ayah_words):
        return

    cur_word = ayah_words[word_idx].strip()
    new_phrase = cur_phrase + ' ' + cur_word

    # Append the current word to the phrase
    populate_phrases(ayah_words, word_idx + 1, ayah_phrases, new_phrase, cache)
    # Start a new phrase with current word as the beginning of the phrase
    populate_phrases(ayah_words, word_idx + 1, ayah_phrases, cur_word, cache)

    cache.add(cache_key)


#
# This function populates the map which defines the juz boundaries (starting
# and ending ayahs).
#
def populate_juz_maps():
    with open('resources/juz_boundaries.csv') as file:
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

    raise Exception('There is a bug in the compare_ayah logic')


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

    raise Exception('There is a bug in the find_juz_num logic')


#
# This function reads the entire Qur'an from a file and finds the minimal length
# unique phrases for each ayah and builds up lookup index maps based on various
# parameters (e.g. by juz number, surah number, ayah number, etc.)
#
def parse_quran():
    with open('resources/quran-simple-plain.txt', encoding='utf_8') as file:
        lines = [l.rstrip() for l in file if l.rstrip() and not l.startswith('#')]

    prev_ayah_num = None
    for line in lines:
        # 'line' has the following format: "1|2|الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ"
        tokens = line.split('|')
        ayah_num = tokens[0] + ':' + tokens[1]
        ayah_phrases = set()

        ayah_num_to_ayah[ayah_num] = tokens[2].strip()

        populate_phrases(tokens[2].split(' '), 0, ayah_phrases, '', set())

        for ayah_phrase in ayah_phrases:
            if ayah_phrase in phrase_to_ayah_num:
                non_unique_phrases.add(ayah_phrase)
            else:
                phrase_to_ayah_num[ayah_phrase] = ayah_num

        ayah_num_to_prev_ayah_num[ayah_num] = prev_ayah_num
        prev_ayah_num = ayah_num

    # Remove duplicates
    for non_uniq_phrase in non_unique_phrases:
        del phrase_to_ayah_num[non_uniq_phrase]

    # Build reverse indexes
    for phrase, ayah_num in phrase_to_ayah_num.items():
        juz_num = find_juz_num(ayah_num)

        if juz_num not in juz_num_to_ayah_phrases:
            juz_num_to_ayah_phrases[juz_num] = {}

        if ayah_num not in juz_num_to_ayah_phrases[juz_num]:
            juz_num_to_ayah_phrases[juz_num][ayah_num] = set()
        juz_num_to_ayah_phrases[juz_num][ayah_num].add(phrase)

        surah_num = int(ayah_num.split(':')[0])
        if surah_num not in surah_num_to_phrases:
            surah_num_to_phrases[surah_num] = set()
        surah_num_to_phrases[surah_num].add(phrase)

    # Only keep the phrases per ayah that have the fewest words
    for ayah_num_to_phrases in juz_num_to_ayah_phrases.values():
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

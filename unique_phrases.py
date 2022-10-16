'''
Finds minimum length unique phrases in the Qur'an and indexes them by ayah 
number. Can be extended and used to quiz yourself by displaying a random unique
phrase and having to continue reciting from there (and guess which surah it's
from). 

MIN_WORDS constant can be used to set the minimum number of words you would like
in the unique phrases.

Usage: python3 unique_phrases.py
'''

import random
import sys

MIN_WORDS = 3
if sys.argv[1]:
    MIN_WORDS = int(sys.argv[1])

juz_num_to_ayah_range = {}
juz_num_to_ayah_phrases = {}
surah_num_to_phrases = {}
phrase_to_ayah_num = {}
non_unique_phrases = set()


# To play the game, run the following command from the command line:
#
#   $ python3 unique_phrases.py <min_word_phrase> <start_surah> <end_surah>
#
# min_word_phrase - (optional, default 3) minimum words in the unique phrase
# start_surah - (optional, default 0) starting surah number
# end_surah - (optional, default 114) ending surah number
#
# For example, if you want at least 3 words in the unique phrases starting
# from surah 78, run:
#
#   $ python3 unique_phrases.py 3 78
def guess_the_surah():
    while True:

        start_surah = 0
        end_surah = 114

        if len(sys.argv) > 2:
            start_surah = int(sys.argv[2])
        if len(sys.argv) > 3:
            end_surah = int(sys.argv[3])

        surah_num = random.randint(start_surah, end_surah)
        phrase = random.choice(list(surah_num_to_phrases[surah_num]))

        guess = input('Which surah is this phrase from? ' + phrase + '\n').strip()

        while guess != str(surah_num) and guess != 'skip':
            guess = input('Incorrect, try again: ').strip()

        if guess == 'skip':
            print('Answer was '' + surah_num + ''\n')
        else:
            print('Correct!\n')


def write_unique_phrases_to_file():
    # Write the output to a file (make sure to update MIN_WORDS constant)
    with open('output/min-three-word-phrases.txt', 'w', encoding='utf-8') as file:
        old_surah_num = 0
        for ayah_num_to_phrases in juz_num_to_ayah_phrases.values():
            for ayah_num, phrases in ayah_num_to_phrases.items():
                new_surah_num = ayah_num.split(':')[0]
                if new_surah_num != old_surah_num:
                    file.write('\n')
                    file.write('Surah ' + new_surah_num + ':\n')
                    file.write('\n')
                    old_surah_num = new_surah_num

                file.write(ayah_num + ' - ' + str(phrases))
                file.write('\n')


# We are not currently going beyond the ayah boundaries
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


def populate_juz_maps():
    with open('resources/juz_boundaries.csv') as file:
        for line in file:
            tokens = line.strip().split(',')
            juz_num = int(tokens[0])
            ayah_range = tokens[1].split('-')

            juz_num_to_ayah_range[juz_num] = (ayah_range[0], ayah_range[1])

# ayah_range is a tuple, e.g. (2:52, 3:20)
# target_ayah_num has the format '2:52'
#
# Returns:
# -1 if the target ayah is less than the range
# 0 if the target ayah is within the range
# 1 if the target ayah is greater than the range
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

    # target surah is greater than start surah
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


def parse_quran():
    with open('resources/quran-simple-plain.txt', encoding='utf_8') as file:
        ayahs = [l.rstrip() for l in file if l.rstrip() and not l.startswith('#')]

    # 'ayah' has the following format:
    # '1|2| الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ'
    for ayah in ayahs:
        tokens = ayah.split(' ')
        surah_num = tokens[0].split('|')[0]
        ayah_num = tokens[0].split('|')[1]

        ayah_phrases = set()
        populate_phrases(tokens, 1, ayah_phrases, '', set())

        for ayah_phrase in ayah_phrases:
            if ayah_phrase in phrase_to_ayah_num:
                non_unique_phrases.add(ayah_phrase)
            else:
                phrase_to_ayah_num[ayah_phrase] = surah_num + ':' + ayah_num

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

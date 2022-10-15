"""
Finds minimum length unique phrases in the Qur'an and indexes them by ayah 
number. Can be extended and used to quiz yourself by displaying a random unique
phrase and having to continue reciting from there (and guess which surah it's
from). 

MIN_WORDS constant can be used to set the minimum number of words you would like
in the unique phrases.

Usage: python3 unique_phrases.py
"""

import random
import sys

if sys.argv[1]:
    MIN_WORDS = int(sys.argv[1])
else:
    MIN_WORDS = 3

def write_unique_phrases_to_file():
    # Write the output to a file (make sure to update MIN_WORDS constant)
    with open('output/min-three-word-phrases.txt', 'w', encoding='utf-8') as file:
        old_surah_num = 0
        for ayah_num, phrases in ayah_num_to_phrases.items():
            new_surah_num = ayah_num.split(':')[0]
            if new_surah_num != old_surah_num:
                file.write('\n')
                file.write('Surah ' + new_surah_num + ':\n')
                file.write('\n')
                old_surah_num = new_surah_num

            file.write(ayah_num + ' - ' + str(phrases))
            file.write('\n')

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
        phrase, ayah_num = random.choice(list(phrase_to_ayah_num.items()))
        surah_num = ayah_num.split(':')[0]

        start_surah = 0
        end_surah = 114

        if len(sys.argv) > 2:
            start_surah = int(sys.argv[2])
        if len(sys.argv) > 3:
            end_surah = int(sys.argv[3])

        if int(surah_num) < start_surah or int(surah_num) > end_surah:
            continue

        guess = input("Which surah is this phrase from? " + phrase + '\n').strip()

        while guess != surah_num and guess != "skip":
            guess = input("Incorrect, try again: ").strip()

        if guess == "skip":
            print("Answer was '" + surah_num + "'\n")
        else:
            print("Correct!\n")

# We are not currently going beyond the ayah boundaries
def populate_phrases(ayah_words, word_idx, ayah_phrases, cur_phrase, cache):
    cache_key = cur_phrase + str(word_idx)
    if cache_key in cache:
        return

    cur_phrase = cur_phrase.strip()
    if len(cur_phrase.split(" ")) >= MIN_WORDS:
        ayah_phrases.add(cur_phrase)

    if word_idx >= len(ayah_words):
        return

    cur_word = ayah_words[word_idx].strip()
    new_phrase = cur_phrase + " " + cur_word

    # Append the current word to the phrase
    populate_phrases(ayah_words, word_idx + 1, ayah_phrases, new_phrase, cache)
    # Start a new phrase with current word as the beginning of the phrase
    populate_phrases(ayah_words, word_idx + 1, ayah_phrases, cur_word, cache)

    cache.add(cache_key)

with open('quran-simple-plain.txt', encoding='utf_8') as file:
    ayahs = [l.rstrip() for l in file if l.rstrip() and not l.startswith("#")]

ayah_num_to_phrases = {}
phrase_to_ayah_num = {}
non_unique_phrases = set()

# 'ayah' has the following format:
# "1|2| الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ"
for ayah in ayahs:
    tokens = ayah.split(' ')
    surah_num = tokens[0].split('|')[0]
    ayah_num = tokens[0].split('|')[1]

    ayah_phrases = set()
    populate_phrases(tokens, 1, ayah_phrases, "", set())

    for ayah_phrase in ayah_phrases:
        if ayah_phrase in phrase_to_ayah_num:
            non_unique_phrases.add(ayah_phrase)
        else:
            phrase_to_ayah_num[ayah_phrase] = surah_num + ":" + ayah_num

# Remove duplicates
for non_uniq_phrase in non_unique_phrases:
    del phrase_to_ayah_num[non_uniq_phrase]

# Build a reverse index of unique phrases by ayah number
for phrase, ayah_num in phrase_to_ayah_num.items():
    if ayah_num not in ayah_num_to_phrases:
        ayah_num_to_phrases[ayah_num] = set()
    ayah_num_to_phrases[ayah_num].add(phrase)

# Only keep the phrases per ayah that have the fewest words
for phrases in ayah_num_to_phrases.values():
    min_phrase_words = 10000
    for phrase in phrases:
        min_phrase_words = min(min_phrase_words, len(phrase.split(" ")))

    for phrase in phrases.copy():
        if len(phrase.split(" ")) != min_phrase_words:
            phrases.remove(phrase)
            del phrase_to_ayah_num[phrase]

guess_the_surah()

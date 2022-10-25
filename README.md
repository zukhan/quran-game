# 'Guess the Surah' Game

Displays a minimal length unique phrase from the Qur'an and asks you to guess
which surah the phrase is from. You can specify the starting and ending surahs
that you would like to be tested on. To play, run the following command from
the command line:

    $ python3 guess_the_surah.py <start_surah> <end_surah>
    
<start_surah> - (optional, default 0) starting surah number<br>
<end_surah> - (optional, default 114) ending surah number

For example, if you want unique phrases starting from surah 78 until surah 90,
run:

    $ python3 guess_the_surah.py 78 90

Actions:
<pre>
'help' - see available actions with descriptions
'hint' or 'h' - adds an extra word to the phrase to make it easier to guess
'skip' or 's' - displays the answer and moves onto the next phrase
'quit' or 'q' - exits the program
</pre>

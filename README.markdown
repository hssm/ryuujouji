I'm resuming this project as of May 2012. What a mess! I will begin
by organizing the various tasks into their own components (or even
their own projects, if I must). Ultimately, I see three main components:
 - Pre-processing: creating the data used for solving a word. This 
 	is done only once and doesn't belong with the main component.
 - The Solver: the component that actually solves a word and deals
 	with all the "segment" logic
 - Metrics: keeping count of what is solved, allowing us to check
 	the effects of a change (newly solved words or regressions)
 	
I might also investigate the performance effects of loading the entire
dataset in memory instead of using an SQLite database.

For now, I've updated the README to explain the goals of this project
a little more clearly.  

--------------
Ryuujouji (粒状字) -- granular characters.
(Alternatively: "I don't actually know Japanese so let's hope this isn't laughable nonsense.")
--------------
Ryuujouji aims to solve two tasks concerning Japanese words:

*1 - Grapheme-phoneme alignment*

That is, given a word (the grapheme) and its reading (the phoneme), it
tries to determine which portion of the reading belongs to which
character in the word. For example:

非常事態[ひじょうじたい]
非 ひ
常 じょう
事 じ
態 たい

日帰り[ひがえり]
日 ひ
帰り がえり

建て替える[タテカエル]
建て タテ
替える カエル

Ryuujouji does this by "solving" words using the comprehensive listing
of character readings in the KANJIDIC2 dictionary.

While the original readings in KANJIDIC2 suffice for a large number of
words, the solving task is made more difficult by transformations in
the phonetic component of Japanese words which do not match the 
dictionary readings exactly. Most of these transformations are
accounted for by Ryuujouji.    

*2 - Link dictionary readings to words (more specifically, exact
segments of words)*

This goal means that, for each individual reading of each individual
character within KANJIDIC2, you will be able to find words that use
both, regardless of position in the word or the transformation the
reading has undertaken.  For example, if searching for words that
include 帰「かえ.る」, you will get back a long list, among them:
帰る 「かえる」
帰り 「かえり」
日帰り 「ひがえり」
家に帰る時 「いえにかえるとき」
帰りなんいざ 「かえりなんいざ」
原点に帰る 「げんてんにかえる」

Notice that, in the examples above, the original reading (かえ.る) has
been modified, but we were still able to find them. Since the specific
transformations are tagged, it will eventually also be possible to
filter words by specific transformation (e.g., words that only contain
かえ.る appearing as がえり).


===========

Unlike existing research, Ryuujouji does not employ any statistical
method to determine the alignment. All solutions are constructed using
data available in KANJIDIC2 and hand-crafted rules that account for
particular features of the Japanese language.

Accuracy is measured against a manually aligned test data set from
existing research that contains 5000 instances. Please see:
http://www.aclweb.org/anthology-new/W/W99/W99-0902.pdf
The data set has its own license and can be found here:
http://www.csse.unimelb.edu.au/research/lt/resources/gpalignment/gpalignment.tgz

Ryuujouji currently achieves 94.46% accuracy on this data set, but is
expected to increase in coming revisions. Also, Ryuujouji is able to
build a solution for 93% of the unique word/reading entries in JMdict
(that's 148,322 out of 159,207 in the current test data), although
their accuracy can't be tested.

Note that many words don't have a solution, such as
those with gikun or jukujikun readings. 
(http://en.wikipedia.org/wiki/Kanji#Other_readings)

This project makes use of KANJIDIC2 and JMdict. Please see:
KANJIDIC2 page: http://www.csse.monash.edu.au/~jwb/kanjidic2/
JMdict page: http://www.csse.monash.edu.au/~jwb/jmdict.html

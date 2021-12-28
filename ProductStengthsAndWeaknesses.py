from lxml import etree
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
import re


aspects = {}
precision = {"pos -> pos": 0, "pos -> neu": 0, "pos -> neg": 0, "neg -> neg": 0, "neg -> neu": 0, "neg -> pos": 0, "neu -> neu": 0, "neu -> pos": 0, "neu -> neg": 0}

# Ensemble de mots négatifs et positifs
with open("E:\Cour\coursTATIA\Projet\\negative-words.txt", "r") as f:
    bad = f.read().splitlines()
with open("E:\Cour\coursTATIA\Projet\\positive-words.txt", "r") as f:
    good = f.read().splitlines()

notWords = {"not", "neither", "never", "nor", "n't"}

# Import des phrases d'une review et de leur aspect

tree = etree.parse("largeDataLaptop.xml")
wordnet_lemmatizer = WordNetLemmatizer()


def get_wordnet_pos(treebank_tag):
    if treebank_tag.startswith('J'):
        return wordnet.ADJ
    elif treebank_tag.startswith('V'):
        return wordnet.VERB
    elif treebank_tag.startswith('N'):
        return wordnet.NOUN
    elif treebank_tag.startswith('R'):
        return wordnet.ADV
    else:
        return None


def lemmatize(pos_data):
    lemma_rew = []
    for word, pos in pos_data:
        if not pos or (get_wordnet_pos(pos) == None):
            lemma_rew.append((word, pos))
        else:
            lemma = wordnet_lemmatizer.lemmatize(
                word, pos=get_wordnet_pos(pos))
            lemma_rew.append((lemma, pos))
    return lemma_rew

for sentence in tree.xpath("/Reviews/Review/sentences/sentence"):

    print("ANALYSED :", sentence[0].text)

    # cleaning the sentence
    wordsArray = sentence[0].text
    wordsArray = wordsArray.lower()
    wordsArray = re.sub('[^a-z ]+', '', wordsArray)

    # TOKENIZER
    wordsArray = word_tokenize(wordsArray)

    # POS TAGGING
    wordsArray = pos_tag(wordsArray)

    # LEMMATIZER
    wordsArray = lemmatize(wordsArray)

    print(wordsArray)

    errorMade = 0

    phraseSentiment = 0
    '''
    0 -> neutral
    1 -> positif
    -1 -> negatif
    2 -> conflicted
    '''

    phraseNotNot = 1
    counterNotAffected = 0

    for i in wordsArray:

        if (counterNotAffected > 0):
            counterNotAffected = counterNotAffected - 1
        if (counterNotAffected == 0):
            phraseNotNot = 1

        # Si on recontre un mot "not", cela inverse le sentiment des mots suivants de la phrase
        if(i[0] in notWords):
            phraseNotNot = -1
            counterNotAffected = 3

        # Un mot à sens positif ou negatif met à jour le sentiment de la phrase
        if(i[0] in bad):
            print("NEGATIVE WORD :", i)
            if((wordsArray.index(i) == len(wordsArray)-1) or (not (wordsArray[wordsArray.index(i) + 1][0] in good))):
                phraseSentiment += (-1 * phraseNotNot)
        elif(i[0] in good):
            print("POSITIVE WORD :", i)
            if((wordsArray.index(i) == len(wordsArray)-1) or (not (wordsArray[wordsArray.index(i) + 1][0] in bad))):
                phraseSentiment += (1 * phraseNotNot)

    print("PHRASE SENTIMENT :", phraseSentiment)

    if (phraseSentiment > 0):
        phraseSentiment = 1
    elif (phraseSentiment < 0):
        phraseSentiment = -1
    else:
        phraseSentiment = 0

    if(len(sentence) > 1):
        for opinion in sentence[1]:
            subject = opinion.get('category')
            print("PHRASE SUBJECT :", subject)

            #We add the subject in our subject list if it is not yet in it
            if subject not in aspects.keys():
                aspects[subject] = [0, 0]

            #we add the sentence polarity to its subject(s)
            if(phraseSentiment == 1):
                aspects[subject][0] += 1
            if(phraseSentiment == -1):
                aspects[subject][1] += 1

            #We check if the result was right for our stats
            if (opinion.get('polarity') == "positive"):
                if (phraseSentiment == 1):
                    precision["pos -> pos"] += 1
                elif (phraseSentiment == 0):
                    precision["pos -> neu"] += 1
                    errorMade = 1
                else :
                    precision["pos -> neg"] += 1
                    errorMade = 1
            if (opinion.get('polarity') == "negative"):
                if (phraseSentiment == -1):
                    precision["neg -> neg"] += 1
                elif (phraseSentiment == 0):
                    precision["neg -> neu"] += 1
                    errorMade = 1
                else :
                    precision["neg -> pos"] += 1
                    errorMade = 1
            if (opinion.get('polarity') == "neutral"):
                if (phraseSentiment == -1):
                    precision["neu -> neg"] += 1
                    errorMade = 1
                elif (phraseSentiment == 0):
                    precision["neu -> neu"] += 1
                else :
                    precision["neu -> pos"] += 1
                    errorMade = 1

    if(errorMade == 1):
        errorMade = 0
        print("<---------!!!!!!! ERROR MADE !!!!!!--------->")

    print("")
print("---------------------------------------")
print()
print("RESULTS (aspect : [number good reviews, number bad reviews]) :\n", aspects)
print()
print("fiability of the algorythme:", precision)
print()
precisionRate = (precision["pos -> pos"] + precision["neg -> neg"] + precision["neu -> neu"]) / \
    (precision["pos -> neu"] + precision["pos -> pos"] + precision["pos -> neg"] + precision["neg -> neg"] + precision["neg -> neu"] + precision["neg -> pos"] + precision["neu -> pos"] +  precision["neu -> neg"])
print("percentage of reviews attributed correctly (the higher the better): %.1f" % (precisionRate * 100))
failRate = (precision["pos -> neg"] + precision["neg -> pos"]) / \
    (precision["pos -> neu"] + precision["pos -> pos"] + precision["pos -> neg"] + precision["neg -> neg"] + precision["neg -> neu"] + precision["neg -> pos"] + precision["neu -> pos"] +  precision["neu -> neg"] + precision["neu -> neu"])
print("percentage of reviews attributed to the opposite category (the lower the better): %.1f"% (failRate * 100))
print()

strenghts = {}
weaknesses = {}

def ratio(aspect):
    if(aspect[1] == 0): return 1
    return aspect[0] / (aspect[1] + aspect[0])

temp = {}
for i in aspects:
    if(aspects.get(i)[0] + aspects.get(i)[1] > 9):
        temp[i] = aspects.get(i)
aspects = temp

print("results after removing low-data aspects (<10 reviews): ", aspects)

for i in range (3):
    inverse = [(ratio(value), key) for key, value in aspects.items()]
    strenghts[max(inverse)[1]] = max(inverse)[0]
    aspects.pop(max(inverse)[1])
    weaknesses[min(inverse)[1]] = min(inverse)[0]
    aspects.pop(min(inverse)[1])

print()
print("---------------------------------------")
print()

print("Strengths are:")
for i in strenghts:
    print("- ", i, " with %.1f" % (100 * strenghts.get(i)), "% of positive reviews.")
print("Weaknesses are:")
for i in weaknesses:
    print("- ", i, " with %.1f" % (100 * weaknesses.get(i)), "% of positive reviews.")
print()


'''
CURRENT PROBLEMS: 
-Several different opinions in a single sentence. How to split the sentence and attribute the right opinions to the right subjects?
-Words with several different meanings. For example "like" recognized as positive because of the verb, but sometimes used
 as a comparaison, or clean, considered positive because of the adjective, but can also be used as a verb.
-Opinions that depend on what we are talking about in the current context. "Dry" is not a negative word, but it can be when we talk
 about a dish.

extra: one opinion can insert several inputs for the same subjects. This should be limited, else an opinion saying 10 times "food
is bad" would tank the food rating even though only one person talked bad about it.

tried sentiWordNet but gave way wore results and often analyzed negative as positive or vice-versa, which is worst case scenario
'''

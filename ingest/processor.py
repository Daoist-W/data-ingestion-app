##################################################################################################
'''
    This module enables us to process text using natual language processing
    to extract known entitities - i.e. nouns (person, place, thing)

    It uses Spacy to extract entities based on a pre built model, 
    The model must be downloaded before using spacy.
'''
##################################################################################################
from collections import Counter
from typing import Dict

import spacy

from .debugging import app_logger as log

class DataProcessor():
    
    def __init__(self) -> None:
        log.info('spacy: loading model')
        # en_core_web_sm is the name of the model, found online in a model list
        self.nlp = spacy.load('en_core_web_sm') # instance variable called nlp that is itself an instance of a spacy nlp model
        log.info('spacy: loaded model') # good practice to have logs before and after information that might consume a lot of memory
        self.skip = ['CARDINAL', 'MONEY', 'ORDINAL', 'DATE', 'TIME'] # This is a list of labels to ignore
        pass

    # create a list comprehension, that will return the entity text
    # for each entity in the doc.ents
    # the result of this is going to be a list of strings
    # we will pass this list to a Counter which will return a dictonary
    # in this dictionary, the string list elements are the keys and their count number is the value
    def entities(self, doc) -> Counter:
        t = [e.text.lower() for e in doc.ents if e.label_ not in self.skip]
        return Counter(t) # tracks the number of times each entity is mentioned in the target text

    # this method takes in string arguments and returns a dictionary data structure to store entities counters 't' inside scalably
    def process(self, text: str) -> Dict:
        return {'entities': self.entities(self.nlp(text))}

    def process_message(self, post):
        return None


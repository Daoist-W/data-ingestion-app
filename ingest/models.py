##################################################################################################
'''
    This module provides models used as messages to be passed via messageq.
'''
##################################################################################################

from collections import Counter
from typing import Any, Dict, List, Tuple

from pydantic import Basemodel

class Post(Basemodel):
    '''Post is used to store content and publication from the front-end'''
    content: str # required because we have no default value if none given
    publication: str # required because we have no default value if none given

class ProcessedPost(Basemodel):
    '''ProcessedPost is to store the results of DataProcessor.'''
    publication: str
    entities: Counter = Counter() # remember that our DataProcessor returns a Counter witl all the extracted entitities
    article_count: int = 0 # count number of articles processed, one processed post can consume more than one article
    # later on this will allow us to merge our results into one object
    
    @property
    def pub_key(self) -> str:
        return None
    
    def transform_for_database(self, top_n=2000) -> List[Tuple[str, str, str, Dict]]:
        return None
    
    def __add__(self, other) -> ProcessedPost:
        return self
    

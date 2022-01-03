##################################################################################################
'''
    This module provides methods for persisting processed data to long-term storage.
'''
##################################################################################################


from google.cloud import firestore

from .debugging import app_logger as log
from .models import ProcessedPost

# this is just a dummy function that we can call in our development environment
# this is for testing, when we really don't want to write to the database
# makes testing easier
def persist_no_op(*args, **kwargs):
    pass

# this will return a new firestore client
# becasue this code is going to run inside of google cloud in production, we don't need
# to make any configuration changes
# it will automatically use the credentials of the service account which are used by
# compute engine (what the hell is compute engine?) https://cloud.google.com/compute
# this will be implemented in another sprint but for now these are the dummies/stubs
# we can use to call these functions to test our integration works
def get_database_client():
    return firestore.Client()


def persist(client, pubname, collname, doc_id, document_dict):
    pass


def increment_publication(client, pubname, count):
    pass    
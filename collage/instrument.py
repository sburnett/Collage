class CollageStatus(object):
    """A collection of possible Collage states.

    For sending:

                +-------------------------------------+
                V                                     |
    INIT -> ENCODING -> ENCRYPTING -> EMBEDDING -> UPLOADING -> SUCCESS
                                                      |
                                                      V
                                                   FAILURE

    For receiving:

    INIT -> DOWNLOADING -> EXTRACTING -> DECRYPTING -> DECODING -> SUCCESS
                ^              |            |             |
                +--------------+------------+-------------+

    """
    INIT = 'Initializing'
    ENCODING = 'Encoding'
    ENCRYPTING = 'Encrypting'
    EMBEDDING = 'Embedding'
    UPLOADING = 'Uploading'
    DOWNLOADING = 'Downloading'
    EXTRACTING = 'Extracting'
    DECODING = 'Decoding'
    DECRYPTING = 'Decrypting'
    SUCCESS = 'Done'
    FAILURE = 'Failed'

class Instrument(object):
    """A base class for monitoring Collage's message layer.

    You provide an instance of this class to the message layer.
    The message layer will call the methods at appropriate points
    to alert you of its status.

    """

    def change_status(self, status):
        """The message layer has entered a new state.

        See the CollageStatus class for possible states.

        """
        pass

    def upload_vector(self, num_bytes):
        """The message layer just uploaded a vector to a UGC host."""
        pass

    def upload_chunks(self, num_bytes):
        """The message layer uploaded some chunks inside a vector to a UGC host."""
        pass

    def process_chunks(self, num_bytes):
        """The message layer just decoded some chunks from a vector."""
        pass

    def process_vector(self, num_bytes):
        """The message layer just downloaded a vector from a UGC host."""
        pass

    def message(self, msg):
        pass

    def error(self, msg):
        pass

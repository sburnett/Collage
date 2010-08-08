class CollageStatus(object):
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
    def change_status(self, status):
        pass

    def upload_vector(self, num_bytes):
        pass

    def upload_chunks(self, num_bytes):
        pass

    def process_chunks(self, num_bytes):
        pass

    def process_vector(self, num_bytes):
        pass


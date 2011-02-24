import os
import sys
import glob
import StringIO
import base64
import time

import Image

from collage_vis.database import get_database

def main():
    db = get_database()

    db.add_article_sender("Test article<br/>"*100);

    directory = sys.argv[1]
    filenames = glob.glob(os.path.join(directory, '*.jpg'))
    for filename in filenames:
        img = Image.open(filename)
        img.thumbnail((64, 64))
        outfile = StringIO.StringIO()
        img.save(outfile, 'JPEG')
        db.enqueue_photo(filename, base64.b64encode(outfile.getvalue()))
        time.sleep(1)

    for filename in filenames:
        db.embed_photo(filename)
        time.sleep(1)
        db.upload_photo(filename)

if __name__ == '__main__':
    main()

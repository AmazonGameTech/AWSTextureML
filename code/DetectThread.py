import boto3
import os, glob
import sqlite3
from threading import Thread

#S3 Sample items
BUCKET = "test-sample-images"
KEYFILE = "test.jpg"
totalcount = 0


def detect_labels(bucket, key, imagebytes=None, max_labels=10, min_confidence=0, region="us-east-1"):
    recclient = None
    while not recclient:
        try:
            recclient = boto3.client("rekognition", region)
        except:
            recclient = None

    if imagebytes is None:
        request = {"S3Object": {"Bucket": bucket, "Name": key, }}
    else:
        request = {"Bytes": imagebytes}

    response = recclient.detect_labels(
        Image=request,
        MaxLabels=max_labels,
        MinConfidence=min_confidence,
    )
    return response['Labels']

def open_database(dbfile):
    conn = sqlite3.connect(dbfile)
    c = conn.cursor()

    c.execute("CREATE TABLE IF NOT EXISTS img_data (img_name TEXT, img_label TEXT, img_confidence TEXT)")
    return c, conn

def process_image(filename, dataresults):
    # Now lets load a local file and send it up
    imagefilesize = os.path.getsize(filename)
    if imagefilesize > 5000000 or imagefilesize < 1:
        print("Skipping {0}: {1}".format(imagefilesize, filename))
        return []

    global totalcount
    totalcount = totalcount + 1
    print("Processing[{0}]: {1}".format(totalcount, filename))
    imagefile = open(filename, "rb")
    imagebytes = imagefile.read(imagefilesize)
    imagefile.close()
    labels = detect_labels(None, None, imagebytes)

    dataresults[filename] = labels

def write_to_db(cur,conn, dataresults):

    for key,value in dataresults.items():
        if len(value) > 0:
            for val in value:
                cur.execute("insert into img_data values (?,?,?)", (key, val['Name'], val['Confidence']))

    conn.commit()

def process_files(filelist, cur,conn):

    dataresults = {}

    threads=[]
    for filename in filelist:
        record = cur.execute("select * from img_data where img_name = '{0}'".format(filename))
        if record.rowcount > -1:
            continue

        threads.append(Thread(target=process_image, args=[filename, dataresults]))
        threads[-1].start()

        global totalcount
        if totalcount > 20:
            break

    for thread in threads:
        thread.join()

    write_to_db(cur, conn, dataresults)

def detect_main(root_dir = "", SQLFILE = "imagetable.db"):
    cur, conn = open_database(SQLFILE)
    filelist = []
    counter = 0

    if root_dir.endswith('/') is False:
        root_dir +='/'

    for filename in glob.iglob(root_dir + '**/*.jpg', recursive=False):
        if filename.endswith(".jpg") is False:
            continue

        counter = counter + 1
        filelist.append(filename)
        if counter > 100:
            process_files(filelist, cur, conn)
            filelist.clear()
            counter = 0

    process_files(filelist, cur, conn)

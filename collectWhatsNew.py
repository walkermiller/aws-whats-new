import boto3
import os
import requests
from requests.models import PreparedRequest
from urllib.parse import quote
import json
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s | %(message)s')
directory = "aws-whats-new"
account = boto3.client('sts').get_caller_identity().get('Account')
ids_url = "https://aws.amazon.com/api/dirs/typeahead-suggestions/items"
item_url = "https://aws.amazon.com/api/dirs/items/search/"
s3 = boto3.resource('s3')


# Create a function to create a bucket only if it doesn't exist
def create_bucket(bucket_name):
    if s3.Bucket(bucket_name) not in s3.buckets.all():
        s3.create_bucket(Bucket=bucket_name)

# Create a function that writes pjson to an s3 object
def write_json(pjson, bucket_name, key): 
    s3.Object(bucket_name, key).put(Body=json.dumps(pjson).encode('utf-8'))

# Create a function that makes an https request to a url and recieves json
def get_json(url, params):
    req = PreparedRequest()
    req.prepare_url(url, params)
    logging.debug(req.url)
    return requests.get(req.url).json()

def handler(event, context):
    # Create bucket if it doesn't already exist
    create_bucket("{}-{}".format(directory, account))

    # Record start time
    start_time = time.time()

    # Get all the ids
    # For each id, make a request to get the items for that id
    for id in get_json(ids_url, {'limit':  500})["items"]:
        simple_id = id['id'].replace("typeahead-suggestions#", "")
        logging.info("Gathering what is new for {}".format(simple_id))
        params = {
            'item.directoryId': 'whats-new',
            'sort_by': 'item.additionalFields.postDateTime',
            'sort_order': 'desc',
            'size': 100,
            'item.locale': 'en_US',
            'tags.id': 'whats-new#general-products#{}'.format(simple_id)
        }
        item_news = get_json(url=item_url, params=params)
        if item_news['metadata']['totalHits'] > 0:
            logging.info("Found {} items for {}".format(item_news['metadata']['totalHits'], simple_id))
            write_json(item_news, "{}-{}".format(directory, account), "{}.json".format(simple_id))
        else:
            logging.info("No items found for {}".format(simple_id))

    # Log time difference
    end_time = time.time()
    logging.info("Time elapsed: {} seconds".format(end_time - start_time))

# If main, execute handler
if __name__ == "__main__":
    handler(None, None)                                                               


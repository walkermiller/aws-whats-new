import boto3
import os
import requests
from requests.models import PreparedRequest
from urllib.parse import quote
import json

directory = "aws-whats-new"
account = boto3.client('sts').get_caller_identity().get('Account')
ids_url = "https://aws.amazon.com/api/dirs/typeahead-suggestions/items"
item_url = "https://aws.amazon.com/api/dirs/items/search/"
s3 = boto3.resource('s3')

# create a function to create a bucket only if it doesn't exist
def create_bucket(bucket_name):
    if s3.Bucket(bucket_name) not in s3.buckets.all():
        s3.create_bucket(Bucket=bucket_name)

# create a function that writes pjson to an s3 object
def write_json(pjson, bucket_name, key): 
    s3.Object(bucket_name, key).put(Body=json.dumps(pjson).encode('utf-8'))

# create a function that makes an https request to a url and recieved json
def get_json(url, params):
    req = PreparedRequest()
    req.prepare_url(url, params)
    print(req.url)
    return requests.get(req.url).json()

create_bucket("{}-{}".format(directory, account))

for id in get_json(ids_url, {'limit':  500})["items"]:
    simple_id = id['id'].replace("typeahead-suggestions#", "")
    print(simple_id)
    params = {
        'item.directoryId': 'whats-new',
        'sort_by': 'item.additionalFields.postDateTime',
        'sort_order': 'desc',
        'size': 100,
        'item.locale': 'en_US',
        'tags.id': 'whats-new#general-products#{}'.format(simple_id)
    }

    write_json(get_json(url=item_url, params=params), "{}-{}".format(directory, account), "{}.json".format(simple_id))

                                                                             


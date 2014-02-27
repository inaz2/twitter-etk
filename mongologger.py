# -*- coding: utf-8 -*-

import sys
import codecs
import os
import re
import urllib2
import json
from datetime import datetime, timedelta
import tweepy
from pymongo import MongoClient

import config

sys.stdout = codecs.getwriter('utf-8')(sys.stdout)


def get_auth():
    auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
    auth.set_access_token(config.access_token, config.access_token_secret)
    return auth


def get_db_messages():
    client = MongoClient('localhost', 27017)
    db_messages = client.twitter_etk.messages
    return db_messages


def parse_dt_string(s):
    return datetime.strptime(s, '%a %b %d %H:%M:%S +0000 %Y') + timedelta(hours=+9)


def save_media(screen_name, media_url, created_at):
    save_dir = "pics/%s" % screen_name
    fpath = "%s/%s%s" % (save_dir, created_at.strftime('%Y%m%d-%H%M%S'), os.path.splitext(media_url)[1])

    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)

    f = urllib2.urlopen(media_url)
    data = f.read()
    f.close()

    with open(fpath, 'wb') as f:
        f.write(data)


def start(args):
    auth = get_auth()
    db_messages = get_db_messages()

    class StdOutListener(tweepy.streaming.StreamListener):
        def on_data(self, data):
            message = json.loads(data)
            db_messages.insert(message)

            if 'in_reply_to_status_id' in message:
                for media in message['entities'].get('media', []):
                    created_at = parse_dt_string(message['created_at'])
                    save_media(message['user']['screen_name'], media['media_url'], created_at)

            return True

        def on_error(self, status):
            print status

    l = StdOutListener()
    stream = tweepy.Stream(auth, l)
    stream.userstream()


def search(args):
    db_messages = get_db_messages()
    messages = db_messages.find({'text': {'$exists': True}}).sort('_id', 1).limit(100000)
    args = [arg.decode('utf-8') for arg in args]

    for message in messages:
        if not all(arg in message['text'] for arg in args if arg[0] != '-'):
            continue
        if any(arg[1:] in message['text'] for arg in args if arg[0] == '-'):
            continue

        created_at = parse_dt_string(message['created_at'])
        print '----'
        print "%s (@%s) at %s\n" % (message['user']['name'], message['user']['screen_name'], created_at)
        print "%s\n" % message['text']


def tweets(args):
    if len(args) < 1:
        print >>sys.stderr, "Usage: python %s tweets SCREEN_NAME" % sys.argv[0]
        sys.exit(1)
    screen_name = args[0]

    db_messages = get_db_messages()
    messages = db_messages.find({'user.screen_name': screen_name}).sort('_id', 1).limit(1000)
    user_id = messages[0]['user']['id']
    deleted_messages = db_messages.find({'delete.status.user_id': user_id}).sort('_id', 1).limit(1000)
    deleted_ids = [m['delete']['status']['id'] for m in deleted_messages]

    for message in messages:
        is_deleted = (message['id'] in deleted_ids)

        created_at = parse_dt_string(message['created_at'])
        if is_deleted:
            sys.stdout.write('\x1b[1:30m')
        print '----'
        print "%s (@%s) at %s\n" % (message['user']['name'], message['user']['screen_name'], created_at)
        print "%s\n" % message['text']
        if is_deleted:
            sys.stdout.write('\x1b[0m')


def show_deleted(args):
    db_messages = get_db_messages()
    messages = db_messages.find({'delete': {'$exists': True}}).sort('_id', 1).limit(1000)
    deleted_ids = [m['delete']['status']['id'] for m in messages]
    messages = db_messages.find({'id': {'$in': deleted_ids}}).sort('_id', 1)

    for message in messages:
        created_at = parse_dt_string(message['created_at'])
        print '----'
        print "%s (@%s) at %s\n" % (message['user']['name'], message['user']['screen_name'], created_at)
        print "%s\n" % message['text']


def events(args):
    db_messages = get_db_messages()
    messages = db_messages.find({'text': {'$regex': r'\D\d{1,2}[/月]\d{1,2}'}}).sort('_id', 1).limit(1000)
    events = []

    for message in messages:
        text = message['text']
        m = re.search(r'\D(\d{1,2})[/月](\d{1,2})', text)
        if m:
            month, day = int(m.group(1)), int(m.group(2))
            events.append((month, day, message))

    for month, day, message in sorted(events):
        created_at = parse_dt_string(message['created_at'])
        print '----'
        print "[%02d/%02d] %s (@%s) at %s\n" % (month, day, message['user']['name'], message['user']['screen_name'], created_at)
        print "%s\n" % message['text']


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print >>sys.stderr, "Usage: python %s [start|search|tweets|show_deleted|events] ..." % sys.argv[0]
        sys.exit(1)
    subcommand, args = sys.argv[1], sys.argv[2:]

    if subcommand == 'start':
        start(args)
    elif subcommand == 'search':
        search(args)
    elif subcommand == 'tweets':
        tweets(args)
    elif subcommand == 'show_deleted':
        show_deleted(args)
    elif subcommand == 'events':
        events(args)
    else:
        print >>sys.stderr, "Usage: python %s [start|search|tweets|show_deleted|events] ..." % sys.argv[0]
        sys.exit(1)

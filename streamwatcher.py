import sys
import codecs
import json
import tweepy

import config

sys.stdout = codecs.getwriter('utf-8')(sys.stdout)


def get_api_and_auth():
    auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
    auth.set_access_token(config.access_token, config.access_token_secret)
    api = tweepy.API(auth)
    return api, auth


class StdOutListener(tweepy.streaming.StreamListener):
    def on_data(self, data):
        message = json.loads(data)

        if 'in_reply_to_status_id' in message:
            print "@%s: %s" % (message['user']['screen_name'], message['text'].replace('\n', ' '))

        return True

    def on_error(self, status):
        print status


def track_list(args):
    if len(args) < 1:
        print >>sys.stderr, 'Usage: python %s list "OWNER_SCREEN_NAME/lists/SLUG"' % sys.argv[0]
        sys.exit(1)
    owner_sname, _, slug = args[0].split('/')

    api, auth = get_api_and_auth()
    members = []
    cursor = tweepy.cursor.Cursor(api.list_members, owner_screen_name=owner_sname, slug=slug)
    for page in cursor.pages():
        members.extend(page)
    print ' / '.join(m.name for m in members)
    ids = [m.id_str for m in members]

    l = StdOutListener()
    stream = tweepy.Stream(auth, l)
    stream.filter(follow=ids)


def track_hashtag(args):
    if len(args) < 1:
        print >>sys.stderr, "Usage: python %s hashtag HASHTAG" % sys.argv[0]
        sys.exit(1)
    hashtag = args[0]

    api, auth = get_api_and_auth()
    l = StdOutListener()
    stream = tweepy.Stream(auth, l)
    stream.filter(track=['#'+hashtag])


def hottweets(args):
    threshould = int(args[0]) if len(args) > 0 else 1

    def contains_kanji(s):
        return any(0x4E00 <= ord(c) <= 0x9FFF for c in s)

    class StdOutListener(tweepy.streaming.StreamListener):
        def on_data(self, data):
            message = json.loads(data)

            if 'retweeted_status' in message:
                if not contains_kanji(message['user']['description'] or ''):
                    return True

                tweet = message['retweeted_status']
                retweet_count = tweet.get('retweet_count', 0)
                if retweet_count >= threshould:
                    print "[%d] @%s: %s" % (tweet['retweet_count'], tweet['user']['screen_name'], tweet['text'].replace('\n', ' '))

            return True

        def on_error(self, status):
            print status

    api, auth = get_api_and_auth()
    l = StdOutListener()
    stream = tweepy.Stream(auth, l)
    stream.sample()


def geotagged(args):
    if len(args) < 1:
        print >>sys.stderr, "Usage: python %s geotagged PLACE_NAME" % sys.argv[0]
        sys.exit(1)
    place_name = args[0]

    api, auth = get_api_and_auth()
    places = api.geo_search(query=place_name)
    for place in places:
        if place.bounding_box:
            print place.full_name
            sw, nw, ne, se = place.bounding_box.coordinates[0]
            bounding_box = sw + ne
            break
    else:
        print 'All'
        bounding_box = [-180,-90,180,90]

    class StdOutListener(tweepy.streaming.StreamListener):
        def on_data(self, data):
            message = json.loads(data)

            if message.get('place'):
                print "[%s] @%s: %s" % (message['place']['full_name'], message['user']['screen_name'], message['text'].replace('\n', ' '))
            elif message.get('coordinates'):
                lng, lat = message['coordinates']['coordinates']
                print "[%f,%f] @%s: %s" % (lat, lng, message['user']['screen_name'], message['text'].replace('\n', ' '))

            return True

        def on_error(self, status):
            print status

    l = StdOutListener()
    stream = tweepy.Stream(auth, l)
    stream.filter(locations=bounding_box)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print >>sys.stderr, "Usage: python %s [list|hashtag|hottweets|geotagged] ..." % sys.argv[0]
        sys.exit(1)
    subcommand, args = sys.argv[1], sys.argv[2:]

    if subcommand == 'list':
        track_list(args)
    elif subcommand == 'hashtag':
        track_hashtag(args)
    elif subcommand == 'hottweets':
        hottweets(args)
    elif subcommand == 'geotagged':
        geotagged(args)
    else:
        print >>sys.stderr, "Usage: python %s [list|hashtag|hottweets|geotagged] ..." % sys.argv[0]
        sys.exit(1)

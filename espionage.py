import sys
import codecs
import tweepy
from datetime import timedelta
from collections import Counter

import config

sys.stdout = codecs.getwriter('utf-8')(sys.stdout)


def get_api():
    auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
    auth.set_access_token(config.access_token, config.access_token_secret)
    api = tweepy.API(auth)
    return api


def timeline(args):
    if len(args) < 1:
        print >>sys.stderr, "Usage: python %s timeline SCREEN_NAME" % sys.argv[0]
        sys.exit(1)
    screen_name = args[0]

    api = get_api()
    tweets = api.user_timeline(screen_name=screen_name, count=200, include_rts=True)
    replies = api.search(q='to:'+screen_name, result_type='recent', count=100, include_entities=False)
    favs = api.favorites(screen_name=screen_name, count=200, include_entities=False)

    lines = []
    for t in tweets:
        t.created_at += timedelta(hours=+9)
        line = "[%s] \x1b[32m%s: %s\x1b[0m" % (t.created_at, t.user.screen_name, t.text.replace('\n', ' ').replace('&lt;', '<').replace('&gt;', '>'))
        lines.append(line)
    for t in replies:
        t.created_at += timedelta(hours=+9)
        line = "[%s] \x1b[37m  %s: %s\x1b[0m" % (t.created_at, t.user.screen_name, t.text.replace('\n', ' ').replace('&lt;', '<').replace('&gt;', '>'))
        lines.append(line)
    for t in favs:
        t.created_at += timedelta(hours=+9)
        line = "[%s] \x1b[37m  %s: %s\x1b[0m" % (t.created_at, t.user.screen_name, t.text.replace('\n', ' ').replace('&lt;', '<').replace('&gt;', '>'))
        try:
            lines.remove(line)
        except ValueError:
            pass
        line = "[%s] \x1b[36m* %s: %s\x1b[0m" % (t.created_at, t.user.screen_name, t.text.replace('\n', ' ').replace('&lt;', '<').replace('&gt;', '>'))
        lines.append(line)

    for line in sorted(lines):
        print line


def fans(args):
    if len(args) < 1:
        print >>sys.stderr, "Usage: python %s fans SCREEN_NAME" % sys.argv[0]
        sys.exit(1)
    screen_name = args[0]

    api = get_api()
    tweets = api.search(q='to:'+screen_name, result_type='recent', count=100, include_entities=False)
    ctr = Counter(t.user.screen_name for t in tweets)
    sname2name = dict((t.user.screen_name, t.user.name) for t in tweets)
    sname2desc = dict((t.user.screen_name, t.user.description.replace('\n', ' ')) for t in tweets)

    for sname, count in ctr.most_common():
        print "%d\t%s\t%s\t\x1b[1;30m%s\x1b[0m" % (count, sname, sname2name[sname], sname2desc[sname])


def sources(args):
    if len(args) < 1:
        print >>sys.stderr, "Usage: python %s sources SCREEN_NAME" % sys.argv[0]
        sys.exit(1)
    screen_name = args[0]

    api = get_api()
    tweets = api.user_timeline(screen_name=screen_name, count=200, include_rts=False)
    ctr = Counter(t.source for t in tweets)

    for source, count in ctr.most_common():
        print "%d\t%s" % (count, source)


def diff_following(args):
    if len(args) < 2:
        print >>sys.stderr, "Usage: python %s diff_following SCREEN_NAME SCREEN_NAME..." % sys.argv[0]
        sys.exit(1)
    screen_name, exclude_screen_names = args[0], args[1:]

    api = get_api()
    f_ids = api.friends_ids(screen_name=screen_name)
    f_ids = set(f_ids)

    for sname in exclude_screen_names:
        exclude_f_ids = api.friends_ids(screen_name=sname)
        f_ids -= set(exclude_f_ids)

    f_ids = list(f_ids)
    friends = []
    for i in xrange(len(f_ids)/100+1):
        ids = f_ids[100*i:100*(i+1)]
        users = api.lookup_users(user_ids=ids)
        friends.extend(users)

    for user in friends:
        print "%s\t%s\t\x1b[1;30m%s\x1b[0m" % (user.screen_name, user.name, user.description.replace('\n', ' '))


def following_protected(args):
    if len(args) < 1:
        print >>sys.stderr, "Usage: python %s following_protected SCREEN_NAME" % sys.argv[0]
        sys.exit(1)
    screen_name = args[0]

    api = get_api()
    f_ids = api.friends_ids(screen_name=screen_name)
    friends = []
    for i in xrange(len(f_ids)/100+1):
        ids = f_ids[100*i:100*(i+1)]
        users = api.lookup_users(user_ids=ids)
        friends.extend(users)

    for user in friends:
        if not user.protected:
            continue
        print "%s\t%s\t\x1b[1;30m%s\x1b[0m" % (user.screen_name, user.name, user.description.replace('\n', ' '))


def dump_tweets(args):
    if len(args) < 1:
        print >>sys.stderr, """Usage: python %s dump_tweets SCREEN_NAME

Note: You can dump only recent 3200 tweets.""" % sys.argv[0]
        sys.exit(1)
    screen_name = args[0]

    api = get_api()
    cursor = tweepy.cursor.Cursor(api.user_timeline, screen_name=screen_name, count=200, include_rts=True)
    for t in cursor.items():
        t.created_at += timedelta(hours=+9)
        if getattr(t, 'in_reply_to_status_id', None):
            print "[%s] \x1b[1;30m%s: %s\x1b[0m" % (t.created_at, t.user.screen_name, t.text.replace('\n', ' ').replace('&lt;', '<').replace('&gt;', '>'))
        elif getattr(t, 'retweeted_status', None):
            print "[%s] \x1b[32m%s: %s\x1b[0m" % (t.created_at, t.user.screen_name, t.text.replace('\n', ' ').replace('&lt;', '<').replace('&gt;', '>'))
        else:
            print "[%s] \x1b[37m%s: %s\x1b[0m" % (t.created_at, t.user.screen_name, t.text.replace('\n', ' ').replace('&lt;', '<').replace('&gt;', '>'))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print >>sys.stderr, "Usage: python %s [timeline|fans|sources|diff_following|following_protected|dump_tweets] ..." % sys.argv[0]
        sys.exit(1)
    subcommand, args = sys.argv[1], sys.argv[2:]

    if subcommand == 'timeline':
        timeline(args)
    elif subcommand == 'fans':
        fans(args)
    elif subcommand == 'sources':
        sources(args)
    elif subcommand == 'diff_following':
        diff_following(args)
    elif subcommand == 'following_protected':
        following_protected(args)
    elif subcommand == 'dump_tweets':
        dump_tweets(args)
    else:
        print >>sys.stderr, "Usage: python %s [timeline|fans|sources|diff_following|following_protected|dump_tweets] ..." % sys.argv[0]
        sys.exit(1)

import urllib.request, urllib.parse, urllib.error
import twurl
import json
import sqlite3
import ssl
import time

TWITTER_URL = 'https://api.twitter.com/1.1/friends/list.json'

conn = sqlite3.connect('friends3.sqlite')
cur = conn.cursor()

cur.execute('''CREATE TABLE IF NOT EXISTS People
            (id INTEGER PRIMARY KEY, name TEXT UNIQUE, retrieved INTEGER, friends INTEGER, followers INTEGER, friendRank REAL)''')
cur.execute('''CREATE TABLE IF NOT EXISTS Follows
            (from_id INTEGER, to_id INTEGER, UNIQUE(from_id, to_id))''')

# Ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

error = 0       # initial value for error code if pulling username fails
cursor = -1     # sets initial cursor value for friends list to allow it to grab first page of results.
acct = input('Enter a Twitter account, or quit: ')

while True:
# first get the next acct in the loop

    if (acct == 'quit'): break
#    print('before lookup up, acct=', acct)
    if (len(acct) < 1) or (cursor == 0) :         # if no acct entered or last account fully retrieved (cursor=0), retrieve next unretrieved acct in database
        cur.execute('SELECT id, name FROM People WHERE retrieved=0 LIMIT 1')
        try:
            (id, acct) = cur.fetchone()
#            print('just looked up', acct, 'with retrieved status:', retr)
            cursor = -1     # reset cursor to -1 to retrieve first page of friends
        except:
            print('No unretrieved Twitter accounts found')
            continue
    else:                       # assume acct entered
        cur.execute('SELECT id FROM People WHERE name = ? LIMIT 1',
                    (acct, ))
        try:                    # check if acct already in db
            id = cur.fetchone()[0]
        except:                 # assume new acct, enter into db
# I could do an API call here on the new starting user to grab their friends and followers counts then insert into their row.
            cur.execute('''INSERT OR IGNORE INTO People
                        (name, retrieved) VALUES (?, 0)''', (acct, ))
            conn.commit()
            if cur.rowcount != 1:
                print('Error inserting account:', acct)
                continue
            id = cur.lastrowid
#    if error == 1:
#        print('just entered error conditional')
#        error = 0
#        print('reset error flag to:', error)
#        continue
# now we have valid acct and id, push request to twitter API
    print('------------------------------')
    print('Retrieving account', acct)
    while cursor != 0:
        url = twurl.augment(TWITTER_URL, {'screen_name': acct, 'cursor': cursor, 'count': '200'}) # add 'cursor': next_cursor between screen_name and count
#        print(url)
        try:
            connection = urllib.request.urlopen(url, context=ctx)
        except Exception as err:
            print('Failed to Retrieve', err)
            # need to set retrieved value to 4 so that it doesn't try to read again
            cur.execute('UPDATE People SET retrieved=4 WHERE name = ?', (acct, ))
            conn.commit()
#            error = 1
            cursor = 0      # need to reset cursor, otherwise it nevers enter the check retrieve=0 SQL lookup to grab a new user
#            print('error after fail to retrieve:', error)
            time.sleep(60)
            break

    # now we have succesfully retrieved info from Twitter, get json data and header for remaining count
        data = connection.read().decode()
        headers = dict(connection.getheaders())

        print('Remaining', headers['x-rate-limit-remaining'])

        try:
            js = json.loads(data)
        except:
            print('Unable to parse json')
            print(data)
            break

        # Debugging
        # print(json.dumps(js, indent=4))
        # debugging: write out the json file for friends list. Want to find next_cursor
        # file = open('dump.json', 'w')
        # file.write(json.dumps(js, indent=4))
        # file.close()


        if 'users' not in js:
            print('Incorrect JSON received')
            print(json.dumps(js, indent=4))
            continue

        cur.execute('UPDATE People SET retrieved=1 WHERE name = ?', (acct, ))
        countnew = 0
        countold = 0
        for u in js['users']:
            friend = u['screen_name']
            numFriends = u['friends_count']         # grab # friends and followers the user has.
            numFollowers = u['followers_count']
            print(friend)
#            print(friend, 'friends:', numFriends, 'followers:', numFollowers)
            cur.execute('SELECT id FROM People WHERE name = ? LIMIT 1',
                        (friend, ))
            try:
                friend_id = cur.fetchone()[0]
                countold = countold + 1
            except:
                if numFriends < 2000:       # filter out users with excessive >2000 friends. Set retrieved = 2 so they won't be crawled in the future.
                    cur.execute('''INSERT OR IGNORE INTO People (name, retrieved, friends, followers)
                            VALUES (?, 0, ?, ?)''', (friend, numFriends, numFollowers))
                else:
                    cur.execute('''INSERT OR IGNORE INTO People (name, retrieved, friends, followers)
                            VALUES (?, 2, ?, ?)''', (friend, numFriends, numFollowers))
                # conn.commit()
                if cur.rowcount != 1:
                    print('Error inserting account:', friend)
                    continue
                friend_id = cur.lastrowid
                countnew = countnew + 1
            cur.execute('''INSERT OR IGNORE INTO Follows (from_id, to_id)
                        VALUES (?, ?)''', (id, friend_id))
        print('New accounts=', countnew, ' revisited=', countold)
        print('Remaining', headers['x-rate-limit-remaining'])
        cursor = js['next_cursor']
        conn.commit()
        time.sleep(60)         # 1 minute timer between each loop to account for API rate limiting
cur.close()

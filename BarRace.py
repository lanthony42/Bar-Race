import os
import re
import csv
from collections import defaultdict
import arrow
import dotenv
import urllib.request
import pylast

# Replace with your own LastFm API key and secret
dotenv.load_dotenv()
API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
fm = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET)

datedefault = 'DD MMM YYYY HH:mm'
dateformat = 'MMM D YYYY'

# Change the following for personal usage:
mode = 'artist' # 'artist', 'album', 'track'
name = 'iamthedj3000' # LastFm Username
threshold = 5 # Minimum amount of plays
use_tags = True # Toggle categorization

def prepare_csv(filename):
    # Ensure header of csv file is:
    # artist, album, track, date
    
    working_list = []
    all_dates = [mode, 'image', 'genre']

    # Add and format dates
    with open(filename, 'r', encoding='utf-8') as _filehandler:
        csv_file_reader = csv.DictReader(_filehandler)
        for row in reversed(list(csv_file_reader)):
            try:
                row['date'] = arrow.get(row['date'], datedefault).format(dateformat)
            except:
                continue
            row[mode] = "'" + row[mode] + "'~'" + row['artist'] + "'"

            working_list.append(row)
            if row['date'] not in all_dates:
                all_dates.append(row['date'])
                
    # Add play counts
    item_play_count = defaultdict(int)
    d = defaultdict(dict)
    for row in working_list:
        if d[row[mode]].get(row['date']):
            d[row[mode]][row['date']] += 1
        else:
            d[row[mode]][row['date']] = 1

    # Compile list
    final_list = []
    images = extract_image() if mode == 'artist' else {}
    for item in d:
        new_row = {}
        for date in d[item]:
            item_play_count[item] += d[item][date]
            new_row[date] = item_play_count[item]

        if item_play_count[item] > threshold:
            new_row[mode] = get_name(item)
            print(get_artist(item) + "    " + get_name(item)) # Debug
            if mode == 'artist':
                try:
                    new_row['image'] = images[get_artist(item)]
                except:
                    new_row['image'] = ''
                    print(get_artist(item) + ' FAILLLLLLLLLLLLLLLLLLLLLLL')
            else:
                new_row['image'] = get_image(mode, item)
            new_row['genre'] = get_tag(mode, item) if use_tags else ''
            final_list.append(new_row)

    with open(name + "_processed.csv", 'w', encoding='utf-8') as f:
        w = csv.DictWriter(f, all_dates)
        w.writeheader()
        for each in final_list:
            w.writerow(each)

def extract_image():
    contents = bytes(urllib.request.urlopen(f'https://www.last.fm/user/{name}/library/artists?date_preset=ALL').read()).decode('utf-8')
    pagecount = max(int(i) for i in re.findall('">(\d+)</[ab]>', contents))
    print(f'{pagecount} pages to load')
    
    extracted = {}
    for i in range(0, pagecount):
        found = re.findall('src="(https://lastfm.freetls.fastly.net/i/u/avatar70s/[a-z0-9]+).[a-z]+"\s+alt="Avatar for ([^"]*)"', contents)
        extracted.update({get_parsed(items[1]): items[0].replace('avatar70s', 'avatar150s') for items in found})
        print(f'Page {i+1} done...')

        contents = bytes(urllib.request.urlopen(f'https://www.last.fm/user/{name}/library/artists?date_preset=ALL&page={i+2}').read()).decode('utf-8')
    extracted['King Crimson'] = 'https://static.independent.co.uk/s3fs-public/thumbnails/image/2019/09/26/15/King-Crimson-1974.jpg' # Thank Mr. Fripp
    return extracted

def get_image(mode, item):
    try:
        return get_resource(mode, item).get_cover_image()
    except:
        return 'https://lastfm.freetls.fastly.net/i/u/64s/c6f59c1e5e7240a4c0d427abd71f3dbb'

def get_tag(mode, item):
    try:
        return str(get_resource(mode, item).get_top_tags(limit=1)[0][0]).lower()
    except:
        return ''

def get_resource(mode, item):
    if mode == 'artist':
        return fm.get_artist(get_artist(item))
    elif mode == 'album':
        return fm.get_album(get_artist(item), get_name(item))
    elif mode == 'track':
        return fm.get_track(get_artist(item), get_name(item))
    return ''

def get_parsed(item):    
    parselist = {',': '', '&amp;': '&', '&#39;': '\''}
    out = item

    for string in parselist.keys():
        if string in item:
            out = out.replace(string, parselist[string])
    return out

def get_artist(item):
    return item[item.find("'~'")+3:len(item)-1]

def get_name(item):
    return re.sub('\(.+\)$', '', item[1:item.find("'~'")])

prepare_csv(name + '.csv')
input()

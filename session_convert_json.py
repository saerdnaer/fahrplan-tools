# -*- coding: UTF-8 -*-

import requests
import json
from collections import OrderedDict
import dateutil.parser
from datetime import datetime
from datetime import timedelta
import pytz
import os.path

days = []
de_tz = pytz.timezone('Europe/Amsterdam')

def main():
    print "Requesting sessions"
    sessions_r = requests.get(
        'https://events.ccc.de/congress/2014/wiki/index.php?title=Special:Ask', 
        params=(
            ('q', '[[Category:Session]]'),
            ('po', "\r\n".join([
                '?Has description',
                '?Has session type', 
                '?Held in language', 
                '?Is organized by', 
                '?Has website'])
            ),
            ('p[format]', 'json'),
            ('p[limit]', 500),
        ),
        verify=False #'cacert.pem'
    )
    
    print "Requesting events"
    events_r = requests.get(
        'https://events.ccc.de/congress/2014/wiki/index.php?title=Special:Ask', 
        params=(
            ('q', '[[Has object type::Event]]'),
            ('po', "\r\n".join([
                '?Has subtitle',
                '?Has start time', '?Has end time', '?Has duration',
                '?Has session location', 
                '?Has event track',
                '?Has color'])
            ),
            ('p[format]', 'json'),
            ('p[limit]', 500),
        ),
        verify=False #'cacert.pem'
    )
    
    print "Requesting schedule"
    schedule_r = requests.get(
        'https://events.ccc.de/congress/2014/Fahrplan/schedule.json', 
        verify=False #'cacert.pem'
    )
    
    #sessions = sessions_r.json()['results']
    sessions = json.JSONDecoder(object_pairs_hook=OrderedDict).decode(sessions_r.text)['results']
    #events = events_r.json()['results']
    events = json.JSONDecoder(object_pairs_hook=OrderedDict).decode(events_r.text)['results']
    full_schedule = json.JSONDecoder(object_pairs_hook=OrderedDict).decode(schedule_r.text)
    
    workshop_schedule = copy_base_structure(full_schedule, 5);
    
    for day in workshop_schedule["schedule"]["conference"]["days"]:
        days.append({
            'index' : day['index'],
            'data' : day['date'],
            'start': dateutil.parser.parse(day['day_start']),
            'end': dateutil.parser.parse(day['day_end']),
        })
    
   # print json.dumps(workshop_schedule, indent=2)
    #print json.dumps(days, indent=2);
    
    print "Processing" 
    
    out = {}
    schedule = dict()
    
    for event_wiki_name, event_r in events.iteritems():
        print event_wiki_name
        event = event_r['printouts']
        temp = event_wiki_name.split('# ', 2);
        session_wiki_name = temp[0]
        guid = temp[1]
        
        if len(event['Has start time']) < 1:
            print "  has no start time"
            day_s = None
        else:
            start_time = de_tz.localize(datetime.fromtimestamp(int(event['Has start time'][0])))
            day_s = get_day(start_time)

        room = ''
        workshop_room_session = False
        # TODO can one Event take place in multiple rooms? 
        if len(event['Has session location']) == 1:
            #print event['Has session location']
            room = event['Has session location'][0]['fulltext'].split(':', 1)[1]
        
            workshop_room_session = (event['Has session location'][0]['fulltext'].split(':', 1)[0] == 'Room')
        elif len(event['Has session location']) == 0:
            print "  has no room yet"
        else:
            raise "  has multipe rooms ???"
        
        session = sessions[session_wiki_name]['printouts'];
        session['Has title'] = [session_wiki_name.split(':', 2)[1]]
        session['fullurl'] = sessions[session_wiki_name]['fullurl']
        
        # http://stackoverflow.com/questions/22698244/how-to-merge-two-json-string-in-python
        # This will only work if there are unique keys in each json string.
        combined = dict(session.items() + event.items())
        
        
        #print json.dumps(combined, indent=4)    
        
        out[event_wiki_name] = combined
        if workshop_room_session and day_s is not None:
            '''
            if day_s not in schedule:
                schedule[day_s] = dict()
            if room not in schedule[day]:
                schedule[day_s][room] = list()
            schedule[day_s][room].append(combined)
            '''
            
            day = int(day_s)
            event_n = OrderedDict([
                ('id', get_id(guid)),
                ('guid', guid),
                ('logo', None),
                ('date', start_time.isoformat()),
                ('start', start_time.strftime('%H,%M')),
                ('duration', str(timedelta(minutes=event['Has duration'][0])) ),
                ('room', room),
                ('slug', ''),
                #('slug', '31c3_-_6561_-_en_-_saal_1_-_201412271100_-_31c3_opening_event_-_erdgeist_-_geraldine_de_bastion',
                ('title', session['Has title'][0]),
                ('subtitle', "\n".join(event['Has subtitle']) ),
                ('track', 'self orgnaized sessions'),
                ('type', session['Has session type'][0].lower()),
                ('language', session['Held in language'][0].split(' - ', 1)[0] ),
                ('abstract', ''),
                ('description', "\n".join(session['Has description']) ),
                ('persons', [{
                    'id': 0,
                    'full_public_name': p['fulltext'].split(':', 1)[1],
                    'url': p['fullurl']
                } for p in session['Is organized by'] ]),
                ('links', session['Has website'] + [session['fullurl']])             
            ])
            
            wsdr = workshop_schedule["schedule"]["conference"]["days"][day]["rooms"]
            if room not in wsdr:
                wsdr[room] = list();
            wsdr[room].append(event_n);
            
            fsdr = full_schedule["schedule"]["conference"]["days"][day]["rooms"]
            if room not in fsdr:
                fsdr[room] = list();
            fsdr[room].append(event_n);
            
        
    #print json.dumps(workshop_schedule, indent=2)
    
    with open("sessions_complete.json", "w") as fp:
        json.dump(out, fp, indent=4)

    
    with open("workshops.schedule.json", "w") as fp:
        json.dump(workshop_schedule, fp, indent=4)
        
    with open("everything.schedule.json", "w") as fp:
        json.dump(full_schedule, fp, indent=4)

    
    print 'end'

def get_day(start_time):
    for day in days:
        if day['start'] > start_time < day['end']:
            return day['index']
    
    return '0'

sos_ids = dict()
next_id = 100

if os.path.isfile("_sos_ids.json"):
    with open("_sos_ids.json", "r") as fp:
        #sos_ids = json.load(fp) 
        # maintain order from file
        temp = fp.read()
        sos_ids = json.JSONDecoder(object_pairs_hook=OrderedDict).decode(temp)
    
  
    
    
    next_id = max(sos_ids.itervalues())+1

def get_id(guid):
    global sos_ids, next_id
    if guid not in sos_ids:
        #generate new id
        sos_ids[guid] = next_id
        next_id = next_id + 1  
    
    return sos_ids[guid]


def copy_base_structure(subtree, level):  
    ret = OrderedDict()
    if level > 0:
        for key, value in subtree.iteritems():
            if isinstance(value, (basestring, int)):
                ret[key] = value
            elif isinstance(value, list):
                ret[key] = copy_base_structure_list(value, level-1) 
            else:
                ret[key] = copy_base_structure(value, level-1) 
    return ret

def copy_base_structure_list(subtree, level):  
    ret = []
    if level > 0:
        for value in subtree:
            if isinstance(value, (basestring, int)):
                ret.append(value)
            elif isinstance(value, list):
                ret.append(copy_base_structure_list(value, level-1))
            else:
                ret.append(copy_base_structure(value, level-1)) 
    return ret

# https://events.ccc.de/congress/2014/wiki/index.php?title=Special:Ask
# &q=[[Category:Session]] OR [[Has object type::Event]]
# &po=?Has event title ?Has subtitle ?Has start time ?Has end time ?Has duration ?Has description ?Has session location ?Has session type ?Held in language ?Is organized by ?Has description ?Has url ?Has event track 
# &eq=yes
# &p[format]=broadtable&sort_num=&order_num=ASC
# &p[limit]=500&p[offset]=&p[link]=all&p[sort]=
# &p[order][ascending]=1&p[headers]=show&p[mainlabel]=&p[intro]=&p[outro]=&p[searchlabel]= further results&p[default]=&p[class]=sortable wikitable smwtable
# &eq=yes


# from http://stackoverflow.com/a/10076823

#from lxml import etree as ET
from xml.etree import cElementTree as ET

def dict_to_etree(d):
    def _to_etree(d, root):
        if not d:
            pass
        elif isinstance(d, basestring):
            root.text = d
        elif isinstance(d, int):
            root.text = str(d)
        elif (isinstance(d, dict) or isinstance(d, OrderedDict)):
            for k,v in d.items():
                assert isinstance(k, basestring)
                if k.startswith('#'):
                    assert k == '#text' and isinstance(v, basestring)
                    root.text = v
                elif k.startswith('@'):
                    assert isinstance(v, basestring)
                    root.set(k[1:], v)
                elif isinstance(v, list):
                    for e in v:
                        _to_etree(e, ET.SubElement(root, k))
                else:
                    _to_etree(v, ET.SubElement(root, k))
        else: assert d == 'invalid type'
    #print d
    assert (isinstance(d, dict) or isinstance(d, OrderedDict)) and len(d) == 1
    tag, body = next(iter(d.items()))
    node = ET.Element(tag)
    _to_etree(body, node)
    return ET.tostring(node)


if __name__ == '__main__':
    main()
    
# TODO write sos_ids to disk
with open("_sos_ids.json", "w") as fp:
    json.dump(sos_ids, fp, indent=4)
    
#os.system("git add *.json")
#os.system("git commit -m 'updates from " + str(datetime.now()) +  "'")
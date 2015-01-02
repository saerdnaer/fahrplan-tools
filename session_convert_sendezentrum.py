# -*- coding: UTF-8 -*-

import requests
import json
from collections import OrderedDict
import dateutil.parser
from datetime import datetime
from datetime import timedelta
import pytz
import os.path
import csv
import hashlib

days = []
sos_ids = {}
next_id = 1000
de_tz = pytz.timezone('Europe/Amsterdam')

#config
offline = True
date_format = '%d/%m/%y %I:%M %p'


def main():
        
    print 'Requesting schedule'
    
    if offline:
        with open('schedule.json') as file:
            schedule_json = file.read()
        full_schedule = json.JSONDecoder(object_pairs_hook=OrderedDict).decode(schedule_json)
    
    else:
        schedule_r = requests.get(
            'https://events.ccc.de/congress/2014/Fahrplan/schedule.json', 
            verify=False #'cacert.pem'
        )        
        full_schedule = json.JSONDecoder(object_pairs_hook=OrderedDict).decode(schedule_r.text)

    
    
    schedule = copy_base_structure(full_schedule, 5);
    
    for day in full_schedule['schedule']['conference']['days']:
        days.append({
            'index' : day['index'],
            'data' : day['date'],
            'start': dateutil.parser.parse(day['day_start']),
            'end': dateutil.parser.parse(day['day_end']),
        })
    

    print 'Processing' 
    
    out = {}
    csv_schedule = []
    
    with open('sendezentrum.csv', 'rb') as f:
        reader = csv.reader(f)
        keys = reader.next()
        keys[0] = 'Weekday'
        for row in reader:
            i = 0
            items = {}
            for value in row:
                items[keys[i].strip()] = value
                i += 1
            csv_schedule.append(items)       
    
    
    for event in csv_schedule:        
        if True:
            '''
            if day_s not in schedule:
                schedule[day_s] = dict()
            if room not in schedule[day]:
                schedule[day_s][room] = list()
            schedule[day_s][room].append(combined)
            '''
            
            room = 'Saal 5'
            guid = hashlib.md5(room + event['Date'] + event['Time Start']).hexdigest()
            
            def norm(timestr):
                timestr = timestr.replace('p.m.', 'pm')
                timestr = timestr.replace('a.m.', 'am')
                ## workaround for failure in input file format
                if timestr.startswith('0:00'):
                    timestr = timestr.replace('0:00', '12:00')
                    
                return timestr
                
            
            start_time   = datetime.strptime( event['Date'] + ' ' + norm(event['Time Start']), date_format)
            if event['Time End'] != 'tbd':
                end_time = datetime.strptime( event['Date'] + ' ' + norm(event['Time End']  ), date_format)
            else:    
                end_time = start_time + timedelta(hours=2)
            
            duration = (end_time - start_time).seconds/60
            
            day = int(start_time.strftime('%d')) - 26
            
            event_n = OrderedDict([
                ('id', get_id(guid)),
                ('guid', guid),
                ('logo', None),
                ('date', start_time.isoformat()),
                ('start', start_time.strftime('%H:%M')),
                #('duration', str(timedelta(minutes=event['Has duration'][0])) ),
                ('duration', '%d:%02d' % divmod(duration, 60) ),
                ('room', room),
                ('slug', ''),
                #('slug', '31c3_-_6561_-_en_-_saal_1_-_201412271100_-_31c3_opening_event_-_erdgeist_-_geraldine_de_bastion',
                ('title', event['Podcast'].strip().decode('utf-8') + ': ' + event['Titel'].decode('utf-8')),
                ('subtitle', ''),
                ('track', 'Sendezentrum'),
                ('type', 'Podcast'),
                ('language', 'de' ),
                ('abstract', ''),
                ('description', '' ),
                ('persons', [{
                    'id': 0,
                    #'full_public_name': p.decode('utf-8'),
                    '#text': p.decode('utf-8'),
                } for p in event['Teilnehmer'].split(',') ]),
                ('links', [])             
            ])
            
            print event_n['title']
            
            wsdr = schedule['schedule']['conference']['days'][day-1]['rooms']
            if room not in wsdr:
                wsdr[room] = list();
            wsdr[room].append(event_n);
            
            
        
    #print json.dumps(workshop_schedule, indent=2)
    
    with open('sendezentrum.schedule.json', 'w') as fp:
        json.dump(schedule, fp, indent=4)
        
    with open('sendezentrum.schedule.xml', 'w') as fp:
        fp.write(dict_to_etree(schedule));
            
    print 'end'


def get_day(start_time):
    for day in days:
        if day['start'] > start_time < day['end']:
            return day['index']
    
    return '0'

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




# dict_to_etree from http://stackoverflow.com/a/10076823

from lxml import etree as ET
#from xml.etree import cElementTree as ET

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
                elif k == 'id' or k == 'guid':
                    if isinstance(v, basestring):
                        root.set(k, v)
                    elif isinstance(v, int):
                        root.set(k, str(v))
                    else:
                        print k, v
                elif isinstance(v, list):
                    for e in v:
                        print e
                        print k
                        if k == 'Saal 5':
                            k = 'event'
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

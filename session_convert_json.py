import requests
import json

sessions_r = requests.get(
    'https://events.ccc.de/congress/2014/wiki/index.php?title=Special:Ask', 
    params=(
        ('q', '[[Category:Session]]'),
        ('po', "\r\n".join([
            '?Has description',
            '?Has session type', '?Held in language', 
            '?Is organized by', 
            '?Has website'])
        ),
        #('eq', 'yes'),
        #('order_num', 'ASC'),
        ('p[format]', 'json'),
        ('p[limit]', 500),
        #('p[sort]', ''),
        ('p[order][ascending]', 1),
        #('p[link]', 'all'),
        #('ea', 'yes')
    ),
    verify=False #'cacert.pem'
)

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

sessions = sessions_r.json()['results'];
events = events_r.json()['results'];

out = {}

for event_wiki_name, event in events.iteritems():
    print event_wiki_name
    temp = event_wiki_name.split('# ', 2);
    session_wiki_name = temp[0]
    guid = temp[1]
    
    session = sessions[session_wiki_name];
    
    # http://stackoverflow.com/questions/22698244/how-to-merge-two-json-string-in-python
    # This will only work if there are unique keys in each json string.
    combined = dict(session['printouts'].items() + event['printouts'].items())
    combined['Has title'] = session_wiki_name.split(':', 1)[1]
    
    #print json.dumps(combined, indent=4)    
    
    out[event_wiki_name] = combined;
    
fp = open("sessions_complete.json", "w")
json.dump(out, fp, indent=4)
fp.close()
print 'end'

# https://events.ccc.de/congress/2014/wiki/index.php?title=Special:Ask
# &q=[[Category:Session]] OR [[Has object type::Event]]
# &po=?Has event title ?Has subtitle ?Has start time ?Has end time ?Has duration ?Has description ?Has session location ?Has session type ?Held in language ?Is organized by ?Has description ?Has url ?Has event track 
# &eq=yes
# &p[format]=broadtable&sort_num=&order_num=ASC
# &p[limit]=500&p[offset]=&p[link]=all&p[sort]=
# &p[order][ascending]=1&p[headers]=show&p[mainlabel]=&p[intro]=&p[outro]=&p[searchlabel]= further results&p[default]=&p[class]=sortable wikitable smwtable
# &eq=yes
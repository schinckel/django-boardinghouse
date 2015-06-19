import codecs
import re
import os

from bs4 import BeautifulSoup

ONREADY = re.compile('\W*jQuery\(document\).ready\((?P<handler>.*)\);\W*')

scripts = []
styles = []
bodies = []
processed = []


def explode(filename):
    processed.append(filename)
    soup = BeautifulSoup(codecs.open(filename, encoding='utf-8'), "lxml")
    body = soup.body
    body.name = 'div'
    body['id'] = filename
    # body['style'] = u'display: none'
    body['class'] = 'body'
    bodies.append(body)
    for script in soup.find_all('script'):
        if 'src' in script.attrs:
            if script['src'] not in scripts:
                scripts.append(script['src'])
                print 'added {}'.format(script['src'])
        elif ONREADY.match(script.string):
            body['data-on-show'] = ONREADY.match(script.string).groupdict()['handler']
            print u'handler: {}'.format(body['data-on-show'])
    for link in soup.find_all('link'):
        if link['href'] not in styles:
            styles.append(link['href'])
    for a in soup.find_all('a'):
        if a['href'][0] == '#':
            anchor = u'{}-{}'.format(filename, a['href'][1:])
            print anchor
            a['href'] = u'#{}'.format(anchor)
            a.parent['id'] = anchor
        elif a['href'] in processed:
            a['href'] = u'#{}'.format(a['href'])
        else:
            try:
                explode(a['href'])
            except IOError:
                pass
            else:
                a['href'] = u'#{}'.format(a['href'])


TEMPLATE = u'''<!DOCTYPE html>
<html>
  <head>
    <meta http-equiv='Content-Type' content='text/html; charset=utf-8'>
    <title>Coverage report</title>
    <style>{styles}</style>
    <script>{scripts}</script>
  </head>
  <body>
    {body}
  </body>
</html>
'''

os.chdir('htmlcov')
body = explode('index.html')

result = TEMPLATE.format(
    styles=u'\n'.join([codecs.open(f, encoding='utf-8').read() for f in styles]),
    scripts=u'\n'.join([codecs.open(f, encoding='utf-8').read() for f in scripts]),
    body=u'\n'.join([unicode(x) for x in bodies])
)

codecs.open('coverage.html', 'w', encoding='utf-8').write(result)
os.chdir('..')
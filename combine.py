import codecs
import os

from bs4 import BeautifulSoup

scripts = []
styles = []
bodies = []
processed = []


def explode(filename):
    # We want to turn the body element into a div so we can use it
    # in one page with all of the other body elements.
    processed.append(filename)
    soup = BeautifulSoup(codecs.open(filename, encoding='utf-8'))
    body = soup.body
    body.name = 'div'
    body['id'] = filename
    body['class'] = 'body'
    bodies.append(body)

    # Ensure that we grab all of the scripts that are required by
    # this page.
    for script in soup.find_all('script'):
        if 'src' in script.attrs:
            content = codecs.open(script['src'], encoding='utf-8').read()
        else:
            content = script.string
        if content not in scripts:
            scripts.append(content)

    # Likewise for the link[stylesheet] elements.
    for link in soup.find_all('link'):
        content = codecs.open(link['href'], encoding='utf-8').read()
        if content not in styles:
            styles.append(content)

    for a in soup.find_all('a'):
        # Make sure all local-links are rewritten to point to a more
        # fully-qualified name (these are line number links).
        if a['href'][0] == '#':
            anchor = u'{}-{}'.format(filename, a['href'][1:])

            a['href'] = u'#{}'.format(anchor)
            a.parent['id'] = anchor
        elif a['href'] in processed:
            # Pages we have already seen, we want to have a local link.
            a['href'] = u'#{}'.format(a['href'])
        else:
            # Otherwise, we want to see if we have a file that matches
            # the href, and embed that. Yay recursion.
            try:
                explode(a['href'])
            except IOError:
                pass
            else:
                a['href'] = u'#{}'.format(a['href'])

    for img in soup.find_all('img'):
        encoded = open(img['src'], 'rb').read().encode('base64')
        img['src'] = u'data:image/{};base64,{}'.format(img['src'].split('.')[-1], encoded)


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

# Fire off the tree walking with htmlcov/index.html
os.chdir('htmlcov')
explode('index.html')

# Override the toggle_lines function to limit it to just our code block.
scripts.append('''
coverage.toggle_lines = function (btn, cls) {
    btn = $(btn);
    var hide = "hide_"+cls;
    if (btn.hasClass(hide)) {
        btn.closest('.body').find("#source ."+cls).removeClass(hide);
        btn.removeClass(hide);
    }
    else {
        $("#source ."+cls).addClass(hide);
        btn.addClass(hide);
    }
};

var file = document.createElement('style');
file.innerHTML = '.body {min-height: ' + (window.innerHeight - 125) + 'px; margin-bottom: 125px;}';
document.head.appendChild(file);
''')

result = TEMPLATE.format(
    styles=u'\n'.join(styles),
    scripts=u'\n'.join(scripts),
    body=u'\n'.join([unicode(x) for x in bodies])
)

codecs.open('coverage.html', 'w', encoding='utf-8').write(result)
os.chdir('..')

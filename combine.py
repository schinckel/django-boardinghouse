import codecs
import os
import re

from bs4 import BeautifulSoup

ONREADY = re.compile(r'\W*jQuery\(document\)\.ready\(coverage\.(?P<handler>.*)\);\W*')

scripts = []
loadscripts = []
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
    body['data-on-show'] = 'x'
    bodies.append(body)

    # Ensure that we grab all of the scripts that are required by
    # this page.
    for script in soup.find_all('script'):
        if 'src' in script.attrs:
            content = codecs.open(script['src'], encoding='utf-8').read()
            if content not in scripts:
                scripts.append(content)
        elif ONREADY.match(script.string):
            print ONREADY.match(script.string).groupdict()['handler']
            body['data-on-show'] = ONREADY.match(script.string).groupdict()['handler']

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

coverage.wire_up_help_panel = function () {
    $(".content > img").click(function (event) {
        var body = $(event.target).closest('.body');
        // Show the help panel, and position it so the keyboard icon in the
        // panel is in the same place as the keyboard icon in the header.
        body.find(".help_panel").show();
        var koff = body.find("#keyboard_icon").offset();
        var poff = body.find("#panel_icon").position();
        body.find(".help_panel").offset({
            top: koff.top-poff.top,
            left: koff.left-poff.left
        });
    });
    $(".help_panel > img").click(function (event) {
        $(event.target).closest('.body').find(".help_panel").hide();
    });
};


var file = document.createElement('style');
file.innerHTML = '.body {}';
document.head.appendChild(file);


function updateVisibility(id) {
    console.log(id);
    // id may have dots in it: $(#id) won't work.
    var target = $(document.getElementById(id)).closest('.body');
    if (target.length) {
        $('.body').hide();
        target.show();
        if (target.data('on-show')) {
            coverage[target.data('on-show')]($);
        }
    }
}

function clickHandler(event) {
    console.log(event);
    event.preventDefault();
    if (event.target.hash) {
        var id = event.target.hash.split('#')[1];
        updateVisibility(id)
    }
}
// document.addEventListener('click', clickHandler);

// document.addEventListener('hashchange', clickHandler);

''')

bodies.append("""<script>
updateVisibility(location.hash.split('#')[1]);
window.onhashchange = function(event){
    console.log(event);
    event.preventDefault();
    updateVisibility(event.newURL.split('#')[1]);
};
</script>""")
# Need to tweak CSS rules for

result = TEMPLATE.format(
    styles=u'\n'.join(styles),
    scripts=u'\n'.join(scripts + loadscripts),
    body=u'\n'.join([unicode(x) for x in bodies])
)

codecs.open('coverage.html', 'w', encoding='utf-8').write(result)
os.chdir('..')

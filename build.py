#!/usr/bin/env python3
"""
Builds the whole site into ./docs (what GitHub Pages serves) from the articles in ./articles.

  python3 build.py

To publish a new article: copy any file in articles/, change the header lines
and the text below the ---, drop a photo in img/, and run the build again.
Everything else (homepage, category pages, sidebar, search, sitemap) updates
itself.
"""
import datetime, html, json, math, os, re, shutil
import markdown

# ------------------------------------------------------------------ settings
SITE_NAME   = 'Pocketwise'                   # placeholder until the domain is chosen
TAGLINE     = 'Money help for real life'
DOMAIN      = ''                             # e.g. 'pocketwise.com' (no https://)
DEMO        = True                           # True = tells search engines not to index it yet

# Google AdSense. Leave ADSENSE_CLIENT empty and the page shows grey boxes where
# the ads will sit. Fill it in (ca-pub-...) and the real ad code goes in instead.
ADSENSE_CLIENT = ''
AD_SLOTS = {                                 # ad unit IDs from AdSense > Ads > By ad unit
    'home-top': '', 'home-mid': '',
    'article-top': '', 'article-mid': '', 'article-end': '', 'sidebar': '',
}
# In-feed ad: AdSense > Ads > By ad unit > In-feed ads. It sits in the article
# lists dressed like one of the stories. Copy data-ad-slot and data-ad-layout-key
# from the code Google gives you.
IN_FEED = {'slot': '', 'layout_key': ''}
GA4_ID = ''                                  # Google Analytics, e.g. 'G-XXXXXXX'
NEWSLETTER_ENDPOINT = ''                     # sign-up form target, once an email service is chosen
CONTACT_ENDPOINT    = ''                     # contact form target

CATEGORIES = ['Benefits', 'Debt & Credit', 'Saving']

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(ROOT, 'docs')

# ------------------------------------------------------------------ helpers
def esc(s): return html.escape(s, quote=True)
def slugify(s): return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
def nice_date(d): return d.strftime('%b %-d, %Y')

def load_articles():
    arts = []
    for fn in sorted(os.listdir(os.path.join(ROOT, 'articles'))):
        if not fn.endswith('.md'): continue
        raw = open(os.path.join(ROOT, 'articles', fn), encoding='utf-8').read()
        head, body = raw.split('\n---\n', 1)
        a = dict(line.split(': ', 1) for line in head.strip().splitlines())
        a['date'] = datetime.date.fromisoformat(a['date'])
        a['body_md'] = body
        a['words'] = len(re.findall(r'\w+', body))
        a['minutes'] = max(1, math.ceil(a['words'] / 230))
        assert a['category'] in CATEGORIES, fn + ': unknown category ' + a['category']
        arts.append(a)
    arts.sort(key=lambda a: a['date'], reverse=True)
    return arts

def ad(slot, p, shape='wide'):
    """One ad position. A labelled grey box until AdSense is connected."""
    if ADSENSE_CLIENT and AD_SLOTS.get(slot):
        return ('<div class="ad ad-%s"><span class="ad-label">Advertisement</span>'
                '<ins class="adsbygoogle" style="display:block" data-ad-client="%s" '
                'data-ad-slot="%s" data-ad-format="auto" data-full-width-responsive="true"></ins>'
                '<script>(adsbygoogle=window.adsbygoogle||[]).push({});</script></div>'
                % (shape, ADSENSE_CLIENT, AD_SLOTS[slot]))
    if ADSENSE_CLIENT:   # Auto ads on, no fixed unit here: Google places ads itself
        return ''
    return ('<div class="ad ad-%s"><span class="ad-label">Advertisement</span>'
            '<div class="ad-box">Ad space &middot; Google AdSense</div></div>' % shape)

def infeed():
    """In-feed ad between stories in a list. Google labels it as an ad itself."""
    if ADSENSE_CLIENT and IN_FEED['slot'] and IN_FEED['layout_key']:
        return ('<div class="infeed"><ins class="adsbygoogle" style="display:block" data-ad-format="fluid" '
                'data-ad-layout-key="%s" data-ad-client="%s" data-ad-slot="%s"></ins>'
                '<script>(adsbygoogle=window.adsbygoogle||[]).push({});</script></div>'
                % (IN_FEED['layout_key'], ADSENSE_CLIENT, IN_FEED['slot']))
    if ADSENSE_CLIENT:
        return ''
    return ('<div class="infeed demo"><div class="row-txt"><span class="ad-label">Sponsored &middot; In-feed ad</span>'
            '<p class="infeed-h">An advertiser\'s headline appears here, styled like the stories around it</p>'
            '<p class="meta">Advertiser name</p></div><div class="ad-box">Ad image</div></div>')

LOGO = ('<svg class="logo-mark" viewBox="0 0 40 32" aria-hidden="true">'
        '<rect x="0" y="2" width="30" height="7" rx="3.5" fill="#7ee0c3"/>'
        '<rect x="5" y="12.5" width="30" height="7" rx="3.5" fill="#4fb8f0"/>'
        '<rect x="10" y="23" width="30" height="7" rx="3.5" fill="#3d7bf2"/></svg>')

def page(p, title, body, desc='', canonical='', og_image='', extra_head=''):
    """p = relative path back to the site root ('' or '../' or '../../')."""
    full_title = title if title == SITE_NAME else '%s | %s' % (title, SITE_NAME)
    head = []
    if DEMO: head.append('<meta name="robots" content="noindex,nofollow">')
    if DOMAIN and canonical is not None:
        head.append('<link rel="canonical" href="https://%s/%s">' % (DOMAIN, canonical))
    if og_image:
        head.append('<meta property="og:image" content="%s">' % esc(og_image))
    if ADSENSE_CLIENT:
        head.append('<script async src="https://pagead2.googlesyndication.com/pagead/js/'
                    'adsbygoogle.js?client=%s" crossorigin="anonymous"></script>' % ADSENSE_CLIENT)
    if GA4_ID:
        head.append('<script async src="https://www.googletagmanager.com/gtag/js?id=%s"></script>'
                    '<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}'
                    "gtag('js',new Date());gtag('config','%s');</script>" % (GA4_ID, GA4_ID))
    nav = ''.join('<a href="%scategory/%s/">%s</a>' % (p, slugify(c), esc(c)) for c in CATEGORIES)
    foot_cats = ''.join('<li><a href="%scategory/%s/">%s</a></li>' % (p, slugify(c), esc(c)) for c in CATEGORIES)
    year = datetime.date.today().year
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(desc or TAGLINE)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:site_name" content="{esc(SITE_NAME)}">
{''.join(head)}
<link rel="icon" href="{p}img/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;700;800&family=IBM+Plex+Mono:wght@500&family=Source+Sans+3:wght@400;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{p}style.css">
{extra_head}
</head>
<body>
<header class="hdr">
  <div class="hdr-in">
    <button class="menu-btn" aria-label="Menu" aria-expanded="false" onclick="toggleMenu(this)"><span></span><span></span><span></span></button>
    <a class="logo" href="{p}" aria-label="{esc(SITE_NAME)} home">{LOGO}<span>{esc(SITE_NAME)}</span></a>
    <nav class="nav" id="nav">{nav}<a href="{p}about/">About Us</a><a href="{p}subscribe/">Subscribe</a></nav>
    <button class="search-btn" aria-label="Search" onclick="openSearch()"><svg viewBox="0 0 24 24" width="22" height="22"><circle cx="10" cy="10" r="6.5" fill="none" stroke="currentColor" stroke-width="2.4"/><path d="M15 15l6 6" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/></svg></button>
  </div>
</header>
{body}
<footer class="ftr">
  <div class="ftr-in">
    <div class="ftr-brand"><a class="logo" href="{p}">{LOGO}<span>{esc(SITE_NAME)}</span></a>
      <p>{esc(TAGLINE)}. Plain-English guides to benefits, bills, debt and saving.</p></div>
    <div><h4>Topics</h4><ul>{foot_cats}</ul></div>
    <div><h4>Company</h4><ul><li><a href="{p}about/">About Us</a></li><li><a href="{p}contact/">Contact</a></li><li><a href="{p}subscribe/">Newsletter</a></li></ul></div>
    <div><h4>Legal</h4><ul><li><a href="{p}privacy-policy/">Privacy Policy</a></li><li><a href="{p}terms-of-use/">Terms of Use</a></li><li><a href="{p}privacy-policy/#ads">Advertising &amp; Cookies</a></li></ul></div>
  </div>
  <p class="ftr-legal">&copy; {year} {esc(SITE_NAME)}. Articles are for general information only and are not financial, legal or tax advice. Program rules change often and differ by state; always confirm details with the agency or provider concerned. {esc(SITE_NAME)} is not affiliated with any government agency.</p>
</footer>
<div class="search" id="search" hidden>
  <div class="search-box">
    <input id="q" type="search" placeholder="Search articles..." autocomplete="off" oninput="runSearch(this.value)">
    <button class="search-x" aria-label="Close search" onclick="closeSearch()">&times;</button>
    <ul id="results"></ul>
  </div>
</div>
<a href="#" class="to-top" aria-label="Back to top">&#8593;</a>
<script>var ROOT={json.dumps(p)};</script>
<script src="{p}site.js" defer></script>
</body>
</html>
'''

def write(rel, content):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w', encoding='utf-8').write(content)

def cat_label(c, p):
    return '<a class="cat" href="%scategory/%s/">%s</a>' % (p, slugify(c), esc(c))

def card(a, p, cls='card', img=True, excerpt=False):
    pic = ('<a class="thumb" href="%s%s/"><img src="%simg/%s" alt="%s" loading="lazy" width="1200" height="800"></a>'
           % (p, a['slug'], p, a['image'], esc(a['alt']))) if img else ''
    ex = '<p class="ex">%s</p>' % esc(a['excerpt']) if excerpt else ''
    return ('<article class="%s">%s<div class="card-txt"><h3><a href="%s%s/">%s</a></h3>%s%s</div></article>'
            % (cls, pic, p, a['slug'], esc(a['title']), ex, cat_label(a['category'], p)))

# ------------------------------------------------------------------ pages
def build_home(arts):
    p = ''
    strip = ''.join(card(a, p, 'strip-item', img=False) for a in arts[1:5])
    f = arts[0]
    feature = f'''<div class="feature">
      <a class="thumb" href="{f['slug']}/"><img src="img/{f['image']}" alt="{esc(f['alt'])}" width="1200" height="800"></a>
      <div class="feature-txt"><h2><a href="{f['slug']}/">{esc(f['title'])}</a></h2>
      <p class="ex">{esc(f['excerpt'])}</p>{cat_label(f['category'], p)}</div></div>'''
    grid = ''.join(card(a, p, 'card') for a in (arts[5:] + arts[1:5])[:4])
    recent = []
    for i, a in enumerate(arts):
        recent.append(f'''<article class="row">
          <div class="row-txt">{cat_label(a['category'], p)}<h3><a href="{a['slug']}/">{esc(a['title'])}</a></h3>
          <p class="ex">{esc(a['excerpt'])}</p><p class="meta">{nice_date(a['date'])} &middot; {a['minutes']} min read</p></div>
          <a class="thumb" href="{a['slug']}/"><img src="img/{a['image']}" alt="{esc(a['alt'])}" loading="lazy" width="1200" height="800"></a>
        </article>''')
        if i in (1, 5): recent.append(infeed())
        if i == 3: recent.append(ad('home-mid', p))
    tabs = '<a class="on" href="./">All</a>' + ''.join(
        '<a href="category/%s/">%s</a>' % (slugify(c), esc(c)) for c in CATEGORIES)
    body = f'''<section class="dark">
  <div class="wrap">
    <div class="strip">{strip}</div>
    {feature}
    <div class="grid4">{grid}</div>
  </div>
</section>
<div class="wrap">{ad('home-top', p)}</div>
<section class="wrap recent">
  <h2 class="sec-title"><span></span>Resources and Guides</h2>
  <div class="sec-bar"><span class="kicker">Recent stories</span><nav class="tabs">{tabs}</nav></div>
  {''.join(recent)}
</section>
{newsletter_band(p)}'''
    write('index.html', page(p, SITE_NAME, body, TAGLINE + '. Plain-English guides to government benefits, bills, debt and saving.', canonical=''))

def newsletter_band(p):
    return f'''<section class="news-band"><div class="wrap news-in">
  <div><h2>Get the weekly money dig</h2><p>One email a week with new guides, deadlines for assistance programs and ways to save. No spam, unsubscribe any time.</p></div>
  <form class="news-form" onsubmit="return subscribe(this)">
    <input type="email" name="email" required placeholder="Your email address" aria-label="Email address">
    <button type="submit">Subscribe</button>
    <p class="news-msg" role="status"></p>
  </form></div></section>'''

def build_article(a, arts):
    p = '../'
    body_html = markdown.markdown(a['body_md'], extensions=['sane_lists'])
    # Split after paragraphs so ads sit between blocks of text, never inside them.
    blocks = re.split(r'(?<=</p>)\n|(?<=</ul>)\n|(?<=</ol>)\n', body_html)
    blocks = [b for b in blocks if b.strip()]
    out, mid_done = [], False
    for i, b in enumerate(blocks):
        out.append(b)
        if i == 1: out.append(ad('article-top', p))
        if not mid_done and i >= len(blocks) // 2 + 1 and b.startswith('<p'):
            out.append(ad('article-mid', p)); mid_done = True
    others = [o for o in arts if o is not a]
    same = [o for o in others if o['category'] == a['category']]
    featured = (same + [o for o in others if o not in same])[:4]
    side = ''.join(card(o, p, 'side-card') for o in featured)
    more = ''.join(card(o, p, 'card light') for o in (same + [o for o in others if o not in same])[:3])
    ld = {"@context": "https://schema.org", "@type": "Article", "headline": a['title'],
          "datePublished": a['date'].isoformat(), "author": {"@type": "Organization", "name": SITE_NAME + ' Staff'},
          "publisher": {"@type": "Organization", "name": SITE_NAME}, "description": a['excerpt']}
    body = f'''<div class="wrap art-wrap">
  <article class="art">
    {cat_label(a['category'], p)}
    <h1>{esc(a['title'])}</h1>
    <p class="meta">By {esc(SITE_NAME)} Staff &middot; {nice_date(a['date'])} &middot; {a['minutes']} min read</p>
    <img class="hero" src="../img/{a['image']}" alt="{esc(a['alt'])}" width="1200" height="800">
    <div class="prose">{''.join(out)}</div>
    {ad('article-end', p)}
    <p class="disclaimer">This article is for general information only and is not financial, legal or tax advice. Program rules, income limits and deadlines change and vary by state. Check the latest details with the agency or provider before you act.</p>
    <div class="share">Share: <a href="#" onclick="return shareIt()">Copy link</a></div>
  </article>
  <aside class="side">
    <h4 class="side-title">Featured</h4>
    {side}
    <div class="sticky">{ad('sidebar', p, 'tall')}</div>
  </aside>
</div>
<section class="wrap more"><h2 class="sec-title"><span></span>Keep reading</h2><div class="grid3">{more}</div></section>
{newsletter_band(p)}'''
    extra = '<script type="application/ld+json">%s</script>' % json.dumps(ld)
    write(a['slug'] + '/index.html', page(p, a['title'], body, a['excerpt'], canonical=a['slug'] + '/',
                                         og_image='../img/' + a['image'], extra_head=extra))

def build_category(c, arts):
    p = '../../'
    items = [a for a in arts if a['category'] == c]
    rows = [f'''<article class="row">
      <div class="row-txt"><h3><a href="{p}{a['slug']}/">{esc(a['title'])}</a></h3>
      <p class="ex">{esc(a['excerpt'])}</p><p class="meta">{nice_date(a['date'])} &middot; {a['minutes']} min read</p></div>
      <a class="thumb" href="{p}{a['slug']}/"><img src="{p}img/{a['image']}" alt="{esc(a['alt'])}" loading="lazy" width="1200" height="800"></a>
    </article>''' for a in items]
    if len(rows) > 2: rows.insert(2, infeed())
    rows = ''.join(rows)
    body = f'''<section class="dark cat-head"><div class="wrap"><span class="kicker light">Topic</span><h1>{esc(c)}</h1>
<p>{len(items)} guide{'s' if len(items) != 1 else ''}</p></div></section>
<section class="wrap recent">{rows}{ad('home-mid', p)}</section>'''
    write('category/%s/index.html' % slugify(c), page(p, c, body, '%s guides from %s' % (c, SITE_NAME),
                                                     canonical='category/%s/' % slugify(c)))

def build_static(slug, title, inner, desc):
    p = '../'
    body = f'<div class="wrap doc"><h1>{esc(title)}</h1>{inner}</div>'
    write(slug + '/index.html', page(p, title, body, desc, canonical=slug + '/'))

def build_static_pages():
    S = esc(SITE_NAME)
    upd = nice_date(datetime.date.today())
    build_static('about', 'About Us', f'''
<p class="lead">{S} publishes plain-English guides for people who are trying to stretch a paycheck, get help they are entitled to, or get out from under debt.</p>
<h2>What we cover</h2>
<p>Government and nonprofit assistance programs, household bills and utilities, debt and credit, and practical ways to save. Every guide explains who a program is for, how to apply, and what to watch out for.</p>
<h2>How we write</h2>
<ul><li>We explain how things actually work, including the limits and the catches.</li>
<li>We point readers to the official agency or program wherever possible, and we never charge for information about public benefits.</li>
<li>We review our guides when rules change, and correct mistakes as soon as we find them.</li></ul>
<h2>How we make money</h2>
<p>{S} is free to read and is supported by advertising. Advertisers do not choose or review our articles, and ads are always labelled and kept separate from the article text.</p>
<h2>Get in touch</h2>
<p>Spotted an error or have a question? <a href="../contact/">Contact us</a>.</p>''', 'About ' + SITE_NAME)

    build_static('contact', 'Contact Us', f'''
<p class="lead">Questions, corrections or partnership enquiries? Send us a message and we will get back to you.</p>
<form class="contact-form" onsubmit="return contactForm(this)">
<label>Your name<input name="name" required></label>
<label>Email<input type="email" name="email" required></label>
<label>Message<textarea name="message" rows="6" required></textarea></label>
<button type="submit">Send message</button>
<p class="news-msg" role="status"></p>
</form>
<p class="small">{S} cannot help with individual benefit applications or account problems. For those, please contact the agency or company directly.</p>''', 'Contact ' + SITE_NAME)

    build_static('subscribe', 'Subscribe', f'''
<p class="lead">Get one email a week with our newest guides, upcoming application windows for assistance programs and practical ways to save.</p>
<form class="news-form big" onsubmit="return subscribe(this)">
<input type="email" name="email" required placeholder="Your email address" aria-label="Email address">
<button type="submit">Subscribe</button>
<p class="news-msg" role="status"></p>
</form>
<p class="small">You can unsubscribe at any time using the link in every email. See our <a href="../privacy-policy/">Privacy Policy</a>.</p>''', 'Subscribe to ' + SITE_NAME)

    build_static('privacy-policy', 'Privacy Policy', f'''
<p class="small">Last updated: {upd}</p>
<p>This policy explains what information {S} ("we", "us") collects when you use this website, and how it is used.</p>
<h2>Information you give us</h2>
<p>If you subscribe to our newsletter or send us a message, we receive the details you enter, such as your name and email address. We use them only to send the newsletter or reply to you. You can unsubscribe at any time.</p>
<h2>Information collected automatically</h2>
<p>Like most websites, we and our partners receive standard technical information such as your IP address, browser type, device, pages viewed and the site that referred you. We use this to run the site, understand which articles are useful and measure advertising.</p>
<h2 id="ads">Advertising and cookies</h2>
<p>This website shows ads served by Google and other third-party vendors.</p>
<ul>
<li>Third-party vendors, including Google, use cookies to serve ads based on your prior visits to this website or other websites.</li>
<li>Google's use of advertising cookies enables it and its partners to serve ads to you based on your visit to this site and/or other sites on the Internet.</li>
<li>You may opt out of personalized advertising by visiting Google's <a href="https://adssettings.google.com" rel="noopener" target="_blank">Ads Settings</a>. You can also opt out of some third-party vendors' use of cookies for personalized advertising at <a href="https://www.aboutads.info/choices/" rel="noopener" target="_blank">www.aboutads.info</a>.</li>
<li>To learn how Google uses information from sites that use its services, see <a href="https://policies.google.com/technologies/partner-sites" rel="noopener" target="_blank">How Google uses information from sites or apps that use our services</a>.</li>
</ul>
<p>We may also use analytics tools, such as Google Analytics, which use cookies to report how visitors use the site. You can block or delete cookies in your browser settings; some features may not work without them.</p>
<p>Visitors from regions that require it are asked for consent before personalized ads or non-essential cookies are used.</p>
<h2>Sharing</h2>
<p>We do not sell your name or email address. We share information with the service providers who host the site, deliver our emails and serve ads, only as needed for them to do so.</p>
<h2>Your choices and rights</h2>
<p>Depending on where you live, you may have the right to access, correct or delete personal information we hold about you, or to opt out of the sale or sharing of personal information for targeted advertising. To make a request, <a href="../contact/">contact us</a>.</p>
<h2>Children</h2>
<p>This site is intended for adults. We do not knowingly collect information from children under 13.</p>
<h2>Changes</h2>
<p>If this policy changes, the updated version will be posted on this page with a new date.</p>''', 'Privacy Policy for ' + SITE_NAME)

    build_static('terms-of-use', 'Terms of Use', f'''
<p class="small">Last updated: {upd}</p>
<p>By using this website you agree to these terms.</p>
<h2>Information only</h2>
<p>Articles on {S} are for general information and education. They are not financial, legal, tax or professional advice, and they do not create any professional relationship. Assistance programs, income limits, deadlines and laws change frequently and differ by state. Always confirm details with the agency, lender or provider concerned before making a decision.</p>
<h2>No government affiliation</h2>
<p>{S} is an independent publisher. It is not affiliated with, endorsed by or acting for any government agency. Applying for public benefits is free, and you never need to pay {S} or anyone else for information about them.</p>
<h2>Advertising and links</h2>
<p>This site is supported by advertising and links to third-party websites. We do not control and are not responsible for the content, products or services of advertisers or other websites.</p>
<h2>Accuracy</h2>
<p>We work to keep our guides accurate and up to date but cannot guarantee that every article is complete or current. If you find an error, please <a href="../contact/">tell us</a>.</p>
<h2>Use of content</h2>
<p>The articles, design and branding on this site belong to {S}. You may share links to our articles, but you may not copy or republish them without permission.</p>
<h2>Limitation of liability</h2>
<p>To the fullest extent permitted by law, {S} is not liable for any loss arising from your use of this website or reliance on its content.</p>
<h2>Changes</h2>
<p>We may update these terms. The version posted on this page applies.</p>''', 'Terms of Use for ' + SITE_NAME)

def build_extras(arts):
    idx = [{'t': a['title'], 'u': a['slug'] + '/', 'c': a['category'], 'e': a['excerpt']} for a in arts]
    write('search.json', json.dumps(idx))
    write('404.html', page('/' if DOMAIN else '', 'Page not found',
          '<div class="wrap doc"><h1>Page not found</h1><p>That page has moved or no longer exists. Try the <a href="./">homepage</a> or the search.</p></div>',
          canonical=None))
    robots = 'User-agent: *\nDisallow: /\n' if DEMO else 'User-agent: *\nAllow: /\n'
    if DOMAIN and not DEMO: robots += 'Sitemap: https://%s/sitemap.xml\n' % DOMAIN
    write('robots.txt', robots)
    if ADSENSE_CLIENT:
        write('ads.txt', 'google.com, %s, DIRECT, f08c47fec0942fa0\n' % ADSENSE_CLIENT.replace('ca-', ''))
    if DOMAIN:
        urls = [''] + [a['slug'] + '/' for a in arts] + ['category/%s/' % slugify(c) for c in CATEGORIES] + \
               ['about/', 'contact/', 'privacy-policy/', 'terms-of-use/']
        write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
              + ''.join('<url><loc>https://%s/%s</loc></url>' % (DOMAIN, u) for u in urls) + '</urlset>\n')
        write('CNAME', DOMAIN + '\n')
    write('.nojekyll', '')
    cfg = {'newsletter': NEWSLETTER_ENDPOINT, 'contact': CONTACT_ENDPOINT}
    js = open(os.path.join(ROOT, 'src', 'site.js'), encoding='utf-8').read()
    write('site.js', 'var CFG=%s;\n%s' % (json.dumps(cfg), js))

def main():
    if os.path.isdir(OUT): shutil.rmtree(OUT)
    os.makedirs(OUT)
    shutil.copytree(os.path.join(ROOT, 'img'), os.path.join(OUT, 'img'))
    shutil.copy(os.path.join(ROOT, 'src', 'style.css'), OUT)
    arts = load_articles()
    build_home(arts)
    for a in arts: build_article(a, arts)
    for c in CATEGORIES: build_category(c, arts)
    build_static_pages()
    build_extras(arts)
    print('Built %d articles into %s' % (len(arts), OUT))

if __name__ == '__main__':
    main()

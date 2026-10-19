"""Genera index.html (español) y en/index.html (inglés) desde _tools/plantilla.html.

Uso, desde la carpeta del repositorio:
    python3 _tools/build.py

La plantilla es la única fuente: cada texto lleva data-es y data-en. Este
script elige el idioma, rellena la cabecera (title, description, hreflang,
Open Graph) y los datos estructurados, y escribe las dos páginas.
GitHub Pages no publica las carpetas que empiezan con "_", así que _tools/
no aparece en la web.
"""
import json
import pathlib

from bs4 import BeautifulSoup

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = 'https://drcjortegaarenas.com'

META = {
    'es': {
        'path': '/',
        'html_lang': 'es-MX',
        'title': 'Médico a domicilio y hotel en CDMX | Dr. Ortega-Arenas',
        'description': 'Médico general bilingüe (español/inglés) en Ciudad de México: consulta en hotel, a domicilio, '
                       'en consultorio (Del Valle, Roma, Polanco, Santa Fe) y teleconsulta. Egresado de la UNAM. '
                       'Honorarios publicados en MXN.',
        'og_title': 'Dr. Cristóbal J. Ortega-Arenas — Médico general bilingüe en CDMX',
        'og_locale': 'es_MX', 'og_alt': 'en_US',
        'phys_desc': 'Médico general bilingüe (español/inglés) en la Ciudad de México: consultorio, '
                     'teleconsulta, visitas a domicilio y a hotel, y terapia de hidratación intravenosa.',
    },
    'en': {
        'path': '/en/',
        'html_lang': 'en',
        'title': 'English-Speaking Doctor in Mexico City | Hotel & House Calls',
        'description': 'Bilingual (English/Spanish) general physician in Mexico City: hotel visits, house calls, '
                       'clinic in Polanco, Roma, Del Valle and Santa Fe, and telemedicine. UNAM-trained. '
                       'Fees published in MXN.',
        'og_title': 'Dr. Cristóbal J. Ortega-Arenas — English-speaking doctor in Mexico City',
        'og_locale': 'en_US', 'og_alt': 'es_MX',
        'phys_desc': 'Bilingual (English/Spanish) general physician in Mexico City: clinic visits, '
                     'telemedicine, house calls, hotel visits and IV hydration therapy.',
    },
}

AREAS = ['Polanco', 'Roma', 'Condesa', 'Del Valle', 'Santa Fe', 'Reforma', 'Coyoacán', 'Pedregal',
         'Centro Histórico', 'Texcoco']


def head_meta(lang):
    m = META[lang]
    url = SITE + m['path']
    esc = lambda t: t.replace('&', '&amp;').replace('"', '&quot;')
    lines = [
        f'<title>{esc(m["title"])}</title>',
        f'<meta name="description" content="{esc(m["description"])}">',
        '<meta name="author" content="Dr. Cristóbal J. Ortega-Arenas">',
        '<meta name="robots" content="index, follow">',
        f'<link rel="canonical" href="{url}">',
        f'<link rel="alternate" hreflang="es-MX" href="{SITE}/">',
        f'<link rel="alternate" hreflang="en" href="{SITE}/en/">',
        f'<link rel="alternate" hreflang="x-default" href="{SITE}/">',
        '<meta name="theme-color" content="#0a0a0a">',
        '<link rel="icon" href="/assets/favicon-48.png" type="image/png" sizes="48x48">',
        '<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">',
        '<meta property="og:type" content="website">',
        '<meta property="og:site_name" content="Dr. Cristóbal J. Ortega-Arenas">',
        f'<meta property="og:title" content="{esc(m["og_title"])}">',
        f'<meta property="og:description" content="{esc(m["description"])}">',
        f'<meta property="og:url" content="{url}">',
        f'<meta property="og:image" content="{SITE}/assets/og-image.png">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        f'<meta property="og:locale" content="{m["og_locale"]}">',
        f'<meta property="og:locale:alternate" content="{m["og_alt"]}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{esc(m["og_title"])}">',
        f'<meta name="twitter:description" content="{esc(m["description"])}">',
        f'<meta name="twitter:image" content="{SITE}/assets/og-image.png">',
    ]
    return '\n'.join(lines) + '\n'


def jsonld(obj):
    body = json.dumps(obj, ensure_ascii=False, indent=2).replace('</', '<\\/')
    return f'<script type="application/ld+json">\n{body}\n</script>\n'


def physician(lang):
    m = META[lang]
    return jsonld({
        '@context': 'https://schema.org',
        '@type': 'Physician',
        'name': 'Dr. Cristóbal J. Ortega-Arenas',
        'description': m['phys_desc'],
        'url': SITE + m['path'],
        'image': SITE + '/assets/og-image.png',
        'logo': SITE + '/assets/logo-white.svg',
        'telephone': '+52 595 109 3969',
        'email': 'cristobaljoa@icloud.com',
        'medicalSpecialty': 'https://schema.org/PrimaryCare',
        'isAcceptingNewPatients': True,
        'currenciesAccepted': 'MXN',
        'paymentAccepted': 'Visa, Mastercard, American Express, Apple Pay, Google Pay, Transfer, Cash (MXN)',
        'knowsLanguage': ['es', 'en'],
        'address': {'@type': 'PostalAddress', 'addressLocality': 'Ciudad de México',
                    'addressRegion': 'CDMX', 'addressCountry': 'MX'},
        'areaServed': [{'@type': 'Place', 'name': f'{a}, Ciudad de México' if a != 'Texcoco' else 'Texcoco, Estado de México'}
                       for a in AREAS],
        'sameAs': ['https://www.instagram.com/dr.cristobalj.ortegaarenas',
                   'https://orcid.org/0000-0002-1924-8781'],
    })


def faq(soup):
    items = []
    for card in soup.select('.faq-item'):
        q = card.find('h3').get_text(' ', strip=True)
        a = card.find('p').get_text(' ', strip=True)
        items.append({'@type': 'Question', 'name': q,
                      'acceptedAnswer': {'@type': 'Answer', 'text': a}})
    return jsonld({'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': items})


def build(lang):
    src = (ROOT / '_tools' / 'plantilla.html').read_text(encoding='utf-8')
    src = src.replace('<!--HEAD_META-->\n', head_meta(lang))
    src = src.replace('<!--PHYSICIAN_JSONLD-->\n', physician(lang))
    soup = BeautifulSoup(src, 'html.parser')
    soup.html['lang'] = META[lang]['html_lang']
    missing = []
    for el in soup.select('[data-es]'):
        text = el.get('data-' + lang)
        if text is None:
            missing.append(str(el)[:80])
            continue
        el.clear()
        el.append(BeautifulSoup(text, 'html.parser'))
        del el['data-es']
        if el.has_attr('data-en'):
            del el['data-en']
    for el in soup.select('[data-alt-en]'):
        if lang == 'en':
            el['alt'] = el['data-alt-en']
        del el['data-alt-en']
    if missing:
        raise SystemExit('Falta traducción en:\n' + '\n'.join(missing))
    html = str(soup).replace('<!--FAQ_JSONLD-->', faq(soup).rstrip('\n'))
    out = ROOT / ('index.html' if lang == 'es' else 'en/index.html')
    out.parent.mkdir(exist_ok=True)
    out.write_text(html, encoding='utf-8')
    print(f'{lang}: {out.relative_to(ROOT)} ({len(html):,} bytes)')


if __name__ == '__main__':
    build('es')
    build('en')

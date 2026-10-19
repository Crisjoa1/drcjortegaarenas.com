"""Genera las páginas del sitio en español e inglés desde las plantillas de _tools/.

Uso, desde la carpeta del repositorio:
    python3 _tools/build.py

  plantilla.html                → index.html y en/index.html
  plantilla-hoteles.html        → hoteles/index.html y en/hotels/index.html
  plantilla-hoja-recepcion.html → assets/hoja-recepcion-hoteles.pdf (con Google Chrome)
  paginas/*.json                → una página por archivo (servicios y guías); cada JSON
                                  dice qué plantilla usa, sus URL ES/EN, título,
                                  descripción y, en las guías, las fuentes citadas
  parciales/nav.html, pie.html  → menú y pie compartidos (<!--NAV--> y <!--PIE-->)
  También genera sitemap.xml y llms.txt.

Las plantillas son la única fuente: cada texto lleva data-es y data-en, y los
enlaces que cambian con el idioma llevan data-href-en. Este script elige el
idioma, rellena la cabecera (title, description, hreflang, Open Graph) y los
datos estructurados, y escribe las páginas. La página de hoteles copia los
estilos y la tabla de tarifas de plantilla.html, así que los precios solo se
editan en un lugar (la tarjeta marcada con data-tarifas-hotel).
GitHub Pages no publica las carpetas que empiezan con "_", así que _tools/
no aparece en la web.
"""
import hashlib
import json
import pathlib
import shutil
import subprocess
import tempfile

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
        'crumb_home': 'Inicio',
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
        'crumb_home': 'Home',
        'phys_desc': 'Bilingual (English/Spanish) general physician in Mexico City: clinic visits, '
                     'telemedicine, house calls, hotel visits and IV hydration therapy.',
    },
}

META_HOTELES = {
    'es': {
        'path': '/hoteles/',
        'html_lang': 'es-MX',
        'title': 'Médico a hotel en CDMX: información para hoteles y concierges',
        'description': 'Cómo solicitar una visita médica bilingüe para un huésped en la Ciudad de México: '
                       'WhatsApp o reserva en línea, llegada estimada de 30 a 45 minutos, tarifas por zona y '
                       'horario, y documentos para el seguro de viaje.',
        'og_title': 'Para hoteles y concierges — Dr. Cristóbal J. Ortega-Arenas',
        'og_locale': 'es_MX', 'og_alt': 'en_US',
        'crumb': 'Para hoteles y concierges', 'home': 'Inicio',
    },
    'en': {
        'path': '/en/hotels/',
        'html_lang': 'en',
        'title': 'Hotel Doctor in Mexico City: Information for Hotels & Concierges',
        'description': 'How to request a bilingual medical visit for a hotel guest in Mexico City: WhatsApp or '
                       'online booking, estimated arrival in 30–45 minutes, fees by zone and time of day, and '
                       'documents for travel insurance.',
        'og_title': 'For hotels & concierges — Dr. Cristóbal J. Ortega-Arenas',
        'og_locale': 'en_US', 'og_alt': 'es_MX',
        'crumb': 'For hotels & concierges', 'home': 'Home',
    },
}

PAGES = [
    {'template': 'plantilla.html', 'meta': META,
     'out': {'es': 'index.html', 'en': 'en/index.html'}},
    {'template': 'plantilla-hoteles.html', 'meta': META_HOTELES,
     'out': {'es': 'hoteles/index.html', 'en': 'en/hotels/index.html'}},
]


def load_pages():
    """Cada _tools/paginas/*.json registra una página nueva sin tocar este script."""
    pages = []
    for f in sorted((ROOT / '_tools' / 'paginas').glob('*.json')):
        cfg = json.loads(f.read_text(encoding='utf-8'))
        meta = {lang: dict(cfg[lang], home=META[lang]['crumb_home']) for lang in ('es', 'en') if lang in cfg}
        for lang in meta:
            meta[lang].setdefault('html_lang', 'es-MX' if lang == 'es' else 'en')
            meta[lang].setdefault('og_locale', 'es_MX' if lang == 'es' else 'en_US')
            meta[lang].setdefault('og_alt', 'en_US' if lang == 'es' else 'es_MX')
            meta[lang].setdefault('og_title', meta[lang]['title'])
        out = {lang: meta[lang]['path'].strip('/') + '/index.html' for lang in meta}
        pages.append({'template': cfg['plantilla'], 'meta': meta, 'out': out, 'cfg': cfg})
    return pages


PAGES += load_pages()

PDF_OUT = ROOT / 'assets' / 'hoja-recepcion-hoteles.pdf'
PDF_HASH = ROOT / '_tools' / '.hoja-recepcion.sha256'
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

AREAS = ['Polanco', 'Roma', 'Condesa', 'Del Valle', 'Santa Fe', 'Reforma', 'Coyoacán', 'Pedregal',
         'Centro Histórico', 'Texcoco']


def head_meta(meta, lang):
    m = meta[lang]
    url = SITE + m['path']
    es_url = SITE + meta['es']['path']
    en_url = SITE + meta['en']['path'] if 'en' in meta else None
    esc = lambda t: t.replace('&', '&amp;').replace('"', '&quot;')
    lines = [
        f'<title>{esc(m["title"])}</title>',
        f'<meta name="description" content="{esc(m["description"])}">',
        '<meta name="author" content="Dr. Cristóbal J. Ortega-Arenas">',
        '<meta name="robots" content="index, follow">',
        f'<link rel="canonical" href="{url}">',
        f'<link rel="alternate" hreflang="es-MX" href="{es_url}">',
        *([f'<link rel="alternate" hreflang="en" href="{en_url}">'] if en_url else []),
        f'<link rel="alternate" hreflang="x-default" href="{es_url}">',
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
        *([f'<meta property="og:locale:alternate" content="{m["og_alt"]}">'] if en_url else []),
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
        '@id': SITE + '/#medico',
        'name': 'Dr. Cristóbal J. Ortega-Arenas',
        'alternateName': 'Cristóbal Jerónimo Ortega-Arenas',
        'alumniOf': {'@type': 'CollegeOrUniversity', 'name': 'Universidad Nacional Autónoma de México (UNAM), Facultad de Medicina'},
        'award': 'Premio al Servicio Social «Gustavo Baz Prada» (UNAM), categoría investigación',
        'hasCredential': [
            {'@type': 'EducationalOccupationalCredential', 'credentialCategory': 'Cédula profesional (Médico Cirujano)',
             'identifier': '14848636',
             'recognizedBy': {'@type': 'GovernmentOrganization', 'name': 'Secretaría de Educación Pública, Dirección General de Profesiones'}},
            {'@type': 'EducationalOccupationalCredential', 'credentialCategory': 'Homologación del título de Médico en España',
             'identifier': '2025-17271',
             'recognizedBy': {'@type': 'GovernmentOrganization', 'name': 'Ministerio de Ciencia, Innovación y Universidades (España)'}},
        ],
        'makesOffer': offers(lang),
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


OFFERS = [  # (es, en, precio "desde" en MXN) — deben coincidir con las tarifas publicadas
    ('Visita médica en hotel', 'Hotel medical visit', 2500),
    ('Consulta a domicilio', 'House call', 1000),
    ('Consulta en consultorio', 'Clinic visit', 1000),
    ('Teleconsulta', 'Telemedicine consultation', 700),
    ('Paquete Viajero', 'Traveler Package', 2200),
    ('Hidratación intravenosa (cargo del nivel, sin visita)', 'IV hydration (level fee, visit not included)', 1800),
    ('Certificado médico digital', 'Digital medical certificate', 500),
]


def offers(lang):
    i = 0 if lang == 'es' else 1
    return [{'@type': 'Offer', 'name': o[i], 'priceCurrency': 'MXN',
             'priceSpecification': {'@type': 'PriceSpecification', 'minPrice': o[2], 'priceCurrency': 'MXN'}}
            for o in OFFERS]


def medical_page(page, lang):
    """MedicalWebPage para servicios y guías: autor, revisión y fuentes citadas."""
    cfg, m = page['cfg'], page['meta'][lang]
    obj = {
        '@context': 'https://schema.org',
        '@type': 'MedicalWebPage',
        'name': m['title'],
        'description': m['description'],
        'url': SITE + m['path'],
        'inLanguage': m['html_lang'],
        'author': {'@id': SITE + '/#medico'},
        'reviewedBy': {'@id': SITE + '/#medico'},
        'lastReviewed': cfg.get('revisado'),
        'publisher': {'@id': SITE + '/#medico'},
    }
    if cfg.get('audiencia'):
        obj['audience'] = {'@type': 'PeopleAudience', 'audienceType': cfg['audiencia'][lang] if isinstance(cfg['audiencia'], dict) else cfg['audiencia']}
    if cfg.get('citas'):
        obj['citation'] = [{'@type': 'CreativeWork', 'name': c['nombre'], 'url': c['url']} for c in cfg['citas']]
    return jsonld({k: v for k, v in obj.items() if v})


def faq(soup):
    items = []
    for card in soup.select('.faq-item'):
        q = card.find('h3').get_text(' ', strip=True)
        a = card.find('p').get_text(' ', strip=True)
        items.append({'@type': 'Question', 'name': q,
                      'acceptedAnswer': {'@type': 'Answer', 'text': a}})
    return jsonld({'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': items})


def breadcrumb(meta, lang):
    m = meta[lang]
    home = m.get('home') or META[lang]['crumb_home']
    return jsonld({
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': home, 'item': SITE + META[lang]['path']},
            {'@type': 'ListItem', 'position': 2, 'name': m['crumb'], 'item': SITE + m['path']},
        ],
    })


def main_template():
    return (ROOT / '_tools' / 'plantilla.html').read_text(encoding='utf-8')


def base_css():
    """Los estilos de plantilla.html, para que todas las páginas se vean igual."""
    src = main_template()
    return src[src.index('<style>') + len('<style>'):src.index('</style>')].strip('\n') + '\n'


def hotel_card():
    """La tarjeta de hoteles de plantilla.html: la única fuente de las tarifas."""
    card = BeautifulSoup(main_template(), 'html.parser').select_one('[data-tarifas-hotel]')
    if card is None:
        raise SystemExit('No encuentro la tarjeta con data-tarifas-hotel en plantilla.html')
    return card.select_one('table.price-table'), card.select_one('.zone-badges')


def hotel_prices_html():
    table, zones = hotel_card()
    return f'{table}\n{zones}\n'


def render(page, lang):
    meta = page['meta']
    src = (ROOT / '_tools' / page['template']).read_text(encoding='utf-8')
    for mark, part in (('<!--NAV-->', 'nav.html'), ('<!--PIE-->', 'pie.html')):
        src = src.replace(mark, (ROOT / '_tools' / 'parciales' / part).read_text(encoding='utf-8'))
    src = src.replace('{{URL_ES}}', meta['es']['path']).replace('{{URL_EN}}', meta['en']['path'] if 'en' in meta else '/en/')
    fills = {
        '<!--PAGE_JSONLD-->\n': lambda: medical_page(page, lang) + breadcrumb(meta, lang),
        '<!--HEAD_META-->\n': lambda: head_meta(meta, lang),
        '<!--PHYSICIAN_JSONLD-->\n': lambda: physician(lang),
        '<!--BREADCRUMB_JSONLD-->\n': lambda: breadcrumb(meta, lang),
        '<!--BASE_CSS-->\n': base_css,
        '<!--HOTEL_PRICES-->\n': hotel_prices_html,
    }
    for mark, fill in fills.items():
        if mark in src:
            src = src.replace(mark, fill())
    soup = BeautifulSoup(src, 'html.parser')
    soup.html['lang'] = meta[lang]['html_lang']
    for el in soup.select('[data-solo]'):  # bloques que existen en un solo idioma
        if el['data-solo'] != lang:
            el.decompose()
        else:
            del el['data-solo']
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
    for el in soup.select('[data-href-en]'):
        if lang == 'en':
            el['href'] = el['data-href-en']
        del el['data-href-en']
    for el in soup.select('[data-tarifas-hotel]'):
        del el['data-tarifas-hotel']
    if missing:
        raise SystemExit('Falta traducción en:\n' + '\n'.join(missing))
    html = str(soup)
    if '<!--FAQ_JSONLD-->' in html:
        html = html.replace('<!--FAQ_JSONLD-->', faq(soup).rstrip('\n'))
    out = ROOT / page['out'][lang]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding='utf-8')
    print(f'{lang}: {out.relative_to(ROOT)} ({len(html):,} bytes)')


def bilingual(td):
    """'Ordinario<br><span>Lun–Vie…</span>' en ES y EN → filas para la hoja impresa."""
    parts = {}
    for lang in ('es', 'en'):
        cell = BeautifulSoup(td['data-' + lang], 'html.parser')
        span = cell.find('span')
        hours = span.get_text(' ', strip=True) if span else ''
        if span:
            span.extract()
        parts[lang] = (cell.get_text(' ', strip=True), hours)
    return parts


def pdf_html():
    table, zones = hotel_card()
    rows = []
    for tr in table.select('tbody tr'):
        tds = tr.find_all('td')
        p = bilingual(tds[0])
        rows.append(f'<tr><td>{p["es"][0]} / {p["en"][0]}<small>{p["es"][1]} · {p["en"][1]}</small></td>'
                    f'<td class="num">{tds[1].get_text(strip=True)}</td>'
                    f'<td class="num">{tds[2].get_text(strip=True)}</td></tr>')
    precios = ('<table><thead><tr><th>Horario / Hours</th><th class="num">Zona A / Zone A</th>'
               '<th class="num">Zona B / Zone B</th></tr></thead><tbody>\n' + '\n'.join(rows) + '\n</tbody></table>')
    zonas = []
    for z in zones.select('.zone-badge'):
        letter = z.strong.extract().get_text(strip=True)
        zonas.append(f'<b>Zona {letter} / Zone {letter}:</b> {z.get_text(" ", strip=True)}')
    zonas = ' &nbsp;·&nbsp; '.join(zonas)
    logo = (ROOT / 'assets' / 'logo-white.svg').read_text(encoding='utf-8').replace('#f2efe9', '#0a0a0a')
    qr = (ROOT / 'assets' / 'qr-whatsapp-hoteles.svg').read_text(encoding='utf-8')
    src = (ROOT / '_tools' / 'plantilla-hoja-recepcion.html').read_text(encoding='utf-8')
    return (src.replace('<!--LOGO_SVG-->', logo).replace('<!--QR_SVG-->', qr)
               .replace('<!--PRECIOS_PDF-->', precios).replace('<!--ZONAS_PDF-->', zonas))


def build_pdf():
    """Imprime la hoja para recepción con Chrome, solo si su contenido cambió
    (cada PDF lleva fecha de creación, y así git no registra cambios vacíos)."""
    html = pdf_html()
    digest = hashlib.sha256(html.encode('utf-8')).hexdigest()
    if PDF_OUT.exists() and PDF_HASH.exists() and PDF_HASH.read_text().strip() == digest:
        print(f'pdf: {PDF_OUT.relative_to(ROOT)} sin cambios')
        return
    if not pathlib.Path(CHROME).exists():
        print('AVISO: no encontré Google Chrome; la hoja PDF para recepción no se actualizó.')
        return
    with tempfile.TemporaryDirectory() as tmp:
        src = pathlib.Path(tmp) / 'hoja.html'
        src.write_text(html, encoding='utf-8')
        tmp_pdf = pathlib.Path(tmp) / 'hoja.pdf'
        subprocess.run([CHROME, '--headless', '--disable-gpu', '--no-pdf-header-footer',
                        '--virtual-time-budget=8000', f'--print-to-pdf={tmp_pdf}', src.as_uri()],
                       check=True, capture_output=True)
        shutil.copyfile(tmp_pdf, PDF_OUT)
    PDF_HASH.write_text(digest + '\n')
    print(f'pdf: {PDF_OUT.relative_to(ROOT)} ({PDF_OUT.stat().st_size:,} bytes)')


def build_sitemap():
    today = __import__('datetime').date.today().isoformat()
    urls = []
    for page in PAGES:
        meta = page['meta']
        alts = ''.join(f'\n    <xhtml:link rel="alternate" hreflang="{"es-MX" if l == "es" else "en"}" href="{SITE}{meta[l]["path"]}"/>'
                       for l in ('es', 'en') if l in meta)
        alts += f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{SITE}{meta["es"]["path"]}"/>'
        for l in ('es', 'en'):
            if l in meta:
                urls.append(f'  <url>\n    <loc>{SITE}{meta[l]["path"]}</loc>\n    <lastmod>{today}</lastmod>{alts}\n  </url>')
    for extra in ('/formularios/', '/aviso-de-privacidad/'):
        urls.append(f'  <url>\n    <loc>{SITE}{extra}</loc>\n    <lastmod>{today}</lastmod>\n  </url>')
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
           + '\n'.join(urls) + '\n</urlset>\n')
    (ROOT / 'sitemap.xml').write_text(xml, encoding='utf-8')
    print(f'sitemap.xml ({len(urls)} URL)')


def build_llms():
    lines = ['# Dr. Cristóbal J. Ortega-Arenas — Médico general bilingüe en Ciudad de México', '',
             '> Médico Cirujano (UNAM, cédula profesional 14848636), título homologado en España (2025-17271). '
             'Medicina general ambulatoria en español e inglés: visitas a hotel (24 h) y a domicilio, consultorio '
             '(Del Valle, Roma, Polanco, Santa Fe), teleconsulta, hidratación intravenosa con valoración previa, '
             'certificados médicos y Resumen Clínico del Viajero. Honorarios publicados en MXN. No es un servicio '
             'de urgencias. Contacto: WhatsApp +52 595 109 3969. Aviso de publicidad COFEPRIS 2515192002A00033.', '',
             '## Páginas / Pages', '']
    for page in PAGES:
        for l in ('es', 'en'):
            if l in page['meta']:
                m = page['meta'][l]
                lines.append(f'- [{m["title"]}]({SITE}{m["path"]}): {m["description"]}')
    (ROOT / 'llms.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('llms.txt')


if __name__ == '__main__':
    for page in PAGES:
        for lang in ('es', 'en'):
            if lang in page['meta']:
                render(page, lang)
    build_pdf()
    build_sitemap()
    build_llms()

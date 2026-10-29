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
import re
import shutil
import subprocess
import tempfile
import urllib.parse

from bs4 import BeautifulSoup

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = 'https://drcjortegaarenas.com'
LANGS = ('es', 'en', 'fr')  # el francés se genera solo en las plantillas que ya traen data-fr
LOCALE = {'es': ('es-MX', 'es_MX'), 'en': ('en', 'en_US'), 'fr': ('fr', 'fr_FR')}

META = {
    'es': {
        'path': '/',
        'html_lang': 'es-MX',
        'title': 'Médico general bilingüe en CDMX | Dr. Ortega-Arenas',
        'description': 'Médico general bilingüe en CDMX: visita a su hotel, a domicilio, en consultorio '
                       '(Del Valle, Roma, Polanco, Santa Fe) y teleconsulta. Honorarios publicados en MXN.',
        'og_title': 'Dr. Cristóbal J. Ortega-Arenas — Médico general bilingüe en CDMX',
        'og_locale': 'es_MX', 'og_alt': 'en_US',
        'crumb_home': 'Inicio',
        'phys_desc': 'Médico general bilingüe (español/inglés) en la Ciudad de México: consultorio, '
                     'teleconsulta, visitas a domicilio y a hotel, y terapia de hidratación intravenosa.',
    },
    'en': {
        'path': '/en/',
        'html_lang': 'en',
        'title': 'English-Speaking Doctor in Mexico City | Hotel, Home & Clinic',
        'description': 'English-speaking doctor in Mexico City: hotel visits, house calls, clinics in Polanco, '
                       'Roma, Del Valle and Santa Fe, and telemedicine. Fees published in MXN.',
        'og_title': 'Dr. Cristóbal J. Ortega-Arenas — English-speaking doctor in Mexico City',
        'og_locale': 'en_US', 'og_alt': 'es_MX',
        'crumb_home': 'Home',
        'phys_desc': 'Bilingual (English/Spanish) general physician in Mexico City: clinic visits, '
                     'telemedicine, house calls, hotel visits and IV hydration therapy.',
    },
    'fr': {
        'path': '/fr/',
        'html_lang': 'fr',
        'title': 'Médecin à Mexico : hôtel, domicile, cabinet | Dr Ortega-Arenas',
        'description': 'Médecin généraliste à Mexico, consultation en espagnol ou en anglais : hôtel, domicile, cabinet '
                       'et téléconsultation. Assistante francophone en option, sous réserve de disponibilité.',
        'og_title': 'Dr Cristóbal J. Ortega-Arenas — Médecin généraliste à Mexico',
        'og_locale': 'fr_FR', 'og_alt': 'es_MX',
        'crumb_home': 'Accueil',
        'phys_desc': 'Médecin généraliste à Mexico (consultation en espagnol ou en anglais, assistante francophone '
                     'en option) : cabinet, téléconsultation, visites à domicile et à l’hôtel.',
    },
}

META_HOTELES = {
    'es': {
        'path': '/hoteles/',
        'html_lang': 'es-MX',
        'title': 'Médico a hotel en CDMX: información para hoteles y concierges',
        'description': 'Visita médica bilingüe para huéspedes en CDMX: cómo solicitarla por WhatsApp o en línea, '
                       'llegada estimada por zona, tarifas y documentos para el seguro.',
        'og_title': 'Para hoteles y concierges — Dr. Cristóbal J. Ortega-Arenas',
        'og_locale': 'es_MX', 'og_alt': 'en_US',
        'crumb': 'Para hoteles y concierges', 'home': 'Inicio',
    },
    'en': {
        'path': '/en/hotels/',
        'html_lang': 'en',
        'title': 'Hotel Doctor in Mexico City: Info for Hotels & Concierges',
        'description': 'Bilingual doctor visits for hotel guests in Mexico City: how to request one by WhatsApp '
                       'or online, arrival time by area, fees and travel insurance documents.',
        'og_title': 'For hotels & concierges — Dr. Cristóbal J. Ortega-Arenas',
        'og_locale': 'en_US', 'og_alt': 'es_MX',
        'crumb': 'For hotels & concierges', 'home': 'Home',
    },
    'fr': {
        'path': '/fr/hotels/',
        'html_lang': 'fr',
        'title': 'Médecin à l’hôtel à Mexico : infos pour hôtels et concierges',
        'description': 'Visite médicale pour vos clients à Mexico : demande par WhatsApp ou en ligne, arrivée '
                       'estimée selon le quartier, tarifs et documents pour l’assurance.',
        'og_title': 'Pour hôtels et concierges — Dr Cristóbal J. Ortega-Arenas',
        'og_locale': 'fr_FR', 'og_alt': 'es_MX',
        'crumb': 'Pour hôtels et concierges', 'home': 'Accueil',
    },
}

PAGES = [
    {'template': 'plantilla.html', 'meta': META,
     'out': {'es': 'index.html', 'en': 'en/index.html', 'fr': 'fr/index.html'}},
    {'template': 'plantilla-hoteles.html', 'meta': META_HOTELES,
     'out': {'es': 'hoteles/index.html', 'en': 'en/hotels/index.html', 'fr': 'fr/hotels/index.html'}},
]


def load_pages():
    """Cada _tools/paginas/*.json registra una página nueva sin tocar este script."""
    pages = []
    for f in sorted((ROOT / '_tools' / 'paginas').glob('*.json')):
        cfg = json.loads(f.read_text(encoding='utf-8'))
        meta = {lang: dict(cfg[lang], home=META[lang]['crumb_home']) for lang in LANGS if lang in cfg}
        for lang in meta:
            meta[lang].setdefault('html_lang', LOCALE[lang][0])
            meta[lang].setdefault('og_locale', LOCALE[lang][1])
            meta[lang].setdefault('og_alt', 'en_US' if lang == 'es' else 'es_MX')
            meta[lang].setdefault('og_title', meta[lang]['title'])
        out = {lang: meta[lang]['path'].strip('/') + '/index.html' for lang in meta}
        pages.append({'template': cfg['plantilla'], 'meta': meta, 'out': out, 'cfg': cfg})
    return pages


PAGES += load_pages()


def con_frances(page):
    """El francés solo se publica si la plantilla ya trae los textos (data-fr)."""
    src = (ROOT / '_tools' / page['template']).read_text(encoding='utf-8')
    if 'fr' in page['meta'] and 'data-fr=' not in src:
        page['meta'] = {k: v for k, v in page['meta'].items() if k != 'fr'}
        page['out'] = {k: v for k, v in page['out'].items() if k != 'fr'}


for _p in PAGES:
    con_frances(_p)

PDF_OUT = ROOT / 'assets' / 'hoja-recepcion-hoteles.pdf'
PDF_HASH = ROOT / '_tools' / '.hoja-recepcion.sha256'
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

# Consultorios: todos en Briyam Coworking Médico. Direcciones tal como están en Cal.com (cada evento de
# consultorio), revisadas el 19-oct-2026. Única fuente de las direcciones: <span data-sede="Polanco"></span>
# en una plantilla se convierte en la dirección con enlace a Google Maps, y aquí salen también en el JSON-LD.
# Sin código postal: no está verificado.
SEDES = {  # sede: (sede en Briyam, calle y número con piso, colonia o None, alcaldía corta, alcaldía oficial)
    'Del Valle': ('Florida del Valle', 'Av. Río Mixcoac 25, piso 8', None, 'Benito Juárez', 'Benito Juárez'),
    'Roma': ('Roma Sur', 'Monterrey 243, piso 5', 'Roma Sur', 'Cuauhtémoc', 'Cuauhtémoc'),
    'Polanco': ('Masaryk', 'Av. Presidente Masaryk 134, piso 4', 'Polanco', 'Miguel Hidalgo', 'Miguel Hidalgo'),
    'Santa Fe': ('Santa Fe', 'Vasco de Quiroga 3900, Torre B, piso 5', 'Santa Fe', 'Cuajimalpa', 'Cuajimalpa de Morelos'),
}


def sede_texto(sede):
    _, calle, colonia, alcaldia, _ = SEDES[sede]
    return ', '.join(x for x in (calle, colonia, alcaldia, 'CDMX') if x)


def sede_maps(sede):
    _, calle, colonia, _, alcaldia = SEDES[sede]
    calle = calle.split(', piso')[0].split(', Torre')[0]  # Maps no necesita piso ni torre
    lugar = ', '.join(x for x in (calle, colonia, alcaldia, 'Ciudad de México') if x)
    return 'https://www.google.com/maps/search/?api=1&query=' + urllib.parse.quote_plus(lugar)


def sede_html(sede):
    return f'<a href="{sede_maps(sede)}" target="_blank" rel="noopener">{sede_texto(sede)}</a>'


def clinica(sede):
    briyam, calle, colonia, _, alcaldia = SEDES[sede]
    direccion = {'@type': 'PostalAddress', 'streetAddress': ', '.join(x for x in (calle, colonia) if x),
                 'addressLocality': alcaldia, 'addressRegion': 'CDMX', 'addressCountry': 'MX'}
    return {'@type': 'MedicalClinic', '@id': f'{SITE}/#consultorio-{sede.lower().replace(" ", "-")}',
            'name': f'Consultorio {sede} — Dr. Cristóbal J. Ortega-Arenas',
            'telephone': '+52 595 109 3969', 'hasMap': sede_maps(sede),
            'url': SITE + {'Polanco': '/zonas/polanco/', 'Roma': '/zonas/roma-condesa/',
                           'Del Valle': '/zonas/del-valle/', 'Santa Fe': '/zonas/santa-fe/'}[sede],
            'openingHoursSpecification': [  # el mismo horario publicado en la tarjeta de consultorio
                {'@type': 'OpeningHoursSpecification', 'opens': '17:00', 'closes': '20:00',
                 'dayOfWeek': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']},
                {'@type': 'OpeningHoursSpecification', 'dayOfWeek': 'Saturday', 'opens': '11:00', 'closes': '15:00'}],
            'address': direccion,
            'containedInPlace': {'@type': 'Place', 'name': f'Briyam Coworking Médico, sede {briyam}', 'address': direccion}}


AREAS = ['Polanco', 'Roma', 'Condesa', 'Del Valle', 'Santa Fe', 'Reforma', 'Coyoacán', 'Pedregal',
         'Centro Histórico', 'Texcoco']


def head_meta(meta, lang):
    m = meta[lang]
    url = SITE + m['path']
    es_url = SITE + meta['es']['path']
    en_url = SITE + meta['en']['path'] if 'en' in meta else None
    fr_url = SITE + meta['fr']['path'] if 'fr' in meta else None
    esc = lambda t: t.replace('&', '&amp;').replace('"', '&quot;')
    lines = [
        f'<title>{esc(m["title"])}</title>',
        f'<meta name="description" content="{esc(m["description"])}">',
        '<meta name="author" content="Dr. Cristóbal J. Ortega-Arenas">',
        '<meta name="robots" content="index, follow">',
        f'<link rel="canonical" href="{url}">',
        f'<link rel="alternate" hreflang="es" href="{es_url}">',
        *([f'<link rel="alternate" hreflang="en" href="{en_url}">'] if en_url else []),
        *([f'<link rel="alternate" hreflang="fr" href="{fr_url}">'] if fr_url else []),
        f'<link rel="alternate" hreflang="x-default" href="{en_url or es_url}">',
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
        'image': SITE + '/assets/foto-perfil-color-813.webp',
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
        'location': [clinica(sede) for sede in SEDES],
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
    ('Hidratación intravenosa (sin visita ni enfermería)', 'IV hydration (visit and nursing not included)', 1800),
    ('Certificado médico digital', 'Digital medical certificate', 500),
]


OFFERS_FR = ['Visite médicale à l’hôtel', 'Visite à domicile', 'Consultation au cabinet', 'Téléconsultation',
             'Forfait Voyageur', 'Hydratation intraveineuse (visite et soins infirmiers non inclus)',
             'Certificat médical numérique']


def offers(lang):
    i = 0 if lang == 'es' else 1
    nombre = (lambda n, o: OFFERS_FR[n]) if lang == 'fr' else (lambda n, o: o[i])
    return [{'@type': 'Offer', 'name': nombre(n, o), 'priceCurrency': 'MXN',
             'priceSpecification': {'@type': 'PriceSpecification', 'minPrice': o[2], 'priceCurrency': 'MXN'}}
            for n, o in enumerate(OFFERS)]


def medical_page(page, lang):
    """MedicalWebPage para servicios y guías: autor, revisión y fuentes citadas."""
    cfg, m = page['cfg'], page['meta'][lang]
    medico = {'@type': 'Physician', '@id': SITE + '/#medico', 'name': 'Dr. Cristóbal J. Ortega-Arenas',
              'url': SITE + META[lang]['path']}
    obj = {
        '@context': 'https://schema.org',
        '@type': 'MedicalWebPage',
        'name': m['title'],
        'description': m['description'],
        'url': SITE + m['path'],
        'inLanguage': m['html_lang'],
        'author': medico,
        'reviewedBy': medico,
        'lastReviewed': cfg.get('revisado'),
        'publisher': medico,
    }
    if cfg.get('audiencia'):
        obj['audience'] = {'@type': 'PeopleAudience', 'audienceType': cfg['audiencia'][lang] if isinstance(cfg['audiencia'], dict) else cfg['audiencia']}
    if cfg.get('sede'):
        obj['about'] = clinica(cfg['sede'])
    if cfg.get('citas'):
        obj['citation'] = [{'@type': 'CreativeWork', 'name': c['nombre'], 'url': c['url']} for c in cfg['citas']]
    return jsonld({k: v for k, v in obj.items() if v})


def faq(soup):
    items = []
    for card in soup.select('.faq-item'):
        q = card.find('h3').get_text(' ', strip=True)
        fr = (soup.html.get('lang') or '').startswith('fr')
        a = re.sub(r'\s+([,.])' if fr else r'\s+([;,.])', r'\1', card.find('p').get_text(' ', strip=True))  # 'CDMX ;' → 'CDMX;'
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


def tarifas():
    """Precios publicados en plantilla.html para las páginas por zona, por clave:
      zona:Polanco          → 'A' o 'B' (zona de hotel según las etiquetas de zona)
      hotel:Polanco:0..2    → visita a hotel en esa zona (0 ordinario, 1 especial, 2 festivo)
      consultorio:Polanco   → consulta en la sede de ese nombre
      domicilio:Polanco:0..2 → consulta a domicilio en la fila que menciona ese nombre
      anticipo:Polanco       → 50 % de la consulta en esa sede (lo que se paga al reservar en Cal.com)
      anticipo-domicilio:Polanco → 50 % de la tarifa ordinaria a domicilio (anticipo por transferencia)
      asistente-frances      → asistente de traducción al francés (tabla de procedimientos)
      asistente-frances-hotel-especial → la misma asistente en visita a hotel en horario especial o festivo
      subsecuente:Del Valle  → segundo precio de la celda del consultorio (consulta subsecuente)
      seguimiento:Del Valle  → segundo precio de la celda de domicilio ordinario (seguimiento*)
      paquete:Del Valle      → Paquete Viajero cuya etiqueta menciona ese nombre
      paquete-sin-certificado:Del Valle → lo que se cobra si el certificado no procede
    En las plantillas: <span data-tarifa="hotel:Polanco:0"></span>, y build.py escribe el precio."""
    soup = BeautifulSoup(main_template(), 'html.parser')
    first = lambda td: td.find(string=True).strip()  # '$1,000<br>$900*' → '$1,000'
    t = {}
    table, zones = hotel_card()
    hotel = [[first(td) for td in tr.find_all('td')[1:]] for tr in table.select('tbody tr')]
    for z in zones.select('.zone-badge'):
        letter = z.strong.get_text(strip=True)
        col = 'AB'.index(letter)
        for area in z.get_text(' ', strip=True)[len(letter):].split('·'):
            area = area.strip()
            t[f'zona:{area}'] = letter
            for i, row in enumerate(hotel):
                t[f'hotel:{area}:{i}'] = row[col]
    for tr in soup.select('[data-tarifas-consultorio] tbody tr'):
        tds = tr.find_all('td')
        sede = first(tds[0])
        t[f'consultorio:{sede}'] = first(tds[2])
        t[f'anticipo:{sede}'] = f"${int(first(tds[2]).strip('$').replace(',', '')) // 2:,}"
        precios = [s for s in tds[2].stripped_strings if s.startswith('$')]
        if len(precios) > 1:
            t[f'subsecuente:{sede}'] = precios[1]
    for tr in soup.select('[data-tarifas-domicilio] tbody tr'):
        tds = tr.find_all('td')
        label = '·'.join(tds[0].stripped_strings).replace('&', '·')
        seguimiento = [s.rstrip('*') for s in tds[1].stripped_strings][1:2]
        for area in label.split('·'):
            for i, td in enumerate(tds[1:]):
                t[f'domicilio:{area.strip()}:{i}'] = first(td)
            if seguimiento:
                t[f'seguimiento:{area.strip()}'] = seguimiento[0]
            t[f'anticipo-domicilio:{area.strip()}'] = f"${int(first(tds[1]).strip('$').replace(',', '')) // 2:,}"
    for txt in soup.select('.offer-text[data-es]'):  # '($1,800 en Del Valle; …)' si no procede el certificado
        for area in ('Del Valle',):
            m = re.search(r'(\$[\d,]+) en ' + area, txt['data-es'])
            if m:
                t[f'paquete-sin-certificado:{area}'] = m.group(1)
    for row in soup.select('[data-tarifa-frances]'):  # asistente de traducción al francés
        t['asistente-frances'] = row.select_one('.proc-price').get_text(strip=True)
    for row in soup.select('[data-tarifa-frances-especial]'):  # en hotel, horario especial o festivo
        t['asistente-frances-hotel-especial'] = row.select_one('.proc-price').get_text(strip=True)
    for div in soup.select('.offer-price[data-es]'):
        oferta = BeautifulSoup(div['data-es'], 'html.parser')
        for area in ('Del Valle',):
            if area in oferta.get_text():
                t[f'paquete:{area}'] = oferta.strong.get_text(strip=True)
    return t


def render(page, lang):
    meta = page['meta']
    src = (ROOT / '_tools' / page['template']).read_text(encoding='utf-8')
    for mark, part in (('<!--NAV-->', 'nav.html'), ('<!--PIE-->', 'pie.html')):
        src = src.replace(mark, (ROOT / '_tools' / 'parciales' / part).read_text(encoding='utf-8'))
    src = (src.replace('{{URL_ES}}', meta['es']['path']).replace('{{URL_EN}}', meta['en']['path'] if 'en' in meta else '/en/')
              .replace('{{URL_FR}}', meta['fr']['path'] if 'fr' in meta else '/fr/'))
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
        for l in LANGS:
            if el.has_attr('data-' + l):
                del el['data-' + l]
    # alt, aria-label y href por idioma; en francés, si falta, se usa el de inglés
    for kind, target in (('alt', 'alt'), ('aria', 'aria-label'), ('href', 'href')):
        for el in soup.select(f'[data-{kind}-en], [data-{kind}-fr]'):
            value = el.get(f'data-{kind}-{lang}') if lang != 'es' else None
            if value is None and lang == 'fr':
                value = el.get(f'data-{kind}-en')
            if value is not None:
                el[target] = value
            for l in ('en', 'fr'):
                if el.has_attr(f'data-{kind}-{l}'):
                    del el[f'data-{kind}-{l}']
    for attr in ('data-tarifas-hotel', 'data-tarifas-consultorio', 'data-tarifas-domicilio', 'data-tarifa-frances', 'data-tarifa-frances-especial'):
        for el in soup.select(f'[{attr}]'):
            del el[attr]
    for el in soup.select('[data-sede]'):
        if el['data-sede'] not in SEDES:
            raise SystemExit(f'No conozco la sede {el["data-sede"]!r} (ver SEDES en build.py)')
        el.clear()
        el.append(BeautifulSoup(sede_html(el['data-sede']), 'html.parser'))
        del el['data-sede']
    marked = soup.select('[data-tarifa]')
    if marked:
        precios = tarifas()
        for el in marked:
            if el['data-tarifa'] not in precios:
                raise SystemExit(f'No encuentro la tarifa {el["data-tarifa"]!r} en plantilla.html')
            el.string = precios[el['data-tarifa']]
            del el['data-tarifa']
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


def fecha(page, today):
    """Fecha de revisión de la página (JSON) o, si no tiene, del último commit de su plantilla."""
    if page.get('cfg', {}).get('revisado'):
        return page['cfg']['revisado']
    r = subprocess.run(['git', 'log', '-1', '--format=%cs', '--', f'_tools/{page["template"]}'],
                       cwd=ROOT, capture_output=True, text=True)
    return r.stdout.strip() or today


def build_sitemap():
    today = __import__('datetime').date.today().isoformat()
    urls = []
    for page in PAGES:
        meta = page['meta']
        alts = ''.join(f'\n    <xhtml:link rel="alternate" hreflang="{l}" href="{SITE}{meta[l]["path"]}"/>'
                       for l in LANGS if l in meta)
        alts += f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{SITE}{meta["en" if "en" in meta else "es"]["path"]}"/>'
        for l in LANGS:
            if l in meta:
                urls.append(f'  <url>\n    <loc>{SITE}{meta[l]["path"]}</loc>\n    <lastmod>{fecha(page, today)}</lastmod>{alts}\n  </url>')
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
             'certificados médicos y Resumen Clínico del Viajero. Honorarios publicados en MXN. Atiende a personas de 15 años o más; no atiende a '
             'menores de 15 años ni a personas embarazadas. No es un servicio de urgencias. Contacto: WhatsApp +52 595 109 3969. Aviso de publicidad COFEPRIS 2515192002A00033.', '',
             '## Consultorios / Clinics (Briyam Coworking Médico, con cita / by appointment)', '',
             *[f'- {sede}: {sede_texto(sede)}' for sede in SEDES], '',
             '## Páginas / Pages', '']
    for page in PAGES:
        for l in LANGS:
            if l in page['meta']:
                m = page['meta'][l]
                lines.append(f'- [{m["title"]}]({SITE}{m["path"]}): {m["description"]}')
    (ROOT / 'llms.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('llms.txt')


if __name__ == '__main__':
    for page in PAGES:
        for lang in LANGS:
            if lang in page['meta']:
                render(page, lang)
    build_pdf()
    build_sitemap()
    build_llms()

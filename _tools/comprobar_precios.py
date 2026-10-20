"""Comprueba que los precios de las páginas por zona son los publicados en la portada.

Uso, desde la carpeta del repositorio, después de python3 -I _tools/build.py:
    python3 -I _tools/comprobar_precios.py

Lee las tablas de tarifas de index.html (lo que ve el público, no la plantilla) y
compara, en español y en inglés, cada celda de la tabla de cada página por zona y
cada monto que aparece en su texto. Termina con error si algo no coincide.
"""
import pathlib
import re

from bs4 import BeautifulSoup

ROOT = pathlib.Path(__file__).resolve().parent.parent

# zona: (archivos ES/EN, nombre en la tabla de hotel, sede de consultorio, fila de domicilio)
ZONAS = {
    'Polanco': (('zonas/polanco', 'en/doctor-polanco', 'fr/medecin-polanco'), 'Polanco', 'Polanco', 'Polanco'),
    'Roma-Condesa': (('zonas/roma-condesa', 'en/doctor-roma-condesa', 'fr/medecin-roma-condesa'), 'Roma', 'Roma', 'Condesa'),
    'Santa Fe': (('zonas/santa-fe', 'en/doctor-santa-fe', 'fr/medecin-santa-fe'), 'Santa Fe', 'Santa Fe', 'Santa Fe'),
    'Del Valle': (('zonas/del-valle', 'en/doctor-del-valle', 'fr/medecin-del-valle'), 'Del Valle', 'Del Valle', 'Del Valle'),
}
MONTO = re.compile(r'\$\s?\d{1,3}(?:,\d{3})+|MXN\s\d{1,3}(?:,\d{3})+')


def norm(m):
    return '$' + re.sub(r'[^\d,]', '', m)


def primero(td):
    return td.find(string=True).strip()


def tabla(soup, encabezado):
    for t in soup.select('table.price-table'):
        if t.find('th') and t.find('th').get_text(strip=True) == encabezado:
            return t
    raise SystemExit(f'No encuentro en index.html la tabla que empieza con {encabezado!r}')


def publicados():
    soup = BeautifulSoup((ROOT / 'index.html').read_text(encoding='utf-8'), 'html.parser')
    hotel = [[primero(td) for td in tr.find_all('td')[1:]] for tr in tabla(soup, 'Horario').select('tbody tr')]
    zona_de = {}
    for z in soup.select('.zone-badge'):
        letra = z.strong.get_text(strip=True)
        for area in z.get_text(' ', strip=True)[len(letra):].split('·'):
            zona_de[area.strip()] = 'AB'.index(letra)
    consultorio, extras = {}, {}
    for tr in tabla(soup, 'Sede').select('tbody tr'):
        tds = tr.find_all('td')
        sede = primero(tds[0])
        consultorio[sede] = primero(tds[2])
        extras.setdefault(sede, set()).add(f"${int(primero(tds[2]).strip('$').replace(',', '')) // 2:,}")  # anticipo 50 %
        extras.setdefault(sede, set()).update(s for s in tds[2].stripped_strings if s.startswith('$'))
    domicilio = {}
    for tr in tabla(soup, 'Zona / Ubicación').select('tbody tr'):
        tds = tr.find_all('td')
        for area in '·'.join(tds[0].stripped_strings).replace('&', '·').split('·'):
            domicilio[area.strip()] = [primero(td) for td in tds[1:]]
            extras.setdefault(area.strip(), set()).update(s.rstrip('*') for s in tds[1].stripped_strings)
            extras[area.strip()].add(f"${int(primero(tds[1]).strip('$').replace(',', '')) // 2:,}")  # anticipo domicilio
    for div in soup.select('.offer-price'):  # Paquete Viajero, por sede
        for area in list(extras):
            if area in div.get_text(' '):
                extras[area].add(div.strong.get_text(strip=True))
    for txt in soup.select('.offer-text'):  # '($1,800 en Del Valle; …)' si no procede el certificado
        for area in list(extras):
            extras[area].update(re.findall(r'(\$[\d,]+) en ' + area, txt.get_text(' ')))
    for row in soup.select('.proc-row'):  # asistente de traducción al francés: válida en todas las zonas
        if 'Francés' in row.get_text(' '):
            for area in list(extras):
                extras[area].add(row.select_one('.proc-price').get_text(strip=True))
    return hotel, zona_de, consultorio, domicilio, extras


def main():
    hotel, zona_de, consultorio, domicilio, extras = publicados()
    errores, revisadas, paginas = [], 0, 0
    for zona, (rutas, h, c, d) in ZONAS.items():
        filas = {
            'hotel': [row[zona_de[h]] for row in hotel],
            'domicilio': domicilio[d],
            'consultorio': [consultorio[c], '—', consultorio['Días Festivos']],
        }
        validos = {m for fila in filas.values() for m in fila if m != '—'}
        validos |= extras.get(c, set()) | extras.get(d, set())  # subsecuente, seguimiento, paquete
        for ruta in rutas:
            if not (ROOT / ruta / 'index.html').exists():  # versión en francés aún no generada
                continue
            paginas += 1
            soup = BeautifulSoup((ROOT / ruta / 'index.html').read_text(encoding='utf-8'), 'html.parser')
            prose = soup.select_one('main.page-body')
            for tr in prose.select('table tbody tr'):
                etiqueta = tr.find('td').get_text(strip=True).lower()
                tipo = ('consultorio' if any(w in etiqueta for w in ('consultorio', 'clinic', 'cabinet'))
                        else 'hotel' if ('hotel' in etiqueta or 'hôtel' in etiqueta) else 'domicilio')
                celdas = [td.get_text(strip=True) for td in tr.find_all('td')[1:]]
                revisadas += len(celdas)
                if celdas != filas[tipo]:
                    errores.append(f'{ruta}: fila {etiqueta!r} = {celdas}, publicado {filas[tipo]}')
            texto = soup.select_one('header.page-hero').get_text(' ') + ' ' + prose.get_text(' ')
            for m in MONTO.findall(texto):
                revisadas += 1
                if norm(m) not in validos:
                    errores.append(f'{ruta}: el monto {m} no es una tarifa publicada de {zona}')
            letra = 'AB'[zona_de[h]]
            for txt in re.findall(r'(?i:Zona|Zone) ([AB])\b', texto):
                if txt != letra:
                    errores.append(f'{ruta}: dice Zona {txt}, pero {h} está en la Zona {letra}')
    if errores:
        raise SystemExit('Precios que NO coinciden:\n' + '\n'.join(errores))
    print(f'OK: {revisadas} precios revisados en {paginas} páginas; todos coinciden con index.html.')


if __name__ == '__main__':
    main()

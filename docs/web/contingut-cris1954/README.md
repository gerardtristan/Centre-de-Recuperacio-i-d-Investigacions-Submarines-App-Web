# Contingut de la web actual del club (cris1954.cat)

Inventari del contingut (no del format) de <https://cris1954.cat/>, perquè sigui la base de les pàgines inicials de l'editor de la web (07) amb la mateixa estructura de menú. Encàrrec del propietari del 27/11/2026 (punt B); tasca T-M07-37 ([`docs/estat/M07.md`](../../estat/M07.md)).

- **Data del rastreig:** 27/11/2026, entre les 22:00 i les 23:00.
- **Com:** des de la portada, seguint tots els enllaços del mateix domini (sense paràmetres de cerca), amb una espera d'1 s entre peticions; a més, la llista de pàgines de l'API pública de WordPress (`/wp-json/wp/v2/pages`, 11 pàgines publicades) i de la biblioteca de mitjans. No hi ha mapa del lloc (`/sitemap.xml` i `/wp-sitemap.xml` donen 404; `robots.txt` només tanca l'administració i WooCommerce). Cap formulari no s'ha enviat.
- **Mateix lloc, tres adreces:** `www.cris1954.cat` redirigeix a `cris1954.cat`, i `cris.barcelona` serveix el mateix WordPress (mateixes pàgines). Per això la [107](../../decisions/107-fotos-reals-del-club-per-a-plantilles-mostres-i-captures.md), que parla de les fotos de cris.barcelona, cobreix aquestes imatges.
- **Tecnologia actual:** WordPress amb el tema Astra, Elementor, WooCommerce (botiga tancada) i Complianz (galetes).

## Índex

| Fitxa | Adreça | Al menú |
|---|---|---|
| [Inici](inici.md) | <https://cris1954.cat/> | Capçalera 1 (i 2 a 4 com a àncores) |
| [Formació / Cursos](formacio-cursos.md) | <https://cris1954.cat/inici/formacio-cursos/> | Capçalera 5 |
| [Activitats](activitats.md) | <https://cris1954.cat/activitats/> | Capçalera 9 |
| [Galeria de fotos](galeria-de-fotos.md) | <https://cris1954.cat/inici/galeria-de-fotos/> | No (el menú va a Google Drive) |
| [Avís Legal](avis-legal.md) | <https://cris1954.cat/avis-legal/> | Peu 1 |
| [Política de cookies (EU)](politica-de-cookies-eu.md) | <https://cris1954.cat/politica-de-cookies-eu/> | Peu 2 |
| [Botiga](botiga.md) | <https://cris1954.cat/botiga/> | No |
| [Samarreta C.R.I.S. Unisex](producte-samarreta-cris.md) | <https://cris1954.cat/producte/samarreta-cris/> | No |
| [Cistella](cistella.md) | <https://cris1954.cat/cistella/> | No |
| [Finalitza la compra](finalitza-la-compra.md) | <https://cris1954.cat/finalitza-la-compra/> | No |
| [El meu compte](el-meu-compte.md) | <https://cris1954.cat/el-meu-compte/> | No |
| [WPMS HTML Sitemap](wpms-html-sitemap.md) | <https://cris1954.cat/wpms-html-sitemap/> | No |

També existeix l'arxiu de la categoria «cursos, com son?» (<https://cris1954.cat/category/detall-dels-cursos/>), buit (diu «Sembla que no trobem aquesta pàgina»): no hi ha cap entrada de blog publicada.

## Arbre del menú

Menú de la capçalera (igual a l'escriptori i al mòbil). És **pla**: cap entrada no té submenú.

1. Inici → <https://cris1954.cat/>
2. Qui som → secció `#Qui-Som` de la portada
3. Serveis → secció `#Serveis` de la portada
4. On sóm → secció `#Mapa` de la portada
5. Informació Cursos → <https://cris1954.cat/inici/formacio-cursos/>
6. Breu Història CRIS → vídeo en un OneDrive extern <https://1drv.ms/v/c/287a41d165f2372f/ES838mXRQXoggCj9AQAAAAABxYLkTO8Mc72lTl_Y7frKBA?e=bMAVDE>
7. Coneix la teva Federativa! → PDF en un OneDrive extern <https://1drv.ms/b/c/287a41d165f2372f/Ee1eC0nnTyxOiz3kgneFu9UBXYC_hFyX-2l6R9NSKWLhSw?e=xGWbXf>
8. **FES-TE SOCI** (entrada destacada) → Cluber <https://app.cluber.es/clubes/69121cfff160b125652830/alta/socios>
9. Activitats → <https://cris1954.cat/activitats/>
10. Galeria de fotos → carpeta de Google Drive <https://drive.google.com/drive/folders/1NAdipVxgk8IT7IwlmTE9hK34wQqolCud>
11. BOTIGA PER ALS SOCIS → Cluber <https://app.cluber.es/clubes/69121cfff160b125652830/pagos/69b1fb8b6b8bf828619185>
12. BOTIGA PER A TOTHOM → Cluber <https://app.cluber.es/clubes/69121cfff160b125652830/pagos/6995f5745e669398128037>
13. COMPRA DE LLIBRES → Cluber <https://app.cluber.es/clubes/69121cfff160b125652830/pagos/69d44cd29e738077657238>

A la dreta de la capçalera, el botó **CONTACTE** → secció `#Contacte` de la portada.

Menú del peu:

1. Avís Legal → <https://cris1954.cat/avis-legal/>
2. Política de cookies (EU) → <https://cris1954.cat/politica-de-cookies-eu/>

Jerarquia de pàgines a WordPress (no és el menú): «Formació / Cursos» i «Galeria de fotos» pengen d'«Inici»; la resta són de primer nivell.

## Elements comuns

**Capçalera.** Enllaç «Vés al contingut» (per a teclat); logotip del club (blanc, text alternatiu «(C.R.I.S.) Centre de Recuperació i d'Investigacions Submarines») que enllaça a la portada; el menú de la capçalera; el botó «CONTACTE».

**Peu.** Logotip del club (text alternatiu «C.R.I.S.») que enllaça a la portada; «Segueix-nos a les nostres xarxes socials» amb [Facebook](https://www.facebook.com/CRIS1954) i [Instagram](https://www.instagram.com/c.r.i.s.oficial/); «El disseny d'aquesta pàgina web ha estat subvencionat per» amb els logotips de l'Ajuntament de Barcelona i de .barcelona (imatge sense text alternatiu); el menú del peu; «Copyright © 2024 C. R. I. S.»; el botó «Desplaça cap amunt».

**Bàner de galetes (Complianz),** literal:

> Gestió del consentiment de cookies
>
> Per a oferir les millors experiències, utilitzem tecnologies com les cookies per a emmagatzemar i/o accedir a la informació del dispositiu. El consentiment d'aquestes tecnologies ens permetrà processar dades com el comportament de navegació o les identificacions úniques en aquest lloc. No consentir o retirar el consentiment, pot afectar negativament unes certes característiques i funcions.
>
> **Funcional** — Sempre actiu. L'emmagatzematge o l'accés tècnic és estrictament necessari per al propòsit legítim de permetre l'ús d'un servei específic sol·licitat explícitament per l'abonat o l'usuari, o amb l'únic propòsit de dur a terme la transmissió d'una comunicació mitjançant una xarxa de comunicacions electròniques.
>
> **Preferències** — L'emmagatzematge tècnic o l'accés és necessari amb la finalitat legítima d'emmagatzemar preferències que no siguin sol·licitades pel subscriptor o usuari.
>
> **Estadístiques** — L'emmagatzematge o accés tècnic que s'utilitza exclusivament amb finalitats estadístiques. L'emmagatzematge o accés tècnic que s'utilitza exclusivament amb finalitats estadístics anònims. Sense una citació judicial, el compliment voluntari per part del seu proveïdor de serveis d'Internet o registres addicionals d'un tercer, la informació emmagatzemada o recuperada únicament a aquest efecte no pot utilitzar-se normalment per a identificar-li.
>
> **Màrqueting** — L'emmagatzematge o l'accés tècnic és necessari per crear perfils d'usuari per enviar publicitat, o per rastrejar l'usuari en una web o en diverses webs amb fines de màrqueting similars.
>
> Botons i enllaços: «Gestiona les opcions», «Gestiona els serveis», «Gestiona {vendor_count} proveïdors», «Llegeix més sobre aquests propòsits» (<https://cookiedatabase.org/tcf/purposes/>), «Accepta», «Denega», «Veure preferències», «Desa les preferències», «Gestionar el consentiment».

## Dades del club

Les que surten a la web (portada, peu de la portada i avís legal); es copien perquè són del club:

| Dada | Valor |
|---|---|
| Nom | Centre de Recuperació i d'Investigacions Submarines (C.R.I.S.), des de 1954 |
| NIF | G61454070 |
| Adreça | Moll de La Vela, 1 – 08930 Sant Adrià de Besòs (Barcelona); despatx al local de la FECDAS, zona de banys del Fòrum |
| Correu | cris@cris.es |
| Telèfon de secretaria | 625 435 047, de dilluns a divendres de 10:00 a 13:00 h |
| Telèfon d'informació de cursos i sortides | 624 430 268 |
| Horari | De dilluns a divendres, de 10.00 a 13.00 |
| Trobada setmanal | Dijous de 19:30 a 22:30 h al restaurant Tàmara, carrer Muntaner 178, Barcelona |
| Xarxes | <https://www.facebook.com/CRIS1954> · <https://www.instagram.com/c.r.i.s.oficial/> |

## Imatges

61 imatges diferents a les pàgines; totes baixades menys una.

- **Al repositori:** 46 imatges, 9,9 MB, a [`static/img/web/cris1954/`](../../../static/img/web/cris1954/) amb noms descriptius, reduïdes a 1.600 px pel costat llarg i sense EXIF, GPS ni cap altra metadada (comprovat amb un script que falla si en queda), i el fitxer [`fotos.yml`](../../../static/img/web/cris1954/fotos.yml) (autor «C.R.I.S.», permís, si hi surten persones, text alternatiu nou i adreça d'origen). Són la foto històrica de «Qui som», les 17 pàgines del dossier de cursos i els cartells del club.
- **Fora del repositori:** 14 imatges a `D:/CRIS/web-cris1954/imatges/` (mateix tractament), per un d'aquests motius: hi surt el nom d'una persona (la pàgina «Escola de busseig» amb els instructors, el collage de cartells de cursos, la conferència de Magallanes amb el nom i la cara del ponent, la presentació d'un llibre i el documental), són obres de tercers (cartells de la FECDAS, de la FEDAS i del Mediterranean Diving Show, la coberta d'AcuSub, els logotips de la subvenció) o són el logotip del club, que ja és a [`assets/marca/`](../../../assets/marca/). Cada fitxa diu quina és quina.
- **No baixada:** la foto de perfil d'Instagram del club, que la pàgina «Activitats» carrega dels servidors d'Instagram amb una adreça signada.
- La biblioteca de mitjans de WordPress té 219 imatges; només s'han baixat les 60 que surten a les pàgines.

## Documents

Cap pàgina no enllaça cap document descarregable. Els fitxers que no són imatges són a la biblioteca de mitjans, accessibles per l'adreça però no enllaçats; s'han baixat a `D:/CRIS/web-cris1954/documents/` (fora del repositori).

| Fitxer | Mida | Data | Adreça | Notes |
|---|---|---|---|---|
| `Guia-Rapida-MINKA.pdf` | 776 KB | 27/09/2026 | <https://cris1954.cat/wp-content/uploads/2026/09/Guia-Rapida-MINKA.pdf> | La guia de MINKA de la pàgina «Activitats», en PDF |
| `Ademas-de-los-projectos-que-ya-tenemos-en-marcha.docx` | 414 KB | 14/09/2026 | <https://cris1954.cat/wp-content/uploads/2026/09/Ademas-de-los-projectos-que-ya-tenemos-en-marcha.docx> | Text en castellà sobre el projecte SEBIOSUB |
| `ORGANIGRAMA-JUNTA-DIRECTIVA-CRIS-2026.pdf` | 298 KB | 13/05/2026 | (no es copia) | **Dades personals:** noms i càrrecs de la junta. És públic a la web actual sense cap enllaç |
| `ESCOLA-BUSSEIG.pdf` | 514 KB | 30/03/2026 | <https://cris1954.cat/wp-content/uploads/2026/03/ESCOLA-BUSSEIG.pdf> | **Dades personals:** la pàgina «Escola de busseig» amb els noms dels instructors |
| Dossier de cursos (febrer de 2026; el nom del fitxer porta un cognom) | 813 KB | 21/02/2026 | (no es copia) | Versió del dossier de cursos |
| `INFORMACIO-CURSOS-CRIS-DEFINITIVA.pdf` | 555 KB | 05/07/2025 | <https://cris1954.cat/wp-content/uploads/2025/07/INFORMACIO-CURSOS-CRIS-DEFINITIVA.pdf> | El dossier de cursos que surt en imatges a «Formació / Cursos» |
| `Parlem-del-Mar-Roig-01-02-26.mp4` | 5,1 MB | 14/01/2026 | <https://cris1954.cat/wp-content/uploads/2026/01/Parlem-del-Mar-Roig-01-02-26.mp4> | Vídeo de la xerrada del Mar Roig (n'hi ha una còpia idèntica amb el sufix `-1`) |
| `Felicitacio-NADAL-2024.pdf` | 233 KB | 11/12/2024 | <https://cris1954.cat/wp-content/uploads/2024/12/Felicitacio-NADAL-2024.pdf> | Felicitació de Nadal |
| `Barco-2.pdf` | 225 KB | 28/09/2024 | <https://cris1954.cat/wp-content/uploads/2024/09/Barco-2.pdf> | Sense text extraïble (imatge) |
| `CURS-DE-BUSSEIG-tardor-1.pdf` | 636 KB | 28/09/2024 | <https://cris1954.cat/wp-content/uploads/2024/09/CURS-DE-BUSSEIG-tardor-1.pdf> | Curs de busseig de tardor 2024 |

Els dos documents del menú allotjats a OneDrive («Breu Història CRIS», vídeo, i «Coneix la teva Federativa!», PDF) **no s'han pogut baixar**: OneDrive demana iniciar sessió. Les carpetes de Google Drive de la galeria tampoc (Drive no dona la llista sense JavaScript).

## Dades personals omeses

Cap nom, telèfon ni correu personal no s'ha copiat al repositori: on n'hi havia, hi ha `[persona: càrrec]`. En total, **11 persones** (cinc a la pàgina «Escola de busseig» —quatre instructors i la coordinadora, que també surt a «Activitats»—, l'autor d'un llibre i el seu compte d'Instagram, el director d'un documental, dos ponents en noms de carpetes de la galeria —un d'ells també al cartell de la seva conferència—, un instructor en un cartell del collage de cursos i un cognom en el nom d'un fitxer), més **1 correu** (la bústia de Gmail de la coordinació de cursos) i l'**organigrama de la junta**, que no es copia. Els telèfons que surten al costat d'una persona són els generals del club (624 430 268 i 625 435 047) i sí que es copien.

## Comparació amb el pla

El que la web actual té i el pla del 07 ([M07](../../planning.md#M07) i l'addenda de la 106) no preveu és a [`pendents.md`](../../decisions/pendents.md), un P per tipus de contingut, P-720 a P-731, i al [tauler](../../decisions/tauler-preguntes.yml):

| P | Contingut |
|---|---|
| P-720 | Entrades del menú que porten a una secció de la portada (àncores) |
| P-721 | Documents i vídeos del menú en un OneDrive extern |
| P-722 | «FES-TE SOCI» i les tres botigues, que enllacen a Cluber |
| P-723 | Galeria de fotos a Google Drive |
| P-724 | Activitats passades com a cartells amb el text d'Instagram |
| P-725 | Inscripcions a webs de tercers dins del text d'una activitat |
| P-726 | Informació dels cursos en imatges, amb els preus escrits |
| P-727 | Recomanació d'una revista externa amb la coberta d'un tercer |
| P-728 | Mapa de Google Maps incrustat |
| P-729 | Reconeixement de la subvenció al peu |
| P-730 | Pàgines legals (avís legal, política de galetes) i bàner de galetes |
| P-731 | Cognoms i telèfon al formulari de contacte (l'únic irreversible: dades personals) |

Ja són previstos i no tenen P: la botiga i els comptes de WooCommerce (mòdul 13, fora d'abast), «Fer-se soci» (01), les adreces de contacte i l'horari (`website.club_contact`), les xarxes socials al peu (`SiteChrome`) i els enllaços externs del menú (`MenuItem`).

# Anàlisi de Magic Portfolio com a referència visual

- **Data:** 27/10/2026
- **Decisió:** [034](decisions/034-patrons-magic-portfolio.md)
- **Referència:** Magic Portfolio, de Once UI (once-ui.com/products/magic-portfolio; demo a demo.magic-portfolio.com).
- **Llicència de la plantilla:** CC BY-NC 4.0. Obliga a citar l'autor i no en permet l'ús comercial. **No se'n copia codi, textos ni imatges.** Només se n'agafen idees de patrons, i els reimplementem en HTML i CSS plans amb els nostres tokens.
- **Fonts consultades:** la pàgina del producte i el README del repositori. La demo no s'ha pogut obrir (error de certificat), i els patrons visuals es descriuen a partir de la documentació i del coneixement general de la plantilla [A validar amb una revisió visual de la demo].

## Resum
| Patró | Decisió |
|---|---|
| Hero amb treball destacat | S'adapta |
| Targetes de casos d'estudi | S'adapta |
| Bloc d'entrades amb data | S'adopta |
| Subscripció a butlletí | S'adapta |
| About (pàgina sobre mi o CV) | S'adapta en part |
| Galeria | S'adopta |
| Contingut separat de la presentació | S'adapta (com a principi) |
| Pàgines activables | S'adapta (com a idea per al mòdul 07) |
| Tipografia i ritme d'espais | S'adopta (el principi, no els valors) |
| Protecció de pàgines amb contrasenya | Es descarta |
| Localització | Es descarta per ara |
| SEO automàtic, imatges per a xarxes i RSS | S'adapta (més endavant) |

## Detall

### 1. Hero amb treball destacat — s'adapta
- **A la plantilla:** un titular gran i, al costat o a sota, el projecte destacat amb imatge i enllaç.
- **Al C.R.I.S.:** el titular del club, una sola acció principal («Veure les activitats») i una **sortida destacada** en una targeta (imatge, data, lloc, estat de places i enllaç). Treu la caixa d'imatge gran que no deia res i posa a la vista una cosa que es pot fer ara.
- **Per què s'adapta:** per al club, el «treball destacat» és la propera sortida, no un projecte de portafoli.

### 2. Targetes de casos d'estudi — s'adapta
- **A la plantilla:** targetes de projecte amb imatge, títol, resum i enllaç a una pàgina de detall.
- **Al C.R.I.S.:** secció «Projectes» amb targetes tipus **memòria** que segueixen sempre el mateix esquema: **objectiu, dades i resultats**. Exemples: Fons nets (medi ambient) i el C.R.I.S. a Minka (ciència ciutadana).
- **Per què s'adapta:** l'esquema fix ajuda a justificar ajuts i a mostrar l'impacte (mapa de la plataforma, «Resultats d'una sortida»). Minka s'enllaça, no es replica.

### 3. Bloc d'entrades amb data — s'adopta
- **A la plantilla:** una llista d'entrades del blog amb la data ben visible i un títol enllaçat.
- **Al C.R.I.S.:** secció «Notícies i conferències» amb la data destacada a l'esquerra, un xip de tipus («Notícia» o «Conferència»), el títol i un resum.
- **Per què s'adopta:** encaixa amb les conferències del Departament d'Història i amb les notícies del club sense cap canvi de fons.

### 4. Subscripció a butlletí — s'adapta
- **A la plantilla:** un bloc de subscripció a la portada i al blog, connectat a un servei extern.
- **Al C.R.I.S.:** un bloc al **peu** amb el correu, una casella de consentiment (RGPD), un enllaç a la política de privacitat, la possibilitat de donar-se de baixa i la confirmació per correu.
- **Per què s'adapta:** el servei de la plantilla es descarta, perquè la [decisió 004](decisions/004-correu.md) ja preveu el butlletí amb Brevo. El consentiment ha de ser explícit i demostrable (P-42).

### 5. About — s'adapta en part
- **A la plantilla:** una pàgina sobre mi amb foto, presentació, trajectòria (cronologia), estudis i habilitats.
- **Al C.R.I.S.:** les seccions «Qui som» i «El Centre» ja fan aquest paper.
  - **S'adapta** la idea de **cronologia** com a proposta futura per a la història del club (Departament d'Història).
  - **Es descarta** el format de CV personal.

### 6. Galeria — s'adopta
- **A la plantilla:** una pàgina de galeria amb imatges de mides diferents.
- **Al C.R.I.S.:** la secció «Sota l'aigua», en columnes tipus maçoneria (2 al mòbil, 3 a la tauleta i 4 a l'escriptori), amb espais reservats i peu de foto (lloc i any).
- **Condició:** no s'hi publica cap foto sense els drets d'imatge resolts (P-41).

### 7. Contingut separat de la presentació — s'adapta (com a principi)
- **A la plantilla:** la configuració, el contingut de cada pàgina i les entrades i projectes en fitxers separats del codi.
- **Al C.R.I.S.:** s'adopta el **principi**: el contingut de la web pública (projectes, notícies, galeria, textos) ha de viure separat de la plantilla, i l'ha de poder editar el club sense tocar codi.
- **Es descarta** el format MDX. L'eina és l'editor de l'etapa 4 i el mòdul 07.

### 8. Pàgines activables — s'adapta (com a idea)
- **A la plantilla:** pàgines que s'activen o es desactiven des de la configuració.
- **Al C.R.I.S.:** proposta per al mòdul 07, que la junta pugui **mostrar o amagar seccions** de la web (per exemple, la galeria mentre no hi hagi fotos amb drets) [A validar]. No s'implementa als wireframes.

### 9. Tipografia i ritme d'espais — s'adopta (el principi)
- **A la plantilla:** titulars grans, etiquetes petites, molt d'aire i poca animació.
- **Al C.R.I.S.:** amb les **nostres** fonts (Barlow Condensed, Source Sans 3 i JetBrains Mono) i l'escala de tokens:
  - etiqueta petita en majúscules sobre cada títol;
  - titular més gran a la portada de l'escriptori (×1,3);
  - targetes planes amb vora fina i radi gran;
  - xips en forma de pastilla;
  - el mateix ritme vertical entre seccions.
- **No es copien** els valors de la plantilla.

### 10. Protecció de pàgines amb contrasenya — es descarta
La plataforma ja té comptes i permisos per rol i per objecte (spec 00). Una contrasenya compartida per pàgina hi aniria en contra.

### 11. Localització — es descarta per ara
La interfície és en català (CLAUDE.md). Si cal castellà o anglès per a la web pública, s'ha de decidir apart [A validar].

### 12. SEO automàtic, imatges per a xarxes i RSS — s'adapta (més endavant)
Es pot fer al mòdul 07: metadades i imatge per compartir a cada pàgina, i un canal RSS de notícies. Queda fora dels wireframes.

## On s'aplica
- `design/wireframes/publica.html`: els patrons 1, 2, 3, 4, 6 i 9.
- `design/wireframes/socis.html`: només el patró 9 (tipografia, targetes i xips), sense canviar-ne l'estructura.
- `design/wireframes/admin.html`: no es toca.

# Encàrrec: editor visual de la web pública (07)

Encàrrec escrit del propietari del 24/11/2026, desat tal com es va donar (des de «Tasca:» fins al final). **No es comença fins que el 07 arribi pel seu ordre al camí crític** ([fase 2, F2-6](pla-acceleracio.md#fase-2-llesques)). La part de la sessió de disseny és a `design/encarrecs/editor-web-07.md`.

---

Tasca: ampliar el mòdul 07 (web pública) perquè la web es pugui editar des de l'administració de l'app com un editor de webs. Ha de tenir blocs, arrossegar i deixar anar, vista prèvia en viu, plantilles que reprodueixin l'aspecte actual, vídeos de YouTube amb clic per carregar, menús, versions i publicació programada. També ha de mostrar les activitats del 02, triant quines surten a la portada, i fotos de l'app.

El propietari ha triat aquestes opcions:

- un editor de blocs propi, integrat a l'app (ni Wagtail ni cap CMS extern);
- YouTube amb clic per carregar des de youtube-nocookie.com, darrere de l'ajust website.youtube_enabled, apagat;
- blocs i variants tancades: cap color, mida ni tipografia lliure, i cap HTML;
- un flux de revisió disponible però apagat d'inici;
- un permís d'editar per pàgina;
- una vista prèvia només amb sessió i permís.

Hi ha una altra sessió, la de disseny, que treballa alhora. Té els wireframes de l'editor (T-M07-01), el catàleg visual de blocs (T-M07-19, el CSS i les plantilles de cada bloc) i les fotos de mostra (T-M07-31). No toquis static/css/, tokens.css, docs/design-system.md, design/ ni templates/website/blocs/. Si hi ha conflicte, guanya el pilot, però avisa a l'informe.

Quan toqui, treballa en bucle i no t'aturis després d'informar.

**Pas 1, la norma (una PR risc:alt, sense codi d'aplicació):**

Llegeix sencers docs/planning.md#M07 i el CLAUDE.md. Llegeix també docs/design-system.md §6.9 i T-DX-36 (Probador i Pregon).

Escriu una decisió nova a docs/decisions/, amb el número lliure següent: «Editor visual de la web pública». Afegeix una addenda datada a la secció M07 (#M07-addenda-<número>), sense duplicar contingut. L'addenda ha de recollir aquests punts:

- **RN-M07-09.** Excepció per a youtube-nocookie.com, només després del clic del visitant. Es mostra un avís («En prémer, es carrega YouTube (Google)») i una miniatura desada al nostre emmagatzematge, i no es carrega res de Google abans del clic. Va darrere de website.youtube_enabled, que no s'encén a producció fins que la junta validi el text de l'avís. CA-M07-14 i CA-M07-15 s'adapten a aquesta excepció.
- **RN-M07-10.** El text es desa en un Markdown restringit: negreta, cursiva, enllaç, llistes i títols 2 i 3. Es converteix amb l'HTML desactivat i s'escapa. Els enllaços només poden ser https:, mailto:, tel: o pàgines internes.
- **Catàleg de blocs.** Uns 20 blocs, en cinc grups: text, mitjans, disposició, acció i dades del club (la llista és a l'estudi). Cada bloc té un esquema amb els seus camps i variants, i el servidor el valida. Aquest esquema és el contracte amb la sessió de disseny, que fa la plantilla de cada bloc amb aquests noms de camp. La llista de tipus i variants es queda al codi.
- **Plantilles i patrons.** Plantilles de pàgina (Portada, Secció, Article, Projecte, Galeria i Captació), amb contingut d'exemple de design/wireframes/publica.html. Els patrons i els blocs compartits són dades.
- **Esborranys i versions.** Esborrany per pàgina, amb desat automàtic i avís si algú altre edita la mateixa pàgina. Les versions es poden comparar. La publicació i la retirada programades van per la cua. Canviar l'adreça d'una pàgina publicada crea una redirecció permanent.
- **Permisos.** WP1 es parteix en WP1a (editar esborranys) i WP1b (publicar, programar i restaurar), amb abast per pàgina. Afegeix WP9 (menús, capçalera, peu i blocs compartits) i WP10 (patrons). La configuració inicial és la de l'actual WP1.
- **Ajustos nous, amb rang:** website.youtube_enabled (no), website.review_flow_enabled (no), website.autosave_seconds (20, de 5 a 120) i website.upload_max_mb (10, d'1 a 25).
- **Pujades i CSP.** Només s'accepten JPEG, PNG i WebP (cap SVG). Es comproven i es tornen a codificar amb Pillow, cosa que en treu l'EXIF i el GPS. Els PDF se serveixen com a descàrrega, amb nosniff. La CSP de la web pública: tot del mateix origen, i frame-src només per a youtube-nocookie.com, i només amb l'ajust encès.
- **Activitats a la web.** Tres blocs: «Properes activitats» (automàtic, amb filtre), «Activitats destacades» i «Activitats fetes» (crònica amb foto). A les destacades, WP1 les tria i les ordena, i el 07 desa només la referència, l'ordre i les dates de visibilitat, sense cap còpia. Una activitat retirada al 02 desapareix a la petició següent, i no hi surt cap nom de persona.
- **Fotos de l'app.** El selector té dues pestanyes: «Biblioteca de la web» i «Fotos d'activitats». A la segona només hi surten les fotos publicables amb consentiment (RN-M02-23). Requisit RP-M07-02 al 02: els serveis de lectura activities.public_past_list i activities.publishable_photos(activity), en una tasca pròpia del 02. Mai fotos privades: ni carnets de la 104, ni avatars, ni documents.
- **Fotos reals (E8, resposta del propietari del 24/11/2026).** Es poden fer servir les fotos de la galeria del club i les de https://cris.barcelona/, també les que tenen persones: tothom qui hi surt, junta inclosa, ha signat el permís d'imatge, i la gestoria ho permet. És una excepció a la norma «mai dades reals de socis fora de producció», i per això va en una decisió numerada pròpia. L'abast és només aquestes fotos, per a les plantilles, les dades de mostra i les captures, i cap altra dada de socis. Les fotos van reduïdes a 1.600 px, sense EXIF ni GPS, amb «C.R.I.S.» com a autor i el permís marcat. Els socis encara no envien fotos (E7 = A, pendent de P-41).
- **Tasques.** Canvien T-M07-01, 04, 06 (que es parteix en 06a i 06b), 07 i 18. N'hi ha de noves: de T-M07-19 a T-M07-31, i la del 02 per a RP-M07-02. Indica qui fa cada una: T-M07-01, 19 i 31 són de la sessió de disseny, i la resta, del pilot. Les dues taules de tasques de l'estudi diuen l'esforç, de què depèn cada una i quan està feta.
- **Dependències noves:** Pillow (fixada), markdown-it-py i SortableJS, aquest a static/vendor/ i sense CDN.

Afegeix els dubtes oberts a docs/decisions/pendents.md i al tauler (docs/decisions/tauler-preguntes.yml): el text de l'avís de YouTube (junta) i qui revisa abans de publicar (P-43).

Obre la PR amb l'etiqueta risc:alt. És un canvi de norma del pla: no la fusionis fins que el propietari escrigui «fusiona la #N».

**Pas 2, el codi (després de la fusió del pas 1).** Construeix les tasques del pilot per ordre de dependències. Primer el nucli de blocs (T-M07-04) i l'esquema de cada bloc, perquè el disseny en depèn. Després l'editor (06a i 06b), les fotos (07 i 30), les activitats (29 i el servei del 02), els menús (21), les versions (22), el vídeo (23), el SEO (24), el revisor (25), el flux de revisió (26), la CSP (27) i l'e2e (28).

Segueix les regles habituals:

- menys de 800 línies per PR, i com a màxim 400 de codi d'aplicació;
- una prova per a cada criteri;
- pytest -m e2e i captures a 1.280 i 390 px;
- una entrada al diari;
- l'estat de cada tasca a docs/estat/M07.md.

Les dependències noves van en PR risc:alt pròpies. Mentre la sessió de disseny no tingui la plantilla d'un bloc, fes servir una plantilla mínima sense estil a templates/website/blocs/_provisional/, i treu-la quan arribi la definitiva. Si et surt un dubte reversible, tria l'opció per defecte i continua. Fusiona segons les regles vigents del CLAUDE.md. Al final de cada tanda, deixa el resum de 5 línies de D4.

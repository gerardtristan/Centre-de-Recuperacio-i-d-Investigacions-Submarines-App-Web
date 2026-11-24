Tasca: el disseny de l'editor visual de la web pública (mòdul 07) i dels blocs amb què es construeixen les pàgines. L'objectiu és que la web que es fa amb l'editor mantingui l'essència i la qualitat de la web actual (design/wireframes/publica.html, decisió 034).

Context de l'estudi «Estudi: editor visual de la web pública (M07)»: editor propi dins l'app, i blocs i variants tancades. Qui edita tria el contingut i variants d'una llista, mai colors, mides ni tipografies. Tot surt de tokens.css, i cap bloc no admet HTML. La sessió pilot fa el codi i, al pas 1, obre una PR risc:alt amb la decisió i l'addenda del M07, on hi ha l'esquema de camps i variants de cada bloc: és el teu contracte. Tu no toques apps/ (tret de templates/website/blocs/) ni docs/planning.md.

Quan toqui, treballa en bucle i no t'aturis després d'informar. Llegeix primer el CLAUDE.md, docs/design-system.md (sobretot §6.6, §6.9, §15 i T-DX-26, T-DX-27 i T-DX-36), design/wireframes/publica.html i les pantalles en construcció portada_publica, editor_web i ajuda.

Feina 1: T-M07-01, wireframes de l'editor (pots començar en arribar el torn del 07, abans que el pilot fusioni la norma, perquè és reversible). Al costat dels que ja hi ha a design/wireframes/, fes aquests:

la llista de pàgines;
l'editor en pantalla partida: a l'esquerra, la llista de blocs i el formulari del bloc triat; a la dreta, la vista prèvia amb Probador (mòbil, tauleta, escriptori, clar i fosc);
la biblioteca de blocs, cercable i per grups, amb arrossegar i l'alternativa de teclat;
l'inserció d'un patró;
«Revisar i publicar», amb el revisor de qualitat i la targeta de compartir (Pregon), publicar ara o programar;
les versions, amb el comparador bloc per bloc i el botó de restaurar;
l'editor de menú: 6 enllaços + «Més» (034), submenús i enllaç extern;
la capçalera i el peu;
la biblioteca de fotos, amb les pestanyes «Biblioteca de la web» i «Fotos d'activitats», el punt focal i els camps d'autor, permís i consentiment;
el selector d'activitats destacades, ordenades arrossegant i amb dates de visibilitat.
Cada flux indica els requisits de seguretat i privacitat, amb els estats d'error, d'accés denegat i de sessió caducada. Els wireframes distingeixen el que és simulació visual dels controls del servidor. Aplica les regles B, C i D (§15) i la comprovació de §15.5.

Feina 2: T-M07-19, el catàleg de blocs (quan el pilot hagi fusionat el pas 1). Per a cada bloc de l'esquema, fes tres coses:

la peça al sistema de disseny, primer el document i després el CSS a static/css/, només amb tokens;
la plantilla templates/website/blocs/<tipus>.html, amb els noms de camp de l'esquema;
les variants permeses: fons, amplada i columnes.
Grups i blocs:

Text: títol, text, cita, llista, pregunta desplegable i avís destacat.
Mitjans: imatge, galeria, imatge amb text, vídeo amb clic per carregar i fitxer.
Disposició: secció d'1 a 3 columnes, separador i espai.
Acció: botó, crida «Fes-te soci», subscripció i contacte.
Dades del club: properes activitats, activitats destacades, activitats fetes, notícies recents, preguntes d'un tema, xifres destacades, targetes de projecte i sortida destacada.
El vídeo mostra la miniatura, el botó de reproduir i l'avís «En prémer, es carrega YouTube (Google)». No hi ha cap iframe fins al clic, i el JavaScript se serveix des del mateix origen. Cada bloc es comprova a 1.280 i 390 px, en clar i en fosc. Respecta prefers-reduced-motion, i el contrast ha de ser d'almenys 4,5:1.

Feina 3: T-M07-31, fotos reals (quan el pilot hagi fusionat la decisió de les fotos). Les fotos del club són a la carpeta local ..\Fotos CRIS, al costat del repositori: zips del Drive per carpetes (Immersions, PROJECTES CRIS, CURSOS, Batejos…). També pots fer servir les de https://cris.barcelona/. El propietari ha confirmat que tothom qui hi surt ha signat el permís d'imatge i que la gestoria ho permet. La decisió del pilot en fixa l'abast.

Tria entre 60 i 100 fotos bones per a les plantilles, les dades de mostra i les captures. Han de ser variades: fons, fauna, immersions, cursos, batejos, projectes de medi ambient i vida del club.
Redueix-les a 1.600 px pel costat llarg, en WebP o JPEG de qualitat 80, i treu-ne l'EXIF i el GPS. Comprova-ho amb un script que falli si en queda.
Desa-les a static/img/web/ amb noms descriptius en català, sense noms de persones. Fes un fitxer static/img/web/fotos.yml amb l'autor («C.R.I.S.»), el permís, si hi surten persones, el text alternatiu i l'origen (Drive o cris.barcelona).
Fes-les servir a les plantilles de pàgina i als patrons (el contingut d'exemple), i passa-les al pilot perquè seed_demo_data les carregui a la biblioteca de la web.
No hi posis mai els zips sencers ni els originals. Que cap PR no passi de 25 MB d'imatges: si cal, reparteix-les en diverses PR.
Segueix les regles habituals: PR petites, captures mirades, entrada al diari, estat a docs/estat/M07.md. Si et surt un dubte reversible, tria l'opció per defecte i continua. Fusiona segons les regles vigents del CLAUDE.md.

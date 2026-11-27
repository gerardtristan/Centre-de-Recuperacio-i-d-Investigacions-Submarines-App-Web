# Especificació 00 — Base comuna

- **Versió:** 2 · 27/10/2026
- **Estat:** la versió 1 (commit 8156443) es va aprovar amb canvis; aquesta versió els incorpora. No es fa `plan.md`, `data-model.md` ni `tasks.md` fins que l'equip doni pas a l'etapa 3.
- **Formalitat:** completa, perquè toca autenticació, permisos, RGPD, importacions i l'estructura dels diners (CLAUDE.md, «Com es treballa», punt 5).
- **Revisió:** la persona de la junta responsable del mòdul [A validar qui: Q-30] i l'equip (metodologia §6).
- **Ordre:** és el primer mòdul de la fase 1 segons la decisió 024 (abast mínim i ordre per deixar Cluber: 00 → 01 → 04 mínim → 05a → 05b).

**Canvis respecte a la versió 1**
1. Duplicar activitats passa al mòdul 02; aquí només hi consta com a servei comú previst (decisió 026).
2. La 00 té només l'estructura bàsica de càrrec i pagament; la 04 hi construeix al damunt (decisió 027).
3. Esborrat RGPD: desactivar, anonimitzar, bloquejar el que obliga la llei i referència anònima al registre d'activitat (decisió 028). Substitueix la proposta de «no esborrar mai un compte».
4. «Compte de soci» passa a dir-se «compte personal» (decisió 029).
5. Les preguntes de valors per defecte s'han convertit en valors proposats (§10.1). Només queden obertes les que han de respondre la junta, la tresoreria o informàtica (§10.2). Els números de pregunta es mantenen de la versió 1.

## Com llegir aquesta spec

Cada regla porta la seva font. Abreviatures de documents:

| Abreviatura | Document |
|---|---|
| CLAUDE | `CLAUDE.md` (constitució del projecte) |
| CTX §n | `docs/context-projecte.md` v4, secció n |
| F §n | `docs/funcionalitats-processos/funcionalitats-processos.docx`, secció n |
| ARQ §n | `docs/arquitectura-integracions.md` v6, secció n |
| CK Xn | `docs/checklist-produccio.md`, requisit Xn |
| ENC | Encàrrec de la spec 00 (equip, 27/10/2026) |
| REV | Revisió de la versió 1 (equip, 27/10/2026) |
| V-nn | Valor proposat d'aquesta spec (§10.1), que la revisió pot canviar |

Codis que surten a la spec i què volen dir:

| Codi | De què es tracta |
|---|---|
| Decisió 004 | Correu transaccional i butlletí amb Brevo, amb el límit de 300 enviaments diaris del pla gratuït |
| Decisió 005 | Fitxers privats a Scaleway (París) amb URL signades de curta durada |
| Decisió 006 | Còpies de seguretat diàries, xifrades i a dos proveïdors |
| Decisió 010 | Tres entorns (local, proves, producció) i només dades inventades fora de producció |
| Decisió 011 | Monitoratge extern i seguiment d'errors sense dades de socis |
| Decisió 012 | Cua de tasques sobre PostgreSQL, sense Redis |
| Decisió 013 | Tot ingrés i tota despesa tenen departament; les comissions de quotes van a «General / Quotes de socis» |
| Decisió 014 | Migració única de Cluber |
| Decisió 015 | Doble factor i dos comptes (personal i d'administrador) per a cada administrador |
| Decisió 017 | Mètodes de pagament per tipus de cobrament; la domiciliació només per a quotes |
| Decisió 018 | Perfil únic per persona, compte d'administrador amb diversos rols i doble factor segons l'entrada |
| Decisió 019 | Domini cris1954.cat; remitent a cris1954.cat amb resposta a cris@cris.es |
| Decisió 021 | Les persones no sòcies participen com a convidades, sense compte per defecte |
| Decisió 022 | Mandats SEPA nous (escenari B): no s'importa l'IBAN de Cluber |
| Decisió 024 | Abast mínim i ordre de construcció per deixar Cluber |
| Decisió 025 | Dos nivells de producció; la plataforma no guarda mai l'IBAN |
| Decisió 026 | Duplicar activitats es construeix al mòdul 02 |
| Decisió 027 | Estructura bàsica de càrrec i pagament a la 00; la 04 hi construeix al damunt |
| Decisió 028 | Esborrat RGPD: anonimitzar, bloquejar el que obliga la llei i referència anònima al registre |
| Decisió 029 | El compte que entra amb correu es diu «compte personal» |
| P-04 | Pendent: la matriu de permisos dels 8 rols no està validada per la junta |
| P-07 | Pendent: si es pot guardar la data de validesa del certificat mèdic |
| P-12 | Pendent: qui pot registrar un cobrament manual i quin justificant cal |
| P-21 | Pendent: creditor dels mandats actuals i format de l'exportació de Cluber |
| P-28 | Pendent: què fa avui Cluber amb les llicències federatives |
| P-33 | Pendent: si el club té socis menors d'edat |

Els requisits de la checklist que se citen (C1, C2, H3…) porten sempre al costat el nom del requisit.

## Glossari

| Terme | Definició | Font |
|---|---|---|
| Persona | Qualsevol individu de qui el club guarda dades: soci, alumne, assistent a una conferència, persona amb llicència d'un dia, membre de la junta. Cada persona té **un únic perfil** | Decisió 018 (perfil únic); CLAUDE |
| Soci | Persona amb una relació de soci (número, tipus, estat). Aquesta relació es defineix al mòdul 01; la 00 només en té la persona | CLAUDE («persona separada de soci»); F §3 |
| Convidat | Persona sense compte que s'inscriu o paga amb un enllaç segur | Decisió 021 (convidats) |
| Compte personal | Compte d'accés a l'àrea de socis. Entra amb correu únic; verificació i recuperació per correu; doble factor opcional. El pot tenir qualsevol persona, sòcia o no. Als documents anteriors es diu «compte de soci» | Decisions 015, 018, 021 i 029 **Precisió (27/11/2026, [108](../../docs/decisions/108-respostes-del-propietari-del-27-11-2026-web-butlleti-i-compte-rapid.md), D):** la persona el pot crear sola en una sola pantalla amb nom, correu, contrasenya, la casella del butlletí (no marcada) i l'acceptació de la política de privacitat; la resta de dades es demana quan cal (fer-se soci, una activitat) i després torna on volia anar. També pot entrar sense contrasenya amb una clau d'accés (WebAuthn) o amb un codi o enllaç pel correu, i amb Google (OpenID Connect; només nom i correu verificat; si el correu ja té compte, s'hi enllaça després de confirmar-ho; excepció acotada a la [035](../../docs/decisions/035-dades-nomes-dins-ue.md); apagat fins que hi hagi la clau). Res d'això val per al compte d'administrador |
| Compte d'administrador | Compte d'accés per l'entrada d'administració. Entra amb nom d'usuari únic; doble factor obligatori; correu no únic i només per a notificacions; mai recupera la contrasenya per correu. Pot tenir diversos rols | Decisions 015 i 018 |
| Rol | Conjunt de permisos. N'hi ha 8: soci, instructor, secretaria, responsable de cursos i sortides, responsable de material, tresorer, Departament d'Història i administrador. Cal no confondre el **rol administrador** amb el **compte d'administrador**: un compte d'administrador pot tenir només el rol instructor | CTX §7; F §2; decisió 018 |
| Compte d'emergència | Compte d'administrador de reserva per si es perd l'accés; com a mínim dos, amb doble factor i codis de recuperació fora de línia | Decisió 015; F §2 |
| Enllaç de convidat | Enllaç secret i de durada limitada, lligat a una inscripció o a un càrrec | Decisió 021; V-02 |
| Càrrec | Import que una persona ha de pagar: quota, inscripció o llicència | ARQ §4.1; ENC; decisió 027 |
| Pagament | Intent o confirmació de pagament d'un càrrec, amb un mètode | ARQ §4.1; decisió 027 |
| Departament | Centre de cost obligatori de tot ingrés i tota despesa | Decisió 013; CLAUDE |
| Anonimitzar | Substituir les dades que identifiquen una persona per una referència anònima (per exemple, «Persona anonimitzada A-0042») | Decisió 028 |
| Bloquejar | Conservar una dada que la llei obliga a guardar sense mostrar-la ni fer-la servir, excepte per complir obligacions legals, fins que s'acaba el termini i es destrueix | Decisió 028 |

---

## 1. Context i objectiu

### 1.1 Context
El C.R.I.S. gestiona avui socis, quotes i carnet amb Cluber, i la resta amb l'app del banc, Excel, Gmail i WhatsApp (CTX §4). La plataforma ha de substituir Cluber (decisió 014, migració única) i tots els mòduls comparteixen les mateixes peces: qui és cada persona, com entra, què pot fer, què queda registrat, com es paga, com s'envien correus i fitxers, i com s'importen dades. Aquestes peces són la base comuna.

La plataforma té tres zones amb una sola base de dades: web pública, àrea de socis i administració amb entrada separada i doble factor (CTX §7).

### 1.2 Objectiu
Que qualsevol mòdul posterior (01, 04, 05a, 05b i la fase 2) pugui:
1. identificar persones amb un perfil únic, siguin sòcies o no;
2. fer entrar cada persona pel compte i l'entrada que li toca, amb el doble factor que li toca;
3. comprovar permisos per rol i per objecte a cada petició;
4. deixar constància de qui ha fet cada canvi en dades de socis i diners;
5. crear càrrecs i pagaments amb una estructura bàsica comuna en cèntims, amb departament i sense IBAN;
6. complir el RGPD (consentiments, exportació, esborrat, mínim de dades, cap dada de salut);
7. enviar correus sense superar el límit diari i guardar fitxers privats;
8. importar dades de Cluber (una vegada) i de l'extracte bancari amb previsualització, validació i opció de desfer;
9. treballar en entorns separats amb dades inventades fora de producció.

### 1.3 Què ofereix la 00 a la resta de mòduls
| Servei comú | El fan servir |
|---|---|
| Persones, comptes, doble factor, enllaços de convidat | Tots |
| Permisos per rol i per objecte | Tots |
| Registre d'activitat | Tots els que toquen dades de socis o diners |
| Consentiments, sol·licituds RGPD, anonimització i bloqueig | 01, 04, 07 (butlletí) |
| Estructura bàsica de càrrec i pagament; departaments. La 04 hi construeix moviments, ingressos, comissions, comptes i conciliació (decisió 027) | 01 (quotes), 04, 05a, 05b, 02 i 06 (fase 2) |
| Correu i notificacions (annex A) | Tots |
| Fitxers (annex B) | 01 (carnet, rebuts), 04 (justificants), 02 i 03 (fase 2) |
| Importacions (marc comú) | 01 (Cluber), 04 (extracte bancari) |
| Duplicar activitats: **servei comú previst**, es construeix al mòdul 02 (decisió 026) | 02 i conferències (fase 2) |
| Entorns i dades de prova | Tots |

---

## 2. Rols i permisos

### 2.1 Actors
| Actor | Com s'identifica | Font |
|---|---|---|
| Visitant anònim | Sense sessió; només endpoints declarats públics | CK C1 (autenticació a cada endpoint) |
| Convidat | Enllaç de convidat vàlid; sense compte | Decisió 021 |
| Persona amb compte personal | Correu i contrasenya a l'àrea de socis (+ TOTP si l'ha activat) | Decisions 015, 018 i 029 |
| Compte d'administrador | Nom d'usuari, contrasenya i TOTP a l'entrada d'administració; té un o més rols | Decisions 015 i 018 |
| Compte d'emergència | Com un compte d'administrador; ús excepcional | Decisió 015 |
| Sistema | Tasques de la cua i notificacions verificades de proveïdors | ARQ §4.2; decisió 012 |

### 2.2 Rols
Els 8 rols surten del context (CTX §7) i del document de funcionalitats (F §2). **La matriu no està validada per la junta (P-04).** Mentre no es validi, la matriu de 2.3 i 2.4 és la base de treball i es pot canviar sense tocar el model (Q-01).

- El **rol soci** l'obté el compte personal d'una persona que és sòcia (estat definit al 01).
- Els altres 7 rols s'assignen a un **compte d'administrador** (decisió 018, punt 2).

### 2.3 Permisos de les funcions de la 00 (per rol)
Llegenda: **Sí** = pot fer-ho; **Propi** = només sobre la seva persona; **—** = no; **[A validar]** = cal que la junta ho confirmi (Q-01).

| # | Acció | Soci | Instructor | Secretaria | Resp. cursos i sortides | Resp. material | Tresorer | Dept. Història | Administrador | Font |
|---|---|---|---|---|---|---|---|---|---|---|
| M1 | Veure i editar el seu perfil, els seus consentiments i els seus comptes (des del compte personal) | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | F §2, fila 1; decisió 018 |
| M2 | Crear i editar perfils d'altres persones i els seus comptes personals | — | — | Sí | [A validar] | — | [A validar] | [A validar] | Sí | F §2, fila 3 (altes); F §9.2 |
| M3 | Crear comptes d'administrador, assignar-hi i retirar-hi rols, desactivar comptes | — | — | — | — | — | — | — | Sí | F §2, fila «Gestionar usuaris i rols» |
| M4 | Restablir la contrasenya o el TOTP d'**un altre** compte d'administrador | — | — | — | — | — | — | — | Sí [A validar: Q-03] | Decisió 018, punt 4 |
| M5 | Generar, reenviar i revocar enllaços de convidat | — | — | [A validar] | [A validar] (inscripcions) | — | [A validar] (càrrecs) | [A validar] (conferències) | Sí | Decisió 021 |
| M6 | Consultar el registre d'activitat | — | — | [A validar] (dades de socis) | — | — | [A validar] (diners) | — | Sí | CK C8 (registre d'activitat) |
| M7 | Mantenir la llista de departaments | — | — | — | — | — | [A validar] | — | Sí | Decisió 013; F §7 |
| M8 | Importar les dades de Cluber i desfer-ho | — | — | — | — | — | — | — | Sí | F §9.13 |
| M9 | Importar l'extracte bancari i desfer-ho | — | — | — | — | — | Sí | — | [A validar] | F §9.9 |
| M10 | Demanar l'exportació o l'esborrat de les seves dades | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | CTX §9; CK H3 (esborrat i exportació) |
| M11 | Atendre sol·licituds RGPD d'altres persones | — | — | [A validar] | — | — | — | — | [A validar] | CTX §9; Q-15 |
| M12 | Publicar versions noves dels textos legals i de consentiment | — | — | — | — | — | — | — | [A validar] | CTX §9; CK H1 (política de privacitat) |
| M13 | Consultar dades bloquejades per obligació legal | — | — | — | — | — | Proposta: Sí | — | Proposta: Sí | Decisió 028 |
| M14 | Registrar un cobrament manual | Bloquejat fins que es resolgui P-12 (qui pot registrar cobraments manuals). Proposta de l'arquitectura: tresorer o administrador | | | | | | | | Decisió 017; ARQ §4.7 |
| M15 | Rebre l'avís del 80 % del límit de correu | [A validar qui: Q-26] | | | | | | | | Decisió 004 |
| M16 | Obtenir un fitxer | Segons el permís sobre l'objecte al qual pertany el fitxer | | | | | | | | Decisió 005 |

Les files M1 i M10 es fan amb el **compte personal**. Un instructor o un membre del Departament d'Història que no sigui soci i no tingui compte personal: vegeu Q-10.

### 2.4 Matriu base per mòduls (de F §2, pendent de validar: P-04)
Es reprodueix perquè la 00 ha de poder expressar-la. Els detalls de cada fila són dels mòduls corresponents.

| Acció | Soci | Instructor | Secretaria | Resp. cursos i sortides | Resp. material | Tresorer | Dept. Història | Administrador |
|---|---|---|---|---|---|---|---|---|
| Veure i editar les seves dades i el carnet | Sí | Sí | Sí | Sí | Sí | Sí | Sí | Sí |
| Inscriure's a activitats i pagar dins l'app | Sí | Sí | Sí | Sí | Sí | Sí | Sí | Sí |
| Aprovar altes, baixes i canvis de tipus | — | — | Sí | — | — | Consulta | — | Sí |
| Crear, duplicar i gestionar cursos i sortides | — | — | — | Sí | Consulta | Consulta | — | Sí |
| Crear, duplicar i gestionar conferències i contingut històric | — | — | — | — | — | — | Sí | Sí |
| Passar llista i registrar resultats | — | Les seves sessions | — | Sí | — | — | Conferències | Sí |
| Avaluar alumnes i programar classes de reforç | — | Els seus alumnes | — | Sí | — | — | — | Sí |
| Gestionar inventari i assignar material | — | Consulta | — | Assignar | Sí | Consulta | — | Sí |
| Registrar ingressos, despeses i factures | — | — | — | — | — | Sí | — | Sí |
| Veure el marge de les activitats | — | — | — | Sí | — | Sí | — | Sí |
| Modificar preus i catàlegs | — | — | — | Sí | — | Sí | — | Sí |
| Gestionar llicències de socis i no socis | — | — | Sí | Consulta | — | Consulta | — | Sí |
| Veure el dashboard | — | — | Parcial | Parcial | Parcial | Complet | Parcial | Complet |
| Gestionar usuaris i rols | — | — | — | — | — | — | — | Sí |

F §2 diu que qui pot canviar preus i catàlegs està [A validar].

### 2.5 Permisos per objecte
| Actor o rol | Abast sobre els objectes | Font |
|---|---|---|
| Compte personal | Només la seva persona i el que en penja: perfil, comptes, consentiments, sol·licituds RGPD, càrrecs, pagaments, rebuts i fitxers propis. Cap llistat d'altres persones | F §3, «Regles»; CLAUDE |
| Convidat | Només l'objecte lligat a l'enllaç (una inscripció o un càrrec) i les seves pròpies dades, emmascarades. Cap llistat ni cap dada d'altres persones | Decisió 021 |
| Instructor | Només les sessions on fa classe i els alumnes d'aquestes sessions. Quines dades dels alumnes veu es fixa a la spec 02 | F §2; CLAUDE |
| Responsable de cursos i sortides | Cursos i sortides. Marge: el text de F §2 diu «de les seves activitats» i la matriu diu «Sí» sense límit [A validar: Q-01] | F §2 |
| Departament d'Història | Només conferències i contingut històric; «sense accés a la resta de la gestió» | F §8.3 |
| Responsable de material | Inventari; consulta d'activitats només per assignar material | F §2 |
| Tresorer | Diners de tot el club; de les persones, només les dades necessàries per cobrar i conciliar [A validar: Q-01] | F §2; CTX §9 (mínim de dades) |
| Secretaria | Persones i socis | F §2 |
| Administrador | Tot, excepte les dades bloquejades, que només es consulten per complir una obligació legal (M13) | F §2; decisió 028 |
| Tots | Les persones anonimitzades no apareixen en cap llistat ni cerca; les dades bloquejades no es mostren fora de M13 | Decisió 028 |

### 2.6 Com es combinen els permisos
1. El permís d'un compte d'administrador és la **unió** dels permisos dels seus rols actius (decisió 018, punt 2: «pot tenir diversos rols»).
2. El compte personal i el compte d'administrador d'una mateixa persona **no comparteixen permisos**: el compte personal no hereta cap rol de gestió i el compte d'administrador no entra a l'àrea de socis (decisió 015, taula «Entrada»).
3. Primer es comprova el rol i després l'objecte. Si falla qualsevol dels dos, no es retorna cap dada (CLAUDE, «Permisos en dos nivells»).
4. Si un compte d'administrador pot modificar dades o diners de la seva pròpia persona (per exemple, el tresorer registrant el pagament de la seva quota): Q-11.

---

## 3. Històries d'usuari

**Persones i convidats**
- **HU-01.** Com a secretaria, vull crear el perfil d'una persona, sòcia o no, amb dades mínimes, i que la plataforma m'avisi si ja existeix, per no tenir la mateixa persona dues vegades.
- **HU-02.** Com a persona no sòcia, vull inscriure'm i pagar amb un enllaç segur sense crear cap compte, per no haver de recordar cap contrasenya.
- **HU-03.** Com a convidat, vull poder crear un compte personal lligat al meu perfil si ho decideixo, per veure les meves inscripcions i rebuts.

**Comptes i doble factor**
- **HU-04.** Com a persona amb compte personal, vull entrar amb el meu correu i recuperar la contrasenya per correu.
- **HU-05.** Com a persona amb compte personal, vull activar o desactivar el doble factor.
- **HU-06.** Com a administrador, vull crear un compte d'administrador amb nom d'usuari, lligat al perfil d'una persona, i assignar-li un o més rols.
- **HU-07.** Com a titular d'un compte d'administrador (de qualsevol rol, inclosos instructor i Departament d'Història), vull entrar per l'entrada d'administració amb nom d'usuari, contrasenya i codi TOTP.
- **HU-08.** Com a administrador, vull restablir la contrasenya o el TOTP d'un altre compte d'administrador que ha perdut l'accés.
- **HU-09.** Com a titular d'un compte d'administrador sense el mòbil, vull entrar amb un codi de recuperació guardat fora de línia.
- **HU-10.** Com a junta, vull com a mínim dos comptes d'emergència per no quedar mai sense accés a l'administració.

**Permisos**
- **HU-11.** Com a soci, vull que ningú sense permís vegi les meves dades i que jo només vegi les meves.
- **HU-12.** Com a instructor, vull veure només les meves sessions i els meus alumnes.
- **HU-13.** Com a administrador, vull retirar rols o desactivar comptes quan algú deixa un càrrec, sense perdre l'historial.

**Registre d'activitat**
- **HU-14.** Com a administrador, vull consultar qui ha canviat què, quan, des de quin compte i quin valor hi havia abans, en dades de socis i diners.

**Diners (estructura bàsica)**
- **HU-15.** Com a tresorer, vull que tot càrrec tingui tipus, import en cèntims, departament, estat i, en pagar-se, mètode, perquè els mòduls de pagament i tresoreria parlin el mateix idioma.
- **HU-16.** Com a tresorer, vull mantenir la llista de departaments, amb «General / Quotes de socis» des del primer dia.

**RGPD**
- **HU-17.** Com a persona, vull donar i retirar els meus consentiments i que quedi constància de la data i de la versió del text.
- **HU-18.** Com a soci, vull demanar una còpia de les meves dades.
- **HU-19.** Com a soci, vull demanar l'esborrat de les meves dades i que el club conservi només el que la llei l'obliga a conservar, i només el temps que calgui.

**Importacions**
- **HU-20.** Com a administrador, vull importar una sola vegada les dades de Cluber, veure-les abans de confirmar, validar-les i poder desfer la importació.
- **HU-21.** Com a tresorer, vull importar l'extracte del banc en CSV amb previsualització, validació i opció de desfer, perquè la tresoreria el pugui conciliar.

**Correu i fitxers**
- **HU-22.** Com a club, vull que els correus importants (recuperació de contrasenya, enllaços de convidat, confirmacions) surtin encara que s'enviï un butlletí, i rebre un avís quan ens apropem al límit diari.
- **HU-23.** Com a usuari autoritzat, vull descarregar un fitxer privat (un rebut, un justificant) sense que quedi exposat a ningú més.

**Entorns**
- **HU-24.** Retirada a la versió 2: duplicar activitats passa a la spec 02 (decisió 026).
- **HU-25.** Com a equip, vull treballar en local i a proves amb dades inventades i sense cap risc de cobrar ni d'escriure a socis reals.

---

## 4. Criteris d'acceptació

Tots els noms, documents i correus dels exemples són inventats.

### HU-01 Perfil únic
- **CA-01.1** Donat que no hi ha cap persona amb el DNI 00000000T, quan la secretaria crea un perfil amb aquest document, llavors es crea un sol perfil i el registre d'activitat guarda la persona i el compte d'administrador de la secretaria.
- **CA-01.2** Donat que ja hi ha una persona amb el DNI 00000000T, quan algú en crea una altra amb el mateix document (encara que l'escrigui amb espais, guions o minúscules), llavors la plataforma no la crea i indica que ja existeix, sense mostrar dades que el seu rol no pot veure (V-03).
- **CA-01.3** Donat que ja hi ha una persona amb el correu anna@example.org, o amb el mateix nom, cognoms i telèfon, quan algú crea un perfil nou amb aquestes dades, llavors la plataforma avisa d'un possible duplicat i qui el crea decideix si fa servir el perfil existent; mai es fusionen sols (V-03).
- **CA-01.4** Donat el formulari de perfil i el model de dades, quan es revisen, llavors no hi ha cap camp de salut (certificat mèdic, declaració mèdica, al·lèrgies, malalties o medicació).
- **CA-01.5** Donat cada cas de persona (soci, alumne, assistent a una conferència, persona amb llicència d'un dia), quan es crea el perfil, llavors només es demanen com a obligatoris els camps de V-04.

### HU-02 Convidat amb enllaç segur
- **CA-02.1** Donat un càrrec pendent d'una persona sense compte, quan un rol autoritzat genera un enllaç de convidat, llavors la plataforma l'envia a l'adreça de la persona, guarda només una empremta (hash) del testimoni i hi fixa la caducitat de V-02.
- **CA-02.2** Donat un enllaç vàlid, quan la persona l'obre, llavors veu només la inscripció o el càrrec lligat, amb les seves dades emmascarades, i pot pagar-lo; cap resposta conté dades d'una altra persona.
- **CA-02.3** Donat un enllaç caducat o revocat, quan s'obre, llavors no es mostra cap dada i s'ofereix demanar-ne un de nou.
- **CA-02.4** Donat un càrrec ja pagat, quan s'obre el seu enllaç abans que caduqui, llavors només es pot veure l'estat i descarregar el rebut; no es pot tornar a pagar (V-02).
- **CA-02.5** Donat que es reenvia un enllaç, quan es genera el nou, llavors l'anterior deixa de funcionar (V-02).
- **CA-02.6** Donat que es demana un enllaç nou amb una adreça de correu, quan l'adreça existeix i quan no existeix, llavors la resposta que veu l'usuari és idèntica.
- **CA-02.7** Donat que des d'un mateix origen hi ha hagut els intents fallits de V-02, quan se'n fa un altre, llavors es rebutja temporalment (CK C3, limitació de peticions).
- **CA-02.8** Donat qualsevol petició amb un enllaç de convidat, quan s'escriu als registres del servidor o al seguiment d'errors, llavors el testimoni no hi apareix sencer.
- **CA-02.9** Donat que el convidat torna del formulari de pagament, quan es mostra la pàgina de retorn, llavors diu que s'està confirmant el pagament i el càrrec no canvia d'estat per aquesta visita (el canvi el fa la confirmació verificada del mòdul 05b).

### HU-03 Del convidat al compte personal opcional
- **CA-03.1** Donat un convidat amb perfil, quan crea un compte personal amb el mateix correu, llavors el compte es lliga al perfil existent (no se'n crea cap de nou), queda pendent de verificar per correu i, un cop verificat, mostra les inscripcions i els càrrecs anteriors.
- **CA-03.2** Donat que el correu ja pertany a un compte personal, quan algú intenta crear-ne un altre amb aquest correu, llavors no es crea i el missatge en pantalla és el mateix que si no existís (l'avís s'envia a l'adreça).

### HU-04 Compte personal: entrada i recuperació
- **CA-04.1** Donat un compte personal verificat, quan la persona entra amb el correu i la contrasenya correctes a l'àrea de socis, llavors obté una sessió de l'àrea de socis.
- **CA-04.2** Donat un compte personal pendent de verificar, quan intenta entrar, llavors no obté sessió fins que confirma el correu; l'enllaç de verificació caduca segons V-01 (CK C5, verificació de correu).
- **CA-04.3** Donat qualsevol adreça, quan es demana recuperar la contrasenya, llavors la resposta és idèntica tant si el compte existeix com si no; si existeix, s'envia un enllaç d'un sol ús que caduca segons V-01 (CK C4, restabliment de contrasenya).
- **CA-04.4** Donat un enllaç de recuperació ja utilitzat o caducat, quan es torna a obrir, llavors no permet canviar la contrasenya.
- **CA-04.5** Donat un compte personal, quan intenta entrar per l'entrada d'administració, llavors no obté cap sessió.
- **CA-04.6** Donat que dues persones comparteixen correu, quan la segona vol un compte personal, llavors ha de fer servir un correu propi; mentrestant pot participar com a convidada amb el correu compartit (V-05).

### HU-05 Doble factor opcional per al compte personal
- **CA-05.1** Donat un compte personal sense TOTP, quan l'activa i confirma un codi vàlid, llavors els inicis de sessió següents demanen el codi.
- **CA-05.2** Donat un compte personal amb TOTP, quan el desactiva, llavors ha de confirmar amb la contrasenya i un codi vàlid, i el canvi queda al registre d'activitat.

### HU-06 Creació de comptes d'administrador
- **CA-06.1** Donat un compte amb el rol administrador, quan crea un compte d'administrador per a una persona que ja té compte personal, amb nom d'usuari, rols i correu de notificació, llavors els dos comptes queden lligats al mateix perfil i no s'envia cap correu de verificació.
- **CA-06.2** Donat un nom d'usuari que ja existeix, quan es crea un altre compte d'administrador amb aquest nom, llavors es rebutja.
- **CA-06.3** Donat un correu de notificació que ja fa servir un altre compte, quan es crea el compte d'administrador, llavors s'accepta (el correu no és únic).
- **CA-06.4** Donat que una persona ja té un compte d'administrador, quan se n'intenta crear un segon per a la mateixa persona, llavors es rebutja (excepció dels comptes d'emergència: Q-02).
- **CA-06.5** Donat un compte d'administrador sense el rol administrador, quan intenta crear comptes o assignar rols, llavors es rebutja sense revelar dades.

### HU-07 Entrada d'administració amb TOTP
- **CA-07.1** Donat un compte d'administrador nou, quan entra per primera vegada amb nom d'usuari i contrasenya, llavors només pot donar d'alta el TOTP; cap altra acció d'administració està disponible fins que el confirma.
- **CA-07.2** Donat un compte d'administrador amb TOTP, quan el codi falta o és incorrecte, llavors no obté cap sessió d'administració.
- **CA-07.3** Donat qualsevol rol (inclosos instructor i Departament d'Història), quan entra per l'administració, llavors se li demana el TOTP igual que a la resta.
- **CA-07.4** Donat l'entrada d'administració, quan es revisa la pantalla i les rutes, llavors no hi ha cap enllaç ni cap endpoint que enviï un correu de recuperació per a un compte d'administrador.
- **CA-07.5** Donat un compte d'administrador, quan s'intenta entrar a l'àrea de socis amb el seu correu de notificació, llavors no obté cap sessió.
- **CA-07.6** Donat que s'han superat els intents fallits de V-01, quan se'n fa un altre, llavors el compte o l'origen queda bloquejat el temps de V-01 i queda al registre (CK C3, limitació de peticions).
- **CA-07.7** Donat una sessió d'administració sense activitat durant el temps de V-01, quan es fa la petició següent, llavors cal tornar a entrar amb TOTP.

### HU-08 Restabliment per un altre administrador
- **CA-08.1** Donat l'administrador A i el compte d'administrador B, quan A restableix la contrasenya de B, llavors es genera una credencial temporal que es mostra una sola vegada a A, que caduca segons V-01 i que B ha de canviar en entrar; el registre guarda que ho ha fet el compte d'A. Per quin canal A la fa arribar a B: Q-03 (mai per correu).
- **CA-08.2** Donat l'administrador A, quan intenta restablir el seu propi compte per aquesta via, llavors es rebutja.
- **CA-08.3** Donat que A restableix el TOTP de B, quan B entra, llavors el TOTP anterior ja no funciona i B l'ha de tornar a donar d'alta.
- **CA-08.4** Donat un restabliment, quan es completa, llavors B rep un avís informatiu al seu correu de notificació, sense cap enllaç ni credencial.

### HU-09 Codis de recuperació fora de línia
- **CA-09.1** Donat l'alta del TOTP d'un compte d'administrador, quan es confirma, llavors es generen els codis de recuperació de V-01, es mostren una sola vegada i es guarden només les seves empremtes.
- **CA-09.2** Donat un codi de recuperació vàlid, quan s'utilitza en lloc del TOTP, llavors permet entrar una vegada, el codi queda invalidat, queda al registre i la plataforma demana tornar a donar d'alta el TOTP.
- **CA-09.3** Donat un codi ja utilitzat, quan es torna a provar, llavors es rebutja.

### HU-10 Comptes d'emergència
- **CA-10.1** Donat el llistat de comptes d'administrador, quan hi ha menys de dos comptes d'emergència actius amb TOTP, llavors la plataforma mostra un avís als comptes amb el rol administrador.
- **CA-10.2** Donat un compte d'emergència, quan s'utilitza, llavors queda al registre d'activitat i s'avisa tots els comptes amb el rol administrador (proposta).

### HU-11 El soci només veu el seu
- **CA-11.1** Donat el soci A i el soci B, quan A demana el perfil, els càrrecs o els fitxers de B pel seu identificador, llavors la resposta no conté cap dada de B.
- **CA-11.2** Donat qualsevol llistat de l'àrea de socis, quan el demana el soci A, llavors només conté objectes d'A.
- **CA-11.3** Donat cada ruta de l'API, quan s'hi accedeix sense sessió, llavors es rebutja, excepte les rutes de la llista de rutes públiques declarades. Una prova automàtica recorre totes les rutes (CK C1, autenticació a cada endpoint).

### HU-12 L'instructor només veu les seves sessions
- **CA-12.1** Donat un objecte de prova assignat a l'instructor I1 i un altre assignat a I2, quan I1 demana l'objecte d'I2, llavors no rep cap dada. (El mecanisme es prova a la 00 amb un objecte de prova; les sessions reals són de la spec 02.)

### HU-13 Retirar rols i desactivar comptes
- **CA-13.1** Donat un compte d'administrador amb els rols tresorer i responsable de material, quan se li retira el rol tresorer, llavors la petició següent ja no té permisos de tresorer i el canvi queda al registre.
- **CA-13.2** Donat un compte que es desactiva fora d'un esborrat RGPD (per exemple, algú deixa un càrrec), quan es desa el canvi, llavors se'n tanquen les sessions obertes, el compte no s'esborra i les entrades del registre d'activitat que en parlen es mantenen.
- **CA-13.3** Donat que només queda un compte actiu amb el rol administrador (sense comptar els d'emergència), quan algú intenta retirar-li el rol o desactivar-lo, llavors es rebutja amb un missatge que ho explica.

### HU-14 Registre d'activitat
- **CA-14.1** Donat un canvi en un camp d'un perfil, quan es desa, llavors hi ha una entrada amb data i hora, persona que actua, compte que actua, objecte, camp, valor anterior i valor nou.
- **CA-14.2** Donat una persona amb compte personal i compte d'administrador, quan fa una acció amb cadascun, llavors les dues entrades indiquen el compte concret.
- **CA-14.3** Donat qualsevol compte, inclòs el rol administrador, quan intenta modificar o esborrar una entrada del registre, llavors no hi ha cap manera de fer-ho des de la plataforma.
- **CA-14.4** Donat un canvi de contrasenya, de TOTP o de codis de recuperació, quan es registra, llavors l'entrada diu què ha passat però no guarda cap valor secret.
- **CA-14.5** Donat una acció d'una tasca o d'una notificació d'un proveïdor, quan es registra, llavors l'actor és «sistema» amb l'origen (per exemple, el nom de la tasca).
- **CA-14.6** Donat una acció feta amb un enllaç de convidat, quan es registra, llavors l'actor és la persona convidada i l'identificador intern de l'enllaç, mai el testimoni.

### HU-15 Estructura bàsica de càrrec i pagament
- **CA-15.1** Donat un càrrec sense departament, quan es desa, llavors es rebutja.
- **CA-15.2** Donat un import que no és un enter positiu de cèntims, quan es desa un càrrec o un pagament, llavors es rebutja.
- **CA-15.3** Donat un càrrec d'inscripció o de llicència, quan s'hi associa un pagament amb el mètode domiciliació, llavors es rebutja.
- **CA-15.4** Donat un càrrec, quan es demana una transició d'estat que no és a la taula de RN-67, llavors es rebutja i l'estat no canvia; cada transició vàlida queda al registre.
- **CA-15.5** Donat un càrrec, quan es vol anul·lar, llavors cal un motiu; cap càrrec ni pagament es pot esborrar.
- **CA-15.6** Donat el model de dades i les migracions, quan una prova automàtica els revisa, llavors no hi ha cap camp que guardi un IBAN ni un número de targeta (CK C9, pagaments).
- **CA-15.7** Donat una petició del navegador (soci, convidat o administrador), quan intenta posar un càrrec en estat «pagat» directament, llavors es rebutja; només ho poden fer el processament d'una confirmació verificada del proveïdor, la conciliació confirmada pel tresorer o el registre manual (aquest últim bloquejat per P-12).
- **CA-15.8** Donat el càrrec d'una quota anual, quan es crea, llavors el seu departament és «General / Quotes de socis» (vegeu Q-18).

### HU-16 Departaments
- **CA-16.1** Donat una instal·lació nova, quan s'executen les migracions, llavors existeix el departament «General / Quotes de socis».
- **CA-16.2** Donat un departament que ja té càrrecs o moviments, quan es vol esborrar, llavors es rebutja; es pot desactivar, i un departament desactivat no es pot triar per a càrrecs nous.

### HU-17 Consentiments
- **CA-17.1** Donat una persona que dona un consentiment, quan es desa, llavors queda la persona, el tipus, la versió exacta del text, la data i l'hora, el canal (web o presencial) i, si és presencial, el compte que l'ha registrat.
- **CA-17.2** Donat una versió nova d'un text, quan es publica, llavors els consentiments anteriors continuen lligats a la versió que es va acceptar. Si cal tornar a demanar-lo: Q-16.
- **CA-17.3** Donat un consentiment atorgat, quan la persona el retira, llavors es crea un registre nou de retirada, l'anterior no es modifica, i l'efecte és immediat (per exemple, deixa de rebre el butlletí).

### HU-18 Exportació de dades
- **CA-18.1** Donat un soci que demana l'exportació, quan la sol·licitud es resol, llavors rep un fitxer en un format estructurat i llegible per màquina amb només les seves dades, accessible amb una URL signada de curta durada; el fitxer s'esborra passat el termini de V-08, i la sol·licitud i la descàrrega queden al registre.

### HU-19 Esborrat de dades (decisió 028)
- **CA-19.1** Donat un soci que demana l'esborrat, quan la persona responsable l'aprova, llavors tots els seus comptes queden desactivats, se'n tanquen les sessions i es revoquen els seus enllaços de convidat.
- **CA-19.2** Donat el mateix esborrat, quan es processa, llavors les dades personals del perfil (nom, cognoms, document, correu, telèfon, adreça), els consentiments i els fitxers que no tenen obligació legal se substitueixen per una referència anònima o s'esborren, i la persona deixa d'aparèixer en llistats i cerques.
- **CA-19.3** Donat que la persona té factures o cobraments, quan es processa l'esborrat, llavors aquestes dades no s'anonimitzen sinó que queden bloquejades amb la data de fi del termini legal [A validar amb la gestoria: Q-14]: no es mostren enlloc excepte a M13 (consulta per obligació legal), i cada consulta queda al registre.
- **CA-19.4** Donat el registre d'activitat d'aquesta persona, quan es processa l'esborrat, llavors les entrades no s'esborren ni canvien d'acció, data ni objecte, però tot el que identifica la persona (com a actora o com a valor anterior o nou) se substitueix per la seva referència anònima.
- **CA-19.5** Donat una dada bloquejada amb el termini vençut, quan s'executa la tasca periòdica de destrucció, llavors la dada es destrueix i queda una entrada al registre amb la referència anònima.
- **CA-19.6** Donat un esborrat completat, quan es revisa la base de dades, llavors no queda cap camp que identifiqui la persona fora de les dades bloquejades.
- **CA-19.7** Donat que qui demana l'esborrat té càrrecs pendents, quan es tramita: pendent de Q-14.

### HU-20 Importació única de Cluber
- **CA-20.1** Donat un fitxer de Cluber amb dades inventades, quan l'administrador el puja, llavors veu una previsualització amb el recompte de registres nous, coincidents i amb error, i encara no s'ha escrit res a la base de dades.
- **CA-20.2** Donat un fitxer amb línies incorrectes, quan es valida, llavors cada error indica la línia i el motiu, i només es pot confirmar si l'administrador exclou explícitament aquestes línies, que surten al resum (V-06).
- **CA-20.3** Donat un registre amb el mateix document d'identitat o número de soci que una persona existent, quan es previsualitza, llavors es marca com a coincident i no es crea una persona nova.
- **CA-20.4** Donat un fitxer amb una columna d'IBAN, quan es puja, llavors es rebutja sencer, no es desa enlloc i es demana una exportació sense IBAN.
- **CA-20.5** Donat una importació confirmada, quan es revisa, llavors cada registre creat porta l'identificador del lot, el fitxer original no s'ha desat (només la seva empremta i les línies normalitzades) i el registre d'activitat guarda el compte que l'ha confirmada.
- **CA-20.6** Donat una importació confirmada sense cap dada creada a partir d'ella (quotes, pagaments, comptes), quan l'administrador la desfà, llavors s'anul·la tot el que va crear aquell lot i queda al registre.
- **CA-20.7** Donat una importació confirmada a partir de la qual ja s'han creat dades, quan l'administrador la vol desfer, llavors es rebutja i es llisten les dades que en depenen (V-06).
- **CA-20.8** Donat que ja hi ha una importació de Cluber confirmada i no desfeta, quan se'n prova una altra, llavors es rebutja (migració única, decisió 014).
- **CA-20.9** Donat un fitxer buit, amb un format no reconegut o amb línies duplicades, quan es puja, llavors es mostra un error clar i no s'escriu res (CK B9, proves d'importació).

### HU-21 Importació de l'extracte bancari
- **CA-21.1** Donat un CSV del banc amb dades inventades, quan el tresorer el puja, llavors veu una previsualització de les línies i les columnes validades abans de confirmar.
- **CA-21.2** Donat un CSV que conté línies ja importades en un extracte anterior, quan es previsualitza, llavors aquestes línies es marquen com a duplicades i no es tornen a importar.
- **CA-21.3** Donat un extracte confirmat, quan es revisa, llavors les línies queden disponibles per a la conciliació del mòdul 04 i la importació queda al registre.
- **CA-21.4** Donat un extracte confirmat en què cap línia s'ha conciliat, quan el tresorer el desfà, llavors les línies desapareixen de la conciliació i queda al registre. Si alguna línia ja s'ha conciliat, es rebutja (V-06).
- **CA-21.5** Donat un fitxer buit o amb un format no reconegut, quan es puja, llavors es mostra un error clar i no s'escriu res (CK B9).

### HU-22 Correu dins del límit diari
Vegeu l'annex A (criteris CA-A1 a CA-A9).

### HU-23 Fitxers privats
Vegeu l'annex B (criteris CA-B1 a CA-B5).

### HU-25 Entorns i dades de prova
- **CA-25.1** Donat l'entorn local o de proves, quan s'executa l'ordre de càrrega de dades de prova, llavors totes les persones, correus i documents són inventats i reconeixibles com a tals.
- **CA-25.2** Donat un entorn que no és producció, quan s'obre qualsevol pantalla, llavors es veu clarament el nom de l'entorn (proposta).
- **CA-25.3** Donat que `STRIPE_LIVE_MODE_ALLOWED` és fals, quan l'aplicació arrenca amb una clau de producció de Stripe, llavors es nega a arrencar (ARQ §4.2, punt 9).
- **CA-25.4** Donat un entorn que no és producció, quan la plataforma envia un correu, llavors no arriba a cap adreça real: queda en una bústia de proves (V-07).
- **CA-25.5** Donat un canvi al repositori, quan s'executa el pipeline, llavors un escaneig de secrets falla si troba claus o contrasenyes (CK A3, secrets fora del repositori).

---

## 5. Regles de negoci

### 5.1 Persones
| ID | Regla | Font |
|---|---|---|
| RN-01 | Persona i soci són entitats separades. Ser soci és una relació que defineix el mòdul 01; la 00 no guarda cap camp de soci a la persona | CLAUDE; CTX §9 |
| RN-02 | Cada persona té un únic perfil, sigui sòcia o no | Decisió 018 (perfil únic), punt 1; CLAUDE |
| RN-03 | Una persona no sòcia (alumne, assistent a una conferència, llicència d'un dia) també té perfil, amb dades mínimes i consentiment, i no té compte per defecte | Decisió 021 (convidats); F §2 |
| RN-04 | Es guarden només les dades mínimes necessàries per a cada cas (V-04) | CTX §9 (RGPD); F §2 |
| RN-05 | Cap dada de salut a la plataforma: ni camps, ni documents, ni categories. La data de validesa del certificat mèdic queda fora de la 00 mentre P-07 (si es pot guardar aquesta data) estigui obert | CLAUDE; CK H4 (dades de salut); F §2; P-07 |
| RN-06 | El document d'identitat (DNI, NIE o passaport, amb el tipus) no es pot repetir entre persones. Es compara normalitzat | F §3, «Regles» (el DNI no es pot repetir); V-03 i V-04 |
| RN-07 | En detectar una possible persona duplicada, la plataforma avisa i no crea un segon perfil sense que qui el crea ho decideixi; mai fusiona perfils sola | Decisió 021, «Conseqüències»; V-03 |
| RN-08 | Si hi ha socis menors d'edat, el mandat SEPA de la seva quota l'ha de signar el titular del compte bancari. Si n'hi ha és P-33 (socis menors); la 00 no modela cap relació tutor-menor ni data de naixement fins que es respongui (Q-09) | Decisió 025 (dos nivells de producció), «Conseqüències»; CK H5 (protocol per a menors) |
| RN-09 | Els camps de text lliure del perfil porten un avís que no s'hi han d'escriure dades de salut | CLAUDE; CK H4. Proposta per complir RN-05 |
| RN-10 | El correu de contacte d'una persona no és únic (famílies que comparteixen correu); el correu d'entrada d'un compte personal sí que ho és | Decisió 015; V-05 |

### 5.2 Comptes, entrada i doble factor
| ID | Regla | Font |
|---|---|---|
| RN-11 | Hi ha dos tipus de compte: **personal** (àrea de socis, entra amb correu únic) i **d'administrador** (entrada d'administració separada, entra amb nom d'usuari únic) | Decisions 015, 018 i 029 |
| RN-12 | Una persona amb funcions de gestió té dos comptes lligats al mateix perfil: un de personal i un d'administrador | Decisió 018, punt 2; decisió 015, punt 2 |
| RN-13 | Una persona té com a màxim un compte de cada tipus. Excepció possible per als comptes d'emergència: Q-02 | Decisions 015 i 018 |
| RN-14 | Cada compte només entra per la seva entrada: el personal per l'àrea de socis, el d'administrador per l'entrada d'administració | Decisió 015, taula «Entrada» |
| RN-15 | El correu d'un compte d'administrador no és únic i només serveix per a notificacions; no serveix per entrar ni per recuperar | Decisió 015; decisió 018 |
| RN-16 | Un compte d'administrador **mai** recupera la contrasenya per correu: la restableix un altre administrador o s'hi entra amb un codi de recuperació d'un sol ús guardat fora de línia. Ningú no pot restablir el seu propi compte d'administrador per la via «un altre administrador» | Decisió 018, punt 4; decisió 015; CK C4 (restabliment de contrasenya) |
| RN-17 | La credencial temporal d'un restabliment no s'envia mai per correu i caduca (V-01) | Conseqüència de RN-16; canal: Q-03 |
| RN-18 | Un compte personal queda pendent fins que confirma el correu; recupera la contrasenya amb un enllaç d'un sol ús i amb caducitat (V-01), i la resposta no revela si el correu existeix | CK C4 i C5 (restabliment i verificació de correu); decisió 018, punt 4 |
| RN-19 | Un compte d'administrador el crea un compte amb el rol administrador i no es verifica per correu | CK C5; decisió 018, punt 4 |
| RN-20 | El doble factor (TOTP) és obligatori per a **qualsevol compte que entri per l'administració**, inclosos instructor i Departament d'Història, i per als comptes d'emergència. És opcional per als comptes personals | Decisió 018, punt 3; decisió 015, punts 1 i 3; CLAUDE; CK C2 (doble factor) |
| RN-21 | Un compte d'administrador no pot fer cap acció d'administració fins que té el TOTP donat d'alta | CK C2: «No es pot accedir a l'administració sense segon factor» |
| RN-22 | Hi ha com a mínim dos comptes d'emergència, amb TOTP i codis de recuperació fora de línia | Decisió 015, punt 3; F §2 |
| RN-23 | Els codis de recuperació són d'un sol ús, es mostren una sola vegada, es guarden fora de línia (paper o gestor de contrasenyes del club) i mai al repositori | Decisió 003 (substituïda per la 015, però aquest punt no es contradiu); ARQ §6, R10b |
| RN-24 | L'inici de sessió, la recuperació de contrasenya, els enllaços de convidat i els formularis públics tenen limitació de peticions i bloqueig temporal (V-01, V-02) | CK C3 (limitació de peticions) |
| RN-25 | Fora d'un esborrat RGPD (algú deixa un càrrec o es dona de baixa), els comptes es desactiven i no s'esborren, perquè el registre d'activitat hi fa referència. En un esborrat RGPD s'apliquen RN-87 a RN-90 | F §2; decisió 028 (substitueix la proposta de la v1 «no esborrar mai un compte») |
| RN-26 | No es pot retirar el rol administrador ni desactivar l'últim compte actiu amb aquest rol (sense comptar els d'emergència) | ARQ §6, R10b (com a mínim dos administradors actius) |
| RN-27 | El permís d'un compte d'administrador és la unió dels seus rols actius | Decisió 018, punt 2 |

### 5.3 Convidats
| ID | Regla | Font |
|---|---|---|
| RN-30 | Les persones no sòcies s'inscriuen i paguen com a convidades amb un enllaç segur de durada limitada, lligat a una inscripció o a un càrrec, i que no revela dades d'altres persones | Decisió 021; V-02 (durada limitada en lloc d'un sol ús, perquè un pagament fallit es pugui tornar a provar) |
| RN-31 | Els enllaços de convidat es poden generar, reenviar i revocar, caduquen i tenen limitació d'intents (V-02) | Decisió 021 («A incloure a la spec 00») |
| RN-32 | L'enllaç és un secret: no es registra sencer als registres ni al seguiment d'errors, i la base de dades en guarda només una empremta | Decisió 021, «Conseqüències»; decisió 011 (errors sense dades de socis) |
| RN-33 | Els pagaments dels convidats segueixen les mateixes regles que els altres (formulari allotjat de Stripe, confirmació verificada) i el càrrec queda lligat al perfil | Decisió 021, «Conseqüències» |
| RN-34 | Una persona no sòcia pot crear un compte personal de manera opcional, amb les mateixes regles (correu únic, verificació i recuperació per correu), lligat al seu perfil existent | Decisió 021; decisió 029 |

### 5.4 Permisos
| ID | Regla | Font |
|---|---|---|
| RN-40 | Cada endpoint exigeix autenticació i permís per defecte. Els públics (web pública, formularis públics, enllaços de convidat, notificacions de proveïdors amb firma) es declaren de manera explícita en una llista revisable | CLAUDE; CK C1 (autenticació a cada endpoint) |
| RN-41 | Els permisos tenen dos nivells: rol i objecte | CLAUDE; CTX §7 |
| RN-42 | Un soci només veu les seves pròpies dades | F §3, «Regles»; CLAUDE |
| RN-43 | L'instructor només veu les seves sessions i els seus alumnes | F §2; CLAUDE |
| RN-44 | El Departament d'Història no té accés a la resta de la gestió | F §8.3 |
| RN-45 | La matriu de permisos de 2.3 i 2.4 és provisional fins que la junta la validi | P-04 (matriu de rols sense validar); Q-01 |

### 5.5 Registre d'activitat
| ID | Regla | Font |
|---|---|---|
| RN-50 | Tot canvi en dades de socis o de persones i en diners deixa una entrada amb: qui (persona i compte concret, o convidat, o sistema), quan, què (objecte, camp, acció) i valor anterior | CLAUDE; CK C8 (registre d'activitat); decisió 015, punt 4; decisió 018, punt 5 |
| RN-51 | Les entrades no es poden modificar ni esborrar. Única excepció: en un esborrat RGPD, el que identifica la persona se substitueix per una referència anònima (RN-89) | F §2; decisió 028 |
| RN-52 | El registre no guarda mai secrets: contrasenyes, secrets TOTP, codis de recuperació, testimonis d'enllaços ni claus | CLAUDE (secrets fora dels registres); decisió 021 |
| RN-53 | També queden al registre: inicis de sessió (correctes i fallits), restabliments, alta i baixa de TOTP, ús de codis de recuperació i de comptes d'emergència, assignació de rols, importacions i desfets, consentiments, sol·licituds RGPD, consultes de dades bloquejades i destruccions | Decisions 015 i 018 (registre per compte); F §9.13 («tot queda registrat»); decisió 028 |

### 5.6 Diners: estructura bàsica de càrrec i pagament
Aquesta secció fixa **només l'estructura bàsica** (decisió 027). La 04 hi construeix al damunt els moviments de tresoreria, els ingressos, les comissions, els comptes i la conciliació; els mòduls 05a i 05b, les passarel·les i els fluxos de cobrament.

| ID | Regla | Font |
|---|---|---|
| RN-60 | Tots els imports són enters en cèntims d'euro (EUR) i positius | CLAUDE; ARQ §4.1 |
| RN-61 | Cap registre econòmic s'esborra: les correccions són anul·lacions amb motiu. En un esborrat RGPD, factures i cobraments es bloquegen (RN-88) | CLAUDE; F §2 i §7; decisió 028 |
| RN-62 | Tot càrrec, ingrés i despesa té departament (centre de cost) | CLAUDE; decisió 013 |
| RN-63 | Les comissions de les quotes anuals van al departament «General / Quotes de socis». L'ingrés de les quotes també hi va, segons l'encàrrec de la spec 00 (pendent de confirmar: Q-18) | Decisió 013; ENC; F §3 (les quotes són ingrés general) |
| RN-64 | Les comissions de les inscripcions van a la mateixa activitat i al seu departament | Decisió 013 |
| RN-65 | Les comissions de les llicències van al departament que decideixi la junta (proposta de la decisió 013: «General / Llicències») | Decisió 013; Q-19 |
| RN-66 | Un càrrec és d'un d'aquests tipus: **quota**, **inscripció** o **llicència** | ARQ §4.1; ENC |
| RN-67 | Estats del càrrec: **pendent**, **pagat**, **retornat**, **anul·lat**. Transicions permeses (la resta es rebutgen): pendent → pagat; pendent → anul·lat (amb motiu); pagat → retornat; pagat → anul·lat (devolució total, amb motiu). Què passa després de «retornat» i les devolucions parcials són de la spec 05b (Q-22) | ARQ §4.1, §4.3 i §4.4 |
| RN-68 | Mètodes de pagament: **domiciliació** (SEPA), **targeta** (inclou Apple Pay i Google Pay), **Bizum**, **transferència** i **manual** | Decisió 017; ARQ §4.1 |
| RN-69 | La domiciliació només s'admet en càrrecs de tipus quota (pagaments recurrents). Inscripcions i llicències: targeta, Bizum, transferència o manual | Decisió 017; CLAUDE |
| RN-70 | Cap camp de la plataforma guarda un IBAN ni dades de targeta. Només es guarden identificadors de Stripe i la referència del mandat | Decisió 025 (la plataforma no guarda l'IBAN); decisió 017; CLAUDE; CK C9 (pagaments) |
| RN-71 | Un càrrec no passa a «pagat» per una acció del navegador: només per una confirmació verificada del proveïdor (05b), una conciliació confirmada pel tresorer (04) o un registre manual | CLAUDE; ARQ §4.2 i §4.6 |
| RN-72 | El registre manual porta motiu obligatori i, si n'hi ha, justificant (opcional, Q-038). El fa qui té M14, que demana veure la tresoreria (072, Q-037; inicialment el Tresorer, P-331). Fet a la tasca P-12 (17/11/2026), encara sense el justificant | Decisió 017; ARQ §4.7; P-12; 072 |
| RN-73 | Les devolucions i els retorns no modifiquen el pagament original: generen un moviment nou de signe contrari (a la 04), i la comissió no es recupera | ARQ §4.1; decisió 013 |
| RN-74 | La llista de departaments la fixa la junta. L'únic decidit ara és «General / Quotes de socis» | Decisió 013; F §7 (pregunta per a la junta); Q-17 |
| RN-75 | Un departament amb càrrecs o moviments no s'esborra; es desactiva | Conseqüència de RN-61. Proposta |
| RN-76 | La 04 no pot canviar aquestes regles bàsiques sense actualitzar primer aquesta spec | Decisió 027 |

### 5.7 RGPD
| ID | Regla | Font |
|---|---|---|
| RN-80 | Els consentiments es guarden amb data i versió del text. Retirar un consentiment crea un registre nou | CTX §9; F §2 |
| RN-81 | Una persona pot demanar l'exportació i l'esborrat de les seves dades | CTX §9; CK H3 (esborrat i exportació) |
| RN-83 | Mínim de dades i cap dada de salut | CTX §9; CLAUDE |
| RN-84 | El butlletí només s'envia a qui hi ha donat consentiment, i sempre amb enllaç de baixa | CK G2 (plantilles i enllaç de baixa); F §8.2 |
| RN-85 | Les sol·licituds es responen en el termini legal (un mes segons l'article 12.3 del RGPD) | RGPD, art. 12.3 [A validar amb el responsable de protecció de dades: Q-15] |
| RN-86 | L'exportació es lliura en un format estructurat, d'ús habitual i llegible per màquina | RGPD, art. 20 |
| RN-87 | **Esborrar** vol dir desactivar tots els comptes de la persona i anonimitzar-ne les dades personals | Decisió 028, punt 1 |
| RN-88 | **Excepció:** les dades que la llei obliga a conservar (factures i cobraments) es bloquegen fins que s'acaba el termini legal i després es destrueixen. Terminis exactes [A validar amb la gestoria: Q-14] | Decisió 028, punt 2; CK H3; F §9.4 |
| RN-89 | Al registre d'activitat, les entrades no es modifiquen, però el que identifica la persona se substitueix per una referència anònima | Decisió 028, punt 3 |
| RN-90 | Una tasca periòdica destrueix les dades bloquejades quan venç el termini i ho deixa al registre amb la referència anònima | Decisió 028, «Conseqüències» |
| RN-91 | Les dades bloquejades només es consulten per complir una obligació legal, pels rols de M13, i cada consulta queda al registre | Decisió 028; M13 és proposta |

(RN-82 de la versió 1 queda substituïda per RN-87 a RN-91.)

### 5.8 Importacions
| ID | Regla | Font |
|---|---|---|
| RN-92 | Tota importació té tres passos: previsualització (sense escriure res), validació i confirmació; i es pot desfer dins dels límits de V-06 | F §2 i §9.13; CK §5 (extres del C.R.I.S.) |
| RN-93 | La importació de Cluber es fa una sola vegada | Decisió 014 (migració única de Cluber); decisió 020 (sense restricció de data) |
| RN-94 | La importació de Cluber no inclou IBAN. Un fitxer amb una columna d'IBAN es rebutja sencer i no es desa | Decisió 025; decisió 022 (escenari B: no cal l'IBAN). El rebuig sencer és proposta |
| RN-95 | Els registres de Cluber es fan coincidir per document d'identitat o número de soci | F §9.13 |
| RN-96 | L'extracte bancari s'importa en CSV de manera periòdica; les línies ja importades no es dupliquen | CTX §7; ARQ §1 |
| RN-97 | La 00 importa i valida l'extracte; casar-lo amb pagaments i liquidacions és del mòdul 04 | ARQ §1 i §9.1 |
| RN-98 | Tota importació, confirmació i desfet queda al registre d'activitat | F §9.13 |
| RN-99 | Els formats de Cluber i del banc són desconeguts; sense una mostra anonimitzada no es pot fixar la validació (Q-23, Q-24) | P-21 (format de l'exportació de Cluber); ARQ §7 |
| RN-100 | Fora de producció, les importacions només es fan amb fitxers inventats o anonimitzats | CLAUDE; decisió 010 (entorns) |
| RN-101 | El fitxer original d'una importació no es desa: només la seva empremta i les línies normalitzades | Mínim de dades (CTX §9); V-06 |

### 5.9 Correu, notificacions i fitxers
Les regles són a l'annex A (correu) i a l'annex B (fitxers).

### 5.10 Duplicar activitats (servei comú previst)
Duplicar cursos, sortides i conferències és un servei comú de la plataforma (F §2 i §9.18), però **es construeix al mòdul 02** (decisió 026). Les seves regles (què es copia i què no) s'especificaran a la spec 02. La 00 no en té cap història ni criteri d'acceptació.

### 5.11 Entorns
| ID | Regla | Font |
|---|---|---|
| RN-110 | Hi ha tres entorns: local, proves i producció. Proves no comparteix servidor ni base de dades amb producció | Decisió 010 (tres entorns); CK A2 (ambients) |
| RN-111 | Fora de producció, només dades inventades | CLAUDE; decisió 010 |
| RN-112 | Stripe en mode de proves excepte en els dos nivells de producció, cadascun amb autorització expressa de la junta. L'aplicació rebutja claus de producció si `STRIPE_LIVE_MODE_ALLOWED` no és cert | Decisió 025; ARQ §4.2 i §5 |
| RN-113 | Cada entorn té els seus buckets i les seves claus; cap fitxer real fora de producció | Decisió 005 (fitxers); decisió 010 |
| RN-114 | Cap secret al repositori, als registres ni als exemples | CLAUDE; CK A3 |
| RN-115 | Fora de producció, cap correu arriba a adreces reals (V-07) | CLAUDE; decisió 010. Proposta |

---

## 6. Entitats

Nivell de domini. Els tipus, els índexs i els noms de codi es fixen a `data-model.md` (llengua dels noms: V-09).

| Entitat | Camps principals | Restriccions |
|---|---|---|
| **Persona** | nom; cognoms; correu de contacte; telèfon; adreça; tipus i número de document d'identitat; estat (activa, anonimitzada); referència anònima (en anonimitzar-la); origen (alta presencial, web, convidat, importació de Cluber); lot d'importació (si escau); dates de creació i d'última modificació | Document únic quan hi és (normalitzat). Camps obligatoris segons el cas (V-04). Correu de contacte no únic. Data de naixement: només si P-33 (socis menors) ho fa necessari (Q-09). Cap camp de salut |
| **Compte** | persona; tipus (personal, administrador); correu d'entrada (personal) o nom d'usuari (administrador); correu de notificació (administrador); empremta de la contrasenya; estat (pendent de verificar, actiu, bloquejat temporalment, desactivat); és d'emergència; TOTP actiu; data d'últim accés | Correu d'entrada únic entre comptes personals. Nom d'usuari únic entre comptes d'administrador. Màxim un compte de cada tipus per persona (excepció d'emergència: Q-02). «És d'emergència» només en comptes d'administrador |
| **Factor TOTP** | compte; secret (xifrat); data d'alta; últim interval utilitzat | Un per compte. L'últim interval impedeix reutilitzar un codi |
| **Codi de recuperació** | compte; empremta; data d'ús | D'un sol ús |
| **Rol** | codi; nom | Llista tancada dels 8 rols |
| **Assignació de rol** | compte d'administrador; rol; data d'assignació; assignat per; data de retirada; retirat per | Només comptes d'administrador. El rol soci no s'assigna: depèn de l'estat de soci (01) |
| **Enllaç de convidat** | empremta del testimoni; persona; objecte lligat (càrrec o inscripció); finalitat; creat per; data de caducitat; data de revocació; substituït per (en reenviar); intents fallits | El testimoni sencer no es guarda mai |
| **Entrada del registre d'activitat** | data i hora; persona que actua (o la seva referència anònima); compte que actua, o enllaç de convidat, o «sistema» amb l'origen; acció; tipus i identificador de l'objecte; camp; valor anterior; valor nou; motiu | Només s'hi afegeix. Cap secret als valors. Única substitució permesa: la identificació de la persona per la seva referència anònima (RN-89) |
| **Text legal** | tipus (privacitat, butlletí, imatge… Q-16); versió; contingut; vigent des de | Una versió publicada no es modifica |
| **Consentiment** | persona; text legal (versió); acció (atorgat, retirat); data i hora; canal (web, presencial); registrat per | Només s'hi afegeix |
| **Sol·licitud RGPD** | persona; tipus (exportació, esborrat); data; estat (rebuda, en curs, resolta, denegada en part); resolta per; data de resolució; motiu (per exemple, conservació legal) | — |
| **Bloqueig legal** | objecte bloquejat (factura, cobrament…); persona (referència anònima); motiu legal; data de fi del termini; data de destrucció | Només es consulta pels rols de M13. Termini [A validar amb la gestoria: Q-14] |
| **Departament** | nom; actiu | Nom únic. «General / Quotes de socis» existeix des de l'inici. Si hi ha jerarquia: Q-17 |
| **Càrrec** (estructura bàsica) | persona deutora; tipus (quota, inscripció, llicència); concepte; import en cèntims; moneda (EUR); departament; activitat (opcional, quan existeixi la 02); estat; motiu d'anul·lació; mòdul d'origen; dates | Import enter positiu. Departament obligatori. Transicions de RN-67. La 04 hi afegeix el que li calgui sense canviar aquestes regles (decisió 027) |
| **Pagament** (estructura bàsica) | càrrec; mètode (domiciliació, targeta, Bizum, transferència, manual); import en cèntims; estat al proveïdor; «a revisar» (sí o no); identificadors externs de Stripe; referència de transferència; data; registrat per i motiu (manual); justificant (fitxer, opcional) | Domiciliació només si el càrrec és una quota. Cap camp d'IBAN ni de targeta |
| **Fitxer** | clau a l'emmagatzematge; nom original; tipus; mida; objecte al qual pertany; pujat per; data; data d'esborrat prevista (exportacions) | Vegeu l'annex B |
| **Plantilla de correu** | codi; categoria (transaccional, butlletí); prioritat; assumpte; cos; versió | Vegeu l'annex A |
| **Enviament de correu** | destinatari (persona o adreça); plantilla; categoria; estat (en cua, enviat, ajornat, error, rebotat); identificador del proveïdor; data | Vegeu l'annex A |
| **Comptador diari de correu** | data; enviats transaccionals; enviats de butlletí; avís del 80 % enviat | Un per dia |
| **Lot d'importació** | tipus (Cluber, extracte bancari); empremta del fitxer; estat (previsualització, confirmat, desfet, rebutjat); creat per; confirmat per; desfet per; dates; resum (nous, coincidents, errors, exclosos, duplicats) | Màxim un lot de Cluber confirmat i no desfet. El fitxer original no es desa |
| **Línia d'importació** | lot; número de línia; dades normalitzades; resultat (nova, coincident, error, exclosa, duplicada); missatge; registre creat | Mai cap columna d'IBAN |

Fora de la 00: el **soci** (01), el **mandat** i els **identificadors de client de Stripe** (05a), els **moviments de tresoreria**, les **comissions** i els **comptes bancaris** (04), les **activitats** i el servei de **duplicar** (02).

---

## 7. Casos límit, estats buits i errors

| # | Cas | Comportament esperat | Font |
|---|---|---|---|
| L1 | Dues persones (per exemple, una parella o un pare i un fill) comparteixen correu | Totes dues poden tenir perfil amb aquest correu de contacte; només una pot tenir compte personal amb aquest correu. L'altra fa servir un correu propi o participa com a convidada | RN-10; V-05 |
| L2 | Un convidat torna amb un correu diferent | Si dona el mateix document, es reconeix el perfil; si no, es pot crear un perfil nou i la plataforma avisa si coincideixen nom, cognoms i telèfon | V-03 |
| L3 | Un convidat es fa soci | Es reutilitza el mateix perfil; el soci es crea al 01 | RN-02 |
| L4 | L'únic administrador perd el mòbil i els codis | Només queden els comptes d'emergència; sense aquests, no hi ha via dins la plataforma | ARQ §6, R10b; RN-22 |
| L5 | Algú intenta restablir el seu propi compte d'administrador | Es rebutja | RN-16 |
| L6 | Un compte d'administrador té el rol instructor i també el de tresorer | Té la unió dels permisos; l'abast per objecte de cada rol es manté | RN-27 |
| L7 | Un instructor que no és soci | Té compte d'administrador però potser no compte personal: Q-10 | Decisió 018 |
| L8 | Un enllaç de convidat s'obre després de pagar el càrrec | Només mostra l'estat i el rebut fins que caduca | V-02 |
| L9 | L'enllaç es reenvia | El nou invalida l'anterior | V-02 |
| L10 | Es revoca un enllaç mentre la persona és al formulari de Stripe | El pagament es processa igualment si arriba confirmat (el càrrec continua sent vàlid); la revocació només impedeix accions noves | RN-33. Proposta |
| L11 | Una confirmació de pagament arriba per a un càrrec anul·lat | La transició no és vàlida: el pagament queda «a revisar» i s'avisa el tresorer | ARQ §4.2, punts 4 i 5 |
| L12 | Es vol esborrar un departament amb moviments | Es rebutja; es pot desactivar | RN-75 |
| L13 | Una persona retira el consentiment del butlletí mentre s'està enviant una tanda | Els enviaments encara no fets de la persona s'anul·len | RN-84 |
| L14 | Una persona demana l'esborrat i té càrrecs pendents | Pendent de Q-14 | Decisió 028 |
| L15 | Una persona anonimitzada torna al club | Es crea un perfil nou; no hi ha cap manera de recuperar l'antic | Decisió 028 |
| L16 | El fitxer de Cluber té línies amb el mateix document | Les dues es marquen com a error de duplicat | CK B9 |
| L17 | El fitxer de Cluber té una columna d'IBAN | Es rebutja sencer i no es desa | RN-94 |
| L18 | Es vol desfer la importació de Cluber quan ja s'han generat quotes o pagaments a partir d'aquestes persones | Es rebutja i es llisten les dades que en depenen | V-06 |
| L19 | Es puja dues vegades el mateix extracte | Totes les línies surten com a duplicades i no s'importa res | RN-96 |
| L20 | S'arriba al 100 % del límit diari de correu | Els correus queden ajornats i surten primer l'endemà, per ordre de prioritat | V-07 |
| L21 | Una URL signada es comparteix | Caduca als 5 minuts; passat el termini no serveix | V-08 |
| L22 | Llistats buits (cap consentiment, cap sol·licitud, cap importació) | Es mostra un estat buit explicat, no una taula en blanc | CK B7 (estats reals) |
| L23 | Error del servidor o pàgina inexistent | Pàgines 404 i 500 pròpies, sense dades internes | CK B7 |
| L24 | Una petició d'un rol sense permís | Es rebutja sense revelar si l'objecte existeix | RN-40 i RN-41 |
| L25 | S'intenta desactivar l'últim administrador | Es rebutja | RN-26 |

---

## 8. Requisits no funcionals

### 8.1 Seguretat
- Autenticació i permís a cada endpoint; llista explícita de rutes públiques (CK C1, autenticació a cada endpoint).
- TOTP segons l'entrada (CK C2, doble factor); limitació de peticions (CK C3).
- Contrasenyes guardades amb un algorisme d'empremta lent i amb sal; política de V-01.
- Sessions d'administració més curtes que les de l'àrea de socis (V-01).
- Entrada d'administració en una ruta discreta (`ADMIN_URL_PATH`, ARQ §5).
- Mode de depuració desactivat i capçaleres de seguretat en producció (CK C7, configuració de producció).
- Secrets fora del repositori i escaneig al pipeline (CK A3).

### 8.2 Privacitat i registres
- Registres estructurats sense contrasenyes ni dades personals innecessàries (CK E1, registres).
- Seguiment d'errors sense correus, noms, documents, IBAN ni cos de les peticions (decisió 011, monitoratge i errors).
- Allotjament a la UE (CK D4); proveïdors amb acord d'encarregat del tractament abans de dades reals (ARQ §7).
- Mínim de dades (CTX §9). Anonimització i bloqueig segons la decisió 028.

### 8.3 Rendiment i volum
- Volum de referència: uns 150 socis i uns 300 subscriptors del butlletí [A validar amb dades reals] (CTX §3).
- Objectius de V-10. Les importacions es processen a la cua de tasques (decisió 012) sense bloquejar l'aplicació.

### 8.4 Accessibilitat i ús
- Objectiu WCAG 2.2 AA (CK B8, accessibilitat). Les pantalles d'entrada, convidat i consentiment són les primeres que veuen els socis.
- Responsive i usable al mòbil (PWA, CK §1).
- Interfície i missatges en català (CLAUDE).
- Missatges d'error clars i sense dades internes (CK B7).

### 8.5 Disponibilitat i continuïtat
- Monitoratge extern de la web i l'API (decisió 011; CK E3).
- Còpies diàries xifrades a dos proveïdors i prova de restauració (decisió 006; CK D1 i D2). Detall tècnic al pla.
- Temps màxim de recuperació acceptable: Q-34.

### 8.6 Arquitectura
- Monòlit modular amb una sola base de dades (CLAUDE).
- Una app no escriu als models d'una altra; ho fa a través de serveis (CLAUDE). Els altres mòduls criden els serveis de la 00 (permisos, registre, correu, fitxers, càrrecs).
- Les tasques en segon pla (correu, importacions, destrucció de dades bloquejades) van a la cua sobre PostgreSQL (decisió 012). La llibreria es tria al pla.

---

## 9. Fora d'abast

| Què | On va | Font |
|---|---|---|
| Integració amb Stripe (sessions de pagament, confirmacions, mandats, remeses, reintents, retornats, devolucions) | 05a i 05b | Decisió 024; ARQ §4 |
| Alta del mètode de pagament i mandats; identificadors de client de Stripe | 05a | Decisió 024 |
| Moviments de tresoreria, ingressos, comissions, comptes bancaris, compte de trànsit de Stripe, casament de l'extracte amb els pagaments | 04 | Decisió 027; ARQ §9.1 |
| Relació de soci (número, tipus, estat, quotes, carnet) i registre mínim de llicència | 01 | Decisió 024 |
| Activitats, sessions, inscripcions i el servei de duplicar activitats | 02 | Decisió 026; ARQ §9.1 |
| Fusionar dos perfils de persona ja creats | No previst ara (proposta) | V-03 |
| Editor i redacció del butlletí; subscriptors de la web | 07 | F §8.2 |
| Procés complet de llicències (preus, renovacions, exportació a la federació) | 06 | Decisió 024; P-28 |
| Notificacions push a la PWA | Més endavant, si cal | CK §1 |
| Doble factor per SMS | Descartat | Decisió 003 (alternativa descartada per cost i seguretat) |
| Inici de sessió amb proveïdors externs (Google, etc.) | No previst | Cap font ho demana |
| Qualsevol dada de salut | Mai | CLAUDE |
| App nativa | Més endavant | CLAUDE |
| Botiga en línia | Fora d'abast ara | CLAUDE |

---

## 10. Valors proposats i preguntes obertes

### 10.1 Valors proposats
Són **propostes** d'aquesta spec per als valors per defecte. Es poden canviar a la revisió; si no es canvien, són els que es fan servir al pla.

| ID | Tema | Proposta | Substitueix |
|---|---|---|---|
| V-01 | Seguretat dels comptes | **Contrasenya:** mínim 12 caràcters; es rebutgen les habituals i les semblants al nom o al correu. **Bloqueig:** 5 intents fallits seguits en un compte → 15 minuts; 20 intents fallits des d'un mateix origen en 15 minuts → 15 minuts. **Codis de recuperació:** 10 per compte d'administrador. **Enllaç de verificació del compte personal:** 48 hores. **Enllaç de recuperació:** 1 hora, d'un sol ús. **Credencial temporal d'un restabliment d'administrador:** 24 hores. **Sessió d'administració:** es tanca després de 30 minuts sense activitat i com a màxim 8 hores. **Sessió de l'àrea de socis:** es tanca després de 14 dies sense activitat | Q-04 |
| V-02 | Enllaços de convidat | **Durada limitada** (no d'un sol ús), perquè un pagament fallit es pugui tornar a provar. **Enllaç de pagament:** 7 dies, o fins que el càrrec es paga o s'anul·la. Un cop pagat, fins que caduca només serveix per veure l'estat i descarregar el rebut. **Enllaç d'inscripció sense pagament** (per exemple, una conferència gratuïta): fins al dia després de l'activitat. **Reenviar** genera un enllaç nou i invalida l'anterior. **Testimoni:** aleatori de 256 bits; només se'n guarda l'empremta. **Intents:** 10 testimonis incorrectes des d'un mateix origen en 15 minuts → bloqueig de 15 minuts. La persona pot demanar un enllaç nou amb el seu correu (resposta idèntica tant si existeix com si no) | Q-05 (excepte qui els genera: Q-01) |
| V-03 | Duplicats de persona | **Mateix document d'identitat** (normalitzat: sense espais ni guions, en majúscules, amb el tipus) → és la mateixa persona: no es crea cap perfil nou. **Mateix correu de contacte, o mateix nom i cognoms amb el mateix telèfon** → avís a qui crea el perfil, que decideix si fa servir l'existent. Mai es fusionen perfils automàticament; la fusió de perfils ja creats queda fora d'abast | Q-06 |
| V-04 | Dades mínimes | **Soci:** nom, cognoms, document, correu i telèfon (adreça opcional). **Alumne no soci:** nom, cognoms, correu i telèfon; el document només si cal tramitar-li una llicència (spec 06). **Assistent a una conferència:** nom i correu (telèfon opcional). **Llicència d'un dia:** nom, cognoms, document i correu, més el que demani la federació (spec 06). **Persona amb compte d'administrador que no és sòcia:** nom, cognoms i correu de notificació. **Document:** DNI, NIE o passaport, amb el tipus. **Data de naixement:** no es demana fins que es respongui Q-09 | Q-07 |
| V-05 | Correu compartit | El compte personal exigeix un correu propi i únic. El correu de contacte del perfil no és únic: una persona sense correu propi pot participar com a convidada amb els enllaços que s'envien al correu compartit | Q-08 |
| V-06 | Importacions | **Confirmar:** només si no hi ha errors, o si l'usuari exclou explícitament les línies amb error (surten al resum). **Desfer Cluber:** només si no s'ha creat cap dada a partir del lot (quotes, pagaments, comptes); si n'hi ha, es rebutja i es llisten. **Desfer un extracte:** només si cap línia està conciliada. **Fitxer original:** no es desa; només l'empremta i les línies normalitzades. **Duplicats de l'extracte:** una línia és la mateixa si coincideixen data, import, concepte i saldo | Q-25 |
| V-07 | Correu | **Reserva diària per als transaccionals:** 100 enviaments; el butlletí pot fer servir fins a 200 al dia (300 subscriptors en dos dies). **Al 100 % del límit:** els correus queden ajornats i surten primer l'endemà, per aquest ordre: recuperació i verificació de comptes, enllaços de convidat, confirmacions, recordatoris i, per últim, el butlletí. **Fora de producció:** cap correu surt cap a adreces reals; es desen en una bústia de proves (eina a triar al pla) | Q-26 (excepte el remitent i qui rep l'avís) |
| V-08 | Fitxers | **Tipus permesos:** PDF, JPEG, PNG, WebP i HEIC (fotos del mòbil); CSV només a les importacions. **Mida màxima:** 10 MB per fitxer. **URL signada:** 5 minuts. **Fitxer d'exportació RGPD:** disponible 7 dies i després s'esborra | Q-27 |
| V-09 | Noms de codi | Codi (models, funcions, variables) en anglès; interfície, missatges i documents en català. Les variables d'entorn ja definides a l'arquitectura §5 es mantenen tal com són. Es decideix una sola vegada al pla | Q-29 |
| V-10 | Rendiment | Previsualització d'una importació de Cluber (fins a 1.000 línies) en menys d'un minut. Pantalles de l'àrea de socis en menys de 2 segons amb una connexió mòbil 4G | 8.3 de la v1 |

### 10.2 Preguntes obertes per a qui ha de respondre
Els números es mantenen de la versió 1; els que falten s'han resolt o s'han convertit en proposta (§10.3).

**Junta**
| ID | Pregunta | Abans de |
|---|---|---|
| Q-01 | Validar la matriu de permisos de 2.3 i 2.4 (P-04: la matriu de rols no està validada), incloses les cel·les marcades [A validar]: qui crea perfils (M2), qui genera enllaços de convidat (M5), qui consulta el registre d'activitat (M6), qui manté els departaments (M7), qui importa l'extracte (M9), qui publica els textos legals (M12), qui consulta les dades bloquejades (M13, proposta: tresorer i administrador), si el responsable de cursos i sortides veu el marge de totes les activitats o només de les seves, i quines dades personals veu el tresorer | Pla |
| Q-02 | Comptes d'emergència: a quina persona es lliguen (una persona real amb un segon compte d'administrador, o un perfil del club), quin rol tenen i qui en custodia les credencials (amb informàtica) | Implementar HU-10 |
| Q-03 | Qui pot restablir un compte d'administrador i per quin canal es lliura la credencial temporal, sabent que mai per correu. Proposta: només el rol administrador, i la credencial es lliura en persona o per telèfon | Implementar HU-08 |
| Q-09 | P-33 (socis menors d'edat): n'hi ha? Si n'hi ha: data de naixement al perfil, relació amb el tutor, consentiment del tutor (la LOPDGDD, art. 7, fixa 14 anys), titular del mandat i persona de referència | Pla (afecta el model de persona) i 05a |
| Q-10 | Un instructor o un membre del Departament d'Història que no és soci: només té compte d'administrador? Com veu i edita les seves dades (fila M1)? | Pla |
| Q-11 | Conflicte d'interès: un compte d'administrador pot modificar dades o diners de la seva pròpia persona (per exemple, registrar el pagament de la seva quota)? | Implementar permisos |
| Q-15 | Qui és el responsable de protecció de dades del club i qui atén les sol·licituds RGPD (fila M11) | Implementar HU-18 i HU-19 |
| Q-16 | Tipus de consentiment i textos (privacitat, butlletí, imatge…), si una versió nova obliga a tornar a demanar-lo, i com s'acredita el consentiment presencial (CK H1, política de privacitat) | Implementar HU-17 |
| Q-17 | Llista de departaments i si hi ha jerarquia (departament i centre de cost, com suggereix el nom «General / Quotes de socis»), amb la tresoreria | Pla |
| Q-19 | Departament de les comissions de llicències (decisió 013, proposta «General / Llicències») | Spec 06, o abans si la 01 cobra llicències |
| Q-20 | P-12: qui pot registrar un cobrament manual i quin justificant cal | Implementar el mètode manual |
| Q-30 | Qui de la junta revisa aquesta spec | Revisió final |
| Q-31 | Es manté el compte personal d'una persona que es dona de baixa (per consultar rebuts)? | Spec 01 |
| Q-32 | P-07: si es pot guardar la data de validesa del certificat mèdic (ara queda fora de la 00) | Spec 01 i 02 |

**Tresoreria (amb la gestoria)**
| ID | Pregunta | Abans de |
|---|---|---|
| Q-14 | Terminis legals exactes de conservació de factures i cobraments (bloqueig de la decisió 028), si també s'han de conservar altres dades (persones convidades, registre d'activitat), i què es fa quan qui demana l'esborrat té càrrecs pendents [A validar amb la gestoria] | Implementar HU-19 |
| Q-18 | Confirmar que l'ingrés de les quotes (no només la comissió) va a «General / Quotes de socis» | Implementar HU-15 |
| Q-22 | Transicions des de «retornat» i devolucions parcials | Spec 05b (a la 00 només afecta la taula de transicions) |
| Q-23 | P-21: format de l'exportació de Cluber i què conté (rebuts, historial, llicències, vegeu P-28) | Implementar HU-20 |
| Q-24 | Format del CSV de l'extracte del banc (cal una mostra anonimitzada) | Implementar HU-21 |

**Informàtica**
| ID | Pregunta | Abans de |
|---|---|---|
| Q-26 | Nom de l'adreça remitent (proposta: `no-respon@cris1954.cat`, l'exemple de la decisió 019) i qui rep l'avís del 80 % del límit de correu (fila M15) | Implementar l'annex A |
| Q-34 | Temps màxim de recuperació acceptable si cau el servidor (hores o dies) (ARQ §8, pregunta 15) | Pla |

### 10.3 Preguntes de la versió 1 que ja no són obertes
| ID v1 | Ara |
|---|---|
| Q-04, Q-05, Q-06, Q-07, Q-08, Q-25, Q-27, Q-29 | Valors proposats V-01, V-02, V-03, V-04, V-05, V-06, V-08 i V-09 |
| Q-12 | Inclosa a Q-01 |
| Q-13 | Resolta per la decisió 028 (esborrat RGPD) |
| Q-21 | Resolta per la decisió 027 (estructura bàsica a la 00) |
| Q-26 | En part a V-07; queden el remitent i l'avís (informàtica) |
| Q-28 | Resolta per la decisió 026 (duplicar al 02) |
| Q-33 | Resolta per la decisió 029 (compte personal) |

---

## 11. Proves derivades

| Prova | Criteris | Requisit de la checklist |
|---|---|---|
| Recorregut automàtic de totes les rutes sense sessió | CA-11.3 | C1 (autenticació a cada endpoint) |
| Matriu de rols convertida en proves (una per cel·la de 2.3) i proves d'objecte | CA-06.5, CA-11.1, CA-11.2, CA-12.1, CA-13.1 | B4 (proves de permisos) |
| Entrada d'administració: sense TOTP no hi ha accés; cap enllaç de recuperació per correu; restabliment per un altre administrador i amb codi | CA-07.1 a CA-07.7, CA-08.x, CA-09.x | C2 (doble factor), C4 (restabliment) |
| Recuperació i verificació del compte personal de principi a fi | CA-04.x | C4, C5 (verificació de correu) |
| Limitació de peticions i bloqueig temporal | CA-02.7, CA-07.6 | C3 (limitació de peticions) |
| Revisió automàtica del model: cap camp d'IBAN, de targeta ni de salut | CA-01.4, CA-15.6 | C9 (pagaments), H4 (dades de salut) |
| Transicions d'estat del càrrec, imports en cèntims i departament obligatori (cobertura completa) | CA-15.x, CA-16.x | B1 (proves unitàries de càlculs econòmics) |
| Registre d'activitat: contingut, immutabilitat, cap secret | CA-14.x | C8 (registre d'activitat), E1 (registres) |
| Importacions amb fitxers incorrectes, duplicats, buits i amb IBAN; desfer amb i sense dependències | CA-20.x, CA-21.x | B9 (proves d'importació) |
| Exportació, esborrat, bloqueig i destrucció de principi a fi, i comprovació que no queda cap dada identificativa | CA-18.1, CA-19.1 a CA-19.6 | H3 (esborrat i exportació) |
| Fitxers maliciosos, tipus i mides no permesos, URL caducades | CA-B1 a CA-B5 | C10 (fitxers pujats) |
| Correu: comptador, reserva, tandes, prioritat, avís del 80 % | CA-A1 a CA-A9 | G2 (plantilles i enllaç de baixa) |
| Arrencada amb clau de producció de Stripe sense autorització | CA-25.3 | C9 |

---

## Annex A — Correu i notificacions (versió lleugera)

**Objectiu.** Un servei únic perquè qualsevol mòdul enviï correus amb plantilla, sense superar el límit diari de Brevo i deixant constància de cada enviament (F §2, «Notificacions»; ARQ §9.2, annex 1b).

### Regles
| ID | Regla | Font |
|---|---|---|
| RN-A1 | Remitent: una adreça de cris1954.cat (nom: Q-26) amb resposta a cris@cris.es | Decisió 019 (domini i correu); CLAUDE |
| RN-A2 | Dues categories separades: transaccionals i butlletí, amb remitents i categories diferents | Decisió 004 (correu amb Brevo) |
| RN-A3 | Límit diari: 300 enviaments al pla gratuït, sumant totes les categories (configurable amb `EMAIL_DAILY_LIMIT`) | Decisió 004; ARQ §2 i §5 |
| RN-A4 | Cada dia es reserva una quota per als transaccionals (`EMAIL_TRANSACTIONAL_RESERVE`, 100 segons V-07). El butlletí només pot fer servir el límit menys la reserva | Decisió 004; V-07 |
| RN-A5 | El butlletí s'envia en tandes al llarg de diversos dies: el que no cap avui passa a l'endemà | Decisió 004 |
| RN-A6 | Quan els enviaments del dia arriben al 80 % del límit, s'envia un sol avís aquell dia a qui toqui (`EMAIL_ALERT_TO`, Q-26) | Decisió 004; ARQ §5 |
| RN-A7 | Cada enviament queda registrat amb la plantilla, el destinatari, l'estat i la data | F §2, «Notificacions» |
| RN-A8 | Cada esdeveniment té la seva plantilla (alta aprovada, inscripció confirmada, recordatori, quota pendent, llicència a punt de caducar…) amb una prioritat. Cada mòdul declara les seves | F §2; V-07 |
| RN-A9 | El butlletí només va a persones amb el consentiment actiu i sempre porta enllaç de baixa | CK G2; RN-84 |
| RN-A10 | Els avisos de rebots i baixes que envia Brevo es verifiquen abans d'acceptar-los (`BREVO_WEBHOOK_SECRET`) | ARQ §5 |
| RN-A11 | SPF, DKIM i DMARC configurats a cris1954.cat abans de dades reals | CK G1 (SPF, DKIM i DMARC); decisió 019 |
| RN-A12 | Els correus no porten mai contrasenyes ni credencials temporals. Els enllaços d'un sol ús o de durada limitada (recuperació del compte personal, convidat) sí que hi poden anar | RN-17; decisió 021 |
| RN-A13 | Els enviaments es fan des de la cua de tasques, no dins de la petició de l'usuari | Decisió 012; ARQ §1 («Correu») |
| RN-A14 | Les persones anonimitzades no reben cap correu | Decisió 028 |

### Criteris d'acceptació
- **CA-A1** Donat qualsevol correu de la plataforma, quan surt, llavors el remitent és de cris1954.cat i la resposta va a cris@cris.es.
- **CA-A2** Donat un límit de 300 i una reserva de 100, quan el butlletí arriba a 200 enviaments en un dia, llavors la resta del butlletí queda ajornada per a l'endemà i els transaccionals continuen sortint fins a 300.
- **CA-A3** Donat que els enviaments del dia arriben al 80 % del límit, quan se n'envia un més, llavors s'envia un sol avís aquell dia.
- **CA-A4** Donat que s'ha arribat al 100 %, quan cal enviar un correu, llavors queda en estat «ajornat» i surt l'endemà.
- **CA-A5** Donat diversos correus ajornats, quan comença el dia següent, llavors surten per l'ordre de prioritat de V-07.
- **CA-A6** Donat qualsevol enviament, quan es consulta el registre d'enviaments, llavors hi consten la plantilla, el destinatari, l'estat i la data.
- **CA-A7** Donat un butlletí, quan es prepara la llista de destinataris, llavors només hi ha persones amb el consentiment actiu i cada correu porta l'enllaç de baixa.
- **CA-A8** Donat un avís de Brevo amb una firma incorrecta, quan arriba, llavors es rebutja.
- **CA-A9** Donat un enviament que falla al proveïdor, quan es reintenta, llavors no es compta dues vegades al comptador diari.

### Fora de l'annex
Editor del butlletí (07), notificacions push (més endavant), correu de confirmació del mandat (05a; CK G3, correu de confirmació del mandat).

---

## Annex B — Fitxers (versió lleugera)

**Objectiu.** Guardar fitxers privats (rebuts, carnet en PDF, justificants, exportacions RGPD) i servir-los només a qui té permís (decisió 005; ARQ §9.2, annex 1a).

### Regles
| ID | Regla | Font |
|---|---|---|
| RN-B1 | Tots els fitxers són en buckets privats de Scaleway (París); cap bucket públic amb dades personals | Decisió 005 (fitxers a Scaleway); ARQ §1 |
| RN-B2 | Per descarregar un fitxer, l'API comprova el rol i l'objecte i genera una URL signada de curta durada (`S3_SIGNED_URL_TTL_SECONDS`, 5 minuts segons V-08) | Decisió 005; V-08 |
| RN-B3 | Tipus i mida limitats (`UPLOAD_MAX_BYTES`, valors de V-08); el tipus es comprova pel contingut, no només per l'extensió | CK C10 (fitxers pujats); decisió 005 |
| RN-B4 | Cada fitxer pertany a un objecte (persona, càrrec, pagament, sol·licitud RGPD…) i hereta el seu permís | Decisió 005; F §2 («Documents adjunts») |
| RN-B5 | Buckets separats per entorn; cap fitxer real fora de producció | Decisió 005; decisió 010 |
| RN-B6 | Els fitxers entren a les còpies creuades | Decisió 006 (còpies xifrades) |
| RN-B7 | Cap fitxer amb dades de salut | CLAUDE; CK H4 |
| RN-B8 | En un esborrat RGPD, els fitxers de la persona sense obligació legal s'esborren; els que en tenen (factures, justificants de cobrament) es bloquegen | Decisió 028 |

### Criteris d'acceptació
- **CA-B1** Donat un fitxer d'un tipus no permès o de més de 10 MB, quan es puja, llavors es rebutja amb un missatge clar.
- **CA-B2** Donat un fitxer amb una extensió permesa però un contingut d'un altre tipus, quan es puja, llavors es rebutja.
- **CA-B3** Donat un usuari amb permís sobre l'objecte, quan demana el fitxer, llavors rep una URL signada que caduca als 5 minuts.
- **CA-B4** Donat un usuari sense permís sobre l'objecte, quan demana el fitxer, llavors no rep cap URL ni cap dada del fitxer.
- **CA-B5** Donat una URL signada caducada, quan s'obre, llavors l'emmagatzematge la rebutja.

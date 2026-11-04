# 066 — Revisió de la T-M01-05: reenviament, límit per origen i tasques noves

- **Data:** 04/11/2026
- **Estat:** Acceptada (punts 1 a 4). El punt 5 (T-M01-39) és una **proposta**: no està aprovada ni és condició del nivell 1 ([P-53](pendents.md)). Precisa la [065](065-enllacos-del-correu-i-restabliment-per-un-altre-administrador.md): **canvia el text de RN-M01-58 i RN-M01-59** i de CA-M01-50 i CA-M01-51 ([addenda](../planning.md#M01-addenda-066)). No resol Q-03, P-52 ni Q-26.

## Context
La revisió al navegador de la T-M01-05 (03/11/2026) va trobar, a més d'E1 (corregit a ad5d53d):
- el reenviament de la verificació era d'un sol ús, una restricció afegida a la implementació i marcada [A validar] a RN-M01-59;
- RN-M01-58 deia que «una petició limitada no compta», però el codi comptava per al límit d'origen les peticions limitades per destinatari;
- la resposta de «He oblidat la contrasenya» triga més quan l'adreça té un compte actiu (pocs mil·lisegons, mesurats en local el 03/11/2026);
- les pantalles de comptes no tenen cap full d'estil ni wireframe, i el límit diari dels correus (V-07) no té tasca.

Aplicar «no compta» al peu de la lletra obriria un canal per saber si una adreça té compte: des d'una IP, deu peticions per a l'adreça de la víctima i després una per a una bústia pròpia. Si l'adreça no té compte actiu, les deu compten i l'origen queda limitat. Si en té, només en compten tres (les enviades) i la bústia pròpia rep el correu. La resposta de la pàgina és la mateixa, però l'efecte en la petició següent revela l'existència del compte.

## Decisió
1. **Reenviament de la verificació.** S'elimina el límit d'un sol ús. Mentre dura l'estat de 10 minuts que deixa la contrasenya correcta d'un compte pendent, es poden demanar reenviaments. Es conserven: els límits de RN-M01-58 (per destinatari i per origen), el destinatari decidit pel servidor i la comprovació que el compte encara és pendent a cada petició.
2. **RN-M01-58: una petició limitada per destinatari compta per al límit d'origen.** Canvia el text de la regla (no és una lectura de «no compta»): una petició limitada per origen no envia res, no compta i no allarga cap finestra; una de limitada per destinatari no envia res ni compta per al límit del destinatari, però **sí per al d'origen**. Així el comptador d'origen avança igual tant si l'adreça té compte com si no. Qualsevol canvi futur (també la T-M01-39) ho ha de conservar i provar.
3. **Es descarta la RN-M01-62** (comptador de peticions rebudes per origen amb llindar 30) com a solució d'aquest canal: no el tanca.
4. **Tasques noves aprovades:**
   - **T-M01-38**, plantilla base, fulls d'estil i wireframes de les pantalles de comptes, a l'[addenda del M01](../planning.md#M01-addenda-066). La T-M01-07b i de la T-M01-13 a la T-M01-22 en depenen ([lectura de les tasques substituïdes](../planning.md#ajustos-060-lectura)). Les pendents de la T-M01-02 continuen a la T-M01-28.
   - **T-M00-06**, reserva, prioritat i límit diari dels correus (V-07), a les [peces de la 00](../planning.md#ajustos-060-peces-00), abans del nivell 1.
5. **Proposta, no aprovada: T-M01-39**, igualar la feina de la petició de «He oblidat la contrasenya» amb una cua. Té tres parts separades: la mesura abans i després, la implementació (només si s'aprova) i la decisió de si és condició del nivell 1, que es pren després de veure la mesura. El disseny és a l'[addenda](../planning.md#M01-addenda-066).

## Sobre les decisions de disseny 030 a 034 després de la 046
Per a la T-M01-38 s'apliquen la [030](030-sistema-de-disseny.md), la [031](031-estil-neumorfic-limitat.md), la [032](032-immersio-socis-i-centre.md) i la [034](034-patrons-magic-portfolio.md), amb aquestes lectures:
- **030:** vigents la paleta, els dos temes, els colors per zona, el groc només per a l'acció principal, els estats amb símbol, text i color, la tipografia, els punts de canvi i els logotips. `tokens.css` deixa de ser la font de veritat «mentre no hi hagi frontend»: n'hi ha, i la font passa a `static/css/` amb una sola còpia. Superats per la [046](046-interficie-django-htmx-servida-des-del-vps.md): «la pila del frontend no es decideix aquí» i «si es tria React i Tailwind». Les fonts s'allotgen al servidor (046 i [035](035-dades-nomes-dins-ue.md)); la llicència continua [A validar].
- **031:** en aquestes pantalles només afecta el selector de tema; formularis, avisos, botons i administració són plans.
- **032:** la portada d'immersió és de l'inici del compte personal (T-M01-16). D'aquí s'apliquen els avisos plans amb contrast ≥4,5:1, cap moviment amb «reduir moviment» i la capçalera sense barra lateral.
- **033:** descartada; no s'aplica.
- **034:** l'administració no es toca; als socis, els afinaments viuen a l'estil de cada pàgina i no a `tokens.css`.
- **046:** on diu «030 a 034» s'ha de llegir 030, 031, 032 i 034. El JavaScript del selector de tema va en un fitxer propi, no en línia.

## Conseqüències
- Addenda del M01: textos nous de RN-M01-58, RN-M01-59, CA-M01-50 i CA-M01-51; T-M01-38; T-M01-39 com a proposta.
- Codi i proves de la T-M01-05: el reenviament ja no consumeix l'estat; prova que el límit d'origen avança igual amb compte i sense.
- Pendents: [P-53](pendents.md) (si la T-M01-39 és condició del nivell 1, el retard màxim i què veu l'usuari).
- La T-M01-05 continua «Feta en part» fins a la revisió del responsable del projecte.

## Fonts
- Respostes del responsable del projecte, 04/11/2026, a la proposta de la revisió de la T-M01-05
- [065](065-enllacos-del-correu-i-restabliment-per-un-altre-administrador.md); diari de la [T-M01-05](../diari-de-construccio/T-M01-05.md)
- Documentació de Django 5.2: `SECURE_PROXY_SSL_HEADER`, `SECURE_SSL_REDIRECT`, `CSRF_TRUSTED_ORIGINS`, `HttpRequest.get_host()` (consultada el 04/11/2026)

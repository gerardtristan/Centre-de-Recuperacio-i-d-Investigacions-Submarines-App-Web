# Textos del mandat, de la invitació i del correu de confirmació: per aprovar a la junta

> **ESBORRANY. NO VIGENT. A VALIDAR: junta** (T-M05a-01; [097](../decisions/097-respostes-del-propietari-a-les-preguntes-obertes-del-18-11-2026.md), bloc C). La junta els aprova tots tres d'una vegada. Fins llavors, la signatura de mandats continua apagada a producció (`MANDATE_SIGNING_ENABLED`) i no es pot obrir cap campanya.
>
> Recull en un sol document els esborranys de [`mandat-sepa.md`](mandat-sepa.md) i [`invitacio-campanya-mandats.md`](invitacio-campanya-mandats.md) i el text provisional del correu G3 (`templates/emails/mandat-signat.ca.txt`). Quan la junta l'aprovi, el mandat i la invitació es publiquen com a textos legals versionats (T-M01-08), el correu G3 passa a la plantilla i aquells dos esborranys es retiren.

## Abans de la junta: l'identificador de creditor (banc)

Cal demanar-lo al banc del club (P-45, punt 5; resposta provisional de la [095](../decisions/095-respostes-del-propietari-a-les-preguntes-irreversibles-de-la-fase-1.md), P-24). És l'identificador SEPA del C.R.I.S. com a creditor, i surt al mandat, a la invitació i al correu G3.

- **Forma:** `ES` + 2 dígits de control + sufix de 3 caràcters (normalment `000`) + NIF del club. Exemple de la forma, inventat: `ES12000G00000000`.
- **Què cal demanar al banc:**
  1. L'identificador de creditor definitiu, per escrit.
  2. El sufix, si n'han de donar un altre que no sigui `000`.
  3. Si accepten el text del mandat d'aquest document o n'exigeixen un altre.
  4. Quants dies d'avís previ demanen com a mínim.
- **On va:** a la variable `SEPA_CREDITOR_IDENTIFIER` del servidor (no és un secret, però no es posa al codi).

## Què ha de decidir la junta

1. Aprova el text del mandat SEPA (text 1)?
2. **Dies d'avís previ** abans de cada càrrec. Ara és un ajust de 14 dies, que el tresorer pot canviar entre 14 i 30 (VC-16). El text 1 diu «com a mínim 14 dies».
3. **Nom legal i NIF del club** tal com han de sortir al mandat: «Centre de Recuperació i d'Investigacions Submarines (C.R.I.S.)» [A validar: junta].
4. Aprova el text de la invitació (text 2), amb l'avís del canvi de creditor?
5. Aprova el correu de confirmació del mandat, G3 (text 3)?

Si la junta canvia alguna paraula, es corregeix aquí i es torna a aprovar sencer.

---

## Text 1. Mandat SEPA (text legal `sepa_mandate`)

La pantalla del mandat ja mostra a part el creditor, l'identificador de creditor, el tipus (recurrent) i la referència del mandat. El text només porta l'autorització i els drets. Es basa en el text de referència del mandat SEPA Core de l'EPC [A validar: banc, que en pot exigir un altre].

> **Ordre de domiciliació SEPA (recurrent)**
>
> Mitjançant l'acceptació d'aquesta ordre de domiciliació, autoritzes el Centre de Recuperació i d'Investigacions Submarines (C.R.I.S.) a enviar instruccions a la teva entitat per carregar al teu compte la quota de soci de cada any, i la teva entitat a fer-ne els càrrecs segons aquestes instruccions.
>
> Com a part dels teus drets, pots demanar a la teva entitat la devolució d'un càrrec en els termes i les condicions del contracte que hi tens. La devolució s'ha de demanar dins de les vuit setmanes següents a la data del càrrec.
>
> Rebràs un avís com a mínim 14 dies abans de cada càrrec, amb l'import i la data. Pots revocar aquest mandat quan vulguis des de la plataforma; la revocació val per als càrrecs que es generin després.

## Text 2. Invitació de la campanya de mandats (text legal `mandate_campaign_invitation`)

Es publica com a text legal i és el cos del correu de la invitació. En confirmar l'enviament, el tresorer en veurà el text sencer a la pantalla de la campanya (P-306, tasca T-M05a-13d). El correu hi afegeix una salutació, l'enllaç personal per triar el mètode i «Si tens cap dubte, respon aquest correu». No porta cap dada personal ni bancària.

**Assumpte:** Com vols pagar la quota del C.R.I.S.?

> **Nova manera de pagar la quota**
>
> Fins ara, la quota de soci es cobrava per domiciliació a través de Cluber. Ara el club té una plataforma pròpia, i els rebuts de la quota els enviarà directament el C.R.I.S., amb l'identificador de creditor [identificador del banc].
>
> Els mandats signats a Cluber no passen a la plataforma. Perquè puguem continuar cobrant la quota, et demanem que triïs com la vols pagar:
>
> - **Domiciliació bancària:** signes un mandat SEPA nou a la plataforma, amb el teu IBAN. El pots revocar quan vulguis.
> - **Pagar cada vegada:** quan es generi la quota, la pagues amb targeta, Bizum o transferència.
>
> Si no tries res, quan es generi la quota la podràs pagar amb targeta, Bizum o transferència.

La frase «Els mandats signats a Cluber no passen a la plataforma» és l'avís del canvi de creditor (arquitectura §9.3; escenari B, decisió 022). Si Cluber cedís els mandats (P-21), aquesta frase canviaria [A validar: banc i Cluber].

## Text 3. Correu de confirmació del mandat (G3)

S'envia des de cris1954.cat, amb resposta a cris@cris.es ([019](../decisions/019-domini-i-correu.md)), quan el soci signa el mandat (CA-M05a-04, RN-M05a-07). Porta la referència, l'identificador de creditor, la data de signatura, com revocar-lo i l'IBAN emmascarat, mai sencer (RN-M05a-06). Entre claudàtors hi ha les dades que posa la plataforma, aquí amb un exemple inventat.

**Assumpte:** Mandat de domiciliació signat: [referència]

> Hola,
>
> Has signat el mandat de domiciliació SEPA de la quota de soci del C.R.I.S. el [18/11/2026].
>
> Referència del mandat: [CRIS000123M01]
> Identificador de creditor: [identificador del banc]
> Compte: [ES…1234]
> Tipus: recurrent (la quota de cada any)
>
> Rebràs un avís abans de cada càrrec. Pots revocar el mandat quan vulguis des de la plataforma:
>
> [enllaç]
>
> Si no has signat aquest mandat, respon aquest correu.

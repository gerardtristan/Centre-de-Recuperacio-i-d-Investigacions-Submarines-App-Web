# Fase 2: preguntes que esperen algú de fora del projecte

Respostes provisionals del propietari del 23/11/2026 ([105](../decisions/105-respostes-del-propietari-a-les-preguntes-per-al-pilot-del-23-11-2026.md)) i de la 104 que només falta confirmar per escrit. Ja estan construïdes així, però no s'encén res a producció fins a la confirmació. Cada pregunta continua oberta a [`pendents.md`](../decisions/pendents.md), on hi ha el detall. Es fa servir el mateix format que a [la fase 1](fase1-pendents-externs.md).

Abans d'enviar res: cap dada personal (ni noms de socis, ni IBAN, ni exportacions reals).

| Qui respon | Pregunta | Resposta provisional | Què queda apagat o pendent fins a la confirmació |
|---|---|---|---|
| Secretaria (amb la FECDAS) | P-444: quin model de fitxer vol la FECDAS per tramitar les llicències (columnes i ordre)? | Un CSV provisional (UTF-8, «;») amb cognoms, nom, data de naixement, tipus de llicència, categoria i inici; cap document ni dada de contacte. Quan la secretaria porti el model, es fa servir aquest (C) | La tramitació real a producció |
| Secretaria | P-446: una llicència «pendent de confirmar» compleix el requisit «llicència vigent» d'una activitat? | No. En mode d'avís, la persona s'inscriu i surt marcada; en mode de bloqueig, no s'hi pot inscriure | Obrir el 02 a producció |
| Junta | P-448: quines quotes de soci surten a la pàgina pública de llicències? | Tots els tipus de soci actius amb la seva quota vigent, de més barat a més car | La pàgina pública de llicències (apagada) |
| Junta | P-458: text de la casella «Soc major d'edat» dels convidats | La proposta, com a text legal editable | Cap versió publicada a producció: les inscripcions de convidats es rebutgen |
| Junta (i gestoria, per al termini) | P-486: a qui arriben els missatges de contacte de la web i quant temps es guarden | Tots a la Secretaria; els tancats s'esborren 6 mesos després (tots dos són ajustos) | El formulari de contacte (`website.contact_enabled`, apagat) |
| Gestoria (Q-14) | P-412: el termini de bloqueig de les dades personals dels registres econòmics | 6 anys, al codi (variable d'entorn), canviable només amb una decisió | L'anonimització d'aquests registres |
| Gestoria | P-425: quant temps es guarda la foto del carnet d'una titulació i amb quina base s'envia a la FECDAS | 3 mesos (ajust VC-57); la base és la petició del mateix soci (104) | Les fotos de titulacions (VC-56, apagat) |
| Junta i tresorer | P-426: el curs de primera estrella ja inclou la primera llicència? | Sí per defecte, configurable a cada versió de preu (104) | — |
| Tresorer | P-427: preu i departament de les tramitacions a la federació | Gratuïtes de moment (preu 0, VC-59 apagat) (104) | Cobrar les tramitacions |
| Assessor de protecció de dades | P-416: les notes de l'administració a l'exportació RGPD | Com s'ha construït | `GDPR_ADMIN_NOTES_EXPORT_ENABLED`, apagat a producció fins a la confirmació i el sí escrit del propietari |
| Assessor de protecció de dades | P-418: com es lliura l'exportació d'un menor de 14 anys | Fora de la plataforma; la plataforma només registra la petició | — |
| Assessor de protecció de dades | P-420: les referències dels pagaments d'una persona esborrada | Es queden en clar; només el nom i el document es bloquegen | El nivell 2 (revisió RGPD, H1) |
| Informàtica | P-474: l'extensió `btree_gist` a la base de dades de producció | Qui administra la base de dades l'activa a mà abans de migrar `equipment/0009` (checklist, A8) | El desplegament d'aquesta migració |

# 084. Adreça de l'avís del límit de correu

- **Data:** 11/11/2026
- **Estat:** Acceptada (responsable del projecte, 11/11/2026)
- **Completa:** la [081](081-respostes-del-responsable-als-25-punts-de-t-m00-i-t-m01.md), punt 21 (l'avís del 80 % només el rep l'administrador, a l'adreça configurada expressament).

## Decisió

L'adreça de l'administrador que rep l'avís del 80 % del límit diari de correu és **cris@cris.es**, la bústia del club. El responsable l'ha donada en majúscules; es desa en minúscules, que és com ja consta a la resta del projecte (resposta dels correus, decisió 019).

## Com queda configurat

- **Producció** (`config/settings/prod.py`): `EMAIL_ALERT_TO` val `cris@cris.es` si no es defineix la variable d'entorn. La variable la pot canviar sense tocar el codi (diverses adreces, separades per comes).
- **Desenvolupament i proves** (`config/settings/base.py`): cap adreça per defecte. Un avís de prova no surt mai cap a la bústia real; només queda al registre d'activitat.
- **CI:** el pas «Comprovació de desplegament» ja no defineix cap adreça de mostra: comprova la de producció. Si quedés buida, `core.W001` el faria fallar. Aquest pas no envia cap correu.

## Què no és

- **No és una posada en producció.** Encara no hi ha cap entorn de producció desplegat: aquesta decisió deixa el valor a la configuració que farà servir producció quan es desplegui aquest codi. A Coolify **no cal** definir `EMAIL_ALERT_TO`; només si es vol una altra adreça.
- No s'ha enviat cap correu real. Les proves fan servir la bústia de proves en memòria.

## Conseqüències

- **T-M00-06:** tots els criteris implementats i verificats; passa a «Feta». L'únic pas que queda és de desplegament, no de desenvolupament: quan hi hagi producció, comprovar que el primer avís arriba a la bústia.
- **Q-26:** resolta del tot (qui el rep i a quina adreça).
- Proves: `apps/core/tests/test_mail_limit.py` (configuració de producció carregada en un procés a part amb valors de mostra; l'avís va només a l'adreça configurada).

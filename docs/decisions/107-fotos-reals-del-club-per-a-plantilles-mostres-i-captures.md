# 107. Fotos reals del club per a plantilles, mostres i captures

- **Data:** 24/11/2026
- **Estat:** Acceptada (resposta E8 del propietari del 24/11/2026, a l'encàrrec [`docs/plans/editor-web-07.md`](../plans/editor-web-07.md)). És una excepció a una regla del [`CLAUDE.md`](../../CLAUDE.md); el propietari en va donar el «fusiona» per escrit (sí del 25/11/2026, donat el 27/11/2026: «Fusiona la #575»).
- **Completa:** la [106](106-editor-visual-de-la-web-publica.md) i l'[addenda de la 106 a M07](../planning.md#M07-addenda-106) (T-M07-31).

## Context

El `CLAUDE.md` diu «Mai dades reals de socis fora de producció: només dades inventades». Les plantilles de la web pública, les dades de mostra (`seed_demo_data`) i les captures necessiten fotos que mostrin el club de debò: immersions, fauna, cursos, batejos, projectes de medi ambient i vida del club. Moltes tenen persones.

El propietari ha confirmat per escrit (E8, 24/11/2026) que tothom qui surt a les fotos de la galeria del club i de https://cris.barcelona/, junta inclosa, ha signat el permís d'imatge, i que la gestoria ho permet.

## Decisió

**Excepció acotada** a la regla «mai dades reals de socis fora de producció»:

1. **Quines fotos:** només les de la galeria del club (els fitxers del Drive del club) i les publicades a https://cris.barcelona/, també les que tenen persones.
2. **Per a què:** les plantilles de pàgina i els patrons de la web pública, les dades de mostra i les captures (proves al navegador, diari i galeria de pantalles). Res més.
3. **Com:** reduïdes a 1.600 px pel costat llarg, sense EXIF ni GPS (comprovat amb un script que falla si en queda), amb «C.R.I.S.» com a autor i el permís marcat, i a `static/img/web/` amb noms descriptius sense noms de persones i un fitxer `fotos.yml` amb l'autor, el permís, si hi surten persones, el text alternatiu i l'origen. Mai els zips sencers ni els originals al repositori.
4. **Cap altra dada de socis:** cap nom, cognom, número, correu, document ni cap altra dada personal acompanya les fotos. Les dades de mostra continuen essent inventades.
5. **Socis que envien fotos:** encara no (E7 = A). Depèn de la P-41 (consentiment de les persones que surten a les fotos que pugen els socis).
6. **Retirada:** si algú que hi surt retira el permís, la foto es treu del repositori i de les plantilles en una PR pròpia, i es deixa constància al diari.

Ho fa la sessió de disseny (T-M07-31). El pilot carrega les fotos a la biblioteca de la web des de `seed_demo_data`.

## Conseqüències

- L'excepció no s'amplia per analogia: qualsevol altra dada real fora de producció necessita una decisió nova.
- Les captures amb persones identificables d'aquestes fotos compleixen la regla D11 del sistema de disseny («només amb consentiment»).
- Cap PR no passa de 25 MB d'imatges.

# 061 — Plataforma preparada per traduir-se, amb el català com a única llengua activa

- **Data:** 02/11/2026
- **Estat:** Acceptada. **Amplia** V-09 de la spec 00 (interfície en català) sense canviar-la: el català continua sent l'única llengua de la interfície. Quines llengües s'hi afegeixen i qui les tradueix: [P-49](pendents.md).

## Context
- El pla només diu «interfície i documents en català» ([planning.md, regles generals](../planning.md#idiomes)). La checklist (F7) diu «català i, si es decideix, castellà i anglès» per a la web pública, i el mapa de la plataforma té «[A validar quins idiomes]» a les pàgines del mòdul 07.
- Es parla de castellà, anglès, francès, basc i gallec, però ningú no ho ha decidit ni s'ha compromès a traduir.
- Preparar-ho ara és barat (poques plantilles, cap dada real); fer-ho quan hi hagi molts mòduls vol dir revisar totes les cadenes i canviar models amb dades.

## Decisió
1. **Llengua activa i de reserva: el català.** `LANGUAGE_CODE = "ca"` i `LANGUAGES` només amb el català fins que es resolgui P-49. Qualsevol petició, sigui quina sigui la capçalera `Accept-Language`, rep la interfície en català. No s'activa cap llengua sense les seves traduccions: els missatges propis de Django sortirien en aquella llengua i els de la plataforma en català.
2. **Configuració:** `LOCALE_PATHS = [BASE_DIR / "locale"]`, `LocaleMiddleware` just després de `SessionMiddleware` i abans de `CommonMiddleware`, el processador de context `i18n` i `<html lang>` amb la llengua activa.
3. **Text original en català.** Les cadenes es marquen amb el seu text català com a original (`gettext`, `gettext_lazy`, `{% translate %}`, `{% blocktranslate %}`); no es passen a l'anglès i no cal cap fitxer `ca.po`. Les traduccions es faran des del català.
4. **Regla de marcatge**, per a tot el codi des d'ara:
   - Es marca tot el que veu l'usuari: plantilles, etiquetes i ajudes de formularis, missatges de vistes i de serveis, errors de validació, `verbose_name` i etiquetes de `choices`.
   - `gettext_lazy` a nivell de mòdul o de classe; `gettext` dins de les funcions.
   - Mai f-strings ni `.format()` dins de `_()`: `_("… «%(kind)s».") % {"kind": kind}`. La regla `INT` de ruff ho comprova.
   - Cadenes amb un comptador: `ngettext` (o `{% blocktranslate count %}`), mai dues cadenes triades amb un `if`.
   - No es marquen els noms de codi, els identificadors ni les dades que escriuen els usuaris (noms de departament, conceptes, descripcions): el contingut traduït és cosa del mòdul 07 (punt 9).
5. **Llengua preferida de la persona:** `Person.preferred_language` (per defecte `"ca"`). És de la persona i no del compte, perquè també en té el convidat sense compte ([021](021-persones-no-socies-com-a-convidades.md)). Un sol servei, `persons.language_for(person)`, retorna la preferència si és una llengua activa i, si no, el català. El selector del perfil i el validador del camp arriben amb el formulari del perfil (T-M01-16) i només es mostren si hi ha més d'una llengua activa. En anonimitzar, el camp torna a `"ca"`.
6. **Textos legals:** `LegalText.language` (per defecte `"ca"`) i restricció única `(kind, version, language)`.
   - Una traducció **no és una versió nova**: és una fila més de la mateixa versió. Publicar en català crea la versió següent.
   - `current_text(kind, language)` retorna la traducció de la **versió vigent** si existeix i, si no, el català. Mai no dona per vigent una traducció d'una versió anterior.
   - `Consent` no té cap camp nou: la seva FK al text ja apunta a la fila exacta, és a dir, a la versió i a la llengua acceptades.
   - **Fora d'abast ara:** el servei per publicar traduccions i la regla de què passa si la persona accepta la mateixa versió en una altra llengua (evidència del consentiment: P-49, per a l'assessor de RGPD). Arriben amb la primera traducció real.
7. **Correus (T-M01-10):** una plantilla per llengua, `emails/<nom>.<llengua>.…`; es tria la de `language_for(persona)` i, si no existeix, la catalana. Es generen dins de `translation.override(llengua)` en posar-los a la cua, i el missatge guarda la llengua amb què s'ha generat. Mai no es fa servir `Accept-Language`: la cua no té petició.
8. **Rols:** la interfície mostra el nom del rol amb `get_code_display()` (traduïble); `Role.name` queda com a dada interna de la migració.
9. **Mòdul 07 i després:** pàgines i anuncis traduïts (`Pàgina.idioma` del mapa), URL amb prefix de llengua, `hreflang`, mapa del lloc, selector de llengua (vista `set_language` declarada pública i galeta segura), fitxers `.po` amb `makemessages` i `compilemessages`. La traducció del contingut que escriuen els usuaris (activitats, etc.) no es proposa: caldria una decisió pròpia.

## Conseqüències
- Tasca nova T-M01-09b al [pla del M01](../planning.md#M01-10-tasques), abans de la T-M01-10, en dos passos: configuració, camps i migració; marcatge de cadenes.
- La T-M01-10 tria la plantilla per llengua; la T-M01-16 hi afegeix el validador i el selector; la T-M01-22 torna la preferència a `"ca"` en anonimitzar.
- Activar una segona llengua demana: resoldre P-49, les eines GNU gettext al CI i a l'entorn de desenvolupament, els fitxers `.po` revisats i les plantilles de correu traduïdes. No demana canviar cap model ni cap servei.
- La checklist F7 enllaça aquesta decisió.

## Fonts
- Aprovació del responsable del projecte, 02/11/2026 (proposta de la decisió 061 i respostes 1 a 3)
- Spec 00, V-09; checklist F7; `design/mapa-plataforma.html` (Pàgina, Idioma)

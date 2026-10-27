# Integració amb Paylands (PaynoPain): resum de la documentació pública

- **Data de consulta:** 27/10/2026
- **Font:** documentació pública de Paylands (https://docs.paylands.com/en/). Només es recull el que hi consta; la resta porta [A verificar].
- **Per què:** és l'opció (a) de la [decisió 043](decisions/043-proveidor-de-pagaments-dins-la-ue.md), si CaixaGuissona confirma el TPV virtual [A verificar].

## 1. Entorns i autenticació
- **Proves (sandbox):** `https://api.paylands.com/v1/sandbox/`. Fa servir serveis i targetes de prova; no mou diners.
- **Producció:** `https://api.paylands.com/v1/`.
- Cada entorn té la seva **clau d'API**, que va a la capçalera `Authorization`, i els seus identificadors de servei, ordres i targetes.
- Un **servei** (`service`, UUID) correspon a un terminal o mètode configurat al compte. Bizum s'ha d'activar a cada terminal.
- Detall de l'autenticació i de com es calcula el camp `signature` de la petició: pàgina «Authentication» [A verificar: no s'ha llegit].

## 2. Crear l'ordre al servidor
1. El servidor de la plataforma fa `POST /v1/sandbox/payment` (o `/v1/payment` a producció) amb, entre d'altres:
   - `amount` (en cèntims; l'exemple fa servir `100`) [A verificar la unitat a la referència de l'API];
   - `operative`: `AUTHORIZATION` (cobrament normal) o `DEFERRED` (es confirma després);
   - `service` (UUID);
   - `customer_ext_id` (identificador del client a la plataforma: es farà servir un identificador intern, mai el DNI ni el correu);
   - `url_post` (notificació al servidor), `url_ok` i `url_ko` (retorn del navegador);
   - `description`, `reference`, `save_card`, `secure`, `expires_in` i `extra_data` (opcionals).
2. La resposta porta un objecte `order` amb un `token` i l'estat `CREATED`.
3. El navegador obre la pàgina de pagament `/payment/process/{token}`, **per redirecció o dins un `iframe`**. El soci hi escriu la targeta i, si cal, fa el 3D Secure amb el seu banc.
4. Quan acaba, el navegador va a `url_ok` o `url_ko`. **Aquesta tornada no canvia l'estat del càrrec**: només ho fa la notificació (punt 3).

Alternativa: SDK de tokenització (`https://api.paylands.com/js/v1-iframe.js`), un formulari de targeta dins un `iframe` del domini de Paylands. Segons la documentació, el comerç no intervé en la recollida ni en la custòdia de les dades de la targeta. L'abast PCI que en resulta és [A verificar amb PaynoPain].

## 3. Notificacions (webhooks) i validació
- Paylands envia la notificació a `url_post` amb l'objecte `order` actualitzat (`paid`, `status`), `client`, `extra_data` (si se'n va enviar), `validation_hash` i, en pagaments Bizum, el camp `bizum`.
- **Validació del hash:** es posen `order`, `client` i `extra_data` en un objecte, es codifica en JSON sense escapar Unicode ni barres (`JSON_UNESCAPED_UNICODE`, `JSON_UNESCAPED_SLASHES`), s'hi afegeix la credencial de signatura i es calcula SHA-256. Ha de coincidir amb `validation_hash`. Cal tenir en compte que `extra_data` pot no venir.
- **Llista d'IP:** Paylands recomana acceptar només les seves IP (es demanen a soporte@paylands.com). Proposta: hash **i** llista d'IP.
- **Ordres caducades:** cal demanar a suport que activi «Notify expired orders» per rebre una notificació quan una ordre passa a caducada.
- No consta: mètode HTTP, reintents ni resposta esperada [A verificar]. Per si de cas, la plataforma aplica les regles de l'arquitectura §4.2: desar l'esdeveniment, respondre de seguida, processar a la cua, idempotència per identificador de l'ordre i de la transacció, i una tasca diària de consulta d'ordres pendents (xarxa de seguretat) [A verificar que l'API permet consultar una ordre].

## 4. Bizum
- Mètode de Redsys, només a Espanya; s'ha d'activar a cada terminal.
- **Redirecció:** ordre amb `secure=true` i el servei de Bizum; el navegador obre `/payment/bizum/{token}`; el soci hi posa el telèfon i la clau de Bizum i confirma el codi per SMS; després va a `url_ok` o `url_ko` i el servidor rep la notificació (amb `source` nul).
- **Push (Request to Pay):** el telèfon va a `extra_data.profile.phone` en crear l'ordre; es crida l'endpoint de pagament push amb `"apm": "BIZUM"`; el soci accepta a l'app del seu banc. Si el dispositiu no pot rebre la sol·licitud, la resposta és un `303` amb una URL alternativa per pagar al navegador.
- **Caducitat:** amb `DEFERRED`, el pagament no confirmat caduca «després d'un temps que depèn del banc del client». No es dona cap xifra [A verificar]. Per a les quotes es farà servir `AUTHORIZATION`.
- **Proves:** telèfon `700000000` = correcte i `600000000` = rebutjat (redirecció), import entre 0,51 € i 15,00 €. En push, `+34700000000` i el resultat depèn de l'import.
- El comerç no rep el telèfon ni el nom del pagador.
- Devolucions de Bizum: no hi consten a la pàgina de Bizum [A verificar si `/payment/refund` les admet].

## 5. Devolucions
- `/payment/refund`: devolució **total o parcial** d'un pagament `AUTHORIZATION`, `PARTIAL_AUTHORIZATION` o `DEFERRED` (aquest últim, només un cop confirmat).
- Estats de l'ordre que hi consten: `CREATED`, `SUCCESS`, `REFUSED`, `REFUNDED`, `PARTIALLY_REFUNDED` i `EXPIRED`, entre d'altres.
- **No es fa servir `PARTIAL_AUTHORIZATION`**: cobra menys del que es demana si no hi ha saldo, i la spec 04 no admet pagaments parcials (QT-05).

## 6. Tokenització per a quotes recurrents
- Es pot guardar la targeta en el primer pagament (`save_card`) o amb l'SDK; la notificació porta la targeta a `source`.
- Per cobrar després cal l'`uuid` de la targeta (llista: `GET /v1/sandbox/customer/{customer_ext_id}/cards`).
- **Pagament directe** (`POST /payment/direct`, amb `order_uuid` i `card_uuid`): sense intervenció del soci; és el cas de les quotes recurrents.
- La documentació diu que una primera transacció amb 3DS genera un testimoni amb autenticació forta (SCA) que permet cobraments posteriors iniciats pel comerç sense tornar a autenticar. També hi ha una autorització de 0 € només per autenticar.
- Si l'antifrau demana 3DS en un pagament directe, la resposta porta una URL on el soci s'ha d'autenticar.
- Apple Pay i Google Pay generen «targetes dinàmiques» que no admeten pagaments tokenitzats amb 3DS.
- La plataforma guarda només l'`uuid` de la targeta i, per mostrar-la, els quatre darrers dígits i la caducitat si l'API els retorna [A verificar]. Mai el número.

## 7. Liquidació
- La documentació pública consultada **no explica** com arriba la liquidació al banc (agrupada o per operació, bruta o neta, amb quin detall de comissions) ni si hi ha un fitxer o un endpoint de liquidacions [A verificar amb PaynoPain i CaixaGuissona: P-45]. És el que necessita la tasca T13 de la spec 04.

## 8. Iniciació de transferència (PSD2)
- No consta a les pàgines consultades. Hi ha operatives `PAYOUT` i `TRANSFER`, però són per enviar diners, no per cobrar [A verificar si Paylands ofereix iniciació de pagaments PSD2].

## 9. Què falta per poder especificar el 05
- Càlcul del camp `signature` de la petició; mètode i reintents de les notificacions; consulta d'ordres; liquidacions; ubicació de les dades i subencarregats; contracte d'encarregat del tractament; tarifes. Tot és a la llista de preguntes P-45 de [pendents.md](decisions/pendents.md).

## Pàgines consultades
- https://docs.paylands.com/en/docs/integration/simple-integration/
- https://docs.paylands.com/en/docs/notification-validation/
- https://docs.paylands.com/en/docs/apm/apm-bizum/
- https://docs.paylands.com/en/docs/guides/guide-cards/
- https://docs.paylands.com/en/docs/guides/sdk-tokenization/
- https://docs.paylands.com/en/docs/api-usage/concepts/

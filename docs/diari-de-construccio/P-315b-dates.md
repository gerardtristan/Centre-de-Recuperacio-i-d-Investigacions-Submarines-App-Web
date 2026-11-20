# P-315b-dates · Proves amb una data calculada en carregar el fitxer

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 20/11/2026 00:37 | 1e08897c | 1 nova (separada d'una parametritzada); 2 ajustades | [A comprovar] |

**En tres línies:** el propietari va demanar tractar les proves que fallen de tant en tant com la P-315 ([T-DX-71](T-DX-71.md)), i el pilot va avisar que la #280 n'arregla una (`test_settlements.py::test_p_226`) que fallava a mitjanit perquè la data es calculava en carregar el fitxer. Aquí s'arreglen les altres tres que tenen el mateix patró i fallen quan es força la condició. `test_settlements.py` no es toca (és de la #280).

## Què s'ha fet
- `apps/members/tests/test_cluber_final_25b.py`: «demà» (una data de renovació que s'ha de rebutjar) surt d'una prova pròpia que la calcula en executar-se; abans era una constant del mòdul dins d'una prova parametritzada.
- `apps/payments/tests/test_receipts.py`: l'any del número de rebut (`R-AAAA-…`) es calcula a cada prova (`year()`).
- `apps/payments/tests/test_principi_a_fi.py`: «avui» (extractes, liquidació, saldos i any del rebut) es calcula a cada prova (`today()`).

## Decisions i perquè
- **La causa.** Una constant com `TODAY = timezone.localdate()` es calcula una sola vegada, quan pytest carrega el fitxer. El CI tarda uns deu minuts: si la mitjanit cau entre la càrrega i la prova, la prova fa servir la data d'ahir i l'aplicació la d'avui. «Demà» passa a ser avui (i la data ja no es rebutja), i el cap d'any canvia l'any dels rebuts.
- **Com s'ha reproduït.** Un connector local de pytest (no és al repositori) avança el rellotge de Django (`timezone.now`) un cop recollides les proves, com si hagués passat la mitjanit. Abans de l'arreglo: amb +1 dia falla la de «demà»; amb el salt a l'1 de gener fallen 3 de `test_principi_a_fi` i 4 de `test_receipts`. Després, cap.
- **Les altres constants de data no fallen amb el rellotge avançat** i no s'han tocat: `test_birth_date_check_081.py` (només fa servir l'any per a una edat amb marge), `test_route_permissions.py` i `test_campaign_final_reminder.py` (passen amb +1 dia i amb el cap d'any).
- **Cap prova saltada, sense reintents ni temps més llargs.**

## Problemes trobats
- Cap més. La recerca de proves inestables és al diari de la [P-315b-carnet](P-315b-carnet.md).

## Com se sap que funciona
- Els tres fitxers i `test_rebut_anullat.py` (que importa de `test_receipts`): 41 passen; també amb el rellotge avançat un dia i amb el salt a l'1 de gener.
- Ruff net.

## Evidències
- Sortida de proves · commit 1e08897c · executada el 20/11/2026 en local (PostgreSQL 16):
  ```
  $ pytest apps/members/tests/test_cluber_final_25b.py apps/payments/tests/test_principi_a_fi.py apps/payments/tests/test_receipts.py apps/payments/tests/test_rebut_anullat.py -q
  41 passed
  ```

## Comprovació §15.5
- Cap pantalla tocada: no calen captures ni axe.

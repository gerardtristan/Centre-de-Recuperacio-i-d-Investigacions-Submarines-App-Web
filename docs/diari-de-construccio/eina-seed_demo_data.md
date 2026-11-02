# Eina · Dades inventades per a captures (`seed_demo_data`)

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 02/11/2026 14:04 – 14:07 | e69793d (origen), 942b752 (ordre) | 722 | [A comprovar] |

No és una tasca del pla: és una eina per fer captures i demostracions sense dades reals.

**En tres línies:** una ordre omple una base de dades local i buida amb persones, consentiments i càrrecs inventats. Amb la mateixa llavor surten sempre les mateixes dades, i així les captures es poden repetir. En producció, o amb una base de dades remota o que ja tingui dades, es nega a funcionar.

## Què s'ha fet
- 12 persones fictícies (cognoms de fauna marina, correus `@example.org`, passaports `PROVA0001`…), textos legals de prova, consentiments atorgats i retirats, un departament de prova i càrrecs pendents, pagats i anul·lats.
- Tot es crea amb els serveis de la 00, de manera que el registre d'activitat queda com quedaria de debò.
- El compte `admin-demo` té el rol administrador, però no té contrasenya ni TOTP: no és operatiu fins que algú li posa contrasenya i dona d'alta el TOTP des del navegador.
- `grant_initial_administrator` rep l'origen, i el registre diu quina ordre ha creat l'administrador.

Com s'executa: [`README.md` del projecte](../../README.md).

## Decisions i perquè
- **Sense Faker:** la seva sortida canvia d'una versió a una altra i genera noms i documents realistes, que podrien coincidir amb persones reals. Unes llistes fixes i una llavor ho fan sense cap dependència nova.
- **Cap secret conegut:** l'ordre no crea ni mostra cap contrasenya, secret ni QR. El secret del TOTP el genera la pantalla d'alta i només el coneix el mòbil de qui el dona d'alta.
- **Un sol administrador:** la plataforma avisa que hi ha menys de dos administradors operatius. És el comportament real, i a les captures s'explica.
- **Cap compte personal, de moment:** un compte personal queda pendent fins que es confirma el correu, i el correu arriba amb la T-M01-10. Activar-lo directament se saltaria aquesta regla.

## Problemes trobats
- `grant_initial_administrator` creava el rol abans de validar l'origen de l'actor. Amb un origen buit, el rol quedava creat sense cap entrada al registre d'activitat. Ara l'actor es valida primer, i una prova ho comprova.

## Com se sap que funciona
- `test_seed_demo_data.py`: es nega amb la configuració de producció, sense `DEBUG`, amb un servidor de base de dades no local o amb dades; la mateixa llavor dona les mateixes persones; només dades inventades; l'administrador té el rol però no és operatiu; la sortida no té cap secret.
- `test_roles.py`: el registre guarda l'origen; dues crides donen un sol rol; un origen buit no crea cap rol.
- Prova manual del 02/11/2026: dues bases de dades noves amb la llavor 1954 donen les mateixes persones, i les quatre negatives s'aturen amb el seu missatge.

## Evidències
- Sortida de proves · commit 942b752 · executada el 02/11/2026 en local (PostgreSQL 16):
  ```
  $ pytest -q
  722 passed
  $ pytest -q apps/core/tests/test_seed_demo_data.py
  12 passed
  ```
- `apps/core/roles.py · commit e69793d · 02/11/2026`
  ```python
  # Abans de crear el rol: un origen buit no ha de deixar un rol sense registre.
  actor = audit.system(origin)
  ```

## Termes nous
- **Llavor** (*seed*): número inicial que fa que una sèrie «aleatòria» surti sempre igual.
- **Dades de demostració** (*demo data*): dades inventades per ensenyar l'aplicació sense fer servir dades reals.
- **Faker**: biblioteca de Python que inventa noms, adreces i documents realistes.
- **Ordre de gestió** (*management command*): programa que s'executa amb `python manage.py …`.

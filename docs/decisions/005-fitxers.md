# 005 — Fitxers a Scaleway Object Storage

- **Data:** 27/10/2026
- **Estat:** Acceptada

## Context
La plataforma guarda factures de despesa (obligatòries), justificants, certificats, fotos de sortides ambientals, fotos de perfil (amb consentiment) i PDF generats (carnet, rebuts). Han de ser privats i visibles només per als rols que toca.

## Alternatives
- Disc del mateix VPS: gratuït, però barreja dades i servidor i complica les còpies i la migració.
- Emmagatzematge d'objectes de proveïdors no europeus: transferència internacional.
- Scaleway Object Storage (França, regió París), compatible amb l'API S3.

## Decisió
- Scaleway Object Storage a París, amb buckets privats.
- Accés només amb URL signades de curta durada, generades per l'API després de comprovar rol i objecte.
- Tipus i mida de fitxer limitats (checklist C10).
- Buckets separats per entorn; cap fitxer real fora de producció.

## Conseqüències
- Cost molt baix per al volum previst (uns 0,0146 €/GB/mes en classe Standard Multi-AZ segons la pàgina oficial consultada el 27/10/2026; [A validar] la classe i la regió definitives).
- Via de sortida: API S3 estàndard; es pot migrar a qualsevol proveïdor compatible amb una sincronització (rclone).
- Els fitxers també entren a les còpies creuades ([006](006-copies-de-seguretat.md)).

## Fonts
- Encàrrec d'arquitectura del 26/10/2026
- `docs/checklist-produccio.md`, C10 i D1
- `docs/funcionalitats-processos/funcionalitats-processos.pdf`, §2 «Documents adjunts» i §7

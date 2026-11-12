// Generat per comprova.py --write a partir de recorreguts.json. No l'editis a mà.
window.RECORREGUTS = {
  "titol": "Recorreguts del mòdul 01 (Socis i carnet digital)",
  "avis": "Prototip de disseny, no és l'aplicació real",
  "font": "Processos P-M01-A a P-M01-G de docs/planning.md (#M01-5-processos), amb les precisions de les decisions 071, 073, 074 i 079. Cada pas enllaça el wireframe original; aquí no se'n duplica ni se'n modifica cap.",
  "distintius": {
    "sense-wireframe": "Sense wireframe",
    "aplicacio-difereix": "L'aplicació difereix",
    "wireframe-sense-implementar": "Wireframe sense implementar"
  },
  "recorreguts": [
    {
      "id": "P-M01-A",
      "titol": "Alta de soci",
      "passos": [
        {
          "pas": "1",
          "actor": "Visitant",
          "permisos": [
            "P1"
          ],
          "que": "Obre «Fer-se soci» des de la web pública.",
          "pantalla": "/fer-se-soci",
          "wireframes": [
            {
              "fitxer": "publica.html",
              "ancora": "fer-se-soci"
            },
            {
              "fitxer": "publica.html",
              "ancora": "alta"
            }
          ],
          "tasca": "T-M01-13"
        },
        {
          "pas": "2",
          "actor": "Visitant",
          "permisos": [
            "P1"
          ],
          "que": "Omple les dades mínimes, tria el tipus i accepta els textos legals obligatoris. Sense mandat SEPA (és del 05a).",
          "pantalla": "/fer-se-soci",
          "wireframes": [
            {
              "fitxer": "publica.html",
              "ancora": "alta"
            }
          ],
          "tasca": "T-M01-13"
        },
        {
          "pas": "3",
          "actor": "Sistema",
          "permisos": [],
          "que": "Comprova duplicats, desa la sol·licitud «pendent de revisió» i els consentiments, i envia el correu de rebut.",
          "pantalla": "",
          "wireframes": [],
          "tasca": "T-M01-13"
        },
        {
          "pas": "3b",
          "actor": "Secretaria",
          "permisos": [
            "P2"
          ],
          "que": "Alta presencial: omple el mateix formulari des de l'administració; el consentiment es registra com a presencial.",
          "pantalla": "/gestio/socis/altes/nova",
          "wireframes": [
            {
              "fitxer": "admin.html",
              "ancora": "vista-socis-alta",
              "rol": "secretaria"
            }
          ],
          "tasca": "T-M01-13"
        },
        {
          "pas": "4",
          "actor": "Secretaria",
          "permisos": [
            "P3a"
          ],
          "que": "Revisa la sol·licitud a «Altes pendents» i veu l'avís de possible duplicat.",
          "pantalla": "/gestio/socis/altes",
          "wireframes": [
            {
              "fitxer": "admin.html",
              "ancora": "vista-socis-sollicituds",
              "rol": "secretaria"
            }
          ],
          "tasca": "T-M01-14"
        },
        {
          "pas": "5a",
          "actor": "Secretaria",
          "permisos": [
            "P3a",
            "P3"
          ],
          "que": "Aprova: es crea el soci (pendent), s'assigna el número, es crea la quota i s'envia la invitació del compte personal.",
          "pantalla": "/gestio/socis/altes",
          "wireframes": [
            {
              "fitxer": "admin.html",
              "ancora": "vista-socis-sollicituds",
              "rol": "secretaria"
            }
          ],
          "tasca": "T-M01-14"
        },
        {
          "pas": "5b",
          "actor": "Secretaria",
          "permisos": [
            "P3a",
            "P3"
          ],
          "que": "Rebutja amb motiu: no es crea cap soci ni es consumeix cap número, i s'avisa la persona.",
          "pantalla": "/gestio/socis/altes",
          "wireframes": [
            {
              "fitxer": "admin.html",
              "ancora": "vista-socis-sollicituds",
              "rol": "secretaria"
            }
          ],
          "tasca": "T-M01-14"
        },
        {
          "pas": "6",
          "actor": "Soci",
          "permisos": [
            "P13"
          ],
          "que": "Activa el compte personal i veu la quota pendent.",
          "pantalla": "/socis",
          "wireframes": [
            {
              "fitxer": "socis.html",
              "ancora": "franja-estat"
            }
          ],
          "tasca": "T-M01-16",
          "nota": "El botó «Paga ara» del wireframe és del 05b."
        },
        {
          "pas": "7",
          "actor": "Sistema",
          "permisos": [],
          "que": "Quan la quota passa a «pagat», el soci passa a actiu i es genera el carnet.",
          "pantalla": "",
          "wireframes": [],
          "tasca": "T-M01-26"
        },
        {
          "pas": "8",
          "actor": "Soci",
          "permisos": [
            "P13"
          ],
          "que": "Veu el carnet.",
          "pantalla": "/socis/carnet",
          "wireframes": [
            {
              "fitxer": "socis.html",
              "ancora": "carnet"
            }
          ],
          "tasca": "T-M01-19"
        }
      ]
    },
    {
      "id": "P-M01-B",
      "titol": "Canvi de tipus",
      "passos": [
        {
          "pas": "1",
          "actor": "Soci (simpatitzant actiu)",
          "permisos": [
            "P14"
          ],
          "que": "Obre «Canvi a ple dret», veu l'import del suplement i envia la sol·licitud.",
          "pantalla": "/socis/canvi-tipus",
          "wireframes": [
            {
              "fitxer": "socis.html",
              "ancora": "canvi-tipus"
            }
          ],
          "tasca": "T-M01-17",
          "distintiu": "aplicacio-difereix",
          "nota": "El wireframe diu «Import pendent de determinar per la secretaria»; l'aplicació mostra l'import calculat, la diferència entre les dues quotes (072, Q-049)."
        },
        {
          "pas": "2",
          "actor": "Sistema",
          "permisos": [],
          "que": "Desa la sol·licitud pendent. El càrrec del suplement es crea en aprovar-la, no en demanar-la (074, RN-M01-76).",
          "pantalla": "",
          "wireframes": [],
          "tasca": "T-M01-17"
        },
        {
          "pas": "3",
          "actor": "Secretaria",
          "permisos": [
            "P3a",
            "P7"
          ],
          "que": "Aprova la sol·licitud (es crea el suplement, que venç una setmana després) o la rebutja amb motiu.",
          "pantalla": "/gestio/socis/sollicituds",
          "wireframes": [
            {
              "fitxer": "admin.html",
              "ancora": "vista-socis-sollicituds",
              "rol": "secretaria"
            }
          ],
          "tasca": "T-M01-17"
        },
        {
          "pas": "4",
          "actor": "Sistema",
          "permisos": [],
          "que": "Quan el suplement es paga, canvia el tipus amb data efectiva, ho desa a l'historial, revoca el carnet anterior i n'emet un de nou.",
          "pantalla": "",
          "wireframes": [],
          "tasca": "T-M01-17"
        },
        {
          "pas": "5",
          "actor": "Soci (de ple dret actiu)",
          "permisos": [
            "P14"
          ],
          "que": "Demana el pas a simpatitzant: veu que s'aplica a la renovació següent i que no hi ha cap devolució. Mentre és pendent, el pot retirar (073; RN-M01-93).",
          "pantalla": "/socis/canvi-tipus",
          "wireframes": [
            {
              "fitxer": "socis.html",
              "ancora": "canvi-tipus"
            }
          ],
          "tasca": "T-M01-42",
          "distintiu": "aplicacio-difereix",
          "nota": "El wireframe diu «El canvi de ple dret a simpatitzant no es pot demanar ara»; l'aplicació té la sol·licitud i la retirada (073 i 079)."
        },
        {
          "pas": "6",
          "actor": "Secretaria",
          "permisos": [
            "P3a",
            "P7"
          ],
          "que": "Accepta o rebutja el pas a simpatitzant. Acceptar-lo no canvia el tipus ni crea cap càrrec.",
          "pantalla": "/gestio/socis/sollicituds",
          "wireframes": [
            {
              "fitxer": "admin.html",
              "ancora": "vista-socis-sollicituds",
              "rol": "secretaria"
            }
          ],
          "tasca": "T-M01-42"
        },
        {
          "pas": "7",
          "actor": "Sistema",
          "permisos": [],
          "que": "Avisa un mes abans de la renovació i, en renovar, canvia el tipus (bloquejada pels punts 1, 5 i 7 de la 073).",
          "pantalla": "",
          "wireframes": [],
          "tasca": "T-M01-43"
        }
      ]
    },
    {
      "id": "P-M01-C",
      "titol": "Baixa",
      "passos": [
        {
          "pas": "1",
          "actor": "Soci",
          "permisos": [
            "P14"
          ],
          "que": "Demana la baixa amb motiu i confirmació.",
          "pantalla": "/socis/baixa",
          "wireframes": [
            {
              "fitxer": "socis.html",
              "ancora": "baixa"
            }
          ],
          "tasca": "T-M01-17"
        },
        {
          "pas": "1b",
          "actor": "Secretaria",
          "permisos": [
            "P7",
            "P4"
          ],
          "que": "Crea una baixa per decisió de la junta, amb motiu.",
          "pantalla": "/gestio/socis/{id}/baixa/nova",
          "wireframes": [
            {
              "fitxer": "admin.html",
              "ancora": "vista-socis-fitxa",
              "rol": "secretaria"
            }
          ],
          "tasca": "T-M01-17"
        },
        {
          "pas": "2",
          "actor": "Secretaria",
          "permisos": [
            "P3a",
            "P7"
          ],
          "que": "La valida i en fixa la data efectiva (si és futura, queda programada), o la rebutja amb motiu.",
          "pantalla": "/gestio/socis/sollicituds",
          "wireframes": [
            {
              "fitxer": "admin.html",
              "ancora": "vista-socis-sollicituds",
              "rol": "secretaria"
            }
          ],
          "tasca": "T-M01-17"
        },
        {
          "pas": "3",
          "actor": "Sistema",
          "permisos": [],
          "que": "A la data efectiva: estat «baixa», carnet revocat, quotes de la RN-M01-20 i correu de confirmació.",
          "pantalla": "",
          "wireframes": [],
          "tasca": "T-M01-17"
        },
        {
          "pas": "4",
          "actor": "Sistema",
          "permisos": [],
          "que": "El compte personal es manté per consultar rebuts.",
          "pantalla": "",
          "wireframes": [],
          "tasca": "T-M01-17"
        }
      ]
    },
    {
      "id": "P-M01-D",
      "titol": "Renovació anual de quotes",
      "passos": [
        {
          "pas": "1",
          "actor": "Tresorer",
          "permisos": [
            "P8"
          ],
          "que": "Tria el període i veu una previsualització: quants socis, quantes quotes de cada tipus i l'import total.",
          "pantalla": "/gestio/quotes",
          "wireframes": [
            {
              "fitxer": "admin.html",
              "ancora": "vista-socis-quotes",
              "rol": "tresorer"
            }
          ],
          "tasca": "T-M01-18",
          "distintiu": "aplicacio-difereix",
          "nota": "L'aplicació no té previsualització ni generació per període: la quota de renovació de cada soci es genera sola el dia del primer recordatori (070; CA-M01-10 precisat per la 079)."
        },
        {
          "pas": "2",
          "actor": "Tresorer",
          "permisos": [
            "P8"
          ],
          "que": "Confirma: es crea una quota per soci actiu o impagat, al departament «General / Quotes de socis».",
          "pantalla": "/gestio/quotes",
          "wireframes": [
            {
              "fitxer": "admin.html",
              "ancora": "vista-socis-quotes",
              "rol": "tresorer"
            }
          ],
          "tasca": "T-M01-18",
          "distintiu": "aplicacio-difereix",
          "nota": "Com el pas 1: a l'aplicació la generació és automàtica i per soci."
        },
        {
          "pas": "3",
          "actor": "Sistema",
          "permisos": [],
          "que": "Envia l'avís de quota nova al soci (correu i safata d'avisos de l'app).",
          "pantalla": "",
          "wireframes": [
            {
              "fitxer": "socis.html",
              "ancora": "avisos"
            }
          ],
          "tasca": "T-M01-18",
          "distintiu": "wireframe-sense-implementar",
          "nota": "L'àrea del soci de l'aplicació encara no té safata d'avisos."
        },
        {
          "pas": "4",
          "actor": "Sistema",
          "permisos": [],
          "que": "Envia recordatoris abans i després del venciment (RN-M01-14).",
          "pantalla": "",
          "wireframes": [],
          "tasca": "T-M01-18"
        },
        {
          "pas": "5",
          "actor": "Tresorer",
          "permisos": [
            "P10",
            "P9"
          ],
          "que": "Revisa les quotes pendents i marca impagat a mà, amb motiu (040).",
          "pantalla": "/gestio/quotes",
          "wireframes": [
            {
              "fitxer": "admin.html",
              "ancora": "vista-socis-quotes",
              "rol": "tresorer"
            }
          ],
          "tasca": "T-M01-18"
        },
        {
          "pas": "6",
          "actor": "Sistema",
          "permisos": [],
          "que": "Quan una quota es paga, avisa per correu qui pot editar les quotes perquè desmarqui l'impagat.",
          "pantalla": "",
          "wireframes": [],
          "tasca": "T-M01-18"
        }
      ]
    },
    {
      "id": "P-M01-E",
      "titol": "Carnet i verificació pública",
      "passos": [
        {
          "pas": "1",
          "actor": "Sistema",
          "permisos": [],
          "que": "En passar a actiu (o en un canvi de tipus), genera el carnet; el QR porta l'URL de verificació.",
          "pantalla": "",
          "wireframes": [],
          "tasca": "T-M01-19"
        },
        {
          "pas": "2",
          "actor": "Soci",
          "permisos": [
            "P13"
          ],
          "que": "Veu el carnet i el pot desar com a PDF des del navegador (079). La web instal·lable el guarda per veure'l sense cobertura.",
          "pantalla": "/socis/carnet",
          "wireframes": [
            {
              "fitxer": "socis.html",
              "ancora": "carnet"
            }
          ],
          "tasca": "T-M01-19"
        },
        {
          "pas": "3",
          "actor": "Qualsevol persona",
          "permisos": [
            "P15"
          ],
          "que": "Escaneja el QR i obre la pàgina de verificació.",
          "pantalla": "/carnet/verificar/{testimoni}",
          "wireframes": [
            {
              "fitxer": "publica.html",
              "ancora": "verificar"
            }
          ],
          "tasca": "T-M01-20"
        },
        {
          "pas": "4",
          "actor": "Sistema",
          "permisos": [],
          "que": "Mostra «Vàlid» o «No vàlid» i el número de soci parcial. Res més.",
          "pantalla": "",
          "wireframes": [],
          "tasca": "T-M01-20"
        }
      ]
    },
    {
      "id": "P-M01-F",
      "titol": "RGPD: exportar i esborrar",
      "passos": [
        {
          "pas": "1",
          "actor": "Soci",
          "permisos": [
            "P16"
          ],
          "que": "Demana «Descarregar les meves dades».",
          "pantalla": "/socis/perfil",
          "wireframes": [
            {
              "fitxer": "socis.html",
              "ancora": "perfil"
            }
          ],
          "tasca": "T-M01-22",
          "distintiu": "wireframe-sense-implementar",
          "nota": "El perfil de l'aplicació encara no té l'exportació de dades."
        },
        {
          "pas": "2",
          "actor": "Sistema",
          "permisos": [],
          "que": "Prepara un fitxer JSON amb les dades de la persona; URL signada, disponible 7 dies.",
          "pantalla": "",
          "wireframes": [],
          "tasca": "T-M01-22"
        },
        {
          "pas": "3",
          "actor": "Soci",
          "permisos": [
            "P16"
          ],
          "que": "Demana «Esborrar el meu compte»: marca la confirmació i torna a escriure la contrasenya (i el codi TOTP si en té).",
          "pantalla": "/socis/perfil/esborrar",
          "wireframes": [
            {
              "fitxer": "socis.html",
              "ancora": "esborrar"
            }
          ],
          "tasca": "T-M01-22"
        },
        {
          "pas": "4",
          "actor": "Responsable RGPD",
          "permisos": [
            "M11"
          ],
          "que": "Aprova la sol·licitud.",
          "pantalla": "/gestio/rgpd",
          "wireframes": [],
          "tasca": "T-M01-22",
          "distintiu": "sense-wireframe",
          "nota": "Fora de la T-M01-02: és una peça de la 00 i l'atén l'administrador."
        },
        {
          "pas": "5",
          "actor": "Sistema",
          "permisos": [],
          "que": "Fa la baixa si és soci actiu, desactiva els comptes, anonimitza les dades personals i bloqueja quotes i rebuts fins al termini legal.",
          "pantalla": "",
          "wireframes": [],
          "tasca": "T-M01-22"
        }
      ]
    },
    {
      "id": "P-M01-G",
      "titol": "Importació de Cluber, en dues fases",
      "passos": [
        {
          "pas": "1",
          "actor": "Administrador",
          "permisos": [
            "P18"
          ],
          "que": "Fase de prova: puja l'exportació de Cluber (fitxer inventat o anonimitzat fora de producció).",
          "pantalla": "/gestio/importacions/cluber",
          "wireframes": [
            {
              "fitxer": "admin.html",
              "ancora": "vista-socis-cluber",
              "rol": "admin"
            }
          ],
          "tasca": "T-M01-24"
        },
        {
          "pas": "2",
          "actor": "Sistema",
          "permisos": [],
          "que": "Descarta la columna d'IBAN en llegir (071), valida cada línia i fa coincidir per document o número de soci.",
          "pantalla": "",
          "wireframes": [],
          "tasca": "T-M01-24b"
        },
        {
          "pas": "3",
          "actor": "Administrador",
          "permisos": [
            "P18"
          ],
          "que": "Veu el resum: nous, coincidents, errors per línia i el que es crearia. No s'escriu res.",
          "pantalla": "/gestio/importacions/cluber",
          "wireframes": [
            {
              "fitxer": "admin.html",
              "ancora": "vista-socis-cluber",
              "rol": "admin"
            }
          ],
          "tasca": "T-M01-24"
        },
        {
          "pas": "4",
          "actor": "Administrador",
          "permisos": [
            "P18"
          ],
          "que": "Fase final: torna a pujar l'exportació definitiva i la confirma, excloent les línies amb error.",
          "pantalla": "/gestio/importacions/cluber",
          "wireframes": [
            {
              "fitxer": "admin.html",
              "ancora": "vista-socis-cluber",
              "rol": "admin"
            }
          ],
          "tasca": "T-M01-25",
          "distintiu": "wireframe-sense-implementar",
          "nota": "El wireframe té «Importa definitivament»; l'aplicació diu «La importació final encara no està disponible» (servei preparat i bloquejat per configuració)."
        },
        {
          "pas": "5",
          "actor": "Sistema",
          "permisos": [],
          "que": "Crea persones i socis amb el número de Cluber, la data d'alta i l'estat. Tot porta l'identificador del lot.",
          "pantalla": "",
          "wireframes": [],
          "tasca": "T-M01-25"
        },
        {
          "pas": "6",
          "actor": "Sistema",
          "permisos": [],
          "que": "Prepara la campanya de mandats nous del 05a: cap IBAN importat.",
          "pantalla": "",
          "wireframes": [],
          "tasca": "T-M05a-13"
        },
        {
          "pas": "7",
          "actor": "Administrador",
          "permisos": [
            "P18"
          ],
          "que": "Pot desfer el lot si encara no s'ha creat res a partir d'ell.",
          "pantalla": "/gestio/importacions/cluber",
          "wireframes": [
            {
              "fitxer": "admin.html",
              "ancora": "vista-socis-cluber",
              "rol": "admin"
            }
          ],
          "tasca": "T-M01-25",
          "distintiu": "wireframe-sense-implementar",
          "nota": "El wireframe té «Desfés el lot»; a l'aplicació, desfer encara no existeix."
        }
      ]
    }
  ]
};

**Audit technique de pymdtools — 26 septembre 2026**

**Mise en œuvre des recommandations**

Les constats de l'audit initial sont conservés ci-dessous comme historique. Les
sources ont depuis été modernisées : adaptateur CommonMark partagé et positions
source, protection des directives dans le code, normalisation conservatrice,
encodage fidèle des chemins, moteur PDF Chromium optionnel, typage distribué,
métadonnées centralisées, environnements verrouillés et contrôles CI renforcés.
La traduction dispose d'un client injectable avec cache borné et reprises, ainsi
que d'un mode paragraphe optionnel avec vérification des marqueurs de formatage.

La suite finale compte 736 tests réussis et 9 ignorés, avec 100 % de couverture
des instructions et des branches. Le test Chromium opt-in passe séparément ;
les huit autres exclusions concernent les liens symboliques et permissions POSIX.
Le benchmark de 2 000 blocs descend de 14,731 s à environ 0,26 s sur cette machine.
Le rendu PDF réel a été testé et inspecté visuellement. Ruff, Pyright strict,
Sphinx sans avertissement, construction isolée, contrôle Twine et installation
fonctionnelle de la wheel ont été vérifiés. L'interface installée obtient 100 %
à `pyright --verifytypes --ignoreexternal` ; cela ne signifie pas l'absence de
`Any` dans les adaptateurs. L'audit des dépendances verrouillées ne signale aucune
vulnérabilité connue à la date de vérification.

Voir [CHANGELOG.md](CHANGELOG.md) pour les changements de comportement et
[CONTRIBUTING.md](CONTRIBUTING.md) pour reproduire la validation. La validation
locale est réalisée sous Windows/Python 3.14.7 ; les jobs Linux/macOS et les autres
versions Python sont configurés dans la CI, mais n'ont pas été exécutés à distance.
La qualité linguistique du mode paragraphe reste à évaluer avec le prestataire
retenu : aucun texte n'a été envoyé au service de traduction pendant ces travaux.
Les protections GitHub/PyPI restent des paramètres externes à vérifier avant une
publication.

**Constats avant modifications**

Version examinée : `2.0.47`, commit `a82e846`. Analyse du code, de la configuration, des tests et des distributions, complétée par des reproductions locales et la consultation des documentations officielles.

Le projet possède une base de maintenance solide : tests nombreux, annotations, écritures atomiques, contrôles des chemins, documentation et publication automatisée. Pour atteindre un niveau de référence, les principaux chantiers sont la fidélité des transformations Markdown, le remplacement du moteur PDF et les performances de l'analyse syntaxique. La couverture actuelle de 100 % ne détecte pas les défauts fonctionnels reproduits ci-dessous.

Les fichiers sources et configurations existants n'ont pas été modifiés. Un environnement `.venv` a été créé pour l'audit. Les distributions et le résultat de l'audit des dépendances sont conservés sous `.venv/audit/`, répertoire ignoré par Git.

Les vérifications ont été réalisées sous Windows avec Python 3.14.7 et les dépendances résolues le jour de l'audit. La matrice distante GitHub Actions et les protections des environnements GitHub/PyPI n'ont pas été exécutées ou vérifiées depuis cet audit.

| Vérification | Résultat |
| --- | --- |
| `python -m pytest` | 660 réussis, 8 ignorés, 9,78 s |
| Couverture configurée | 100 % : 2 238 instructions et 770 branches |
| Tests ignorés | 7 tests nécessitant des liens symboliques indisponibles ici ; 1 test de permissions POSIX |
| Pyright strict, avec l'interpréteur de `.venv` explicitement sélectionné | 0 erreur, 0 avertissement |
| Sphinx avec `-W --keep-going` | Réussite |
| `pip check` | Aucune incohérence de dépendances |
| Construction wheel + sdist, `build --no-isolation` | Réussite ; wheel reconstruite depuis la sdist |
| `twine check --strict` | Réussite pour les deux archives |
| `scripts/release.py check` | Versions Python et batch cohérentes |
| Ruff 0.16.9, règles explicites `E4,E7,E9,F` | 17 diagnostics dans les scripts et les tests : 15 imports inutilisés et 2 noms ambigus |
| Ruff format | Vérification complète interrompue par un plantage de Ruff sur `pymdtools/__init__.py`, qui contient un BOM UTF-8 ; hors fichiers `__init__.py`, 12 fichiers à reformater et 4 déjà conformes |
| `pip-audit`, environnement installé | Une alerte distincte sur `pdfkit==1.0.0`, retournée deux fois avec le même identifiant ; distribution locale éditable ignorée |

La construction utilise les outils installés dans `.venv`, sans isolation supplémentaire du backend. Le rendu réel par `wkhtmltopdf` n'a pas été exécuté : l'exécutable n'est pas présent dans le PATH. Les tests PDF existants simulent l'appel à ce moteur, tout en exerçant réellement plusieurs opérations `pypdf`. Aucun document n'a été envoyé au service de traduction.

**1. Priorité haute : préserver réellement la syntaxe et le sens du Markdown.**

Les fonctions de [mdcommon.py](pymdtools/mdcommon.py) combinent expressions régulières et détection maison des plages de code. Plusieurs cas valides échappent à cette logique. [normalize.py](pymdtools/normalize.py) effectue quant à lui un aller-retour via le renderer Markdown de Mistune, qui ne garantit pas la conservation sémantique de toutes les entrées.

Reproductions exécutées avec Mistune 3.3.4 :

| Entrée / opération | Résultat observé | Conséquence |
| --- | --- | --- |
| `md_beautifier(r'\[label](file.md)')` | `[label](file.md)` | Un texte littéral devient un lien ; les rendus HTML avant/après diffèrent |
| `search_link_in_md_text('[doc](file(v2).md)')` | `[]` | Destination contenant des parenthèses non détectée |
| `search_link_in_md_text(r'\[literal](file.md)')` | Un lien est retourné | Un texte échappé est traité comme un lien |
| `[A][ID]` avec une définition `[id]: file.md` | Aucun lien | La résolution des références ne normalise pas la casse |
| `[one][id] [two][id]` avec une définition commune | Une seule occurrence, nommée `two` | Le dictionnaire indexé par référence écrase la première occurrence |

Autre cas reproduit : une directive dans une clôture de code `~~~` à l'intérieur d'une citation est exécutée. Le texte ci-dessous est un bloc de code selon le parseur CommonMark de comparaison :

````markdown
> ~~~md
> <!-- include-file(example.md) -->
> ~~~
````

Avec un lecteur de fichier simulé renvoyant `READ_FILE`, `include_files_to_md_text(..., render_mode="raw")` remplace la directive par `READ_FILE` et appelle le lecteur une fois. Une déclaration `var(secret)` dans le même contexte est également extraite. Le test simule la lecture : il démontre l'exécution indue d'une directive, sans établir de contournement des racines autorisées.

Recommandation : définir explicitement le dialecte supporté, puis partager une représentation syntaxique entre inspection, substitutions et normalisation. Évaluer l'AST de Mistune ou un parseur CommonMark adapté aux positions source ; conserver les positions nécessaires pour modifier seulement les segments concernés. Le changement de parseur doit être validé par un corpus, car aucun aller-retour Markdown ne garantit à lui seul la fidélité attendue. La [spécification CommonMark](https://spec.commonmark.org/0.31.2/) fournit les règles et exemples de référence.

Critères de validation : les cas ci-dessus sont couverts, les exemples de code restent inchangés, toutes les occurrences de liens sont conservées, la normalisation est idempotente et préserve le sens du document. Ajouter des tests génératifs ciblés, par exemple avec [Hypothesis](https://hypothesis.readthedocs.io/en/latest/), pour les échappements, imbrications et caractères Unicode.

**2. Priorité haute : remplacer `pdfkit` / `wkhtmltopdf`.**

Le pipeline dépend directement de ce moteur dans [mdtopdf.py](pymdtools/mdtopdf.py), notamment `convert_html_to_pdf` à la ligne 669. Le mainteneur de [python-pdfkit](https://github.com/JazzCore/python-pdfkit) déclare le projet déprécié. La page officielle [wkhtmltopdf status](https://wkhtmltopdf.org/status) décrit l'ancienneté de Qt/WebKit et déconseille le traitement de HTML non fiable.

`pip-audit` signale `CVE-2025-26240` / `GHSA-9g3x-6x24-vf9f` sur la version installée, sans version corrigée indiquée. L'[avis GitHub](https://github.com/advisories/GHSA-9g3x-6x24-vf9f) concerne `from_string` ; pymdtools utilise `from_file`. Il s'agit d'une alerte de dépendance confirmée, mais l'exploitabilité précise de ce chemin pymdtools n'a pas été démontrée.

Recommandation : introduire une petite interface de rendu PDF et évaluer [WeasyPrint](https://doc.courtbouillon.org/weasyprint/stable/) pour les documents imprimables HTML/CSS. Si la fidélité à un navigateur ou JavaScript est nécessaire, évaluer [Chromium via Playwright](https://playwright.dev/python/docs/api/class-page#page-pdf). Comparer quelques documents représentatifs avant de retenir le moteur : pagination, polices, tableaux, images, liens, en-têtes et plateformes supportées.

Le nouveau backend doit prévoir une durée maximale de conversion, une politique explicite d'accès aux fichiers et au réseau, et des erreurs utiles. Le moteur actuel n'expose pas de timeout dans l'appel à `pdfkit.from_file`. Déplacer les dépendances PDF dans un extra dédié permettrait également d'alléger l'installation du cœur Markdown.

Critères de validation : au moins un test d'intégration exécute réellement le moteur choisi ; le texte, la pagination et les ressources sont vérifiés sur un corpus de référence, avec contrôle visuel des changements de rendu.

**3. Priorité haute pour les gros documents : réduire la complexité de l'analyse.**

Dans `markdown_code_ranges`, [mdcommon.py](pymdtools/mdcommon.py), lignes 283–315, chaque position de texte peut entraîner une recherche linéaire dans les blocs déjà repérés. `search_link_in_md_text` recalcule ensuite les plages pour plusieurs motifs.

Mesures locales d'un seul appel à `markdown_code_ranges`, pour un document synthétique alternant bloc de code et paragraphe :

| Blocs | Taille ASCII | Temps |
| ---: | ---: | ---: |
| 250 | 23 750 octets | 0,246 s |
| 500 | 47 500 octets | 0,942 s |
| 1 000 | 95 000 octets | 3,724 s |
| 2 000 | 190 000 octets | 14,731 s |

Ce sont des mesures ponctuelles sur cette machine, sans protocole de benchmark statistique. La multiplication du temps par environ quatre lorsque la taille double concorde avec la recherche imbriquée observée dans le code.

Recommandation : parcourir les intervalles triés avec un curseur, ou utiliser une recherche dichotomique ; partager les plages entre les passes ; regrouper les modifications avant de reconstruire le texte. Définir un budget de performance et le suivre sur documents synthétiques et réels.

**4. Priorité moyenne : corriger la réécriture des chemins existants.**

`move_base_path_in_md_text('[doc](file.md)', 'My Docs')` produit `[doc](my-docs/file.md)`. L'appel à `common.path_to_url` transforme le chemin en minuscules, remplace les espaces et translittère par défaut. Il fabrique ainsi un nom différent du répertoire fourni ; cela peut casser les liens, particulièrement sur un système sensible à la casse. Voir [mdcommon.py](pymdtools/mdcommon.py), ligne 659, et [common/text.py](pymdtools/common/text.py), ligne 296.

Séparer la création d'un slug de l'encodage d'un chemin réel. Pour un chemin existant, conserver casse et caractères, puis encoder les espaces en `%20`. Prévoir une transition compatible pour les utilisateurs qui attendent le comportement historique. Ajouter des essais avec espaces, accents et différences de casse.

**5. Priorité moyenne : consolider le packaging et distribuer le typage.**

Les métadonnées sont réparties entre `setup.py`, `setup.cfg`, `pyproject.toml` et trois fichiers requirements. Les tests vérifient leur synchronisation, mais cette duplication reste une charge de maintenance.

Recommandation : migrer les métadonnées vers `[project]` dans `pyproject.toml`, en conservant setuptools si cela convient au projet. Regrouper les extras et configurations ; générer les éventuels requirements nécessaires à partir d'une source unique. Utiliser les champs modernes de licence et d'inventaire de fichiers décrits par la [documentation PyPA](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/). L'archive contient actuellement `License: MIT`, mais pas `License-Expression` ; l'expression à publier doit tenir compte des ressources tierces effectivement distribuées et de leur inventaire existant.

Le fichier `py.typed` est absent du dépôt et de la wheel générée. Ajouter et distribuer ce marqueur pour rendre le typage disponible aux outils des utilisateurs, comme prévu par la [spécification de distribution du typage](https://typing.python.org/en/latest/spec/distributing.html). Vérifier ensuite l'API installée avec `pyright --verifytypes pymdtools`, puis réduire les `Any` qui traversent l'API publique, notamment les options PDF et les adaptateurs.

La sdist construite ne contient pas la suite complète de tests, `pytest.ini`, `.coveragerc`, la documentation ni `scripts/release.py`. Elle se construit correctement, mais ne permet pas de reproduire toute la validation depuis l'archive seule. Inclure les fichiers nécessaires à cet usage et vérifier leur présence dans un test d'archive.

**6. Priorité moyenne : compléter les contrôles de qualité et de distribution.**

Conserver Pyright strict et les tests actuels. Ajouter [Ruff](https://docs.astral.sh/ruff/linter/) pour le lint et le formatage, avec une configuration et une version explicites. Commencer par les diagnostics utiles, puis adopter progressivement les règles d'import et de modernisation. Le plantage du formatter observé sur le BOM doit être traité comme une limite de l'outil ; vérifier la solution retenue avant de rendre ce contrôle bloquant.

Le contrôle de wheel dans [.github/workflows/ci.yml](.github/workflows/ci.yml), ligne 65, est utile, mais installe sans dépendances et ne fait qu'importer la racine paresseuse du package et vérifier deux ressources. Il n'exerce pas les fonctions des sous-modules. Ajouter des tests fonctionnels de la wheel installée avec ses dépendances, lancés hors de l'arborescence source. Une organisation `src/` peut renforcer cette séparation, sans être un préalable aux corrections fonctionnelles. Voir les [pratiques recommandées par pytest](https://docs.pytest.org/en/stable/explanation/goodpractices.html).

Conserver l'indicateur de couverture, mais compléter son interprétation par des invariants métier, des cas CommonMark et des tests du moteur PDF réel. Les tests qui imposent le texte exact de la configuration CI devraient vérifier les garanties recherchées : par exemple, accepter un SHA épinglé et contrôler sa forme plutôt qu'imposer exclusivement `action@vX.Y.Z`.

**7. Priorité moyenne : rendre les environnements reproductibles et durcir la CI.**

Les dépendances sont bornées mais non verrouillées. Créer un environnement de développement reproductible, par exemple avec `uv.lock` et `uv sync --locked`, tout en gardant des contraintes compatibles pour les consommateurs de la bibliothèque. Maintenir un job périodique avec les dépendances récentes et, si les bornes minimales sont contractuelles, un job qui les vérifie. Le [fonctionnement du verrouillage uv](https://docs.astral.sh/uv/concepts/projects/sync/) permet de distinguer environnement reproductible et mises à jour volontaires.

Les workflows utilisent des versions d'actions précises, mais référencées par tags. Les épingler par SHA complet, avec un commentaire de version et les mises à jour Dependabot, suit les [recommandations GitHub](https://docs.github.com/en/actions/reference/security/secure-use). Ajouter [pip-audit](https://github.com/pypa/pip-audit) à la CI et définir le traitement des alertes pertinentes.

La séparation construction/publication et l'usage d'OIDC constituent déjà de bons choix. Le YAML référence un environnement `pypi`, mais ses protections effectives doivent être contrôlées dans GitHub. Ajouter un job macOS si cette plateforme fait partie du support effectivement promis.

**8. Priorité secondaire : clarifier les responsabilités et les contrats de l'API.**

Le package contient 18 fichiers Python et 8 258 lignes, documentation et commentaires inclus. `instruction.py` compte 1 843 lignes, `common/fs.py` 1 370 et `mdtopdf.py` 1 026. Découper progressivement par responsabilité : détection des directives, résolution, transformations de texte, accès aux fichiers, rendu HTML et traitement PDF. Préserver les imports publics existants par des modules de compatibilité.

Remplacer les groupes de `**kwargs: Any` par des options structurées ou des signatures explicites ; définir quelques exceptions métier ; utiliser `logging.getLogger(__name__)` pour permettre aux applications clientes de régler la journalisation du package. Expliquer dans la documentation le dialecte Markdown, les transformations potentiellement destructrices, les garanties de chaque mode et la politique de compatibilité. Ajouter un historique des changements et un guide de contribution.

La traduction traite actuellement chaque token textuel séparément, donc une phrase contenant du gras entraîne plusieurs requêtes sans contexte commun. Pour cet usage, étudier une traduction par phrase ou paragraphe avec marqueurs protégés, un transport injectable, un cache et des reprises bornées sur erreurs transitoires. Tester ces contrats hors réseau ; conserver la documentation existante sur l'envoi des contenus au prestataire.

L'ordre de réalisation conseillé est le suivant :

1. Ajouter les reproductions Markdown comme tests de régression, corriger la préservation du contenu et la réécriture des chemins.
2. Remplacer le moteur PDF, avec corpus de rendu et dépendances optionnelles.
3. Réduire le coût du repérage des plages de code et fixer un budget de performance.
4. Unifier les métadonnées, distribuer `py.typed`, vérifier la wheel et compléter la sdist.
5. Installer les contrôles Ruff, dépendances et CI reproductible, puis effectuer les découpages internes utiles.

Les quatre premiers chantiers ont des critères de réussite observables : absence d'altération sémantique sur le corpus, conversion PDF réellement exercée, croissance maîtrisée du temps d'analyse, et distribution installable dont l'API typée fonctionne hors du dépôt.

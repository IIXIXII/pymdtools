  csq
 
 [label]    (#metadonneelabel) cqsc qsc qs
c sqc qs


>[Professeu
r de danse]
(ds053.
md)
c sq
[an example](http://example.com/ "Title") 
[blabla]    
[id1] reference-style link.
[bla bla][id4]
[id1]: http://example.com/id1 
 "un title
sur 
plusieurs lignes"





>[Professeur de danse](www.guichet.fr)
[bla bla][id3] reference-style link.
"jkbnjk"
[id4]:http://exampleID4.com/ 
l"pas de title"
>[sport d'opposition](qp 119.md
"infobulle sport (d'op)position")ccqscs 
c sq

This is [an example][id] reference-style link.

[This link](http://example.net/)
c qs
>[sport](Sport.fr "salut")

 qsc

>[la page 42](page42.md)
qsc 
[id]: http://mylink.com/  "Title Here"
[id3]: http://exampleid3.com/
> [retour à l'intro](#intro)c sq
 c
 csq cqs sq  [texte alt](www.logo.ge.png "avec une info bulle 
sur plusieurs ligne") cq csq
<!-- var(reference)="Xenon" -->
<!-- var(lang)="fr" -->
<!-- include-file(license) -->

Présentation de Xenon
------

<!--anc:intro-->

# Introduction 

Xenon est un algorithme qui produit un site internet statique à partir d'un ensemble organisé de fichier markdown.
l'ensemble des fiches est indexé de manière récursive. Pour qu'une fiche soit indexée, il suffit qu'un lien pointe vers elle dans le fichier index.md (qui fait office de sommaire) du même répertoire. Les catégories (répertoire) peuvent être imbriquées.

Des meta données peuvent etre renseigné dans le code markdown pour affiner la présentation ou fournir certain élément à l'algorithme. Ils se déclarent grâce à la commande suivante :

>&#8249;!-- var(ma_variable)="toto" --&#8250;

Un site de 177 pages sur 3 langues différentes se génère en 12 sec environ.

# Les pages

Les pages classiques doivent être présente, sous la forme d'un lien, dans le fichier index.md du même répertoire pour être indexée. Grâce à cet index, on pourra créer un lien vers cette page très facilement depuis n'importe quelle autre page sans se soucier de son emplacement physique.

## Menu

Le nom de la page dans le menu est par défaut le label du lien dans le fichier index.md du répertoire où la page se trouve. Ce nom peut être surchargé par la meta donnée ["label"](#metadonneelabel)

## Meta données

<!--anc:metadonneelabel-->

### label (facultative) 

La Meta donnée label d'une page viendra surcharger le nom de la page dans le menu. Si elle n'est pas présente, le nom du lien dans l'index.md sera utilisé.

>&#8249;!-- var(label)="mon label" --&#8250;

### reference (facultative)

La meta donnée "reference" permet d'indexer le fichier .md pour pouvoir lier la fiche à ses traduction dans d'autres langue.

>&#8249;!-- var(reference)="ma_reference" --&#8250; 

## Liens

Voici un exemple de lien vers une fiche. Peu importe son emplacement, il suffit de renseigner le nom du fichier :

>&#91;sport d'opposition&#93;(qp 119.md)

>[sport d'opposition](qp 119.md)

Voici un exemple de lien vers une fiche. Peu importe son emplacement, il suffit de renseigner le nom du fichier :

>&#91;Professeur de danse&#93;(DS053_prof_de_danse.md)

>[Professeur de danse](DS053_prof_de_danse.md)

Il est également possible de renseigner une infobulle sur ce lien :

>&#91;sport d'opposition&#93;(qp 119.md "infobulle sport d'opposition")

>[sport d'opposition](qp 119.md "infobulle sport d'opposition")

# Les catégories

Les catégories sont des pages spéciales qui se comportent comme des sommaires. Chaque répertoire comporte une et une seule catégorie matérialisé par un fichier index.md.
Les liens présents dans ce fichier qui pointe vers des fichiers qui se trouvent dans le même répertoire seront indexé pour être retrouvé plus facilement.
Ce fichier index.md comporte obligatoirement la meta donnée "reference".


## Menu

le nom de la catégorie dans le menu est le nom du répertoire dans lequel se trouve le fichier index.md

## Meta données

### reference (obligatoire)

La meta donnée "reference" permet d'indexer le fichier .md pour pouvoir y faire référence dans des liens, ainsi que pour retrouver une page dans une autre langue

>&#8249;!-- var(reference)="ma_reference" --&#8250; 

## Liens

Pour écrire un lien vers une catégorie (index.md) peu importe son emplacement, il suffit de renseigner le nom (meta donné "reference") de la catégorie précédé du mot clé "reference:" :

>&#91;sport&#93;(reference:Sport)

>[sport](reference:Sport)

# Les images

Les images doivent se trouver dans le répertoire "/template/images", Xenon renseignera le chemin de l'image directement peut importe l'endroit où on souhaite l'afficher. Il suffit pour cela d'utiliser le mot clé "img:" :

> !&#91;texte alt&#93;(img:logo/ge.png "avec une info bulle")

> ![texte alt](img:logo/ge.png "avec une info bulle")

Il est aussi possible de transformer cette image en lien en l'encapsulant et en combinant les mots clés :

> &#91;!&#91;Logo guichet-entreprises.fr&#93;(img:logo/ge.png "avec une info bulle")&#93;(reference:Sport)

> [![Logo guichet-entreprises.fr](img:logo/ge.png "avec une info bulle")](reference:Sport)

# La page d'erreur 404

Si un lien pointe vers du contenu du site qui n'existe pas, Xenon le remplacera automatiquement par un lien vers une page 404. le même comportement est appliqué si une version de la page n'existe pas dans une langue paramétrée.


>&#91;la page 42&#93;(page42.md)

>[la page 42](page42.md)

Note : les logs Xenon indique un erreur lorsque un lien vers une page 404 est généré.

# Les ancres

les ancres ne sont pas géré par le langage markdown. Heureusement, il est toujours possible d'ajouter du code HTML pour renseigner une ancre. Xenon simplifie la démarche en proposant une balise spéciale avec le mot clé "anc:" :

> &#8249;!--anc:intro--&#8250; introduction de la page

pour faire un lien vers cette ancre il suffit d'écrire :

> &#91;retour à l'intro&#93;(#intro)

> [retour à l'intro](#intro)

# Les blocs plier/deplier

le composant est automatiquement créer grâce aux balises collapse de Xenon : &#8249;!--collapse--&#8250; Par exemple le paragraphe [Autres fonctionnalitées](#autres) a été construit grâce à ce composant. voici un autre exemple :

> &#x23; le titre &#8249;!--collapse--&#8250;<br/>
> le text à plier/déplier<br/>
> &#x23; un autre titre &#8249;!--collapse--&#8250;<br/>
> un autre text à plier/déplier<br/>

# le titre<!--collapse-->
le text à plier/déplier

# un autre titre<!--collapse-->
un autre text à plier/déplier

# Le sommaire
L'extention toc permet d'afficher un sommaire grace à la balise &#8249;toc&#8250

# Les sections à sommaire

Xenon étend les possibilité de toc et il est possible de définir un sommaire pour une partie de la page avec la balise :

> **&#8249;!--summary--&#8250;**<br/>
> &#9839;&#9839;un titre<br/>
> Lorem ipsum dolor...<br/>
> &#9839;&#9839;un autre titre<br/>
> Pellentesque a imperdiet est...<br/>
> &#9839;&#9839;encore un autre<br/>
> Aliquam rutrum semper risus...<br/>
> **&#8249;!--summary-end--&#8250;**

Ce qui donne par exemple :

<!--summary-->

## Un titre
Lorem ipsum dolor [sport](reference:Sante) sit amet, consectetur adipiscing elit. Vestibulum eu viverra purus, eget volutpat neque. Maecenas lacinia rutrum rhoncus. Mauris vulputate ullamcorper feugiat. 
## Un autre titre
Pellentesque a imperdiet est. Donec eget lorem quis velit efficitur sollicitudin. Suspendisse tortor quam, dapibus id pulvinar id, lacinia eget dui. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. 
## Encore un autre
Aliquam rutrum semper risus, a accumsan mauris mattis a. Sed non est sed nisi porta cursus. 

<!--summary-end-->

<!--anc:autres-->
# Autres fonctionnalités

#Plier/Deplier<!--collapse-->
il est possible d'utiliser toutes sorte de balise dans les cadres collapse comme cette image :<br/>
![texte alt](img:logo/ge.png "avec une info bulle")

#Menu<!--collapse-->
Le menu est automatiquement construit grâce à différentes informations : meta données, nom des répertoire, langue, etc.

#Sélecteur  de langue<!--collapse-->
Le sélecteur  de langue est construit automatiquement et retrouve automatiquement les pages concernées dans les différentes langues.

#Fil d'Ariane<!--collapse-->
le file d'Ariane est également construit automatiquement en reprenant les informations du menu.

#Les includes<!--collapse-->
Xenon peut inclure directement un fichier existant dans la page. le fichier à inclure doit se trouver dans le répertoire "referenced_files". Par exemple l'include suivant inclu le fichier license.txt si la page est en français ou le fichier license.en.txt si la page est en anglais :<br/><br/>&lsaquo;!-- include-file(license) --&rsaquo;

#Integration avec feedback<!--collapse-->
Une ligne de code, merci minecraft !

#Génération du site par environnement (recr, prod, etc.)<!--collapse-->
Xenon offre possibilité de générer le site pour des environnements de test. Les urls (feedback compris) sont donc modifiées en conséquence en fonction de l'environnement et un bandeau apparait en haut à gauche.

# TODO
	- ancre sur une **page différente**
	- mot clé pour les fiches simple ?
	- pages particulières/complexes (page d'accueil, FAQ)
	- des css

# La Base - backend

## Installation et développement en local

- créer un environnement virtuel sous Python >= 3.9 et installer les dépendances:
`python install -r requirements.txt`
- initialiser la base de donnée : `python manage.py migrate`
- créer un super-utilisateur : `python manage.py createsuperuser`
- lancer le serveur local : `python manage.py runserver`, le serveur back tourne alors
sur le port local `8000`

### `pre-commit` et tests automatiques

[`pre-commit`](https://pre-commit.com/) est un outil qui permet à chaque commit de
vérifier qu'un certain nombre de règles soient respectées : lint, syntaxe...
Il est également pour lancer à chaque commit la commande `python manage.py test` qui
lance donc les tests automatiques configurés.

Une fois `pre-commit` installé globalement sur votre PC, lancer `pre-commit install`
pour activer les vérifications automatiques à chaque commit.

Les tests se trouvent donc dans le dossier `main/tests`.

## Configurations locales

Le projet ne nécessite pas d'autres configurations, mais certains peuvent être
pratiques.

Certains paramètres peuvent être modifiés dans le fichier de configuration
`local_settings.conf` (à créer à la racine du back s'il n'existe pas). Les principaux
paramètres utiles :

### Sauvegarde / récupération de la base de donnée

```text
[db_backup]
access=xxx
secret=xxx
bucket=labase-backup
```

permet d'avoir les mêmes paramètres de sauvegarde de base de donnée qu'en production.

```text
[database]
postgres = true
name = xxx
user = xxx
password = xxx
```

Permet d'utiliser `postgres` comme database. En combinaison avec le paramètre précédent,
la commande `python manage.py backup_db recover latest` permet d'avoir en local la même
base de donnée qu'en production.

### Utilisation d'un service externe pour les fichiers

```text
[external_file_storage]
access=xx
secret=xx
bucket=moine
endpoint_url=https://cellar-c2.services.clever-cloud.com
```

Permet d'utiliser le stockage de fichier externe.

```text
[mail]
api_key = xxx
```
Permet d'envoyer des mails avec le service externe. Tant que `DEBUG=True`, les mails ne
sont pas envoyés et simplement affichés dans la console.

## Modifier les données dans l'admin

Un certain nombre de modèle sont éditables dans l'interface d'administration de Django,
accessible depuis `/admin/`.

### Bases

Pour certifier une base, cocher la case "est certifiée" dans l'édition

### Blocs de textes

Un certain nombre de blocs de texte du frontend sont modifiables directement dans
l'admin. L'identifant est en général assez explicite sur à quoi ça correspond.

### Bulle de didacticiel

- Les bulles de didacticiel dont le champ `slug` commence par `draft` sont ignorées.
- Celles dont le champ `slug` commence par `INDEX_` ne sont visibles que depuis
l'accueil ou le moteur de recherche (utile par exemple pour le header, afin que les
utilisateurs ne voient pas les bulles correspondent sur tout le site).
-

### Catégories de tag

- Convention pour les slugs:
Le slug d'une catégorie de tag comporte deux parties, la famille à laquelle se réfère
la catégorie et un identifiant explicite : `famille_01nomDeLIDentifiant`. À l'intérieur
d'une famille, les catégories sont rangées par ordre alphabétique, donc utiliser une
numérotation permet de régler l'ordre.
- Il est possible donc de paramétrer le nombre maximum de tags dans une catégorie, si
cette catégorie accepte des tags libres (dans le cas positif, un utilisateur peut
ajouter de nouveaux tags dans cette catégorie depuis le front ; dans le cas négatif,
seuls les admin peuvent en ajouter depuis l'admin).

### Critères d'évaluations

Ils sont éditables dans l'admin, leur ordre peut aussi être réglé.

### Pages

Les pages sont des pages statiques et permettent d'avoir une sorte de mini-CMS
accessible. Les pages statiques sont accessibles depuis le front à l'adresse
`/page/slug-de-la-page`. Le champ "Faire apparaitre la page dans le menu" permet
d'ajouter la page dans le menu de navigation du front.

### Ressources

Pour labeliser une ressource, choisir l'état "accepté" dans la liste déroulante
"État de la labélisation". En février 2023, ce champ n'est pas encore utilisé par le
frontend.

### Utilisateurs

Les Conseillers Numériques France Service ont un traitement particulier. Ils ont ce
statut sur le site s'ils ont le tag du même nom. Il n'est pas possible aux utilisateurs
de se déclarer eux-mêmes avec ce tag. Les utilisateurs CnFS ont un menu de navigation
légèrement différent dans le front, avec des raccourcis vers les bases CnFS.

### Importer les comptes CnFS

Les CnFS peuvent être importés en lançant la commande
`python manage.py import_cnfs_accounts`, lorsqu'un fichier `cnfs_accounts.csv` est
présent à la racine du projet back. Ce fichier est obtenu avec un compte administrateur
sur l'espace Co-Op. Depuis la
[page d'accueil](https://coop.conseiller-numerique.gouv.fr/accueil), cliquer sur le
bouton "Exporter les données".

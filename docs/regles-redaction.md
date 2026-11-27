# Règles de rédaction

Ces règles s'appliquent à toute page du site, qu'elle soit écrite par une personne ou
rédigée avec l'aide d'une IA. Les règles mesurables sont vérifiées par
`tools/checks/check_content.py` (voir le README).

## 1. En-tête de chaque page (front matter)

```yaml
---
title: "Les anticoagulants oraux"
description: "Une phrase qui dit ce que la page apporte (utilisée par les moteurs de recherche)."
public: [patients, professionnels]   # patients, professionnels, etudiants
statut: brouillon                    # brouillon | relu | publie
relu_par: null                       # nom du relecteur, une fois relu
relu_le: null                        # AAAA-MM-JJ
prochaine_relecture: null            # AAAA-MM-JJ
substances: [warfarine, apixaban]    # fiches de classe et « maux courants » : substances, telles qu'écrites sur la page
sources:
  - titre: "ANSM, Thésaurus des interactions médicamenteuses"
    url: "https://ansm.sante.fr/documents/reference/thesaurus-des-interactions-medicamenteuses-1"
    consulte_le: 2026-11-25
pour_aller_plus_loin:                # facultatif : lectures complémentaires
  - titre: "Je prends un anticoagulant oral, quels sont les risques ?"
    url: "https://www.rfcrpv.fr/prends-anticoagulant-oral-risques/"
    site: rfcrpv                     # rfcrpv | cnpm, ou le nom du site en clair
---
```

- `sources` : au moins une source officielle par page de contenu (RCP ou notice de la
  base de données publique des médicaments, ANSM, HAS, EMA, recommandation d'une société
  savante, article publié). Pas de source secondaire quand la source primaire existe.
- Le filtre `assets/filters/page-meta.lua` affiche automatiquement le bandeau
  « Brouillon », les sources et les dates de relecture : ne pas les réécrire à la main.
- `substances` (fiches de classe et « maux courants ») : les substances dont parle la fiche, six
  au plus ; pour un mal courant, celles du traitement. Pas sur les fiches « situations », qui
  parlent de familles de médicaments. Le filtre
  ajoute « Notices et RCP officiels » : pour chacune, la page de la base de données publique
  des médicaments d'un médicament commercialisé qui la contient seule (forme orale, puis
  médicament de référence en premier), choisi par `tools/build/make_bdpm_liens.py`. Après
  avoir ajouté une substance, relancer ce script ; `check_content.py` signale une substance
  sans lien.
- Un médicament de la base de données publique cité en source doit être encore
  commercialisé : `check_content.py` le vérifie (erreur `FM-BDPM`) d'après
  `data/bdpm-liens.json`, mis à jour chaque mois avec `fetch_bdpm.py` puis
  `make_bdpm_liens.py`.
- `pour_aller_plus_loin` : liens vers des contenus qui prolongent la page, d'abord ceux du
  réseau des CRPV ([rfcrpv.fr](https://www.rfcrpv.fr), `site: rfcrpv`) et du Collège national de
  pharmacologie médicale ([pharmacomedicale.org](https://pharmacomedicale.org), `site: cnpm`,
  écrit pour les professionnels et les étudiants). Trois liens au plus, en https, vérifiés
  avant d'être ajoutés ; le filtre les affiche dans « Pour aller plus loin », avant les
  sources. Ce ne sont pas des sources : ce que la page affirme reste sourcé dans `sources`.

## 2. Texte destiné aux patients

Tout texte pour les patients est placé dans un bloc :

```markdown
::: {.texte-patient}
...
:::
```

Les contrôles automatiques ne lisent que ces blocs pour les règles de vulgarisation.

Règles (d'après les guides de la HAS sur l'information écrite des patients, 2008 et 2012,
et les principes du FALC) :

1. Phrases courtes : 15 mots en moyenne, 25 au plus. Une idée par phrase.
2. Mots courants. Un terme médical est remplacé, ou expliqué entre parenthèses à sa
   première apparition (liste dans `data/jargon.yml`).
3. Pas de sigle sans sa forme développée à la première apparition.
4. Risques en fréquences naturelles : « 1 personne sur 100 », pas « 1 % » ni « 0,01 ».
   Même dénominateur pour comparer deux risques.
5. On s'adresse au lecteur : « vous ». Voix active.
6. Le message principal d'abord, dans un encadré :

   ```markdown
   ::: {.a-retenir}
   - trois points au plus
   :::
   ```

7. Sur chaque fiche médicament et chaque page « maux courants », un encadré
   `::: {.quand-consulter}` qui liste les signes qui doivent faire consulter. Il vient
   en tête de la partie patient pour les maux courants.
8. Des intertitres fréquents, de préférence sous forme de questions (un intertitre au
   moins tous les 150 mots).
9. Toujours : « Ne modifiez pas votre traitement sans en parler à votre médecin ou à votre
   pharmacien. »
10. Pas de tournures creuses ou typiques des textes générés : « il est important de
    noter », « en effet », « jouer un rôle clé », « dans un monde où », etc.

## 3. Texte destiné aux professionnels

Placé dans un bloc `::: {.texte-pro}`. Style d'une fiche de pharmacologie clinique :
précis, sourcé, chiffré. Les niveaux d'interaction suivent le Thésaurus de l'ANSM
(contre-indication, association déconseillée, précaution d'emploi, à prendre en compte).

### Dire le niveau de preuve d'un effet

Un effet signalé n'est pas un effet établi. Écrire ce que la source permet d'affirmer,
dans les textes patients comme professionnels :

| Ce que dit la source | Formulation |
|---|---|
| Effet indésirable listé à la rubrique 4.8 du RCP | « X peut provoquer Y », avec la fréquence du RCP |
| Signal en cours d'évaluation (ANSM, PRAC) | Pas de commentaire (voir section 4) ; au plus, renvoyer à la communication officielle |
| Association observée dans une étude | « Une étude a observé plus de Y chez les personnes traitées par X », avec le type d'étude |
| Cas rapportés (notifications, publications de cas) | « Des cas de Y ont été rapportés avec X » |

Ne jamais écrire « X provoque Y » sur la seule base de cas rapportés ou d'une
association observée. Rappeler, quand c'est utile, qu'une déclaration ne prouve pas
que le médicament est en cause.

## 4. Ce que le site ne fait pas

- Pas de conseil individuel. Renvoyer vers le CRPV, le médecin ou le pharmacien.
- Pas de commentaire sur un signal ou une enquête en cours d'évaluation.
- Pas d'information tirée des dossiers des centres (secret médical).
- Pas de chiffre inventé : un chiffre sans source est retiré ou remplacé par
  « [à compléter : source] ».
- Pas de nom de personne réelle sans son accord (équipes : gabarits seulement).

## 5. Figures

- Au moins une figure par page patient quand elle aide à comprendre (schéma, grille de
  personnages, frise du moment de prise).
- SVG de préférence, avec un texte alternatif (`fig-alt`) qui dit ce que la figure montre.
- Couleurs lisibles par les personnes daltoniennes et en niveaux de gris.

#show: doc => vigiking(
$if(title)$
  title: [$title$],
$endif$
$if(numero)$
  numero: [$numero$],
$endif$
$if(couverture)$
  couverture: "$couverture$",
$endif$
$if(couverture-alt)$
  couverture-alt: "$couverture-alt$",
$endif$
$if(logo-gauche)$
  logo-gauche: "$logo-gauche$",
$endif$
$if(logo-droite)$
  logo-droite: "$logo-droite$",
$endif$
$if(bandeau)$
  bandeau: "$bandeau$",
$endif$
  doc,
)

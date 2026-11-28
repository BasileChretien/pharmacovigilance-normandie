# Installe ce dont le bulletin Vigiking a besoin, pour l'utilisateur (sans droits
# d'administrateur quand c'est possible) :
#   - Quarto, l'outil de mise en page (PDF et page web) ;
#   - uv, l'outil qui lance la fabrication (il installe Python lui-même) ;
#   - l'icône « Fabriquer le Vigiking » sur le bureau : on y dépose le fichier Word.
# Lancé par Installer.bat. Avec -Verifier, il dit seulement ce qui manque.
# Messages pour des personnes qui ne sont pas informaticiennes : quand quelque chose
# échoue, la fenêtre dit d'appeler le service informatique et ce qu'il faut lui montrer.
param([switch]$Verifier)

$ErrorActionPreference = 'Stop'
$ici = Split-Path -Parent $MyInvocation.MyCommand.Path
$depot = Split-Path -Parent $ici
$appel = '      Ce n''est pas une erreur de votre part : appelez le service informatique et montrez-lui cette fenêtre.'

function Test-Outil([string]$nom) {
    [bool](Get-Command $nom -ErrorAction SilentlyContinue)
}

function Update-Chemin {
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' +
                [Environment]::GetEnvironmentVariable('Path', 'User')
}

# Lancé depuis un fichier ZIP ouvert sans l'extraire, le dossier est temporaire : l'icône
# du bureau mènerait à un dossier que Windows efface ensuite.
function Test-DossierTemporaire {
    $chemin = $ici.ToLowerInvariant()
    if ($chemin -match '\\temp\\|\.zip|\\rar\$') {
        Write-Host '  !!  Le dossier du bulletin est encore dans le fichier compressé (ZIP).'
        Write-Host '      Fermez cette fenêtre, faites un clic droit sur le fichier ZIP, choisissez'
        Write-Host '      « Extraire tout », puis relancez le fichier Installer du dossier extrait.'
        return $true
    }
    return $false
}

function Install-Outil([string]$nom, [string]$libelle, [string]$id) {
    if (Test-Outil $nom) { Write-Host "  OK  $libelle est installé."; return $true }
    if ($Verifier) { Write-Host "  --  $libelle manque."; return $false }
    if (Test-Outil 'winget') {
        Write-Host "  ... installation de $libelle (quelques minutes)."
        Write-Host '      Des lignes en anglais et des barres de progression vont défiler : c''est normal, ne fermez pas la fenêtre.'
        winget install --id $id --exact --source winget --scope user
        if ($LASTEXITCODE -ne 0) {
            Write-Host '  ... nouvel essai pour tout l''ordinateur : si Windows demande un mot de passe administrateur, appelez le service informatique.'
            winget install --id $id --exact --source winget
        }
        Update-Chemin
        if (Test-Outil $nom) { Write-Host "  OK  $libelle est installé."; return $true }
    }
    Write-Host "  !!  Votre ordinateur n'a pas permis d'installer $libelle."
    Write-Host $appel
    Write-Host "      (Pour le service informatique : winget install --id $id, pour l'utilisateur.)"
    return $false
}

function Install-Python {
    if ($Verifier) { return $true }
    Write-Host '  ... préparation de Python (la première fois seulement).'
    uv run --quiet --project $depot python -c "print('  OK  Python est prêt.')"
    if ($LASTEXITCODE -eq 0) { return $true }
    Write-Host '  !!  Python n''a pas pu être préparé (la connexion Internet est peut-être bloquée).'
    Write-Host $appel
    return $false
}

function New-Raccourci {
    $bureau = [Environment]::GetFolderPath('Desktop')
    $lien = Join-Path $bureau 'Fabriquer le Vigiking.lnk'
    if ($Verifier) {
        if (Test-Path $lien) { Write-Host "  OK  l'icône « Fabriquer le Vigiking » est sur le bureau."; return $true }
        Write-Host "  --  l'icône « Fabriquer le Vigiking » n'est pas sur le bureau."
        return $false
    }
    $raccourci = (New-Object -ComObject WScript.Shell).CreateShortcut($lien)
    $raccourci.TargetPath = Join-Path $ici 'Fabriquer le Vigiking.bat'
    $raccourci.WorkingDirectory = $ici
    $raccourci.Description = 'Déposez le fichier Word du numéro sur cette icône'
    $raccourci.Save()
    Write-Host "  OK  icône « Fabriquer le Vigiking » posée sur le bureau."
    return $true
}

# The shared folder (logos, banner, back cover) is not online: say so, without blocking.
function Test-Commun {
    if (Test-Path (Join-Path $ici 'commun')) { Write-Host '  OK  le dossier commun (logos, dos du bulletin) est là.'; return }
    Write-Host '  --  le dossier commun manque : les numéros n''auront ni logos ni dernière page.'
    Write-Host '      Demandez-le à la personne qui gère le bulletin, et placez-le dans le dossier bulletin, à côté du fichier Installer.'
}

Write-Host ''
Write-Host 'Bulletin Vigiking : installation'
Write-Host ''
if (Test-DossierTemporaire) { Write-Host ''; exit 1 }
$quarto = Install-Outil 'quarto' 'l''outil de mise en page (Quarto)' 'Posit.Quarto'
$uv = Install-Outil 'uv' 'l''outil qui lance la fabrication (uv)' 'astral-sh.uv'
$python = $quarto -and $uv -and (Install-Python)
$icone = New-Raccourci
Test-Commun
Write-Host ''
if ($quarto -and $uv -and $python -and $icone) {
    Write-Host 'Prêt. Pour fabriquer un numéro : faites glisser son fichier Word sur l''icône'
    Write-Host '« Fabriquer le Vigiking » du bureau, et lâchez-le.'
} elseif ($Verifier) {
    Write-Host 'L''installation n''est pas terminée : lancez le fichier Installer (sans rien ajouter).'
} else {
    Write-Host 'L''installation n''est pas terminée : voir les lignes !! ci-dessus.'
}
Write-Host ''

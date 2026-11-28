# Installe ce dont le bulletin Vigiking a besoin, pour l'utilisateur (sans droits
# d'administrateur quand c'est possible) :
#   - Quarto, qui fait la mise en page (PDF et page web) ;
#   - uv, qui lance les scripts du bulletin (il installe Python lui-même) ;
#   - l'icône « Fabriquer le Vigiking » sur le bureau : on y dépose le fichier Word.
# Lancé par Installer.bat. Avec -Verifier, il dit seulement ce qui manque.
param([switch]$Verifier)

$ErrorActionPreference = 'Stop'
$ici = Split-Path -Parent $MyInvocation.MyCommand.Path
$depot = Split-Path -Parent $ici

function Test-Outil([string]$nom) {
    [bool](Get-Command $nom -ErrorAction SilentlyContinue)
}

function Update-Chemin {
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' +
                [Environment]::GetEnvironmentVariable('Path', 'User')
}

function Install-Outil([string]$nom, [string]$id, [string]$page) {
    if (Test-Outil $nom) { Write-Host "  OK  $nom est installé."; return $true }
    if ($Verifier) { Write-Host "  --  $nom manque."; return $false }
    if (Test-Outil 'winget') {
        Write-Host "  ... installation de $nom (cela peut prendre quelques minutes)"
        winget install --id $id --exact --scope user
        if ($LASTEXITCODE -ne 0) { winget install --id $id --exact }
        Update-Chemin
        if (Test-Outil $nom) { Write-Host "  OK  $nom est installé."; return $true }
    }
    Write-Host "  !!  $nom n'a pas pu être installé automatiquement."
    Write-Host "      Téléchargez-le ici, installez-le, puis relancez Installer.bat : $page"
    return $false
}

function New-Raccourci {
    $bureau = [Environment]::GetFolderPath('Desktop')
    $lien = Join-Path $bureau 'Fabriquer le Vigiking.lnk'
    if ($Verifier) {
        if (Test-Path $lien) { Write-Host "  OK  l'icône est sur le bureau." }
        else { Write-Host "  --  l'icône « Fabriquer le Vigiking » n'est pas sur le bureau." }
        return
    }
    $raccourci = (New-Object -ComObject WScript.Shell).CreateShortcut($lien)
    $raccourci.TargetPath = Join-Path $ici 'Fabriquer le Vigiking.bat'
    $raccourci.WorkingDirectory = $ici
    $raccourci.Description = 'Déposez le fichier Word du numéro sur cette icône'
    $raccourci.Save()
    Write-Host "  OK  icône « Fabriquer le Vigiking » posée sur le bureau."
}

Write-Host ''
Write-Host 'Bulletin Vigiking : installation'
Write-Host ''
$quarto = Install-Outil 'quarto' 'Posit.Quarto' 'https://quarto.org/docs/get-started/'
$uv = Install-Outil 'uv' 'astral-sh.uv' 'https://docs.astral.sh/uv/getting-started/installation/'
if ($quarto -and $uv -and -not $Verifier) {
    Write-Host '  ... préparation de Python (la première fois seulement)'
    uv run --quiet --project $depot python -c "print('  OK  Python est prêt.')"
}
New-Raccourci
Write-Host ''
if ($quarto -and $uv) {
    Write-Host 'Prêt. Pour fabriquer un numéro : déposez son fichier Word sur l''icône'
    Write-Host '« Fabriquer le Vigiking » du bureau.'
} else {
    Write-Host 'Il manque encore un outil : voir ci-dessus.'
}
Write-Host ''

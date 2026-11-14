$ErrorActionPreference = 'Stop'
$projectDir = $PSScriptRoot
$previousTectonicCache = $env:TECTONIC_CACHE_DIR
$previousFontconfigFile = $env:FONTCONFIG_FILE
Push-Location -LiteralPath $projectDir
try {
    $latexmkCmd = Get-Command latexmk -ErrorAction SilentlyContinue
    $pdfCmd = Get-Command pdflatex -ErrorAction SilentlyContinue
    $bibCmd = Get-Command bibtex -ErrorAction SilentlyContinue
    if ($latexmkCmd) {
        & $latexmkCmd.Source -pdf -interaction=nonstopmode -halt-on-error main.tex
        if ($LASTEXITCODE -ne 0) { throw 'latexmk compilation failed.' }
    } elseif ($pdfCmd -and $bibCmd) {
        & $pdfCmd.Source -interaction=nonstopmode -halt-on-error main.tex
        if ($LASTEXITCODE -ne 0) { throw 'First LaTeX pass failed.' }
        & $bibCmd.Source main
        if ($LASTEXITCODE -ne 0) { throw 'BibTeX failed.' }
        1..2 | ForEach-Object {
            & $pdfCmd.Source -interaction=nonstopmode -halt-on-error main.tex
            if ($LASTEXITCODE -ne 0) { throw 'LaTeX compilation failed.' }
        }
    } else {
        $tectonicCmd = Get-Command tectonic -ErrorAction SilentlyContinue
        $tectonicPath = Join-Path $projectDir '.tools\tectonic.exe'
        if ($tectonicCmd) { $tectonicPath = $tectonicCmd.Source }
        if (-not (Test-Path -LiteralPath $tectonicPath)) {
            $localTools = Join-Path $projectDir '.tools'
            New-Item -ItemType Directory -Path $localTools -Force | Out-Null
            $archive = Join-Path $localTools 'tectonic.zip'
            Invoke-WebRequest -Uri 'https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.17.0/tectonic-0.17.0-x86_64-pc-windows-msvc.zip' -OutFile $archive
            Expand-Archive -LiteralPath $archive -DestinationPath $localTools -Force
        }
        $env:TECTONIC_CACHE_DIR = Join-Path $projectDir '.tools\tectonic-cache'
        $fontconfigPath = Join-Path $projectDir '.tools\fonts.conf'
        if (Test-Path -LiteralPath $fontconfigPath) { $env:FONTCONFIG_FILE = $fontconfigPath }
        & $tectonicPath --keep-logs --keep-intermediates main.tex
        if ($LASTEXITCODE -ne 0) { throw 'Tectonic compilation failed.' }
    }
    Write-Host ('PDF: ' + (Join-Path $projectDir 'main.pdf'))
} finally {
    $env:TECTONIC_CACHE_DIR = $previousTectonicCache
    $env:FONTCONFIG_FILE = $previousFontconfigFile
    Pop-Location
}

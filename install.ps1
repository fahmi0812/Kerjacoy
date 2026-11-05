# Kerjacoy installer — mesin loker saja (Windows PowerShell). Idempoten:
#   repo di $env:KERJACOY_HOME\src (default %USERPROFILE%\.kerjacoy),
#   venv di %USERPROFILE%\.kerjacoy\venv, launcher loker.cmd di bin\
#   (ditambahkan ke PATH user).
# Ini HANYA mesin pencari kerja (loker). Distribusi penuh (agen TUI kerjacoy)
# di Windows: npm install -g https://github.com/fahmi0812/Kerjacoy/tarball/v2.0.0
# Pakai:  irm https://raw.githubusercontent.com/fahmi0812/Kerjacoy/main/install.ps1 | iex
#   atau: powershell -ExecutionPolicy Bypass -File install.ps1 [-Uninstall] [-DryRun]
param([switch]$Uninstall, [switch]$DryRun)

$Version = "2.0.0"
$KcHome = if ($env:KERJACOY_HOME) { $env:KERJACOY_HOME } else { "$env:USERPROFILE\.kerjacoy" }
$BinDir = "$KcHome\bin"
$Src = "$KcHome\src"
$RepoUrl = if ($env:KERJACOY_REPO_URL) { $env:KERJACOY_REPO_URL } else { "https://github.com/fahmi0812/Kerjacoy.git" }

function Say($m) { Write-Host "[kerjacoy] $m" }
function Ok($m) { Write-Host "  OK   $m" }
function Warn($m) { Write-Host "  WARN $m" -ForegroundColor Yellow }
function Die($m) { Write-Host "  FAIL $m" -ForegroundColor Red; exit 1 }

if ($Uninstall) {
    foreach ($l in @("$BinDir\loker.cmd", "$BinDir\kerjacoy.cmd", "$BinDir\kc.cmd")) {
        if (Test-Path $l) {
            $isi = Get-Content $l -Raw -ErrorAction SilentlyContinue
            if ($isi -match "KC-LAUNCHER") { Remove-Item $l -Force; Ok "hapus $l" }
        }
    }
    if (Test-Path "$KcHome\.kerjacoy-home") { Remove-Item $KcHome -Recurse -Force; Ok "hapus $KcHome" }
    else { Warn "$KcHome tanpa marker — tidak dihapus" }
    exit 0
}

Say "Kerjacoy $Version · Windows · KERJACOY_HOME=$KcHome"
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { Die "butuh git (https://git-scm.com/download/win)" }

# Cari Python 3.10+ (py launcher dulu, lalu python).
$Py = $null
foreach ($c in @("py -3", "python")) {
    try {
        $v = & cmd /c "$c --version 2>&1"
        if ($v -match "Python (\d+)\.(\d+)") {
            if ([int]$Matches[1] -gt 3 -or ([int]$Matches[1] -eq 3 -and [int]$Matches[2] -ge 10)) { $Py = $c; break }
        }
    } catch { }
}
if (-not $Py) { Die "butuh Python >= 3.10 (https://www.python.org/downloads/ — centang 'Add python to PATH')" }

if ($DryRun) {
    Say "1/3 repo (dry-run) clone/pull $RepoUrl -> $Src"
    Say "2/3 venv (dry-run) buat venv $KcHome\venv, pip install -e $Src"
    Say "3/3 launcher (dry-run) buat loker.cmd di $BinDir + tambah ke PATH"
    Say "Selesai (dry-run). Jalankan: loker"
    exit 0
}

# ---------- 1/3 repo ----------
Say "1/3 repo"
New-Item -ItemType Directory -Force -Path $KcHome | Out-Null
New-Item -ItemType File -Force -Path "$KcHome\.kerjacoy-home" | Out-Null
if (Test-Path "$Src\.git") { git -C $Src pull --ff-only origin main | Out-Null; Ok "repo diperbarui" }
else { git clone --depth 1 $RepoUrl $Src | Out-Null; Ok "repo di-clone" }

# ---------- 2/3 venv + pip ----------
Say "2/3 venv + dependensi"
$VenvPy = "$KcHome\venv\Scripts\python.exe"
if (-not (Test-Path $VenvPy)) { & cmd /c "$Py -m venv `"$KcHome\venv`"" }
$pip = "$KcHome\venv\Scripts\pip.exe"
& $pip install -q -e $Src 2>$null
if ($LASTEXITCODE -ne 0) {
    # Workaround konflik metadata numpy di python-jobspy (sudah teruji).
    Warn "pip install biasa gagal — coba workaround jobspy"
    & $pip install -q --no-deps python-jobspy==1.4.1
    & $pip install -q pydantic tls-client requests markdownify regex curl_cffi
    & $pip install -q --no-deps -e $Src
    if ($LASTEXITCODE -ne 0) { Die "pip install gagal" }
}
& "$KcHome\venv\Scripts\loker.exe" --help | Out-Null
Ok "loker terpasang di venv"

# ---------- 3/3 launcher ----------
Say "3/3 launcher $BinDir"
New-Item -ItemType Directory -Force -Path $BinDir | Out-Null
foreach ($name in @("loker")) {
    $L = "$BinDir\$name.cmd"
    if ((Test-Path $L) -and ((Get-Content $L -Raw) -notmatch "KC-LAUNCHER")) { Warn "$L sudah ada dan bukan milik Kerjacoy — dilewati"; continue }
    "@echo off`r`nREM KC-LAUNCHER (hapus: install.ps1 -Uninstall)`r`n`"$KcHome\venv\Scripts\loker.exe`" %*`r`n" | Set-Content -Path $L -Encoding ASCII
    Ok $L
}
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$BinDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$BinDir", "User")
    $env:Path = "$env:Path;$BinDir"
    Ok "PATH user ditambah: $BinDir (buka terminal baru bila loker belum dikenali)"
} else { Ok "$BinDir sudah di PATH" }
Say "Selesai. Jalankan: loker (agen penuh di Windows: npm install -g, lihat README)"

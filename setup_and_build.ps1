$ErrorActionPreference = "Stop"

$BaseDir = "c:\Users\Ikeda\Desktop\PhysicsScienceCalculation"
$ToolsDir = Join-Path $BaseDir ".tools"
$QuartoZip = Join-Path $ToolsDir "quarto.zip"
$QuartoDir = $ToolsDir

if (-not (Test-Path $ToolsDir)) {
    Write-Host "Creating .tools directory..."
    New-Item -ItemType Directory -Path $ToolsDir | Out-Null
}

# 1. Download Quarto CLI Portable Zip if not exists
if (-not (Test-Path $QuartoZip)) {
    Write-Host "Downloading Quarto CLI v1.5.56 Portable (approx. 150MB)..."
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri "https://github.com/quarto-dev/quarto-cli/releases/download/v1.5.56/quarto-1.5.56-win.zip" -OutFile $QuartoZip -UseBasicParsing
    Write-Host "Download complete."
}

# 2. Extract Quarto CLI
$QuartoBinDir = Join-Path $ToolsDir "bin"
if (-not (Test-Path $QuartoBinDir)) {
    Write-Host "Extracting Quarto CLI..."
    Expand-Archive -Path $QuartoZip -DestinationPath $ToolsDir
    Write-Host "Quarto CLI extracted."
}

# 3. Generate _quarto.yml using Python
Write-Host "Generating _quarto.yml..."
& "C:\Users\Ikeda\AppData\Local\Microsoft\WindowsApps\python.exe" "$BaseDir\convert_summary_to_quarto.py"

# 4. Build rust-computational-physics-tutorial-main using Quarto
$QuartoExe = Join-Path $QuartoDir "bin\quarto.exe"
if (-not (Test-Path $QuartoExe)) {
    Write-Error "Quarto executable not found at $QuartoExe"
}

Write-Host "Building mdBook (Quarto Book)..."
& $QuartoExe render "$BaseDir\rust-computational-physics-tutorial-main\src" --to html

# 5. Build isingModel/Memo.md using Quarto
Write-Host "Building Ising Model Memo..."
& $QuartoExe render "$BaseDir\isingModel\Memo.md" --to html --output "Memo.html"

# 6. Setup portal_html directory
$PortalDir = Join-Path $BaseDir "portal_html"
if (Test-Path $PortalDir) {
    Remove-Item -Path $PortalDir -Recurse -Force -ErrorAction SilentlyContinue
}
New-Item -ItemType Directory -Path $PortalDir | Out-Null

# Copy book_html to portal_html/book
$BookHtmlSource = Join-Path $BaseDir "rust-computational-physics-tutorial-main\book_html"
$BookHtmlDest = Join-Path $PortalDir "book"
Copy-Item -Path $BookHtmlSource -Destination $BookHtmlDest -Recurse

# Copy Memo.html to portal_html/
$MemoSource = Join-Path $BaseDir "Memo.html"
$MemoDest = Join-Path $PortalDir "Memo.html"
Copy-Item -Path $MemoSource -Destination $MemoDest

# Clean up Memo.html from source to keep source clean
Remove-Item -Path $MemoSource -ErrorAction SilentlyContinue

# Copy portal_index.html to portal_html/index.html
$PortalIndexSrc = Join-Path $BaseDir "portal_index.html"
$PortalIndexDest = Join-Path $PortalDir "index.html"
if (Test-Path $PortalIndexSrc) {
    Copy-Item -Path $PortalIndexSrc -Destination $PortalIndexDest
    Write-Host "Portal index page copied to $PortalIndexDest"
} else {
    Write-Warning "Portal index page source not found at $PortalIndexSrc"
}

# Copy Memo resources (like image files if any) if they are created by quarto
# quarto typically embeds images in HTML, so it should be fine.

Write-Host "Web site files successfully generated in $PortalDir!"

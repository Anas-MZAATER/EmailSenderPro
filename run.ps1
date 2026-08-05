# EmailSenderPro PowerShell Launcher
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$SrcPath = Join-Path $ProjectRoot "src"

$env:PYTHONPATH = "$SrcPath;$env:PYTHONPATH"

& python -c "import sys; sys.path.insert(0, r'$SrcPath'); from emailsenderpro.app import main; main()"

# Carga las variables del archivo .env en el entorno actual de PowerShell
if (Test-Path ".env") {
    Get-Content .env | ForEach-Object {
        if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
        $name, $value = $_ -split '=', 2
        Set-Item -Path Env:$name -Value $value
    }
    Write-Host "✅ Variables del archivo .env cargadas correctamente."
} else {
    Write-Host "⚠️ No se encontró el archivo .env en esta carpeta."
}
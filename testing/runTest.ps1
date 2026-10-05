param(
    [Parameter(Position = 0)]
    [int]$Threads = 10,

    [Parameter(Position = 1)]
    [int]$Loops = 10
)

# --- Adjust these paths to match your machine ---
$JMeterBin   = "C:\Program Files (x86)\Apache\apache-jmeter-5.6.3\bin\jmeter.bat"
$TestPlan    = Join-Path $PSScriptRoot "Lab2_Test_Plan.jmx"
$ResultsFile = Join-Path $PSScriptRoot "results.jtl"
$ReportDir   = Join-Path $PSScriptRoot "report"
# --------------------------------------------------

Write-Host "Running with $Threads threads, $Loops loops"

# JMeter refuses to run if old results/report already exist
if (Test-Path $ResultsFile) {
    Remove-Item $ResultsFile -Force
}
if (Test-Path $ReportDir) {
    Remove-Item $ReportDir -Recurse -Force
}

& $JMeterBin `
    -n `
    -t $TestPlan `
    -Jthreads=$Threads `
    -Jloops=$Loops `
    -l $ResultsFile `
    -e -o $ReportDir
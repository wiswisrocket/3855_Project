param(
    [int]$Threads = 10,
    [int]$Loops = 10
)

$COURSE_DIR = $PSScriptRoot

Remove-Item "$COURSE_DIR\results.jtl" -Force -ErrorAction SilentlyContinue
Remove-Item "$COURSE_DIR\report" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "$Threads threads, $Loops loops"

& "C:\Program Files\Apache\apache-jmeter-5.6.3\bin\jmeter.bat" `
    -n `
    -t "$COURSE_DIR\Lab2_Test_Plan.jmx" `
    "-Jthreads=$Threads" `
    "-Jloops=$Loops" `
    -l "$COURSE_DIR\results.jtl" `
    -e `
    -o "$COURSE_DIR\report"
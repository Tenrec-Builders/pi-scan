mkdir -p pi-scan
cp ~/git/pi-scan/src/* pi-scan
cp ~/git/pi-scan/resources/* pi-scan
zip -r pi-scan-update-$1.archive pi-scan

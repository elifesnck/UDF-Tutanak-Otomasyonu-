@echo off
echo ========================================
echo 🚀 UDF Tutanak Otomasyonu
echo ========================================
echo.

echo 📦 Gerekli paketler kontrol ediliyor...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ✅ Başlatılıyor...
echo 🌐 Tarayıcı otomatik açılacak: http://localhost:5000
echo ⏹️  Durdurmak için: Ctrl+C
echo.

python app.py

echo.
echo Program sonlandı. Çıkmak için bir tuşa basın...
pause
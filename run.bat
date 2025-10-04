@echo off
chcp 65001 >nul
echo ========================================
echo 🚀 UDF Tutanak Otomasyonu
echo ========================================
echo.

echo 📦 Gerekli paketler kontrol ediliyor...
python -m pip install --upgrade pip
pip install flask pandas openpyxl

echo.
echo ✅ Başlatılıyor...
echo 🌐 Tarayıcı otomatik açılacak: http://localhost:5000
echo ⏹️  Durdurmak için: Ctrl+C
echo.

:: Yönetici izni olmadan çalıştır
python app.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ Hata: Program çalıştırılamadı
    echo 🔧 Çözüm: Sağ tık -> "Yönetici olarak çalıştır" deneyin
)

echo.
echo Program sonlandı. Çıkmak için bir tuşa basın...
pause

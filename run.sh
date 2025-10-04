#!/bin/bash
echo "========================================"
echo "🚀 UDF Tutanak Otomasyonu"
echo "========================================"
echo

echo "📦 Gerekli paketler kontrol ediliyor..."
python3 -m pip install --upgrade pip
pip3 install -r requirements.txt

echo
echo "✅ Başlatılıyor..."
echo "🌐 Tarayıcıyı açın: http://localhost:5000"
echo "⏹️  Durdurmak için: Ctrl+C"
echo

python3 app.py
import os
import sys
from flask import Flask, render_template_string, request, send_file, jsonify
from datetime import datetime
import pandas as pd
import shutil
import zipfile
import tempfile
import io
import struct

# ==================== AYARLAR ====================
BASE_DIR = r"C:\Users\elife\OneDrive\Masaüstü\TutanakOtomasyon"
CIKTI_KLASORU = os.path.join(BASE_DIR, "cikti_dosyalar")
SABLON_KLASORU = os.path.join(BASE_DIR, "sablonlar")
UDF_KLASORU = os.path.join(BASE_DIR, "udf_dosyalar")
VERI_DOSYASI = os.path.join(BASE_DIR, "veriler.xlsx")

# ŞABLON DOSYALARI
ANLASMA_SABLONU = os.path.join(SABLON_KLASORU, "ANLASMA_TUTANAK.SABLON.udf")
SON_TUTANAK_SABLONU = os.path.join(SABLON_KLASORU, "SON_TUTANAG.SABLON.udf")

# Klasörleri oluştur
for klasor in [CIKTI_KLASORU, SABLON_KLASORU, UDF_KLASORU]:
    os.makedirs(klasor, exist_ok=True)

app = Flask(__name__)

print("🚀 UDF OTOMASYONU BAŞLATILIYOR...")

class UDFGenerator:
    def __init__(self):
        self.required_fields = ['ARABULUCULUK_NO', 'TRFAD_SOYAD']
        self.all_fields = [
            'ARABULUCULUK_NO', 'TRFAD_SOYAD', 'TC', 'TOPLANTI_TARIHI',
            'POLICE_NO', 'SIGORTA_PLAKA', 'HASAR_TARIHI', 'MAGDUR_PLAKA',
            'ARABULUCU_ADI', 'ASIL_ALACAK', 'VEKALET_UCRET', 'ODEME_TARIHI',
            'BANKA_ADI', 'IBAN'
        ]
    
    def generate_both_udf(self, data):
        """Hem Anlaşma hem Son Tutanak oluştur"""
        try:
            arabuluculuk_no = data['ARABULUCULUK_NO']
            
            anlasma_yolu, anlasma_adi = self.generate_single_udf(data, "anlasma")
            son_yolu, son_adi = self.generate_single_udf(data, "son")
            
            print(f"✅ Çift UDF oluşturuldu: {anlasma_adi}, {son_adi}")
            return {
                'anlasma': (anlasma_yolu, anlasma_adi),
                'son': (son_yolu, son_adi)
            }
            
        except Exception as e:
            print(f"❌ Çift UDF oluşturma hatası: {e}")
            raise
    
    def generate_single_udf(self, data, sablon_tipi="anlasma"):
        """Tek UDF dosyası oluştur"""
        try:
            if sablon_tipi == "anlasma" and os.path.exists(ANLASMA_SABLONU):
                sablon_dosya = ANLASMA_SABLONU
                cikti_adi = f"ANLASMA_TUTANAK_{data['ARABULUCULUK_NO']}.udf"
            elif sablon_tipi == "son" and os.path.exists(SON_TUTANAK_SABLONU):
                sablon_dosya = SON_TUTANAK_SABLONU
                cikti_adi = f"SON_TUTANAK_{data['ARABULUCULUK_NO']}.udf"
            else:
                raise FileNotFoundError("Şablon dosyası bulunamadı")
            
            cikti_yolu = os.path.join(CIKTI_KLASORU, cikti_adi)
            
            # Şablonu kopyala
            shutil.copy2(sablon_dosya, cikti_yolu)
            
            # UDF'yi UTF-16-LE encoding ile işle (UYAP'ın kullandığı encoding)
            self.process_udf_utf16(cikti_yolu, data)
            
            print(f"✅ {sablon_tipi} oluşturuldu: {cikti_yolu}")
            return cikti_yolu, cikti_adi
            
        except Exception as e:
            print(f"❌ UDF oluşturma hatası: {e}")
            raise
    
    def process_udf_utf16(self, udf_path, data):
        """UDF'yi UTF-16-LE encoding ile işle (UYAP standardı)"""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # ZIP'i aç
                with zipfile.ZipFile(udf_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # Tüm dosyaları işle
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        self.process_file_utf16(file_path, data)
                
                # Yeniden ZIP'le
                with zipfile.ZipFile(udf_path, 'w', zipfile.ZIP_DEFLATED) as new_zip:
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, temp_dir)
                            new_zip.write(file_path, arcname)
                
        except Exception as e:
            print(f"❌ UDF işleme hatası: {e}")
            raise
    
    def process_file_utf16(self, file_path, data):
        """Dosyayı UTF-16-LE encoding ile işle"""
        try:
            # Dosyayı binary olarak oku
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # UTF-16-LE decoding dene (UYAP'ın kullandığı encoding)
            try:
                text_content = content.decode('utf-16-le')
                print(f"🔧 UTF-16-LE encoding bulundu: {os.path.basename(file_path)}")
                
                modified = False
                for field in self.all_fields:
                    placeholder = f"<<{field}>>"
                    if placeholder in text_content:
                        value = data.get(field, '')
                        if value:
                            # TARİH FORMATI DEĞİŞTİRME - ORJİNAL HALİYLE BIRAK
                            if field.endswith('_TARIHI') and value:
                                # Tarihi olduğu gibi kullan, format değiştirme
                                value = value
                            
                            # Değeri placeholder boyutuna uydur
                            value = self.adjust_value_length(value, len(placeholder))
                            text_content = text_content.replace(placeholder, value)
                            print(f"   ✅ {placeholder} -> {value}")
                            modified = True
                
                if modified:
                    # UTF-16-LE ile tekrar encode et
                    new_content = text_content.encode('utf-16-le')
                    with open(file_path, 'wb') as f:
                        f.write(new_content)
                    return True
                    
            except UnicodeDecodeError:
                # UTF-16-LE değilse, diğer encoding'leri dene
                pass
            
            # UTF-8 encoding dene
            try:
                text_content = content.decode('utf-8')
                print(f"🔧 UTF-8 encoding bulundu: {os.path.basename(file_path)}")
                
                modified = False
                for field in self.all_fields:
                    placeholder = f"<<{field}>>"
                    if placeholder in text_content:
                        value = data.get(field, '')
                        if value:
                            # TARİH FORMATI DEĞİŞTİRME - ORJİNAL HALİYLE BIRAK
                            if field.endswith('_TARIHI') and value:
                                # Tarihi olduğu gibi kullan, format değiştirme
                                value = value
                            
                            # Değeri placeholder boyutuna uydur
                            value = self.adjust_value_length(value, len(placeholder))
                            text_content = text_content.replace(placeholder, value)
                            print(f"   ✅ {placeholder} -> {value}")
                            modified = True
                
                if modified:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(text_content)
                    return True
                    
            except UnicodeDecodeError:
                print(f"   ❌ Encoding bulunamadı: {os.path.basename(file_path)}")
            
        except Exception as e:
            print(f"   ❌ Dosya işleme hatası: {e}")
        
        return False
    
    def adjust_value_length(self, value, target_length):
        """Değeri placeholder boyutuna uydur"""
        if len(value) < target_length:
            # Sağa boşluk ekle
            return value + ' ' * (target_length - len(value))
        elif len(value) > target_length:
            # Kısalt
            return value[:target_length]
        else:
            # Aynı boyutta
            return value

def save_to_excel(data):
    """Veriyi Excel'e kaydet"""
    try:
        for sablon_tipi in ['anlasma', 'son']:
            yeni_veri = data.copy()
            yeni_veri['SABLON_TIPI'] = sablon_tipi
            yeni_veri['OLUSTURULMA_TARIHI'] = datetime.now().strftime("%d.%m.%Y %H:%M")
            yeni_veri['DOSYA_ADI'] = f"tutanak_{data['ARABULUCULUK_NO']}_{sablon_tipi}.udf"
            
            if os.path.exists(VERI_DOSYASI):
                df = pd.read_excel(VERI_DOSYASI)
                df = pd.concat([df, pd.DataFrame([yeni_veri])], ignore_index=True)
            else:
                df = pd.DataFrame([yeni_veri])
            
            df.to_excel(VERI_DOSYASI, index=False)
        
        print(f"✅ Excel'e kaydedildi: {data['ARABULUCULUK_NO']}")
        return True
    except Exception as e:
        print(f"❌ Excel kaydetme hatası: {e}")
        return False

# HTML TEMPLATE
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UDF Tutanak Otomasyonu</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; 
            padding: 20px;
        }
        .container { 
            max-width: 800px; 
            margin: 0 auto; 
            background: white; 
            padding: 30px; 
            border-radius: 15px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        h1 { 
            color: #333; 
            text-align: center; 
            margin-bottom: 10px;
            font-size: 2.2em;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 1.1em;
        }
        .form-group { 
            margin-bottom: 20px; 
        }
        label { 
            display: block; 
            margin-bottom: 8px; 
            font-weight: 600; 
            color: #333;
        }
        .required label::after {
            content: " *";
            color: red;
        }
        input, select { 
            width: 100%; 
            padding: 12px; 
            border: 2px solid #e1e1e1; 
            border-radius: 8px; 
            font-size: 14px; 
        }
        input:focus, select:focus { 
            outline: none; 
            border-color: #667eea; 
        }
        .btn { 
            color: white; 
            padding: 15px; 
            border: none; 
            border-radius: 8px; 
            cursor: pointer; 
            font-size: 16px; 
            font-weight: 600; 
            width: 100%;
            margin-top: 10px;
            transition: all 0.3s;
        }
        .btn-anlasma {
            background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
        }
        .btn-son {
            background: linear-gradient(135deg, #6f42c1 0%, #5a2d91 100%);
        }
        .btn-both {
            background: linear-gradient(135deg, #fd7e14 0%, #e55a00 100%);
        }
        .btn:hover { 
            opacity: 0.9;
            transform: translateY(-2px);
        }
        .info-box {
            background: #e7f3ff;
            border: 1px solid #b3d9ff;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
        }
        .optional-note {
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }
        .download-buttons {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-top: 20px;
        }
        .download-both {
            grid-column: 1 / -1;
        }
        .button-icon {
            margin-right: 8px;
        }
        .signature {
            text-align: center;
            margin-top: 20px;
            padding: 15px;
            background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
            border-radius: 8px;
            font-weight: bold;
            color: #8b6914;
            font-size: 1.1em;
            border: 2px solid #ffc107;
        }
        .currency-note {
            font-size: 0.8em;
            color: #28a745;
            margin-top: 5px;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📋 UDF Tutanak Otomasyonu</h1>
        <div class="subtitle">Elif Ebrar Sancak Hayratıdır</div>
        
        <div class="info-box">
            <strong>✅ UTF-16 SİSTEMİ AKTİF!</strong><br>
            • UYAP encoding (UTF-16-LE) tespiti<br>
            • Otomatik alan doldurma<br>
            • Boyut koruma - kayma yok<br>
            • Çift UDF desteği<br>
            • <strong>Tarih formatı koruma</strong> - kopyalanan format aynen kullanılır<br>
            • <strong>Virgül desteği</strong> - 200.200,00 formatında yazabilirsiniz
        </div>

        <form action="/generate" method="post" id="tutanakForm">
            <!-- ZORUNLU ALANLAR -->
            <div class="form-group required">
                <label>Arabuluculuk No:</label>
                <input type="text" name="ARABULUCULUK_NO" required placeholder="2024-001">
            </div>
            
            <div class="form-group required">
                <label>Taraf Ad Soyad:</label>
                <input type="text" name="TRFAD_SOYAD" required placeholder="Ahmet Yılmaz">
            </div>
            
            <!-- İSTEĞE BAĞLI ALANLAR -->
            <div class="form-group">
                <label>TC Kimlik No:</label>
                <input type="text" name="TC" placeholder="11 haneli TC no">
                <div class="optional-note">İsteğe bağlı - boş bırakılabilir</div>
            </div>
            
            <div class="form-group">
                <label>Toplantı Tarihi:</label>
                <input type="text" name="TOPLANTI_TARIHI" placeholder="21.10.2025 veya 21/10/2025">
                <div class="optional-note">İsteğe bağlı - istediğiniz formatta girebilirsiniz</div>
            </div>
            
            <div class="form-group">
                <label>Poliçe No:</label>
                <input type="text" name="POLICE_NO" placeholder="">
                <div class="optional-note">İsteğe bağlı - boş bırakılabilir</div>
            </div>
            
            <div class="form-group">
                <label>Sigorta Plaka:</label>
                <input type="text" name="SIGORTA_PLAKA" placeholder="34 ABC 123">
                <div class="optional-note">İsteğe bağlı - boş bırakılabilir</div>
            </div>
            
            <div class="form-group">
                <label>Hasar Tarihi:</label>
                <input type="text" name="HASAR_TARIHI" placeholder="15.10.2025 veya 15/10/2025">
                <div class="optional-note">İsteğe bağlı - istediğiniz formatta girebilirsiniz</div>
            </div>
            
            <div class="form-group">
                <label>Mağdur Plaka:</label>
                <input type="text" name="MAGDUR_PLAKA" placeholder="34 XYZ 456">
                <div class="optional-note">İsteğe bağlı - boş bırakılabilir</div>
            </div>
            
            <div class="form-group">
                <label>Arabulucu Adı:</label>
                <input type="text" name="ARABULUCU_ADI" placeholder="">
                <div class="optional-note">İsteğe bağlı - boş bırakılabilir</div>
            </div>
            
            <div class="form-group">
                <label>Asıl Alacak (TL):</label>
                <input type="text" name="ASIL_ALACAK" placeholder="200.200,00 veya 200200,00">
                <div class="currency-note">✅ Virgül kullanabilirsiniz: 1.500,00 veya 2500,50</div>
            </div>
            
            <div class="form-group">
                <label>Vekalet Ücret (TL):</label>
                <input type="text" name="VEKALET_UCRET" placeholder="1.250,00 veya 1250,00">
                <div class="currency-note">✅ Virgül kullanabilirsiniz: 500,00 veya 1.000,00</div>
            </div>
            
            <div class="form-group">
                <label>Ödeme Tarihi:</label>
                <input type="text" name="ODEME_TARIHI" placeholder="25.10.2025 veya 25/10/2025">
                <div class="optional-note">İsteğe bağlı - istediğiniz formatta girebilirsiniz</div>
            </div>
            
            <div class="form-group">
                <label>Banka Adı:</label>
                <input type="text" name="BANKA_ADI" placeholder="Ziraat Bankası">
                <div class="optional-note">İsteğe bağlı - boş bırakılabilir</div>
            </div>
            
            <div class="form-group">
                <label>IBAN:</label>
                <input type="text" name="IBAN" placeholder="TR00 0000 0000 0000 0000 0000 00">
                <div class="optional-note">İsteğe bağlı - boş bırakılabilir</div>
            </div>
            
            <!-- İNDİRME BUTONLARI -->
            <div class="download-buttons">
                <button type="submit" name="download_type" value="anlasma" class="btn btn-anlasma">
                    <span class="button-icon">🤝</span> Anlaşma Tutanağı
                </button>
                
                <button type="submit" name="download_type" value="son" class="btn btn-son">
                    <span class="button-icon">📄</span> Son Tutanak
                </button>
                
                <button type="submit" name="download_type" value="both" class="btn btn-both download-both">
                    <span class="button-icon">🚀</span> İkisini Birden İndir
                </button>
            </div>
        </form>

        <div class="signature">
            ⭐ Elif Ebrar Sancak Hayratıdır ⭐
        </div>
    </div>

    <script>
        document.getElementById('tutanakForm').addEventListener('submit', function(e) {
            const arabuluculukNo = document.querySelector('input[name="ARABULUCULUK_NO"]').value;
            const tarafAdSoyad = document.querySelector('input[name="TRFAD_SOYAD"]').value;
            
            if (!arabuluculukNo || !tarafAdSoyad) {
                e.preventDefault();
                alert('Lütfen zorunlu alanları (Arabuluculuk No ve Taraf Ad Soyad) doldurun.');
                return false;
            }
        });

        // Virgül formatı için input event listener'ları
        document.querySelector('input[name="ASIL_ALACAK"]').addEventListener('input', function(e) {
            // Sadece rakam, nokta ve virgüle izin ver
            this.value = this.value.replace(/[^\d,.]/g, '');
        });

        document.querySelector('input[name="VEKALET_UCRET"]').addEventListener('input', function(e) {
            // Sadece rakam, nokta ve virgüle izin ver
            this.value = this.value.replace(/[^\d,.]/g, '');
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/generate', methods=['POST'])
def generate_udf():
    try:
        data = request.form.to_dict()
        download_type = data.pop('download_type', 'both')
        
        # Boş alanları temizle - VİRGÜL DESTEĞİ EKLENDİ
        cleaned_data = {}
        for key, value in data.items():
            if value and value.strip():
                # Ücret alanları için virgül/nokta kontrolü
                if key in ['ASIL_ALACAK', 'VEKALET_UCRET']:
                    # Noktaları kaldır, virgülü noktaya çevir (opsiyonel)
                    # VEYA olduğu gibi bırak - UDF şablonu nasıl bekliyorsa
                    cleaned_value = value.strip()
                    # Sadece temizle, formatı koru
                    cleaned_value = cleaned_value.replace(' ', '')  # Boşlukları temizle
                    cleaned_data[key] = cleaned_value
                else:
                    cleaned_data[key] = value.strip()
        
        print(f"📝 İstek: {download_type} - {cleaned_data['ARABULUCULUK_NO']}")
        print(f"💰 Ücret verileri: ASIL_ALACAK={cleaned_data.get('ASIL_ALACAK', '')}, VEKALET_UCRET={cleaned_data.get('VEKALET_UCRET', '')}")
        
        generator = UDFGenerator()
        
        if download_type == 'both':
            # İkisini birden oluştur ve ZIP olarak indir
            udf_files = generator.generate_both_udf(cleaned_data)
            save_to_excel(cleaned_data)
            
            # ZIP oluştur
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for sablon_tipi, (file_path, file_name) in udf_files.items():
                    zip_file.write(file_path, file_name)
            
            zip_buffer.seek(0)
            
            return send_file(
                zip_buffer,
                as_attachment=True,
                download_name=f"TUTANAKLAR_{cleaned_data['ARABULUCULUK_NO']}.zip",
                mimetype='application/zip'
            )
            
        else:
            # Tek birini oluştur
            udf_yolu, udf_adi = generator.generate_single_udf(cleaned_data, download_type)
            save_to_excel(cleaned_data)
            
            return send_file(
                udf_yolu,
                as_attachment=True,
                download_name=udf_adi,
                mimetype='application/octet-stream'
            )
        
    except Exception as e:
        return f"❌ Hata: {str(e)}", 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 UDF OTOMASYONU - UTF-16 SİSTEMİ")
    print("="*60)
    print("✅ UYAP encoding (UTF-16-LE) tespiti")
    print("✅ Otomatik alan doldurma") 
    print("✅ Boyut koruma - kayma yok")
    print("✅ Çift UDF desteği")
    print("✅ Tarih formatı koruma - kopyalanan format aynen kullanılır")
    print("✅ Virgül desteği - 200.200,00 formatında yazılabilir")
    print("⭐ Elif Ebrar Sancak Hayratıdır")
    print("="*60)
    print("🌐 http://127.0.0.1:5000")
    print("="*60)
    
    app.run(debug=True, host='127.0.0.1', port=5000)
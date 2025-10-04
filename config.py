import os

# TEMEL AYARLAR
BASE_DIR = os.path.join(os.path.expanduser("~"), "UDF_Otomasyon")
CIKTI_KLASORU = os.path.join(BASE_DIR, "cikti_dosyalar")
SABLON_KLASORU = os.path.join(BASE_DIR, "sablonlar")
VERI_DOSYASI = os.path.join(BASE_DIR, "veriler.xlsx")

# ŞABLON DOSYALARI
ANLASMA_SABLONU = os.path.join(SABLON_KLASORU, "ANLASMA_TUTANAK.SABLON.udf")
SON_TUTANAK_SABLONU = os.path.join(SABLON_KLASORU, "SON_TUTANAG.SABLON.udf")

# DİĞER AYARLAR
DEBUG = False
HOST = 'localhost'
PORT = 5000
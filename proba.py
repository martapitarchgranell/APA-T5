import estereo

# Define la ruta de tu carpeta para no tener que escribirla todo el rato
ruta_carpeta = "/Volumes/KODAK/apat5/"

# 1. Probar estereo2mono
print("Probando estereo2mono...")
estereo.estereo2mono(ruta_carpeta + "komm.wav", ruta_carpeta + "komm_mono.wav", canal=2)

# 2. Extracció de canals individuals
print("Extrayendo canales izquierdo y derecho...")
estereo.estereo2mono(ruta_carpeta + "komm.wav", ruta_carpeta + "komm_izq.wav", canal=0)
estereo.estereo2mono(ruta_carpeta + "komm.wav", ruta_carpeta + "komm_der.wav", canal=1)

# 3. Probar mono2estereo
print("Probando mono2estereo...")
estereo.mono2estereo(ruta_carpeta + "komm_izq.wav", ruta_carpeta + "komm_der.wav", ruta_carpeta + "komm_reconstruido.wav")

# 4. Probar codEstereo
print("Probando codEstereo...")
estereo.codEstereo(ruta_carpeta + "komm.wav", ruta_carpeta + "komm_codificado.wav")

# 5. Probar decEstereo
print("Probando decEstereo...")
estereo.decEstereo(ruta_carpeta + "komm_codificado.wav", ruta_carpeta + "komm_decodificado.wav")

print("¡Pruebas ejecutadas con éxito!")
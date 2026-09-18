import easyocr

# Inicializar el lector (admite varios idiomas)
reader = easyocr.Reader(['es'])

# Leer texto de la imagen
resultados = reader.readtext('tu_imagen.jpg')

# Filtrar solo los números (o usar allowlist)
for bbox, texto, prob in resultados:
  if texto.isdigit():
    print(f'Número detectado: {texto} (Confianza: {prob:.2f})')
"""
Nom de l'alumne: Marta Pitarch Granell
Descripció: Mòdul per a la manipulació de canals de senyals d'àudio estèreo,
             conversió a mono i codificació mitjançant els bits menys
             significatius en fitxers WAVE de 16 i 32 bits.
"""

import struct


def _llegir_wav(fic):
    """
    Funció auxiliar interna que llegeix un fitxer WAVE, valida el seu format
    i retorna la capçalera RIFF, el subcacho 'fmt ' i les dades d'àudio.
    """
    with open(fic, "rb") as f:
        # Llegir la capçalera RIFF inicial (12 bytes)
        riff_header = f.read(12)
        if (
            len(riff_header) < 12
            or riff_header[0:4] != b"RIFF"
            or riff_header[8:12] != b"WAVE"
        ):
            raise ValueError(f"El fitxer {fic} no és un fitxer WAVE vàlid.")

        fmt_chunk = b""
        data_chunk = b""

        # Llegir els subcachos seqüencialment
        while True:
            chunk_id = f.read(4)
            if len(chunk_id) < 4:
                break  # Final de fitxer

            (chunk_size,) = struct.unpack("<I", f.read(4))
            chunk_data = f.read(chunk_size)

            if chunk_id == b"fmt ":
                fmt_chunk = chunk_id + struct.pack("<I", chunk_size) + chunk_data
            elif chunk_id == b"data":
                data_chunk = chunk_data
                data_header = chunk_id + struct.pack("<I", chunk_size)
                break

        if not fmt_chunk or not data_chunk:
            raise ValueError(
                f"Manquen subcachos essencials ('fmt ' o 'data') a {fic}."
            )

        return riff_header, fmt_chunk, data_header, data_chunk


def _escriure_wav(fic_desti, fmt_chunk, data_payload):
    """
    Funció auxiliar interna que empaqueta i escriu un fitxer WAVE complet
    calculant les mides de les capçaleres de manera dinàmica.
    """
    # La mida del cacho data són els 8 bytes de la seva capçalera + el payload de dades
    data_chunk = b"data" + struct.pack("<I", len(data_payload)) + data_payload
    # La mida total del RIFF és: 4 bytes ('WAVE') + mida de 'fmt ' + mida de 'data'
    riff_size = 4 + len(fmt_chunk) + len(data_chunk)
    riff_header = b"RIFF" + struct.pack("<I", riff_size) + b"WAVE"

    with open(fic_desti, "wb") as f:
        f.write(riff_header)
        f.write(fmt_chunk)
        f.write(data_chunk)


def estereo2mono(ficEste, ficMono, canal=2):
    """
    Llegeix un fitxer estèreo de 16 bits i extreu el canal esquerre (0),
    el dret (1), la semisuma (2) o la semidiferència (3), desant-lo en mono.
    """
    riff_header, fmt_chunk, _, data_chunk = _llegir_wav(ficEste)

    num_channels = struct.unpack("<H", fmt_chunk[10:12])[0]
    if num_channels != 2:
        raise ValueError("El fitxer d'origen ha de ser estèreo.")

    num_samples = len(data_chunk) // 2
    mostres = struct.unpack(f"<{num_samples}h", data_chunk)

    izq = mostres[0::2]
    der = mostres[1::2]

    if canal == 0:
        res = izq
    elif canal == 1:
        res = der
    elif canal == 2:
        res = [int((l + r) / 2) for l, r in zip(izq, der)]
    elif canal == 3:
        res = [int((l - r) / 2) for l, r in zip(izq, der)]
    else:
        raise ValueError("Canal no vàlid. Ha de ser 0, 1, 2 o 3.")

    fmt_llista = list(fmt_chunk)
    fmt_llista[10:12] = struct.pack("<H", 1)  # Canals = 1
    fmt_llista[22:24] = struct.pack("<H", 2)  # BlockAlign = 1 * (16 // 8) = 2

    sample_rate = struct.unpack("<I", fmt_chunk[12:16])[0]
    fmt_llista[16:20] = struct.pack("<I", sample_rate * 2)
    fmt_chunk_mono = bytes(fmt_llista)

    data_payload = struct.pack(f"<{len(res)}h", *res)
    _escriure_wav(ficMono, fmt_chunk_mono, data_payload)


def mono2estereo(ficIzq, ficDer, ficEste):
    """
    Llegeix dos fitxers monofònics (esquerre i dret) de 16 bits
    i els combina per construir un únic fitxer estèreo.
    """
    _, fmt_izq, _, data_izq = _llegir_wav(ficIzq)
    _, _, _, data_der = _llegir_wav(ficDer)

    mostres_izq = struct.unpack(f"<{len(data_izq)//2}h", data_izq)
    mostres_der = struct.unpack(f"<{len(data_der)//2}h", data_der)

    min_len = min(len(mostres_izq), len(mostres_der))

    mostres_estereo = [
        val
        for par in zip(mostres_izq[:min_len], mostres_der[:min_len])
        for val in par
    ]

    fmt_llista = list(fmt_izq)
    fmt_llista[10:12] = struct.pack("<H", 2)  # Canals = 2
    fmt_llista[22:24] = struct.pack("<H", 4)  # BlockAlign = 2 * 2 = 4
    sample_rate = struct.unpack("<I", fmt_izq[12:16])[0]
    fmt_llista[16:20] = struct.pack("<I", sample_rate * 4)  # ByteRate
    fmt_chunk_estereo = bytes(fmt_llista)

    data_payload = struct.pack(f"<{len(mostres_estereo)}h", *mostres_estereo)
    _escriure_wav(ficEste, fmt_chunk_estereo, data_payload)


def codEstereo(ficEste, ficCod):
    """
    Llegeix un fitxer estèreo de 16 bits, calcula la semisuma i la semidiferència,
    i ho empaqueta en un fitxer monofònic de 32 bits on:
    - Els 16 bits més significatius contenen la semisuma.
    - Els 16 bits menys significatius contenen la semidiferència.
    """
    _, fmt_chunk, _, data_chunk = _llegir_wav(ficEste)

    num_samples = len(data_chunk) // 2
    mostres = struct.unpack(f"<{num_samples}h", data_chunk)

    izq = mostres[0::2]
    der = mostres[1::2]
    min_len = min(len(izq), len(der))

    mostres_32bits = [
        (int((l + r) / 2) << 16) | (int((l - r) / 2) & 0xFFFF)
        for l, r in zip(izq[:min_len], der[:min_len])
    ]

    fmt_llista = list(fmt_chunk)
    fmt_llista[10:12] = struct.pack("<H", 1)  # Canals = 1
    fmt_llista[22:24] = struct.pack("<H", 4)  # BlockAlign = 1 * (32 // 8) = 4
    fmt_llista[24:26] = struct.pack("<H", 32)  # BitsPerSample = 32

    sample_rate = struct.unpack("<I", fmt_chunk[12:16])[0]
    fmt_llista[16:20] = struct.pack("<I", sample_rate * 4)  # ByteRate
    fmt_chunk_cod = bytes(fmt_llista)

    data_payload = struct.pack(f"<{len(mostres_32bits)}i", *mostres_32bits)
    _escriure_wav(ficCod, fmt_chunk_cod, data_payload)


def decEstereo(ficCod, ficEste):
    """
    Decodifica un fitxer monofònic de 32 bits per restaurar els canals originals
    L i R de 16 bits basant-se en la seva suma i diferència.
    """
    # 1. Lectura i validació del fitxer d'entrada usant la funció comuna
    _, fmt_chunk, _, data_chunk = _llegir_wav(ficCod)

    num_channels = struct.unpack("<H", fmt_chunk[10:12])[0]
    bits_per_sample = struct.unpack("<H", fmt_chunk[24:26])[0]

    if num_channels != 1 or bits_per_sample != 32:
        raise ValueError(
            "El fitxer d'origen ha de ser de 32 bits i un sol canal."
        )

    # 2. Extracció dels paquets de dades de 32 bits (unsigned int 'I' per processament binari)
    total_mostres = len(data_chunk) // 4
    dades_32 = struct.unpack(f"<{total_mostres}I", data_chunk)

    # 3. Processament i decodificació dels canals (Suma/Diferència)
    audio_intercalat = []
    for bloc in dades_32:
        val_superior = bloc >> 16
        val_inferior = bloc & 0xFFFF

        # Conversió a enter de 16 bits amb signe (complement a dos manual)
        mig = val_superior if val_superior < 32768 else val_superior - 65536
        dif = val_inferior if val_inferior < 32768 else val_inferior - 65536

        # Reconstrucció de canals: L = M + D, R = M - D
        canal_L = mig + dif
        canal_R = mig - dif

        audio_intercalat.extend([canal_L, canal_R])

    # 4. Configurar la capçalera per a un estèreo de 16 bits estàndard
    fmt_llista = list(fmt_chunk)
    fmt_llista[10:12] = struct.pack("<H", 2)  # Canals = 2
    fmt_llista[22:24] = struct.pack("<H", 4)  # BlockAlign = 2 * (16 // 8) = 4
    fmt_llista[24:26] = struct.pack("<H", 16)  # BitsPerSample = 16

    sample_rate = struct.unpack("<I", fmt_chunk[12:16])[0]
    fmt_llista[16:20] = struct.pack("<I", sample_rate * 4)  # ByteRate
    fmt_chunk_estereo = bytes(fmt_llista)

    # Empaquetem com a enters de 16 bits amb signe ('h')
    data_payload = struct.pack(f"<{len(audio_intercalat)}h", *audio_intercalat)

    # Generació de l'arxiu de sortida
    _escriure_wav(ficEste, fmt_chunk_estereo, data_payload)
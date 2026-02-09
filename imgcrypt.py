#!/usr/bin/env python3
from pickletools import optimize
import sys
import os
import zlib
import math
import numpy as np
from PIL import Image


def get_header(data_len):
    """Membuat header 4 byte untuk menyimpan ukuran file asli."""
    return data_len.to_bytes(4, byteorder="big")


def parse_header(data_bytes):
    """Membaca 4 byte pertama untuk mengetahui ukuran file asli."""
    return int.from_bytes(data_bytes[:4], byteorder="big")


def encode(input_file, output_image):
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' tidak ditemukan.")
        return

    print(f"Mengenkripsi: {input_file} -> {output_image}...")

    # Baca file binary
    with open(input_file, "rb") as f:
        raw_data = f.read()

    file_size = len(raw_data)

    # KOMPRESI DATA (ZLIB) - Langkah Baru
    # Kita kompres dulu byte-nya sebelum dijadikan piksel
    print(f"   Mengompresi data...")
    compressed_data = zlib.compress(raw_data, level=9)
    compressed_size = len(compressed_data)

    # Hitung rasio penghematan
    ratio = (1 - (compressed_size / file_size)) * 100
    print(f"   Ukuran: {file_size:,} -> {compressed_size:,} bytes (Hemat {ratio:.1f}%)")

    # Tambahkan Header (4 byte) di depan data
    # Ini penting agar saat decode kita tahu kapan harus berhenti membaca
    data_with_header = get_header(file_size) + raw_data

    total_bytes = len(data_with_header)

    # Hitung dimensi gambar (harus persegi)
    # 1 pixel = 3 bytes (R, G, B)
    required_pixels = math.ceil(total_bytes / 3)
    dimension = math.ceil(math.sqrt(required_pixels))

    # Tambahkan Padding (byte kosong) agar pas dengan ukuran matriks gambar
    padding_len = (dimension * dimension * 3) - total_bytes
    final_data = data_with_header + (b"\0" * padding_len)

    # Ubah array byte menjadi array 3D (Tinggi, Lebar, RGB)
    np_arr = np.frombuffer(final_data, dtype=np.uint8)
    np_arr = np_arr.reshape((dimension, dimension, 3))

    # Buat gambar dan simpan sebagai PNG (Lossless)
    img = Image.fromarray(np_arr, mode="RGB")
    img.save(output_image, "PNG", optimize=True, compress_level=9)

    print(f"Sukses! Gambar tersimpan di: {output_image}")
    print(
        f"Info: Ukuran asli {file_size} bytes, Dimensi gambar {dimension}x{dimension} px."
    )


def decode(input_image, output_file):
    if not os.path.exists(input_image):
        print(f"Error: Gambar '{input_image}' tidak ditemukan.")
        return

    print(f"Mendekripsi: {input_image} -> {output_file}...")

    try:
        # Buka gambar
        img = Image.open(input_image)

        # Ubah gambar ke numpy array lalu ke bytes datar
        np_arr = np.array(img)
        flat_data = np_arr.tobytes()

        # Baca Header (4 byte pertama)
        file_size = parse_header(flat_data)

        # Ambil data asli sesuai ukuran header (buang padding & header)
        compressed_data = flat_data[4 : 4 + file_size]

        # Dekompresi data
        original_data = zlib.decompress(compressed_data)

        # Tulis ke file
        with open(output_file, "wb") as f:
            f.write(original_data)

        print(f"Sukses! File dipulihkan ke: {output_file}")

    except Exception as e:
        print(f"Gagal: File gambar mungkin rusak atau bukan hasil enkripsi alat ini.")
        print(f"Detail error: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Penggunaan:")
        print("  Enkripsi: python imgcrypt.py -e <input_file> <output.png>")
        print("  Dekripsi: python imgcrypt.py -d <input.png> <output_file>")
        sys.exit(1)

    mode = sys.argv[1]
    input_path = sys.argv[2]
    output_path = sys.argv[3]

    if mode == "-e":
        encode(input_path, output_path)
    elif mode == "-d":
        decode(input_path, output_path)
    else:
        print("Mode tidak dikenal. Gunakan -e atau -d.")

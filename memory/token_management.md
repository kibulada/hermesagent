# Token Management & Context Optimization

- **Ekspektasi User:** Pembatasan input token proaktif agar thread panjang tidak melebihi limit input (~190k), dengan tetap mempertahankan poin-poin inti konteks percakapan.

- **Aturan Operasional Efisiensi Token & Retensi Konteks:**
    1. **Penggunaan RTK (Rust Token Killer)**: Gunakan RTK untuk memangkas output command CLI/terminal secara otomatis (hemat 60-90% token dev ops).
    2. **Filtering Tool Output**: WAJIB memotong/memfilter keluaran API/CLI menggunakan `jq`, `grep`, `head -n 20`, atau `tail -n 20`. Jangan dump JSON/log mentah.
    3. **Rangkuman Konteks Padat (Memory Anchor)**: Pada percakapan panjang, simpan poin penting (seperti nomor tiket, endpoint, status MR, dan temuan kunci) ke file memory/notes lokal, lalu sampaikan ringkasan padatnya di thread.
    4. **Pemuatan Selektif**: Hanya baca file/bagian file yang relevan dengan pertanyaan saat ini.
    5. **Sub-agent / Task Isolation**: Gunakan sub-task terisolasi untuk tugas pencarian/investigasi berat agar tidak membebankan history thread utama.
    6. **Respons Padat & Faktual**: Hindari narasi/penjelasan berulang, fokus pada status dan temuan kunci agar respon selalu nyambung tanpa menghamburkan token.
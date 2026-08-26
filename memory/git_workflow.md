# Git Workflow

- **Sumber Analisis Kode:**
    - `git pull develop` langsung dari GitLab (bukan salinan lokal `D:\Hermes-QA\sourcecode`).
    - Jika MR tidak ditemukan:
        - Cek langsung dari daftar commit di branch `develop`.
        - Atau secara eksplisit cek branch `develop`.
        - Pastikan untuk `git pull` terlebih dahulu agar kode terbaru.
- **Lokal Repo `D:\Hermes-QA\sourcecode`:**
    - Selalu `git pull` dari branch `develop` untuk tujuan testing.
- **Cek dari GitLab:**
    - Gunakan API GitLab langsung, bukan file lokal.
- **Branch Master:**
    - Jangan `git pull master` kecuali ada instruksi eksplisit.
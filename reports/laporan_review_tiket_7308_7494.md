# Laporan Review & Analisis Perbaikan Tiket #7308 & #7494
**Sistem / Proyek**: Kesia SIMRS  
**Tanggal Review**: 31 Juli 2026  
**Reviewer**: Salsabila (Hermes QA)  

---

## 📌 Ringkasan Status Tiket

| No | ID Tiket | Komponen | Judul / Deskripsi | Target Branch | Status Review |
|---|---|---|---|---|---|
| 1 | **#7494** | `kesia-fe` | [FE] Adjustment feature notification | `develop` (!7293) | ✅ **LULUS** |
| 2 | **#7308** | `sirs-masterdata-microservice` | Config `isNotificationV2` | `develop` (!1118) | ✅ **LULUS** |
| 3 | **#7308** | `sirs-notification-microservice` | Infra WebSocket & Group Notification Read | `develop` (!65, !73) | ⚠️ **DEFECT & PERFORMANCE ISSUE** |

---

## 🚨 Temuan Defect & Isu Performa di Branch `develop` (`sirs-notification-microservice`)

**Lokasi File**: `controller/PushNotificationController.js:189-215`

### 1. Defect Logis: Race Condition pada `Promise.all`
* **Permasalahan**: `dao.list` (baca data) dan `dao.update` (ubah status data) dijalankan secara **paralel** di dalam `Promise.all`:
  ```javascript
  return Promise.all([
    dao.list(findByGroupParam),
    dao.update({ status: true }, { notificationGroupId: groupId })
  ]).then(([groupResult]) => { ... })
  ```
* **Dampak**: Waktu eksekusi tidak terprediksi (Non-deterministic). Jika `dao.list` selesai *sesudah* `dao.update` berjalan, maka pesan sudah terlanjur berstatus `status: true`. Akibatnya `affectedUserIds` menjadi kosong dan signal `refresh` **gagal dikirimkan ke user lain dalam unit**.

### 2. Isu Performa: Query Database Redundant & Hardcoded Limit
* **Permasalahan**: Setelah melakukan update massal berdasarkan `notificationGroupId`, controller melakukan loop lagi untuk melakukan `dao.update` individual per-ID:
  ```javascript
  return Promise.all(
    groupMessages.map(msg => dao.update({ status: true }, { id: msg.id }))
  )
  ```
* **Dampak**: Menghasilkan **N+1 UPDATE query** ke database. Jika 1 notifikasi dikirim ke unit berisi 50 user, terjadi 51 kali query UPDATE ke DB.
* **Batas Limit**: `limit = 1000` di-hardcode. Jika terdapat >1000 pesan/target dalam grup, sisanya terpotong.

### 3. Isu Performa (FE/BE): Potential Thundering Herd Effect
* **Permasalahan**: Saat 1 user membaca notifikasi, BE melakukan broadcast `{ method: "refresh" }` ke seluruh WS client di unit tersebut. Seluruh tab browser perawat yang aktif akan serentak mengirimkan payload `{ action: "reload" }` ke WS BE.
* **Dampak**: Terjadi lonjakan query database serentak (Multi-read spike) dari banyak user aktif di unit yang sama dalam detik yang persis sama.

---

## 💡 Rekomendasi Solusi & Adjustment Kode

### 1. Refactor BE (`sirs-notification-microservice/controller/PushNotificationController.js`)
Ganti logika penanganan `notifType === 'V2'` menjadi operasi sekuensial dan atomic:

```javascript
if (notifType === 'V2') {
  dao.model.findOne({ where: { id: notificationId } }).then(targetMessage => {
    if (!targetMessage) return

    const { notificationGroupId: groupId } = targetMessage

    if (!groupId) {
      return dao.update({ status: true }, { id: notificationId }).then(() => {
        dao.getTotalUnread(userId, channel).then(unread => {
          sendMessage(wsInstance, channel, userId, {
            unread,
            method: 'patch',
            messages: { id: notificationId, status: true }
          })
        })
      })
    }

    // 1. Ambil ID user yang masih unread SEBELUM di-update
    dao.findUnreadByGroupId(groupId).then(unreadRecords => {
      const affectedUserIds = [...new Set(unreadRecords.map(r => r.targetUserId).filter(Boolean))]

      // 2. Update massal sekaligus (Atomic Query)
      return dao.readGroup(groupId).then(() => {
        const broadcastTargets = [...new Set([...affectedUserIds, userId])]

        // 3. Broadcast signal refresh ke user terdampak
        broadcastTargets.forEach(targetId => {
          sendMessage(wsInstance, channel, targetId, { method: 'refresh' })
        })
      })
    }).catch(e => error(e))
  })
}
```

### 2. Mitigasi FE (`kesia-fe/src/utils/context/NotificationContext/index.js`)
Tambahkan jitter delay (100–300ms) saat menerima signal `refresh` untuk mencegah Thundering Herd ke DB:

```javascript
} else if (response?.data?.data?.method === "refresh") {
  if (newClient.readyState === newClient.OPEN) {
    const jitter = Math.floor(Math.random() * 200) // Delay acak 0-200ms
    setTimeout(() => {
      newClient.send(
        JSON.stringify({
          target: user.id,
          action: "reload",
        })
      )
    }, jitter)
  }
}
```

---

## ⚡ Dampak Jika Adjustment Tidak Dilakukan

1. **Inkosistensi UI Notification**: Notifikasi di screen perawat lain tidak otomatis ter-update sebagai terbaca akibat gagalnya broadcast signal `refresh` (karena race condition).
2. **Lonjakan Load DB**: Eksekusi puluhan query update individual per 1 klik user akan membuang koneksi DB dan meningkatkan latency API.
3. **Penurunan Performa WS Service**: Lonjakan request `reload` bersamaan saat notifikasi baru dibaca berpotensi memicu CPU/Memory spike di pod Kubernetes.
4. **Requirement Filtering Belum Utuh**: Logika pemilahan penerima notifikasi spesifik role/unit memerlukan penyesuaian payload pengirim dari `sirs-emr-microservice`.

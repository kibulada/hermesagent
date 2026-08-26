**Tiket**: #7308 — [BE] Konfigurasi role notifikasi receipt
**MR**: feature/7308-TASK-add_notification_group_message-develop
**Reviewer**: Salsabila QA

**Temuan & Fix:**

### [1] ❌ N+1 + nested promise pyramid di V2 read path

**File**: `sirs-notification-microservice/controller/PushNotificationController.js:175-205`

**Before:**
```js
dao.list(findByIdParam).then(result => {
  const targetMessage = result && result.rows && result.rows[0]
  if (!targetMessage) {
    return Promise.resolve([])
  }
  const { notificationGroupId: groupId } = targetMessage

  if (!groupId) {
    return dao.update({ status: true }, { id: notificationId }).then(() => [userId])
  }

  const findByGroupParam = generatePagingParam({ query: {} }, 'createdAt')
  findByGroupParam.filter[0] = ['$eq(notificationGroupId)']
  findByGroupParam.filter[1] = [groupId]
  findByGroupParam.grouping = ['and']
  findByGroupParam.offset = 0
  findByGroupParam.limit = 1000

  return dao.list(findByGroupParam).then(groupResult => {
    const groupMessages = (groupResult && groupResult.rows) || []

    const affectedUserIds = [...new Set(
      groupMessages
        .filter(msg => !msg.status)
        .map(msg => msg.targetUserId)
        .filter(Boolean)
    )]

    return Promise.all(
      groupMessages.map(msg => dao.update({ status: true }, { id: msg.id }))
    ).then(() => affectedUserIds)
  })
}).then((affectedUserIds) => {
  if (!affectedUserIds || !affectedUserIds.length) return
  const broadcastTargets = [...new Set([...affectedUserIds, userId])]
  return Promise.all(
    broadcastTargets.map(targetId =>
      dao.getTotalUnread(targetId, channel).then(unread => {
        sendMessage(wsInstance, channel, targetId, {
          unread, method: 'patch', messages: []
        })
      })
    )
  )
}).catch(e => error(e))
```

**After:**
```js
dao.list(findByIdParam).then(async result => {
  const targetMessage = result && result.rows && result.rows[0]
  if (!targetMessage) return []

  const { notificationGroupId: groupId } = targetMessage

  if (!groupId) {
    await dao.update({ status: true }, { id: notificationId })
    return [userId]
  }

  const bulkResult = await dao.bulkUpdateByGroup(groupId, { status: true })
  const meta = (bulkResult && bulkResult[1] && bulkResult[1][0]) || {}
  return meta.affectedUserIds || []
}).then((affectedUserIds) => {
  if (!affectedUserIds || !affectedUserIds.length) return
  const broadcastTargets = [...new Set([...affectedUserIds, userId])]
  return Promise.all(
    broadcastTargets.map(targetId =>
      dao.getTotalUnread(targetId, channel).then(unread => {
        sendMessage(wsInstance, channel, targetId, {
          unread, method: 'patch', messages: []
        })
      })
    )
  )
}).catch(e => error(e))
```

### [2] ❌ Missing `bulkUpdateByGroup` + no `maxScore` cutoff di `_listByGroupId`

**File**: `sirs-notification-microservice/dao/notification/RedisNotificationStorage.js:199-216`

**Before:**
```js
async _listByGroupId (groupId, offset, limit) {
  try {
    const redis = this._redis
    const groupKey = KEY.group(groupId)
    const total = await redis.zcount(groupKey, '-inf', '+inf')
    const ids = await redis.zrevrangebyscore(groupKey, '+inf', '-inf', 'LIMIT', offset, limit)
    if (ids.length === 0) return { rows: [], count: total }

    const pipeline = redis.pipeline()
    ids.forEach(id => pipeline.hgetall(KEY.data(id)))
    const results = await pipeline.exec()
    const rows = results.map(([, hash]) => (hash ? this._deserialize(hash) : null)).filter(Boolean)
    return { rows, count: total }
  } catch (err) {
    error(err)
    return { rows: [], count: 0 }
  }
}
```

**After:**
```js
async _listByGroupId (groupId, offset, limit, maxScore) {
  try {
    const redis = this._redis
    const groupKey = KEY.group(groupId)
    const total = await redis.zcount(groupKey, '-inf', '+inf')
    const upper = maxScore || '+inf'
    const ids = await redis.zrevrangebyscore(groupKey, upper, '-inf', 'LIMIT', offset, limit)
    if (ids.length === 0) return { rows: [], count: total }

    const pipeline = redis.pipeline()
    ids.forEach(id => pipeline.hgetall(KEY.data(id)))
    const results = await pipeline.exec()
    const rows = results.map(([, hash]) => (hash ? this._deserialize(hash) : null)).filter(Boolean)
    return { rows, count: total }
  } catch (err) {
    error(err)
    return { rows: [], count: 0 }
  }
}

async bulkUpdateByGroup (groupId, values) {
  try {
    const redis = this._redis
    const groupKey = KEY.group(groupId)
    const ids = await redis.zrange(groupKey, 0, -1)
    if (ids.length === 0) return [0, []]

    const fields = { updatedAt: new Date().toISOString() }
    Object.keys(values).forEach(k => { fields[k] = String(values[k]) })

    const setPipeline = redis.pipeline()
    const unreadByUser = new Map()
    for (const id of ids) {
      const key = KEY.data(id)
      const existing = await redis.hgetall(key)
      if (!existing || Object.keys(existing).length === 0) continue
      if (values.status === true && existing.status === 'false' && existing.targetUserId) {
        const u = existing.targetUserId
        if (!unreadByUser.has(u)) unreadByUser.set(u, { channel: existing.channel, ids: [] })
        unreadByUser.get(u).ids.push(id)
      }
      setPipeline.hset(key, fields)
    }
    await setPipeline.exec()

    if (values.status === true && unreadByUser.size > 0) {
      const rmPipeline = redis.pipeline()
      for (const [userId, { channel, ids: userIds }] of unreadByUser) {
        if (!channel) continue
        rmPipeline.zrem(KEY.unread(channel, userId), userIds)
      }
      await rmPipeline.exec()
    }

    const affectedUserIds = [...unreadByUser.keys()]
    return [ids.length, [{ notificationGroupId: groupId, affectedCount: ids.length, affectedUserIds }]]
  } catch (err) {
    error(err)
    return [0, []]
  }
}
```

### [3] ❌ Hybrid layer tidak delegate method baru

**File**: `sirs-notification-microservice/dao/notification/HybridNotificationStorage.js:37-39`

**Before:**
```js
update (values, where) {
  return this._redis.update(values, where)
}
```

**After:**
```js
update (values, where) {
  return this._redis.update(values, where)
}

bulkUpdateByGroup (groupId, values) {
  return this._redis.bulkUpdateByGroup(groupId, values)
}
```

**Verdict**: PERLU PERBAIKAN — patch sudah diaplikasikan ke working tree.

**Dampak**: read 1 group = 1 RTT (sebelumnya 1 + N×3 RTT). `_listByGroupId` no full scan.

**Skip**: debounce FE #7494 (luar scope BE), `KEY.unreadByGroup` (belum bukti dipakai), populate `messages: []` (FE contract).

**Verifikasi**: `node -c` lulus di 3 file. Siap commit.

import LodashId from 'lodash-id'
const low = require('lowdb')
const FileSync = require('lowdb/adapters/FileSync')

const adapter = new FileSync('db.json')
const db = low(adapter)
db._.mixin(LodashId)
if (!db.has('todos').value()) {
  db.set('todos', []).write() // 不存在就创建
}

export default db

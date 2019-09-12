import LodashId from 'lodash-id'
import fs from 'fs-extra'
import path from 'path'
import { remote, app } from 'electron'

const APP = process.type === 'renderer' ? remote.app : app
const STORE_PATH = APP.getPath('userData')
if (process.type !== 'renderer') {
  if (!fs.pathExistsSync(STORE_PATH)) {
    fs.mkdirpSync(STORE_PATH)
  }
}

const low = require('lowdb')
const FileSync = require('lowdb/adapters/FileSync')

const adapter = new FileSync(path.join(STORE_PATH, 'db.json'))
const db = low(adapter)
db._.mixin(LodashId)
if (!db.has('todos').value()) {
  db.set('todos', []).write() // 不存在就创建
}

export default db

<template>
  <Layout>
    <Header>TodoList</Header>
    <Content>
      <Row>
        <Col span="9" offset="8">
          <Input v-model="value" enter-button @on-enter="save_data" />
        </Col>
        <Col span="1" offset="0">
          <Button type="primary" icon="md-add" @click="save_data"></Button>
        </Col>
      </Row>
      <Row>
        <h1>待完成事项</h1>
        <ul>
          <li color="primary" closable :key="todo.id" v-for="todo in finish_todos">
            <Checkbox v-model="todo.finish" @on-change="finish_todo_by_id(todo.id)"></Checkbox>
            {{todo.item}}
          </li>
        </ul>
      </Row>
      <Row>
        <h1>已完成事项</h1>
        <ul>
          <li color="primary" closable :key="todo.id" v-for="todo in unfinish_todos">
            <Checkbox v-model="todo.finish" @on-change="finish_todo_by_id(todo.id)"></Checkbox>
            {{todo.item}}
          </li>
        </ul>
      </Row>
    </Content>
    <Footer></Footer>
  </Layout>
</template>

<script>
import db from '../../datastore'
export default {
  name: 'TodoList',
  data () {
    return {
      value: '',
      todos: []
    }
  },
  computed: {
    finish_todos () {
      return this.todos.filter(todo => { return todo.finish === false })
    },
    unfinish_todos () {
      return this.todos.filter(todo => { return todo.finish === true })
    }
  },
  methods: {
    save_data () {
      let now = new Date().getTime()
      db.get('todos').insert(
        {
          // id: db.id,
          item: this.value,
          create_date: now,
          finish: false
        }).write()
      this.get_todos()
      this.value = ''
    },
    get_todos () {
      this.todos = db.get('todos').orderBy('create_date', 'desc').value()
    },
    finish_todo_by_id (TodoId) {
      let now = new Date().getTime()
      db.updateById('todos', TodoId, { finish: true, create_date: now }).write()
      this.get_todos()
    }

  },
  mounted () {
    this.get_todos()
  }
}
</script>
<style>
* {
  box-sizing: border-box;
}

/* Remove margins and padding from the list */
ul {
  margin: 20;
  padding: 0;
}

/* Style the list items */
ul li {
  cursor: pointer;
  position: relative;
  padding: 12px 8px 12px 40px;
  background: #eee;
  font-size: 18px;
  transition: 0.2s;

  /* make the list items unselectable */
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  user-select: none;
}

/* Set all odd list items to a different color (zebra-stripes) */
ul li:nth-child(odd) {
  background: #f9f9f9;
}

/* Darker background-color on hover */
ul li:hover {
  background: #ddd;
}

/* When clicked on, add a background color and strike out text */
ul li.checked {
  background: #888;
  color: #fff;
  text-decoration: line-through;
}

/* Add a "checked" mark when clicked on */
ul li.checked::before {
  content: "";
  position: absolute;
  border-color: #fff;
  border-style: solid;
  border-width: 0 2px 2px 0;
  top: 10px;
  left: 200px;
  transform: rotate(45deg);
  height: 15px;
  width: 7px;
}

/* Style the close button */
.close {
  position: absolute;
  right: 220;
  top: 0;
  /* padding: 12px 16px 12px 16px; */
}

.close:hover {
  background-color: #f44336;
  color: white;
}
</style>
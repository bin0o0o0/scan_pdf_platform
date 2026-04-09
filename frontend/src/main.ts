import { createApp } from "vue";

import App from "./App.vue";
import { router } from "./router";
import { pinia } from "./stores";
import "./styles/tokens.css";
import "./styles/base.css";

// 入口文件负责把“根组件 + 全局插件 + 全局样式”串起来。
// 这里先注册 Pinia，再注册 Router，
// 是因为路由守卫里会读取登录状态 store，顺序反过来容易在初始化时拿不到 store。
createApp(App).use(pinia).use(router).mount("#app");

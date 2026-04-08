import { createApp } from "vue";

import App from "./App.vue";
import { router } from "./router";
import { pinia } from "./stores";
import "./styles/tokens.css";
import "./styles/base.css";

// 入口文件里先注册 Pinia，再注册 Router，
// 是因为路由守卫会读取登录态 store；如果顺序反过来，守卫初始化时可能拿不到 store。
createApp(App).use(pinia).use(router).mount("#app");

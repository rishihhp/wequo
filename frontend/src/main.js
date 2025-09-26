import { createApp } from 'vue';
import './style.css';
import './styles/weq.css';
import './scripts/slow-scroll.js';
import App from './App.vue';
import router from './router';

const app = createApp(App);

app.use(router);
app.mount('#app');

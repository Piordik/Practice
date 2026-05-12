import http from 'k6/http';
import { sleep, check } from 'k6';

export const options = {
    stages: [
        { duration: '30s', target: 30 },   // Разгон
        { duration: '2m',  target: 100 },  // Основная нагрузка
        { duration: '30s', target: 0 },    // Снижение
    ],
    thresholds: {
        'http_req_duration': ['p(95)<300'], // 95% запросов быстрее 300мс
        'http_req_failed': ['rate<0.05'],   // Не более 5% ошибок
    },
};

export default function () {
    // Главная страница
    let res = http.get('http://localhost:8000/');
    check(res, { 'status is 200': (r) => r.status === 200 });

    // Операции со счётчиком
    http.post('http://localhost:8000/increment');
    http.post('http://localhost:8000/decrement');

    sleep(0.3); // небольшая пауза
}
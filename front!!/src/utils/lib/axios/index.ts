import axios from 'axios';

export const AxiosInstanceToFlask = axios.create({
  baseURL: import.meta.env.PROD
    ? import.meta.env.VITE_FLASK_API_URL
    : 'http://localhost:5002/',
  withCredentials: true,
});

export const AxiosInstanceToNest = axios.create({
  baseURL: import.meta.env.PROD
    ? import.meta.env.VITE_NEST_API_URL
    : 'http://localhost:3003/',
  withCredentials: true,
});

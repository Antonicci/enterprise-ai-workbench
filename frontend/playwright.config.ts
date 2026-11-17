import {defineConfig} from '@playwright/test';
export default defineConfig({testDir:'./e2e',timeout:60000,fullyParallel:false,workers:1,retries:0,
 use:{baseURL:'http://localhost:8080',trace:'retain-on-failure'},reporter:'list'});

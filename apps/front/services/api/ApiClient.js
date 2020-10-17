import console from 'console';
import axios from 'axios';

import UrlUtils from '@/lib/utils/url';

class ApiClient {
  constructor () {
    this.axios = axios.create({
      headers: { accept: 'application/json' },
    });
  }

  init (store, baseUrl) {
    this.baseUrl = baseUrl;
    this.axios.defaults.baseURL = baseUrl;

    // Add a request interceptor
    this.axios.interceptors.request.use(function (config) {
      const token = store && store.state && store.state.auth && store.state.auth.token;
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    console.info('[api-client] Initiated');
  }

  get (url, params = {}, headers = {}) {
    const urlWithParams = UrlUtils.addQueryParams(url, params);
    this.log('GET', urlWithParams);
    return this.axios.get(urlWithParams, { headers })
      .then(res => res.data)
      .catch((err) => { throw err.response.data; })
    ;
  }

  post (url, data, headers = {}, responseType = null) {
    const config = headers ? { headers } : {};
    if (responseType) {
      config.responseType = responseType;
    }
    this.log('POST', url);
    return this.axios.post(url, data, config)
      .then(res => res.data)
      .catch((err) => { throw err.response.data; })
    ;
  }

  put (url, data, headers = {}) {
    const config = headers ? { headers } : {};
    this.log('PUT', url);
    return this.axios.put(url, data, config)
      .then(res => res.data)
      .catch((err) => { throw err.response.data; })
    ;
  }

  delete (url, params, headers) {
    const config = headers ? { headers } : {};
    this.log('DELETE', url);
    return this.axios.delete(url, params, config)
      .then(res => res.data)
      .catch((err) => { throw err.response.data; })
    ;
  }

  log (method, url) {
    if (this.logger) {
      console.info(`[api-client] ${method.toUpperCase()} ${url}`);
    }
  }
};

export default new ApiClient();

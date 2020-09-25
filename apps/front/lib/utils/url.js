export default {
  /* ********************* QUERY STRING */
  addQueryParams (url, params = {}) {
    const { baseUrl, querystring } = this.explodeUrl(url);
    const querystringParams = {
      ...this.parseUrlParams(querystring),
      ...params,
    };
    return `${baseUrl}${this.buildUrlString(querystringParams)}`;
  },
  removeQueryParam (url, param) {
    const { baseUrl, querystring } = this.explodeUrl(url);
    const querystringParams = this.parseUrlParams(querystring);
    delete querystringParams[param];
    return `${baseUrl}${this.buildUrlString(querystringParams)}`;
  },
  /* ********************* HASH */
  getHash () {
    return document && document.location.hash;
  },
  updateHash (hash) {
    document.location.hash = hash;
  },
  getHashValues () {
    return this.getValuesFromHash(this.getHash());
  },
  getHashKeyValue (key) {
    const hashValues = this.getHashValues();
    return hashValues[key] || null;
  },
  getValuesFromHash (hash) {
    if (hash.substr(0, 1) === '#') {
      hash = hash.substr(1);
    }
    return this.parseUrlParams(hash);
  },
  removeHashKeys (keys) {
    const hashValues = this.getHashValues();
    for (const key of keys) {
      delete hashValues[key];
    }
    const hash = this.buildUrlString(hashValues, '#');
    this.updateHash(hash);
  },
  updateHashKey (key, value) {
    const hashValues = this.getHashValues();
    hashValues[key] = value;
    const hash = this.buildUrlString(hashValues, '#');
    this.updateHash(hash);
  },
  /* ********************* COMMON */
  explodeUrl (url) {
    const regex = new RegExp('(.*)[?]([a-z0-9=&_-]*)(?:#([.]*))?', 'i');
    const matches = url.match(regex);
    const parts = { baseUrl: url, querystring: '' };
    if (matches && matches.length > 2) {
      parts.baseUrl = matches[1];
      parts.querystring = matches[2] !== undefined ? matches[2] : '';
    }
    return parts;
  },
  parseUrlParams (str) {
    const parts = str.split('&');
    const values = {};
    parts.forEach((part) => {
      const splitted = part.split('=');
      if (splitted.length === 2) {
        values[splitted[0]] = splitted[1];
      }
    });
    return values;
  },
  buildUrlString (params, starter = '?') {
    let str = '';
    const keys = Object.keys(params);
    if (keys.length) {
      keys.forEach((key) => {
        if (params[key] !== null && params[key] !== undefined && params[key] !== '') {
          str = `${str}${str === '' ? starter : '&'}${key}=${params[key]}`;
        }
      });
    }
    return str;
  },
  encodeUrl (url) {
    /* JS encode URI function does not encode following characters: '()& */
    return encodeURI(url)
      .replace(/'/g, '%27')
      .replace(/\(/g, '%28')
      .replace(/\)/g, '%29')
      .replace(/&/g, '%26')
    ;
  },
};

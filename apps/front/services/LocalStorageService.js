import console from 'console';

class LocalStorageService {
  constructor () {
    console.info('[local-storage] Initiated');
  }

  get (key) {
    return localStorage.getItem(key);
  }

  set (key, value) {
    localStorage.setItem(key, value);
  }

  remove (key) {
    localStorage.removeItem(key);
  }
}

export default LocalStorageService;

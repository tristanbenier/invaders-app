import apiClient from '@/services/api/ApiClient';

class AuthService {
  constructor () {
    this.apiClient = apiClient;
  }

  login (username, password) {
    return this.apiClient.post('/login_check', { username, password })
      .catch((err) => {
        if (err.message) { throw err; }
        throw new Error('An error occured');
      })
    ;
  }
}

export default AuthService;

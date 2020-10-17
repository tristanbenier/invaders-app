import AuthService from '@/services/AuthService';

export default (_, inject) => {
  inject('auth', new AuthService());
};

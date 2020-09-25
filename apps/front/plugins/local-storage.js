import LocalStorageService from '@/services/LocalStorageService';

export default (_, inject) => {
  inject('storage', new LocalStorageService());
};

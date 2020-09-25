import apiClient from '@/services/api/ApiClient';

export default ({ store }) => {
  apiClient.init(store, process.env.API_URL);
};

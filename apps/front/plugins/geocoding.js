import GeocodingService from '@/services/GeocodingService';

export default (_, inject) => {
  inject('geocoding', new GeocodingService());
};

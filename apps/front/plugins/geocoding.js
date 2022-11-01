import GeocodingService from '@/services/GeocodingService';

const GMAP_API_KEY = process.env.GMAP_API_KEY;

export default (_, inject) => {
  inject('geocoding', new GeocodingService(GMAP_API_KEY));
};

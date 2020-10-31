import GeocodingService from '@/services/GeocodingService';

const PLACES_APP_ID = process.env.PLACES_APP_ID;
const PLACES_API_KEY = process.env.PLACES_API_KEY;

export default (_, inject) => {
  inject('geocoding', new GeocodingService(PLACES_APP_ID, PLACES_API_KEY));
};

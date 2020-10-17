import console from 'console';
import axios from 'axios';

class GeocodingService {
  constructor () {
    console.info('[geocoding] Initiated');
  }

  getAddressFromLatLng (lat, lng) {
    return axios.get(`https://nominatim.openstreetmap.org/reverse?format=json&lon=${lng}&lat=${lat}`);
  }
}

export default GeocodingService;

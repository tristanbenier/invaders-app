import axios from 'axios';

class GeocodingService {
  getAddressFromLatLng (lat, lng) {
    return axios.get(`https://nominatim.openstreetmap.org/reverse?format=json&lon=${lng}&lat=${lat}`);
  }
}

export default GeocodingService;

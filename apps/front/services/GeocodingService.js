import console from 'console';
import axios from 'axios';
import places from 'places.js';

class GeocodingService {
  constructor (appId, apiKey) {
    this.appId = appId;
    this.apiKey = apiKey;

    console.info('[geocoding] Initiated');
  }

  getAddressFromLatLng (lat, lng) {
    return axios.get(`https://nominatim.openstreetmap.org/reverse?format=json&lon=${lng}&lat=${lat}`);
  }

  initGeocodingInput (container) {
    return places({
      appId: this.appId,
      apiKey: this.apiKey,
      container,
    });
  }
}

export default GeocodingService;

import console from 'console';
import axios from 'axios';

class GeocodingService {
  constructor (googleMapApiKey) {
    this.googleMapApiKey = googleMapApiKey;
    this.googleMapService = null;

    console.info('[geocoding] Initiated');
  }

  getAddressFromLatLng (lat, lng) {
    return axios.get(`https://nominatim.openstreetmap.org/reverse?format=json&lon=${lng}&lat=${lat}`);
  }

  getPlacesFromQuery (query) {
    if (!this.googleMapService) {
      const map = new window.google.maps.Map(document.getElementById('fake-map'));
      this.googleMapService = new window.google.maps.places.PlacesService(map);
    }

    return new Promise((resolve) => {
      const request = { query, fields: ['formatted_address', 'geometry.location'] };
      this.googleMapService.findPlaceFromQuery(
        request,
        (results) => {
          return resolve(results);
        },
      );
    });
  }
}

export default GeocodingService;

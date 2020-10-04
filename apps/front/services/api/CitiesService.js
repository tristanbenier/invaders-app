import ApiResourceService from './ApiResourceService';

class CitiesService extends ApiResourceService {}

export default new CitiesService('/cities', 'City', 'Cities');

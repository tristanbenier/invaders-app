import apiClient from '@/services/api/ApiClient';

class ResourceService {
  constructor (baseUrl, resourceName, resourceNamePlural) {
    this.apiClient = apiClient;

    this.baseUrl = baseUrl;
    this.resourceName = resourceName;
    this.resourceNamePlural = resourceNamePlural;
  }

  fetch (params) {
    return this.apiClient.get(this.baseUrl, params)
      .catch((err) => {
        if (err.message) { throw err; }
        throw new Error(`Impossible to load ${this.resourceNamePlural} 😞`);
      })
    ;
  }

  fetchOne (id, params) {
    return this.apiClient.get(`${this.baseUrl}/${id}`, params)
      .catch((err) => {
        if (err.message) { throw err; }
        throw new Error(`Impossible to load ${this.resourceName} 😞`);
      })
    ;
  }

  createOne (params, headers) {
    return this.apiClient.post(this.baseUrl, params, headers)
      .catch((err) => {
        if (err.message) { throw err; }
        throw new Error(`Impossible to create ${this.resourceName} 😞`);
      })
    ;
  }

  updateOne (id, params, headers) {
    return this.apiClient.put(`${this.baseUrl}/${id}`, params, headers)
      .catch((err) => {
        if (err.message) { throw err; }
        throw new Error(`Impossible to update ${this.resourceName} 😞`);
      })
    ;
  }

  removeOne (id) {
    return this.apiClient.delete(`${this.baseUrl}/${id}`)
      .catch((err) => {
        if (err.message) { throw err; }
        throw new Error(`Impossible to remove ${this.resourceName} 😞`);
      })
    ;
  }

  updateMany (ids, params) {
    return this.apiClient.put(`${this.baseUrl}/`, { ids, ...params })
      .catch((err) => {
        if (err.message) { throw err; }
        throw new Error(`Impossible to update ${this.resourceNamePlural} 😞`);
      })
    ;
  }
}

export default ResourceService;

import ApiResourceService from './ApiResourceService';

class ImagesService extends ApiResourceService {
  createOne (params) {
    const formData = new FormData();
    Object.keys(params).forEach((key) => {
      formData.append(key, params[key]);
    });
    return super.createOne(formData, { 'Content-Type': 'multipart/form-data' });
  }
}

export default new ImagesService('/images', 'Image', 'Images');

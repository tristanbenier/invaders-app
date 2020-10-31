import Status from '@/entities/Status';
import City from '@/entities/City';
import Image from '@/entities/Image';

class Invader {
  static get POINTS () {
    return [0, 10, 20, 30, 40, 50, 100];
  }

  constructor () {
    this.id = null;
    this.name = null;
    this.points = null;
    this.status = null;
    this.latitude = null;
    this.longitude = null;
    this.address1 = null;
    this.address2 = null;
    this.zipcode = null;
    this.city = null;
    this.comment = null;
    this.users = [];
    this.images = null;
  }

  get iri () {
    return `/invaders/${this.id}`;
  }

  get coordinates () {
    return {
      lat: this.latitude,
      lng: this.longitude,
    };
  }

  addImage (image) {
    this.images.push(image);
  }

  toFormData () {
    return {
      id: this.id,
      name: this.name,
      points: this.points,
      statusId: (this.status && this.status.id) || null,
      latitude: this.latitude,
      longitude: this.longitude,
      address1: this.address1,
      address2: this.address2,
      zipcode: this.zipcode,
      cityId: (this.city && this.city.id) || null,
      comment: this.comment,
      usersId: this.users.map(u => u.id),
      images: this.images,
    };
  }

  static createFromApi ({ id, name, points, status, latitude, longitude, address1, address2, zipcode, city, comment, images, users } = {}) {
    const item = new Invader();

    item.id = id;
    item.name = name;
    item.points = parseInt(points);
    item.status = Status.createFromApi(status);
    item.latitude = latitude;
    item.longitude = longitude;
    item.position = { latitude, longitude };
    item.address1 = address1;
    item.address2 = address2;
    item.zipcode = zipcode;
    item.city = City.createFromApi(city);
    item.comment = comment;
    item.images = (images || []).map(i => Image.createFromApi(i));
    item.users = users;

    return item;
  }
}

export default Invader;

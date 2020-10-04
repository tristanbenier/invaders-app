import Status from '@/entities/Status';
import City from '@/entities/City';
import Image from '@/entities/Image';

class Invader {
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
      statusId: this.status.id,
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
    item.points = points;
    item.status = Status.createFromApi(status);
    item.latitude = latitude;
    item.longitude = longitude;
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

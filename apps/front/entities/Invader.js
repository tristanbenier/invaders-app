class Invader {
  get coordinates () {
    return {
      lat: this.latitude,
      lng: this.longitude,
    };
  }

  static createFromApi ({ id, name, points, latitude, longitude } = {}) {
    const item = new Invader();

    item.id = id;
    item.name = name;
    item.points = points;
    item.latitude = latitude;
    item.longitude = longitude;

    return item;
  }
}

export default Invader;

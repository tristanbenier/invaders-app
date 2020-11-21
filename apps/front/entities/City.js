class City {
  get iri () {
    return `/cities/${this.id}`;
  }

  get fileUrl () {
    return `${process.env.API_URL}${this._fileUrl}`;
  }

  static createFromApi ({ id, name, prefix, fileUrl, thumbnailUrl } = {}) {
    const item = new City();

    item.id = id;
    item.name = name;
    item.prefix = prefix;
    item._fileUrl = fileUrl;
    item.thumbnailUrl = thumbnailUrl;

    return item;
  }
}

export default City;

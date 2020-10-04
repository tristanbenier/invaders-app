class City {
  get iri () {
    return `/cities/${this.id}`;
  }

  static createFromApi ({ id, name, prefix } = {}) {
    const item = new City();

    item.id = id;
    item.name = name;
    item.prefix = prefix;

    return item;
  }
}

export default City;

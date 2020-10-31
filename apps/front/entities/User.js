class User {
  get iri () {
    return `/users/${this.id}`;
  }

  static createFromApi ({ id, name, color } = {}) {
    const item = new User();

    item.id = id;
    item.name = name;
    item.color = color;

    return item;
  }
}

export default User;

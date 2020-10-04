class User {
  get iri () {
    return `/users/${this.id}`;
  }

  static createFromApi ({ id, name } = {}) {
    const item = new User();

    item.id = id;
    item.name = name;

    return item;
  }
}

export default User;

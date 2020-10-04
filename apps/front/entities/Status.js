class Status {
  get iri () {
    return `/statuses/${this.id}`;
  }

  static get STATUSES () {
    return {
      ACTIVE: 'Active',
      DEAD: 'Dead',
      REACTIVATED: 'Re-activated',
    };
  }

  static createFromApi ({ id, name, color } = {}) {
    const item = new Status();

    item.id = id;
    item.name = name;
    item.color = color;

    return item;
  }
}

export default Status;

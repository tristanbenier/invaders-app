class Image {
  get iri () {
    return `/images/${this.id}`;
  }

  get url () {
    return `${process.env.API_URL}${this.fileUrl}`;
  }

  static createFromApi ({ id, fileUrl } = {}) {
    const item = new Image();

    item.id = id;
    item.fileUrl = fileUrl;

    return item;
  }
}

export default Image;

class Image {
  get iri () {
    return `/images/${this.id}`;
  }

  get url () {
    return `${process.env.API_URL}${this.fileUrl}`;
  }

  static createFromApi ({ id, fileUrl, thumbnailUrl } = {}) {
    const item = new Image();

    item.id = id;
    item.fileUrl = fileUrl;
    item.thumbnailUrl = thumbnailUrl;

    return item;
  }
}

export default Image;

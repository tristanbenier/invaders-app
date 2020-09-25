export default {
  toggleElement (arr, element) {
    const index = arr.indexOf(element);
    if (index === -1) {
      arr.push(element);
    } else {
      arr.splice(index, 1);
    }

    return arr;
  },

  addElementIfNotExists (arr, element) {
    if (!this.hasElement(arr, element)) {
      arr.push(element);
    }

    return arr;
  },

  removeElement (arr, element) {
    const index = arr.indexOf(element);
    if (index !== -1) {
      arr.splice(index, 1);
    }

    return arr;
  },

  hasElement (arr, element) {
    return arr.includes(element);
  },
};

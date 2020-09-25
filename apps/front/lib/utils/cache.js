export default {
  buildCacheKey (filters) {
    const elements = [];

    for (const key in filters) {
      const value = filters[key];
      if (value !== undefined && value !== null && value !== '') {
        elements.push(`${key}:${value}`);
      }
    }

    return `_${elements.join('_')}`;
  },
};

import UrlUtils from '@/lib/utils/url';

import Invader from '@/entities/Invader';
import Status from '@/entities/Status';

export default {
  data () {
    return {
      filters: {
        points: {
          label: 'Points',
          value: null,
          choices: Invader.POINTS.map(p => ({
            label: p !== 0 ? p : '-',
            value: p,
          })),
        },
        status: {
          label: 'Status',
          value: null,
          choices: Object.values(Status.STATUSES)
            .map(s => ({ label: s, value: s }))
            .sort((a, b) => a.label.localeCompare(b.label)),
        },
        users: {
          label: 'Caught By',
          value: null,
          choices: this.usersChoices,
        },
        cities: {
          label: 'City',
          value: null,
          choices: this.citiesChoices,
        },
      },
    };
  },
  computed: {
    users () {
      return this.$store.getters['users/usersList'];
    },
    usersChoices () {
      return [
        { label: '-', value: 0 },
        ...this.users
          .map(u => ({ label: u.name, value: u.id }))
          .sort((a, b) => a.label.localeCompare(b.label)),
      ];
    },
    cities () {
      return this.$store.getters['cities/citiesList'];
    },
    citiesChoices () {
      return this.cities
        .map(c => ({ label: c.name, value: c.id }))
        .sort((a, b) => a.label.localeCompare(b.label))
      ;
    },
  },
  watch: {
    '$route.hash' () {
      this.updateFilterValuesFromHash();
    },
    users () {
      this.filters.users.choices = this.usersChoices;
    },
    cities () {
      this.filters.cities.choices = this.citiesChoices;
    },
  },
  mounted () {
    this.updateFilterValuesFromHash();
  },
  methods: {
    updateFilterValuesFromHash () {
      throw new Error('This methods needs to be implemented in component');
    },
    onFiltersClear () {
      UrlUtils.removeHashKeys(Object.keys(this.filters));
    },
    onFilterUpdate ({ key, value }) {
      let filterValues = [...(this.filterValues[key] || [])];
      if (filterValues.includes(value)) {
        filterValues = filterValues.filter(v => v !== value);
      } else {
        filterValues.push(value);
      }

      // Specific behaviour for users
      if (key === 'users') {
        if (value === 0 && filterValues.length) {
          filterValues = [value];
        } else if (value !== 0) {
          filterValues = filterValues.filter(v => v !== 0);
        }
      }

      UrlUtils.updateHashKey(key, filterValues.join(','));
    },
  },
};

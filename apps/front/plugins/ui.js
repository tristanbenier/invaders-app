import Vue from 'vue';

import {
  Pie,
  mixins,
} from 'vue-chartjs';

import UiModal from '@/components/ui/UiModal';
import UiBlurImageLoader from '@/components/ui/UiBlurImageLoader';

// Import globally all UI components
Vue.component('UiModal', UiModal);
Vue.component('UiBlurImageLoader', UiBlurImageLoader);

// Create statistics components
const DefaultMixin = {
  props: {
    options: {
      type: Object,
      default: () => ({}),
    },
  },
  mixins: [mixins.reactiveProp],
  computed: {
    computedOptions () {
      const DEFAULT_OPTIONS = {
        responsive: true,
        title: { display: false },
        maintainAspectRatio: false,
        tooltips: { mode: 'nearest', intersect: false },
        legend: { display: false },
      };

      const options = {
        ...DEFAULT_OPTIONS,
        ...this.options,
      };

      return options;
    },
  },
  mounted () {
    this.renderChart(this.chartData, this.computedOptions);
  },
};

Vue.component('UiPieChart', {
  extends: Pie,
  mixins: [DefaultMixin],
});

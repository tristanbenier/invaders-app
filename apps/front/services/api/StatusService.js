import ApiResourceService from './ApiResourceService';

class StatusService extends ApiResourceService {}

export default new StatusService('/statuses', 'Statu', 'Status');

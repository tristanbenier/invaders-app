import ApiResourceService from './ApiResourceService';

class UsersService extends ApiResourceService {}

export default new UsersService('/users', 'User', 'Users');

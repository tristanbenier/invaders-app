import ApiResourceService from './ApiResourceService';

class InvadersService extends ApiResourceService {}

export default new InvadersService('/invaders', 'Invader', 'Invaders');

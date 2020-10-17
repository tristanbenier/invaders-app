import jwtDecode from 'jwt-decode';
// import Cookie from 'js-cookie';

// import JwtUtils from 'shared-js-lib/utils/jwt';
// import apiClient from 'shared-js-lib/services/api/ApiClient';

// import AdminUser from '@/models/AdminUser';

class TokenManager {
  checkToken (token, roles = []) {
    // Decode token
    const decoded = this.decodeToken(token);

    // Check if token is still valid
    if (!this.isDecodedTokenStillValid(decoded)) {
      throw new Error('Token expired');
    }

    // Check if user is allowed
    if (roles.length) {
      const tokenRoles = decoded.roles;
      if (!roles.filter(value => tokenRoles.includes(value)).length) {
        throw new Error('Not allowed');
      }
    }
  }

  extractUserIdFromToken (token) {
    // Decode token
    const decoded = this.decodeToken(token);

    return decoded.id || null;
  }

  extractExpirationDelayFromToken (token) {
    const decoded = this.decodeToken(token);

    return (decoded.exp * 1000) - Date.now();
  }

  decodeToken (token) {
    return jwtDecode(token);
  }

  isDecodedTokenStillValid (decoded) {
    const tokenDate = new Date(decoded.exp * 1000);
    const now = Date.now();
    return tokenDate.getTime() > now;
  }
}

export default ({ app, store }, inject) => {
  inject('token', new TokenManager(app, store));
};

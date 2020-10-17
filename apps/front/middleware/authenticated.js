export default function ({ route, store, redirect, from }) {
  const isUserAuthenticated = store.getters['auth/authenticated'];

  // If the user is not authenticated and not login page -> redirect to login page
  if (route.name !== 'login' && !isUserAuthenticated) {
    const callbackRoute = (from && from.query.callback) || route.fullPath;
    return redirect(`/login?callback=${callbackRoute}`);
  }

  // If user is authenticated and login page -> redirect to map page
  if (route.name === 'login' && isUserAuthenticated) {
    return redirect('/');
  }
}

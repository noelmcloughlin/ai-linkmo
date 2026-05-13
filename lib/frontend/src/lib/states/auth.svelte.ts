class AuthState {
  loggedIn = $state(false);
  user = $state<{ name: string; avatar: string } | null>(null);

  setLoggedIn(loggedIn: boolean) {
    this.loggedIn = loggedIn;
  }

  setUser(user: { name: string; avatar: string } | null) {
    this.user = user;
  }

  reset() {
    this.loggedIn = false;
    this.user = null;
  }
}
export const authState = new AuthState();
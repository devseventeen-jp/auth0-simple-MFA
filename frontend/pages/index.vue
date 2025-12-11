<template>
  <div style="text-align: center; margin-top: 50px;">
    <h1>Auth0 + Django MFA Demo</h1>
    
    <div v-if="isLoading">Loading...</div>
    
    <div v-else>
      <div v-if="isAuthenticated">
        <p>Welcome, {{ user?.name }}</p>
        <button @click="logout" style="padding: 10px 20px;">Logout</button>
        <br><br>
        <NuxtLink to="/dashboard">Go to Dashboard</NuxtLink>
      </div>
      <div v-else>
        <button @click="login" style="padding: 10px 20px; font-size: 16px;">Log In</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useAuth0 } from '@auth0/auth0-vue';

const { loginWithRedirect, logout: auth0Logout, user, isAuthenticated, isLoading } = useAuth0();

const login = () => {
  loginWithRedirect();
};

const logout = () => {
  auth0Logout({ logoutParams: { returnTo: window.location.origin } });
};
</script>

<template>
  <div style="padding: 20px;">
    <h1>Dashboard</h1>
    <p>This is a protected area.</p>
    
    <div v-if="pending">Loading...</div>
    <div v-else-if="error">Error: {{ error }}</div>
    <div v-else>
      <h3>User Profile (Django)</h3>
      <pre>{{ data }}</pre>
      
      <p><strong>MFA Method:</strong> {{ data.mfa_method }}</p>
      <p><strong>Is Approved:</strong> {{ data.is_approved }}</p>
    </div>
    
    <NuxtLink to="/">Back to Home</NuxtLink>
  </div>
</template>

<script setup>
import { useAuth0 } from '@auth0/auth0-vue';

const { getAccessTokenSilently } = useAuth0();
const config = useRuntimeConfig();

const { data, pending, error, refresh } = await useAsyncData('me', async () => {
    const token = await getAccessTokenSilently();
    return $fetch(`${config.public.apiBaseUrl}/api/auth/me`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
});
</script>

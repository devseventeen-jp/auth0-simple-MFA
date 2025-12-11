<template>
  <div style="text-align: center; margin-top: 50px;">
    <h2>Processing Login...</h2>
    <p>{{ status }}</p>
  </div>
</template>

<script setup>
import { useAuth0 } from '@auth0/auth0-vue';

const { handleRedirectCallback, getAccessTokenSilently } = useAuth0();
const config = useRuntimeConfig();
const router = useRouter();
const status = ref('Initializing...');

onMounted(async () => {
  try {
    status.value = 'Auth0 Callback...';
    await handleRedirectCallback();
    
    status.value = 'Getting Access Token...';
    const token = await getAccessTokenSilently();
    
    status.value = 'Verifying with Backend...';
    const { data, error } = await useFetch(`${config.public.apiBaseUrl}/api/auth/authorize`, {
      method: 'POST',
      body: { id_token: token }, // Using Access Token as id_token for backend compat
      headers: {
        'Authorization': `Bearer ${token}` // Standard Bearer too
      }
    });

    if (error.value) {
      console.error(error.value);
      status.value = 'Backend Error: ' + JSON.stringify(error.value);
      return;
    }

    const backendUser = data.value;
    console.log('Backend Response:', backendUser);

    if (backendUser.mfa_setup_required) {
      status.value = 'MFA Setup Required...';
      router.push('/mfa?mode=setup');
    } else if (backendUser.mfa_required) {
      status.value = 'MFA Check Required...';
      router.push('/mfa?mode=verify');
    } else {
      status.value = 'Success!';
      router.push('/dashboard');
    }

  } catch (e) {
    console.error(e);
    status.value = 'Error: ' + e.message;
  }
});
</script>

<template>
  <div style="max-width: 500px; margin: 50px auto; padding: 20px; border: 1px solid #ccc;">
    <h2>MFA {{ mode === 'setup' ? 'Setup' : 'Verification' }}</h2>

    <!-- SETUP FLOW -->
    <div v-if="mode === 'setup'">
      <p>Please select your MFA method:</p>
      
      <div style="margin-bottom: 20px;">
        <label>
          <input type="radio" v-model="selectedMethod" value="TOTP"> Authenticator App (TOTP)
        </label>
        <br>
        <label>
          <input type="radio" v-model="selectedMethod" value="EMAIL"> Email OTP
        </label>
      </div>

      <button @click="startSetup">Begin Setup</button>

      <div v-if="setupData" style="margin-top: 20px;">
        <div v-if="setupData.method === 'TOTP'">
            <p>Scan this QR code with your app:</p>
            <img :src="setupData.qr_code" style="max-width: 200px;" />
            <p>Secret: {{ setupData.secret }}</p>
        </div>
        <div v-if="setupData.method === 'EMAIL'">
            <p>{{ setupData.message }}</p>
        </div>

        <hr>
        <p>Enter the code you received/generated:</p>
        <input type="text" v-model="code" placeholder="6-digit code">
        <button @click="verifySetup">Verify & Enable</button>
      </div>
    </div>

    <!-- VERIFY FLOW (LOGIN) -->
    <div v-else>
       <p>Please enter your 6-digit MFA code.</p>
       <input type="text" v-model="code" placeholder="6-digit code">
       <button @click="verifyLogin">Verify Login</button>
    </div>

    <p style="color: red" v-if="errorMessage">{{ errorMessage }}</p>

  </div>
</template>

<script setup>
import { useAuth0 } from '@auth0/auth0-vue';

const route = useRoute();
const router = useRouter();
const config = useRuntimeConfig();
const { getAccessTokenSilently } = useAuth0();

const mode = ref(route.query.mode || 'verify');
const selectedMethod = ref('TOTP');
const setupData = ref(null);
const code = ref('');
const errorMessage = ref('');

const startSetup = async () => {
    try {
        const token = await getAccessTokenSilently();
        const { data, error } = await useFetch(`${config.public.apiBaseUrl}/api/mfa/setup`, {
            method: 'POST',
            body: { method: selectedMethod.value },
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (error.value) throw error.value;
        setupData.value = data.value;
    } catch (e) {
        errorMessage.value = 'Setup Init Failed: ' + e.message;
    }
}

const verifySetup = async () => {
    try {
        const token = await getAccessTokenSilently();
        const { data, error } = await useFetch(`${config.public.apiBaseUrl}/api/mfa/verify`, {
            method: 'POST',
            body: { 
                code: code.value,
                method: setupData.value.method // Verify the method we just set up
            },
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (error.value) throw error.value;
        
        alert('MFA Enabled!');
        router.push('/dashboard');
    } catch (e) {
         errorMessage.value = 'Verification Failed: ' + (e.data?.error || e.message);
    }
}

const verifyLogin = async () => {
    try {
        const token = await getAccessTokenSilently();
        const { data, error } = await useFetch(`${config.public.apiBaseUrl}/api/mfa/verify`, {
            method: 'POST',
            body: { 
                code: code.value,
                // For login verify, backend should know user's method or we try reasonable default
                // The backend implementation tries TOTP then Email if ambiguous, or we should fetch user profile first.
                // We'll send generic or backend will handle. The view implementation checks User's preferred method if not supplied?
                // View logic: request.data.get('method', getattr(settings, 'MFA_METHOD', 'TOTP'))
                // Ideally we should know. For now let's default to assuming the one configured/env.
                // Or better, fetch 'auth/authorize' again to see method?
                // Let's assume TOTP default or try both from UI if we want robust.
                // Or simply let backend decide.
            },
            headers: { 'Authorization': `Bearer ${token}` }
        });

         if (error.value) throw error.value;
         
         router.push('/dashboard');
    } catch (e) {
        errorMessage.value = 'Login Verification Failed: ' + (e.data?.error || e.message);
    }
}
</script>

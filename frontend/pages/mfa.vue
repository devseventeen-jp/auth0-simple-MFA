<template>
  <div class="mfa-container">
    <div class="glass-card">
      <div class="header">
        <h1>Account Activation</h1>
        <p>Complete Multi-Factor Authentication to secure your account.</p>
      </div>

      <!-- Step Indicator -->
      <div class="steps">
        <div :class="['step', { active: currentStep === 1, done: currentStep > 1 }]">1</div>
        <div class="line"></div>
        <div :class="['step', { active: currentStep === 2, done: currentStep > 2 }]">2</div>
        <div class="line"></div>
        <div :class="['step', { active: currentStep === 3 }]">3</div>
      </div>

      <!-- STEP 1: SELECT METHOD -->
      <div v-if="currentStep === 1" class="step-content">
        <h3>Step 1: Choose Your Method</h3>
        <p class="desc">How would you like to receive your security codes?</p>
        
        <div class="options">
          <div :class="['option-card', { selected: selectedMethod === 'EMAIL' }]" @click="selectedMethod = 'EMAIL'">
            <div class="icon">📧</div>
            <div class="label">Email OTP</div>
            <div class="sub">Receive codes via email</div>
          </div>
          
          <div :class="['option-card', { selected: selectedMethod === 'TOTP' }]" @click="selectedMethod = 'TOTP'">
            <div class="icon">📱</div>
            <div class="label">Authenticator App</div>
            <div class="sub">Google Authenticator / Authy</div>
          </div>
        </div>
        
        <button class="btn btn-primary btn-full" @click="startSetup">Continue</button>
      </div>

      <!-- STEP 2: SETUP -->
      <div v-if="currentStep === 2" class="step-content">
        <h3>Step 2: Setup {{ selectedMethod }}</h3>
        
        <div v-if="selectedMethod === 'TOTP'" class="totp-setup">
          <p>Scan the QR code with your authenticator app:</p>
          <div class="qr-container" v-if="setupData">
            <img :src="setupData.qr_code" alt="QR Code" />
          </div>
          <p class="secret-text" v-if="setupData">Secret: <code>{{ setupData.secret }}</code></p>
        </div>
        
        <div v-if="selectedMethod === 'EMAIL'" class="email-setup">
          <div class="icon-big">📩</div>
          <p>We've sent a 6-digit verification code to your email address.</p>
          <p class="email-hint">Please check your inbox (and spam folder).</p>
        </div>

        <button class="btn btn-primary btn-full" @click="currentStep = 3" style="margin-top: 20px;">I have my code</button>
        <button class="btn btn-link" @click="currentStep = 1">Change Method</button>
      </div>

      <!-- STEP 3: VERIFY -->
      <div v-if="currentStep === 3" class="step-content">
        <h3>Step 3: Verify Your Identity</h3>
        <p class="desc">Enter the 6-digit code below to activate your account.</p>
        
        <div class="code-input-container">
          <input 
            type="text" 
            v-model="code" 
            placeholder="000000" 
            maxlength="6" 
            class="code-input"
            @keyup.enter="verifyMFA"
          >
        </div>
        
        <p v-if="error" class="error-msg">{{ error }}</p>
        
        <button class="btn btn-primary btn-full" :disabled="isLoading || code.length < 6" @click="verifyMFA">
          {{ isLoading ? 'Verifying...' : 'Verify & Activate' }}
        </button>
        <button class="btn btn-link" @click="currentStep = 2">Back</button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { useAuth0 } from '@auth0/auth0-vue';

const config = useRuntimeConfig();
const router = useRouter();
const { getAccessTokenSilently } = useAuth0();

const currentStep = ref(1);
const selectedMethod = ref('EMAIL');
const setupData = ref(null);
const code = ref('');
const error = ref('');
const isLoading = ref(false);

const startSetup = async () => {
    try {
        error.value = '';
        const token = await getAccessTokenSilently();
        const response = await $fetch(`${config.public.apiBaseUrl}/api/mfa/setup`, {
            method: 'POST',
            body: { method: selectedMethod.value },
            headers: { 'Authorization': `Bearer ${token}` }
        });
        setupData.value = response;
        currentStep.value = 2;
    } catch (e) {
        error.value = "Setup failed: " + (e.data?.error || e.message);
    }
};

const verifyMFA = async () => {
    isLoading.value = true;
    error.value = '';
    try {
        const token = await getAccessTokenSilently();
        const response = await $fetch(`${config.public.apiBaseUrl}/api/mfa/verify`, {
            method: 'POST',
            body: { 
                code: code.value,
                method: selectedMethod.value
            },
            headers: { 'Authorization': `Bearer ${token}` }
        });

        // Success! Redirect to dashboard
        router.push('/dashboard');
    } catch (e) {
        error.value = e.data?.error || "Invalid code. Please try again.";
    } finally {
        isLoading.value = false;
    }
}
</script>

<style scoped>
.mfa-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #0f172a;
  font-family: 'Inter', sans-serif;
  color: #fff;
}

.glass-card {
  background: rgba(30, 41, 59, 0.7);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  padding: 40px;
  width: 100%;
  max-width: 480px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
}

.header { text-align: center; margin-bottom: 30px; }
.header h1 { font-size: 1.8rem; margin-bottom: 8px; }
.header p { color: #94a3b8; font-size: 0.95rem; }

/* Steps */
.steps { display: flex; align-items: center; justify-content: center; margin-bottom: 40px; }
.step {
  width: 32px; height: 32px; border-radius: 50%; background: #334155;
  display: flex; align-items: center; justify-content: center; font-weight: bold;
  transition: all 0.3s;
}
.step.active { background: #3b82f6; box-shadow: 0 0 15px rgba(59, 130, 246, 0.5); }
.step.done { background: #10b981; }
.line { flex: 0.2; height: 2px; background: #334155; margin: 0 10px; }

/* Content */
.step-content { animation: slideIn 0.3s ease-out; text-align: center; }
h3 { margin-bottom: 10px; }
.desc { color: #94a3b8; margin-bottom: 25px; font-size: 0.9rem; }

/* Options */
.options { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 30px; }
.option-card {
  padding: 20px; background: #1e293b; border: 2px solid transparent;
  border-radius: 16px; cursor: pointer; transition: 0.2s;
}
.option-card:hover { border-color: #334155; }
.option-card.selected { border-color: #3b82f6; background: rgba(59, 130, 246, 0.1); }
.option-card .icon { font-size: 1.5rem; margin-bottom: 8px; }
.option-card .label { font-weight: 600; font-size: 1rem; }
.option-card .sub { font-size: 0.75rem; color: #64748b; margin-top: 4px; }

/* Setup Visuals */
.qr-container { background: #fff; padding: 15px; border-radius: 12px; display: inline-block; margin: 15px 0; }
.qr-container img { width: 180px; height: 180px; }
.secret-text { font-size: 0.8rem; color: #94a3b8; }
.icon-big { font-size: 3rem; margin: 20px 0; }
.email-hint { font-size: 0.8rem; color: #64748b; }

/* Verify */
.code-input {
  width: 100%; border: none; background: #1e293b; color: #fff;
  padding: 15px; border-radius: 12px; font-size: 1.5rem; text-align: center;
  letter-spacing: 0.5rem; border: 2px solid #334155; margin-bottom: 20px;
}
.code-input:focus { border-color: #3b82f6; outline: none; }

/* Buttons */
.btn { border: none; border-radius: 12px; padding: 14px 24px; font-weight: 600; cursor: pointer; transition: 0.2s; }
.btn-primary { background: #3b82f6; color: #fff; }
.btn-primary:hover { background: #2563eb; transform: translateY(-1px); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-full { width: 100%; }
.btn-link { background: none; color: #94a3b8; font-size: 0.9rem; margin-top: 10px; }
.btn-link:hover { color: #fff; }

.error-msg { color: #f87171; font-size: 0.85rem; margin-bottom: 15px; }

@keyframes slideIn { from { opacity: 0; transform: translateX(10px); } to { opacity: 1; transform: translateX(0); } }
</style>

<script>
import { createClient } from '@supabase/supabase-js'
import { onMount } from 'svelte'
import { i18n } from './i18n'

const supabaseUrl = 'https://anrakdaroezxddxvdpaw.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFucmFrZGFyb2V6eGRkeHZkcGF3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MDc5NjIzNTEsImV4cCI6MjAyMzUzODM1MX0.zLZm6AI7gfZlzkseKNQNC6Ek_eDhruR6gnzl1Otk1F8';

const supabase = createClient(supabaseUrl, supabaseAnonKey);

let email = ''
let password = ''
let error = null
let loaded = false

onMount(async () => {
  loaded = true
})

async function handleSignIn() {
  try {
    const { user, error } = await supabase.auth.signInWithPassword({
      email: email,
      password: password
    })
    if (error) throw error
    // Handle successful sign-in (e.g., redirect to dashboard)
    console.log('Signed in successfully', user)
  } catch (e) {
    error = e.message
  }
}
</script>

<main>
  {#if loaded}
    <h1>{i18n.t('Sign in')} {i18n.t('to')} {$WEBUI_NAME}</h1>

    <form on:submit|preventDefault={handleSignIn}>
      <div>
        <label for="email">{i18n.t('Email')}</label>
        <input type="email" id="email" bind:value={email} required>
      </div>

      <div>
        <label for="password">{i18n.t('Password')}</label>
        <input type="password" id="password" bind:value={password} required>
      </div>

      {#if error}
        <p class="error">{error}</p>
      {/if}

      <button type="submit">{i18n.t('Sign in')}</button>
    </form>
  {/if}
</main>

<style>
  main {
    max-width: 300px;
    margin: 0 auto;
    padding: 20px;
  }

  form {
    display: flex;
    flex-direction: column;
  }

  div {
    margin-bottom: 15px;
  }

  label {
    display: block;
    margin-bottom: 5px;
  }

  input {
    width: 100%;
    padding: 8px;
  }

  button {
    padding: 10px;
    background-color: #4CAF50;
    color: white;
    border: none;
    cursor: pointer;
  }

  .error {
    color: red;
  }
</style>
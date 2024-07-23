<script>
    import { goto } from '$app/navigation';
    import Spinner from '$lib/components/common/Spinner.svelte';
    import { WEBUI_NAME, config, user, socket } from '$lib/stores';
    import { onMount } from 'svelte';
    import { toast } from 'svelte-sonner';
    import { createClient } from '@supabase/supabase-js';

    const supabaseUrl = 'https://anrakdaroezxddxvdpaw.supabase.co';
    const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFucmFrZGFyb2V6eGRkeHZkcGF3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MDc5NjIzNTEsImV4cCI6MjAyMzUzODM1MX0.zLZm6AI7gfZlzkseKNQNC6Ek_eDhruR6gnzl1Otk1F8'; 

    const supabase = createClient(supabaseUrl, supabaseAnonKey);

    let loaded = false;
    let mode = 'signin';  
    let email = '';
    let password = '';

    const setSessionUser = async (session) => {
        if (session) {
            console.log(session);
            toast.success('You\'re now logged in.');
            if (session.access_token) {
                localStorage.token = session.access_token;
            }

            socket.emit('user-join', { auth: { token: session.access_token } });
            await user.set(session.user);
            goto('/');
        }
    };

    const signInHandler = async () => {
        try {
            const { data, error } = await supabase.auth.signInWithPassword({
                email,
                password
            });
            if (error) {
                toast.error(error.message);
                return;
            }
            await setSessionUser(data.session);
        } catch (error) {
            toast.error(error.message);
        }
    };

    const submitHandler = async () => {
        if (mode === 'signin') {
            await signInHandler();
        }
    };

    onMount(async () => {
        // Check if the user is already logged in
        const { data: { session }, error } = await supabase.auth.getSession();
        if (session) {
            await setSessionUser(session);
        }
        loaded = true; // Ensure the loading state is updated
    });
</script>

<svelte:head>
    <title>{`${WEBUI_NAME}`}</title>
</svelte:head>

{#if loaded}
    <div class="fixed m-10 z-50">
        <div class="flex space-x-2">
            <div class="self-center">
                <img
                    crossorigin="anonymous"
                    src="{WEBUI_BASE_URL}/static/favicon.png"
                    class="w-8 rounded-full"
                    alt="logo"
                />
            </div>
        </div>
    </div>

    <div class="bg-white dark:bg-gray-950 min-h-screen w-full flex justify-center font-primary">
        <div class="w-full sm:max-w-md px-10 min-h-screen flex flex-col text-center">
            <div class="my-auto pb-10 w-full dark:text-gray-100">
                <form
                    class="flex flex-col justify-center"
                    on:submit|preventDefault={() => {
                        submitHandler();
                    }}
                >
                    <div class="mb-1">
                        <div class="text-2xl font-medium">
                            {mode === 'signin' ? 'Sign in' : 'Create Account'} 
                            to {WEBUI_NAME}
                        </div>
                    </div>
                    <div class="flex flex-col mt-4">
                        <div class="mb-2">
                            <div class="text-sm font-medium text-left mb-1">Email</div>
                            <input
                                bind:value={email}
                                type="email"
                                class="px-5 py-3 rounded-2xl w-full text-sm outline-none border dark:border-none dark:bg-gray-900"
                                autocomplete="email"
                                placeholder="Enter Your Email"
                                required
                            />
                        </div>
                        <div>
                            <div class="text-sm font-medium text-left mb-1">Password</div>
                            <input
                                bind:value={password}
                                type="password"
                                class="px-5 py-3 rounded-2xl w-full text-sm outline-none border dark:border-none dark:bg-gray-900"
                                placeholder="Enter Your Password"
                                autocomplete="current-password"
                                required
                            />
                        </div>
                    </div>

                    <div class="mt-5">
                        <button
                            class="bg-gray-900 hover:bg-gray-800 w-full rounded-2xl text-white font-medium text-sm py-3 transition"
                            type="submit"
                        >
                            Sign in
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>
{/if}

<style>
    .font-mona {
        font-family: 'Mona Sans', -apple-system, 'Inter', ui-sans-serif, system-ui, 'Segoe UI', 
        Roboto, Ubuntu, Cantarell, 'Noto Sans', sans-serif, 'Helvetica Neue', Arial, 
        'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', 'Noto Color Emoji';
    }
</style>
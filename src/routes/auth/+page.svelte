<script>
	import { goto } from '$app/navigation';
	import { createClient } from '@supabase/supabase-js';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import { WEBUI_API_BASE_URL, WEBUI_BASE_URL } from '$lib/constants';
	import { WEBUI_NAME, config, user, socket } from '$lib/stores';
	import { onMount, getContext } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { page } from '$app/stores';
	import { v4 as uuidv4 } from 'uuid';

	const i18n = getContext('i18n');
    const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFucmFrZGFyb2V6eGRkeHZkcGF3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MDc5NjIzNTEsImV4cCI6MjAyMzUzODM1MX0.zLZm6AI7gfZlzkseKNQNC6Ek_eDhruR6gnzl1Otk1F8'; 	const supabase = createClient('https://your-supabase-url.supabase.co', 'your-anon-key');

	let loaded = false;
	let email = '';
	let password = '';

	const setSessionUser = async (sessionUser) => {
		if (sessionUser) {
			console.log('Setting session user:', sessionUser);
			toast.success($i18n.t(`You're now logged in.`));
			if (sessionUser.token) {
				localStorage.token = sessionUser.token;
			}

			$socket.emit('user-join', { auth: { token: sessionUser.token } });
			await user.set(sessionUser);
			goto('/');
		}
	};

	const mapUserToDatabase = async (email) => {
		try {
			// Check if user exists in your application's database
			const response = await fetch(`${WEBUI_API_BASE_URL}/check-user`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ email })
			});
			const userExists = await response.json();

			// If user does not exist, create a new user with a random password
			if (!userExists) {
				const randomPassword = uuidv4();
				await fetch(`${WEBUI_API_BASE_URL}/create-user`, {
					method: 'POST',
					headers: {
						'Content-Type': 'application/json'
					},
					body: JSON.stringify({ email, password: randomPassword })
				});
			}

			// Fetch the user from your application's database
			const userResponse = await fetch(`${WEBUI_API_BASE_URL}/get-user`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ email })
			});
			const appUser = await userResponse.json();
			console.log('Mapped user:', appUser);
			return appUser;
		} catch (error) {
			console.error(error);
			toast.error($i18n.t('An error occurred while mapping the user.'));
			return null;
		}
	};

	const signInHandler = async () => {
		console.log('Signing in with:', email, password);
		const { data, error } = await supabase.auth.signInWithPassword({
			email,
			password
		});
		if (error) {
			toast.error(error.message);
		} else {
			console.log('Supabase sign in data:', data);
			const appUser = await mapUserToDatabase(email);
			if (appUser) {
				await setSessionUser(appUser);
			}
		}
	};

	const submitHandler = async () => {
		console.log('Submitting form');
		await signInHandler();
	};

	const checkTrustedHeader = async () => {
		if (($config?.features.auth_trusted_header ?? false) || $config?.features.auth === false) {
			await signInHandler();
		}
	};

	onMount(async () => {
		if ($user !== undefined) {
			await goto('/');
		}
		await checkOauthCallback();
		await checkTrustedHeader();
		loaded = true;
	});
</script>

<svelte:head>
	<title>{`${$WEBUI_NAME}`}</title>
</svelte:head>

{#if loaded}
	<div class="fixed m-10 z-50">
		<div class="flex space-x-2">
			<div class=" self-center">
				<img
					crossorigin="anonymous"
					src="{WEBUI_BASE_URL}/static/favicon.png"
					class=" w-8 rounded-full"
					alt="logo"
				/>
			</div>
		</div>
	</div>

	<div class=" bg-white dark:bg-gray-950 min-h-screen w-full flex justify-center font-primary">
		<div class="w-full sm:max-w-md px-10 min-h-screen flex flex-col text-center">
			{#if ($config?.features.auth_trusted_header ?? false) || $config?.features.auth === false}
				<div class=" my-auto pb-10 w-full">
					<div
						class="flex items-center justify-center gap-3 text-xl sm:text-2xl text-center font-semibold dark:text-gray-200"
					>
						<div>
							{$i18n.t('Signing in')}
							{$i18n.t('to')}
							{$WEBUI_NAME}
						</div>

						<div>
							<Spinner />
						</div>
					</div>
				</div>
			{:else}
				<div class=" my-auto pb-10 w-full dark:text-gray-100">
					<form
						class=" flex flex-col justify-center"
						on:submit|preventDefault={() => {
							submitHandler();
						}}
					>
						<div class="mb-1">
							<div class=" text-2xl font-medium">
								{$i18n.t('Sign in')}
								{$i18n.t('to')}
								{$WEBUI_NAME}
							</div>
						</div>

						<div class="flex flex-col mt-4">
							<div class="mb-2">
								<div class=" text-sm font-medium text-left mb-1">{$i18n.t('Email')}</div>
								<input
									bind:value={email}
									type="email"
									class=" px-5 py-3 rounded-2xl w-full text-sm outline-none border dark:border-none dark:bg-gray-900"
									autocomplete="email"
									placeholder={$i18n.t('Enter Your Email')}
									required
								/>
							</div>

							<div>
								<div class=" text-sm font-medium text-left mb-1">{$i18n.t('Password')}</div>

								<input
									bind:value={password}
									type="password"
									class=" px-5 py-3 rounded-2xl w-full text-sm outline-none border dark:border-none dark:bg-gray-900"
									placeholder={$i18n.t('Enter Your Password')}
									autocomplete="current-password"
									required
								/>
							</div>
						</div>

						<div class="mt-5">
							<button
								class=" bg-gray-900 hover:bg-gray-800 w-full rounded-2xl text-white font-medium text-sm py-3 transition"
								type="submit"
							>
								{$i18n.t('Sign in')}
							</button>
						</div>
					</form>
				</div>
			{/if}
		</div>
	</div>
{/if}

<style>
	.font-mona {
		font-family: 'Mona Sans', -apple-system, 'Inter', ui-sans-serif, system-ui, 'Segoe UI', Roboto,
			Ubuntu, Cantarell, 'Noto Sans', sans-serif, 'Helvetica Neue', Arial, 'Apple Color Emoji',
			'Segoe UI Emoji', 'Segoe UI Symbol', 'Noto Color Emoji';
	}
</style>

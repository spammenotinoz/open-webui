<script>
	import { goto } from '$app/navigation';
	import { userSignIn } from '$lib/apis/auths';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import { WEBUI_API_BASE_URL, WEBUI_BASE_URL } from '$lib/constants';
	import { WEBUI_NAME, config, user } from '$lib/stores';
	import { onMount, getContext } from 'svelte';
	import { toast } from 'svelte-toast';

	const i18n = getContext('i18n');

	let loaded = false;
	let email = '';
	let password = '';

	const setSessionUser = async (sessionUser) => {
		if (sessionUser) {
			console.log(sessionUser);
			toast.success(i18n.t(`You're now logged in.`));
			localStorage.token = sessionUser.token;
			await user.set(sessionUser);
			goto('/');
		}
	};

	const signInHandler = async () => {
		const sessionUser = await userSignIn(email, password).catch((error) => {
			toast.error(error);
			return null;
		});

		await setSessionUser(sessionUser);
	};

	onMount(async () => {
		if (user !== undefined) {
			await goto('/');
		}
		loaded = true;
		if ((config?.trusted_header_auth ?? false) || config?.auth === false) {
			await signInHandler();
		}
	});
</script>

<svelte:head>
	<title>{`${WEBUI_NAME}`}</title>
</svelte:head>

{#if loaded}
	<div class="fixed m-10 z-50">
		<div class="flex space-x-2">
			<div class="self-center">
				<img src="{WEBUI_BASE_URL}/static/favicon.png" class="w-8 rounded-full" alt="logo" />
			</div>
		</div>
	</div>

	<div class="bg-white dark:bg-gray-950 min-h-screen w-full flex justify-center font-mona">
		<div class="w-full sm:max-w-md px-10 min-h-screen flex flex-col text-center">
			{#if (config?.trusted_header_auth ?? false) || config?.auth === false}
				<div class="my-auto pb-10 w-full">
					<div class="flex items-center justify-center gap-3 text-xl sm:text-2xl text-center font-bold dark:text-gray-200">
						<div>
							{i18n.t('Signing in to')} {WEBUI_NAME}
						</div>
						<div>
							<Spinner />
						</div>
					</div>
				</div>
			{:else}
				<div class="my-auto pb-10 w-full dark:text-gray-100">
					<form class="flex flex-col justify-center" on:submit|preventDefault={signInHandler}>
						<div class="mb-1">
							<div class="text-2xl font-bold">
								{i18n.t('Sign in to')} {WEBUI_NAME} !! Warning may inadvertently create NSFW Pictures !!
							</div>
						</div>

						<div class="flex flex-col mt-4">
							<div class="mb-2">
								<div class="text-sm font-semibold text-left mb-1">{i18n.t('Email')}</div>
								<input bind:value={email} type="email" class="px-5 py-3 rounded-2xl w-full text-sm outline-none border dark:border-none dark:bg-gray-900" autocomplete="email" placeholder={i18n.t('Enter Your Email')} required />
							</div>

							<div>
								<div class="text-sm font-semibold text-left mb-1">{i18n.t('Password')}</div>
								<input bind:value={password} type="password" class="px-5 py-3 rounded-2xl w-full text-sm outline-none border dark:border-none dark:bg-gray-900" placeholder={i18n.t('Enter Your Password')} autocomplete="current-password" required />
							</div>
						</div>

						<div class="mt-5">
							<button class="bg-gray-900 hover:bg-gray-800 w-full rounded-2xl text-white font-semibold text-sm py-3 transition" type="submit">
								{i18n.t('Sign in')}
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
		font-family: 'Mona Sans', -apple-system, 'Arimo', ui-sans-serif, system-ui, 'Segoe UI', Roboto, Ubuntu, Cantarell, 'Noto Sans', sans-serif, 'Helvetica Neue', Arial, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', 'Noto Color Emoji';
	}
</style>
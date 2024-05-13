<script lang="ts">
	import { Collapsible } from 'bits-ui';

	import { setDefaultModels } from '$lib/apis/configs';
	import { models, showSettings, settings, user } from '$lib/stores';
	import { onMount, tick, getContext } from 'svelte';
	import { toast } from 'svelte-sonner';
	import Selector from './ModelSelector/Selector.svelte';
	import Tooltip from '../common/Tooltip.svelte';

	const i18n = getContext('i18n');

	export let selectedModels = [''];
	export let disabled = false;

	export let showSetDefault = true;

	const saveDefaultModel = async () => {
		const hasEmptyModel = selectedModels.filter((it) => it === '');
		if (hasEmptyModel.length) {
			toast.error($i18n.t('Choose a model before saving...'));
			return;
		}
		settings.set({ ...$settings, models: selectedModels });
		localStorage.setItem('settings', JSON.stringify($settings));

		if ($user.role === 'admin') {
			console.log('setting default models globally');
			await setDefaultModels(localStorage.token, selectedModels.join(','));
		}
		toast.success($i18n.t('Default model updated'));
	};

	$: if (selectedModels.length > 0 && $models.length > 0) {
		selectedModels = selectedModels.map((model) =>
			$models.map((m) => m.id).includes(model) ? model : ''
		);
	}
</script>

<div class="flex flex-col mt-0.5 w-full">
	{#each selectedModels as selectedModel, selectedModelIdx}
		<div class="flex w-full max-w-fit">
			<div class="overflow-hidden w-full">
				<div class="mr-1 max-w-full">
					<Selector
						placeholder={$i18n.t('Select a model')}
						items={$models
							.filter((model) => model.name !== 'hr')
							.map((model) => ({
								value: model.id,
								label: model.name,
								info: model
							}))}
						bind:value={selectedModel}
					/>
				</div>
			</div>



			
		</div>
	{/each}
</div>